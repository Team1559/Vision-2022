#!/usr/bin/python
import subprocess
from typing import *
import cv2
import platform
from socket import *
import zmq
import numpy as np
import ball_finder
import target_finder
import ray


def init(do_hoop=True, do_ball=True) -> NoReturn:
    global is_jetson
    global cpuArch
    global do_hoop_finder
    global do_ball_finder

    do_ball_finder = do_ball
    do_hoop_finder = do_hoop

    is_jetson = False
    cpuArch = platform.uname()[4]
    if cpuArch != "x86_64" and cpuArch != "AMD64":
        is_jetson = True

    if is_jetson:
        subprocess.check_call(["uvcdynctrl", "-s", "White Balance Temperature, Auto", "0"])
        subprocess.check_call(["uvcdynctrl", "-s", "Brightness", "30"])
        subprocess.check_call(["uvcdynctrl", "-s", "Exposure, Auto", "1"])
        subprocess.check_call(["uvcdynctrl", "-s", "Exposure (Absolute)", "5"])


@ray.remote
def get_hoop(hoop_frame: np.ndarray) -> tuple:
    hoop = target_finder.target_finder()
    hd, hf = hoop.find(hoop_frame)
    return hd, hf


@ray.remote
def get_ball(ball_frame: np.ndarray) -> tuple:
    ball = ball_finder.ball_finder()
    bd, bf = ball.find(ball_frame)
    return bd, bf


def main() -> NoReturn:
    s = socket(AF_INET, SOCK_DGRAM)

    context = zmq.Context()
    footage_socket = context.socket(zmq.PUB)
    if is_jetson:
        footage_socket.connect('tcp://10.15.59.5:5555')
        laptop_address = ("10.15.59.2", 5554)
    else:
        footage_socket.connect('tcp://localhost:5555')
        laptop_address = ("localhost", 5554)

    ball_camera = None
    hoop_camera = None
    hoop_frame = np.zeros(shape=(480, 640, 3))
    ball_frame = np.zeros(shape=(480, 640, 3))

    # address = ("169.254.210.151", 5801)

    # dns based address ↓↓↓↓
    # address = ("roborio-1559-frc.local", 5801)
    # ip based address ↓↓↓↓↓
    if do_hoop_finder:
        hoop_camera = cv2.VideoCapture(0)  # ID should be 1
    if do_ball_finder and do_hoop_finder:
        ball_camera = cv2.VideoCapture(1)  # id should be 0
    elif not do_hoop_finder:
        ball_camera = cv2.VideoCapture(0)

    while True:
        try:
            hoop_result = None
            ball_result = None
            if do_ball_finder:
                ball_cam_status, ball_cam_frame = ball_camera.read()
                if not ball_cam_status:
                    print("ball camera error")
                if ball_cam_frame is None:
                    ball_cam_frame = np.zeros(shape=(480, 640, 3))
                ball_detector = get_ball.remote(ball_cam_frame.astype('uint8'))
                ball_data = ray.get(ball_detector)
                ball_result = ball_data[0]
                ball_frame = ball_data[1]

            if do_hoop_finder:
                hoop_cam_status, hoop_cam_frame = hoop_camera.read()
                if not hoop_cam_status:
                    print("hoop camera error")
                if hoop_cam_frame is None:
                    hoop_cam_frame = np.zeros(shape=(480, 640, 3))
                hoop_detector = get_hoop.remote(hoop_cam_frame.astype('uint8'))
                hoop_data = ray.get(hoop_detector)
                hoop_result = hoop_data[0]
                hoop_frame = hoop_data[1]

            if not is_jetson and do_hoop_finder and do_ball_finder and hoop_result is not None and ball_result is not \
                    None:
                print(str(hoop_result) + " <-- Hoop, Ball--> " + str(ball_result))
            elif not is_jetson and do_hoop_finder and hoop_result is not None:
                print(str(hoop_result) + " <-- Hoop")
            if not is_jetson and do_ball_finder and ball_result is not None:
                print("Ball--> " + str(ball_result))

            if do_ball_finder and do_hoop_finder and hoop_result is not None and ball_result is not None:
                send_data(hoop_result[0], hoop_result[1], hoop_result[2], hoop_result[3], ball_result[0],
                          ball_result[1], ball_result[2], ball_result[3], 0)

            elif do_ball_finder and not do_hoop_finder and ball_result is not None:
                send_data(*(False, 0, 0, 0), ball_result[0], ball_result[1], ball_result[2], ball_result[3], 0)

            elif not do_ball_finder and do_hoop_finder and hoop_result is not None:
                send_data(hoop_result[0], hoop_result[1], hoop_result[2], hoop_result[3], *(False, 0, 0, 0), 0)

            if do_hoop_finder and do_ball_finder and hoop_result is not None and ball_result is not None:
                # put both frames side by side
                h1, w1 = hoop_frame.shape[:2]
                h2, w2 = ball_frame.shape[:2]
                # create empty matrix
                vis = np.zeros((max(h1, h2), w1 + w2, 3), np.uint8)
                # combine 2 images
                vis[:h1, :w1, :3] = hoop_frame
                vis[:h2, w1:w1 + w2, :3] = ball_frame
                encoded, buffer = cv2.imencode('.jpg', vis.astype('uint8'))
                footage_socket.send(buffer)
                s.sendto(bytes(str(1), 'utf-8'), laptop_address)

            elif do_ball_finder and not do_hoop_finder and ball_result is not None:
                encoded, buffer = cv2.imencode('.jpg', ball_frame.astype('uint8'))
                footage_socket.send(buffer)
                s.sendto(bytes(str(1), 'utf-8'), laptop_address)

            elif not do_ball_finder and do_hoop_finder and hoop_result is not None:
                encoded, buffer = cv2.imencode('.jpg', hoop_frame.astype('uint8'))
                footage_socket.send(buffer)
                s.sendto(bytes(str(1), 'utf-8'), laptop_address)

        except KeyboardInterrupt:
            s.sendto(bytes(str(-1), 'utf-8'), laptop_address)
            cv2.destroyAllWindows()
            print("exiting")
            exit(69420)


def send(data: str) -> NoReturn:
    s = socket(AF_INET, SOCK_DGRAM)
    s.sendto(bytes(data, 'utf-8'), address)


def send_data(hoop_found: bool, hoop_x: float, hoop_y: float, hoop_angle: float, ball_found: bool, ball_x: float,
              ball_y: float, ball_angle: float, wait_for_other_robot: int) -> NoReturn:
    ball_status = 1 if ball_found else 0
    hoop_status = 1 if hoop_found else 0

    data = '%3.1f %3.1f %3.1f %3.1f %3.1f %3.1f %d %d %d \n' % (hoop_x, hoop_y, hoop_angle, ball_x, ball_y,
                                                                ball_angle, ball_status, hoop_status,
                                                                wait_for_other_robot)
    send(data)


if __name__ == "__main__":
    ray.init()

    is_jetson = False
    cpuArch = ""
    do_hoop_finder = True
    do_ball_finder = True

    address = ("10.15.59.2", 5801)

    init(do_ball=True, do_hoop=False)
    main()

# it works and has multiprocessing now :)
