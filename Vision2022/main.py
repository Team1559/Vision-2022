#!/usr/bin/python
import subprocess
import cv2
import platform
from socket import *
# import zmq
import numpy as np
import ball_finder
import target_finder
import time


CAMERA_PATH = "/dev/v4l/by-path/"

BALL_CAMERA_ID = CAMERA_PATH + "platform-70090000.xusb-usb-0:4.4:1.0-video-index0"
HOOP_CAMERA_ID = CAMERA_PATH + "platform-70090000.xusb-usb-0:4.3:1.0-video-index0"

def init(do_hoop=True, do_ball=True):
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
        # Both

        subprocess.check_call(["uvcdynctrl", "-s", "Sharpness", "128"])
        subprocess.check_call(["uvcdynctrl", "-s", "Contrast", "128"])
        subprocess.check_call(["uvcdynctrl", "-s", "Exposure, Auto", "2"])

        # Hoop stuff
        subprocess.check_call(["uvcdynctrl", "-s", "White Balance Temperature", "6500"])
        subprocess.check_call(["uvcdynctrl", "-s", "White Balance Temperature, Auto", "0"])
        subprocess.check_call(["uvcdynctrl", "-s", "Brightness", "1"])
        subprocess.check_call(["uvcdynctrl", "-s", "Exposure (Absolute)", "5"])

        # Ball stuff
        # subprocess.check_call(["uvcdynctrl", "-s", "White Balance Temperature", "4659"])
        # subprocess.check_call(["uvcdynctrl", "-s", "White Balance Temperature, Auto", "0"])
        # subprocess.check_call(["uvcdynctrl", "-s", "Brightness", "128"])
        # subprocess.check_call(["uvcdynctrl", "-s", "Sharpness", "128"])
        # subprocess.check_call(["uvcdynctrl", "-s", "Contrast", "128"])
        # subprocess.check_call(["uvcdynctrl", "-s", "Exposure, Auto", "2"])
        # subprocess.check_call(["uvcdynctrl", "-s", "Exposure (Absolute)", "1800"])

        # print(subprocess.check_output(["uvcdynctrl", "-g", "Brightness"]))
        # print(subprocess.check_output(["uvcdynctrl", "-g", "Exposure (Absolute)"]))

def get_hoop(hoop_frame):
    hoop = target_finder.target_finder()
    hd, hf = hoop.find(hoop_frame)
    return hd, hf
def get_ball(ball_frame):
    ball = ball_finder.ball_finder()
    bd, bf = ball.find(ball_frame)
    return bd, bf

def main():
    s = socket(AF_INET, SOCK_DGRAM)

    ball_camera = None
    hoop_camera = None
    hoop_frame = np.zeros(shape=(480, 640, 3))
    ball_frame = np.zeros(shape=(480, 640, 3))


    if do_hoop_finder:
        hoop_camera = cv2.VideoCapture(HOOP_CAMERA_ID)  # ID should be 1
    if do_ball_finder and do_hoop_finder:
        ball_camera = cv2.VideoCapture(BALL_CAMERA_ID)  # id should be 0
    elif not do_hoop_finder:
        ball_camera = cv2.VideoCapture(BALL_CAMERA_ID)

    # ball_camera.set(cv2.CAP_PROP_EXPOSURE, -1)
    # ball_camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)

    while True:
        try:
            hoop_result = None
            ball_result = None
            elapsed = ""

            if do_ball_finder:
                ball_cam_status, ball_cam_frame = ball_camera.read()
                if not ball_cam_status:
                    print("ball camera error")
                if ball_cam_frame is None:
                    ball_cam_frame = np.zeros(shape=(480, 640, 3))
                start_time = time.time()
                ball_detector = get_ball(ball_cam_frame.astype('uint8'))
                end_time = time.time()
                elapsedBall = " " + str(round(1000 * (end_time - start_time), 1))

                ball_data = ball_detector
                ball_result = ball_data[0]
                ball_frame = ball_data[1]

            if do_hoop_finder:
                hoop_cam_status, hoop_cam_frame = hoop_camera.read()
                if not hoop_cam_status:
                    print("hoop camera error")
                if hoop_cam_frame is None:
                    hoop_cam_frame = np.zeros(shape=(480, 640, 3))
                start_time = time.time()
                hoop_detector = get_hoop(hoop_cam_frame.astype('uint8'))
                end_time = time.time()
                elapsedHoop = " " + str(round(1000 * (end_time - start_time), 1))
                hoop_data = hoop_detector
                hoop_result = hoop_data[0]
                hoop_frame = hoop_data[1]

            if do_hoop_finder and do_ball_finder and hoop_result is not None and ball_result is not \
                    None:
                print(str(hoop_result) + elapsedHoop + " <-- Hoop, Ball--> " + str(ball_result) + elapsedBall)
            elif not is_jetson and do_hoop_finder and hoop_result is not None:
                print(str(hoop_result) + elapsedHoop + " <-- Hoop" + elapsedBall)
            elif not is_jetson and do_ball_finder and ball_result is not None:
                if ball_result[0]:
                    print("Ball--> " + str(ball_result) + elapsedBall)
            #if ball_result and ball_result[0] :
            #    print("Ball--> " + str(ball_result) + elapsedBall)
            if do_ball_finder and do_hoop_finder and hoop_result is not None and ball_result is not None:
                send_data(hoop_result[0], hoop_result[1], hoop_result[2], 0, ball_result[0],
                          ball_result[1], ball_result[2], ball_result[3], 0)

            elif do_ball_finder and not do_hoop_finder and ball_result is not None:
                send_data(False, 0, 0, 0, ball_result[0], ball_result[1], ball_result[2], ball_result[3], 0)

            elif not do_ball_finder and do_hoop_finder and hoop_result is not None:
                send_data(hoop_result[0], hoop_result[1], hoop_result[2], 0, False, 0, 0, 0, 0)

            if do_hoop_finder and do_ball_finder and hoop_result is not None and ball_result is not None:
                new_Hoop_Frame = cv2.resize(hoop_frame, None, fx = 0.25, fy = 0.25)
                new_Ball_Frame = cv2.resize(ball_frame, None, fx = 0.25, fy = 0.25)

                vis = np.vstack((new_Hoop_Frame, new_Ball_Frame))

                encoded, buffer = cv2.imencode('.jpg', vis.astype('uint8'))
                # footage_socket.send(buffer)
                # status(1)

            elif do_ball_finder and not do_hoop_finder and ball_result is not None:
                encoded, buffer = cv2.imencode('.jpg', ball_frame.astype('uint8'))
                # footage_socket.send(buffer)
                # status(1)

            elif not do_ball_finder and do_hoop_finder and hoop_result is not None:
                encoded, buffer = cv2.imencode('.jpg', hoop_frame.astype('uint8'))
                # footage_socket.send(buffer)
                # status(1)
            cv2.waitKey(1)

        except KeyboardInterrupt:
            # status(-1)
            time.sleep(0.25)
            cv2.destroyAllWindows()
            print("exiting")
            exit(69420)


def send(data):
    s = socket(AF_INET, SOCK_DGRAM)
    s.sendto(data.encode('utf-8'), address)


def send_data(hoop_found, hoop_x, hoop_y, hoop_angle, ball_found, ball_x,
              ball_y, ball_angle, wait_for_other_robot):
    ball_status = 1 if ball_found else 0
    hoop_status = 1 if hoop_found else 0

    data = '%3.1f %3.1f %3.1f %3.1f %3.1f %3.1f %d %d %d \n' % (hoop_x, hoop_y, hoop_angle, ball_x, ball_y,
                                                                ball_angle, ball_status, hoop_status,
                                                                wait_for_other_robot)
    send(data)
    if is_jetson:
        pass
        # print(data)


def status(data):
    s = socket(AF_INET, SOCK_DGRAM)
    if is_jetson:
        laptop_address = ("10.15.59.2", 5554)
    else:
        laptop_address = ("localhost", 5554)
        s.sendto(data.encode('utf-8'), laptop_address)


if __name__ == "__main__":
    try:

        is_jetson = False
        cpuArch = ""
        do_hoop_finder = True
        do_ball_finder = True

        address = ("10.15.59.2", 5801)

        init(do_ball=do_ball_finder, do_hoop=do_hoop_finder)
        main()

    except KeyboardInterrupt:
        # status(-1)
        time.sleep(0.25)
        cv2.destroyAllWindows()
        print("exiting")
        exit(69420)
# it works and has multiprocessing now :)
