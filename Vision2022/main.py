#!/usr/bin/python
import subprocess
from typing import *
import cv2
import platform
from socket import *
from datetime import datetime
import zmq
import numpy as np
from Vision2022 import ball_finder
from Vision2022 import target_finder


def main(do_hoop_finder=True, do_ball_finder=True) -> NoReturn:
    is_jetson = False
    cpuArch = platform.uname()[4]
    if cpuArch != "x86_64" and cpuArch != "AMD64":
        is_jetson = True

    context = zmq.Context()
    footage_socket = context.socket(zmq.PUB)
    if is_jetson:
        footage_socket.connect('tcp://10.15.59.5:5555')
    else:
        footage_socket.connect('tcp://localhost:5555')

    s = socket(AF_INET, SOCK_DGRAM)
    # address = ("169.254.210.151", 5801)

    # dns based address ↓↓↓↓
    # address = ("roborio-1559-frc.local", 5801)
    # ip based address ↓↓↓↓↓
    address = ("10.15.59.2", 5801)

    def send(data: str) -> NoReturn:
        s.sendto(bytes(data, 'utf-8'), address)
        print(data)

    def send_data(hoop_found: bool, hoop_x: float, hoop_y: float, hoop_angle: float, ball_found: bool, ball_x: float,
                  ball_y: float, ball_angle: float, wait_for_other_robot: int) -> NoReturn:
        ball_status = 1 if ball_found else 0
        hoop_status = 1 if hoop_found else 0

        data = '%3.1f %3.1f %3.1f %3.1f %3.1f %3.1f %d %d %d \n' % (hoop_x, hoop_y, hoop_angle, ball_x, ball_y,
                                                                    ball_angle, ball_status, hoop_status,
                                                                    wait_for_other_robot)
        if not is_jetson:
            print(data)
        send(data)

    if is_jetson:
        subprocess.check_call(["uvcdynctrl", "-s", "White Balance Temperature, Auto", "0"])
        subprocess.check_call(["uvcdynctrl", "-s", "Brightness", "30"])
        subprocess.check_call(["uvcdynctrl", "-s", "Exposure, Auto", "1"])
        subprocess.check_call(["uvcdynctrl", "-s", "Exposure (Absolute)", "5"])
    if is_jetson:
        if do_ball_finder:
            ball_camera = cv2.VideoCapture(1)
        if do_hoop_finder:
            hoop_camera = cv2.VideoCapture(2)
    else:
        if do_hoop_finder:
            hoop_camera = cv2.VideoCapture(1)
        if do_ball_finder:
            ball_camera = cv2.VideoCapture(0)
    if do_hoop_finder:
        hoop = target_finder.target_finder(hoop_camera)
    if do_ball_finder:
        ball = ball_finder.ball_finder(ball_camera)

    while 1:

        try:
            start = datetime.now()
            if do_hoop_finder:
                hoop_result, hoop_frame = hoop.find()
            if do_ball_finder:
                ball_result, ball_frame = ball.find()

            end = datetime.now()
            timeElapsed = end - start

            if do_ball_finder and do_hoop_finder:
                send_data(*hoop_result, *ball_result, 0)

            elif do_ball_finder and not do_hoop_finder:
                send_data(*(False, 0, 0, 0), *ball_result, 0)

            elif not do_ball_finder and do_hoop_finder:
                send_data(*hoop_result, *(False, 0, 0, 0), 0)

            if do_hoop_finder and do_ball_finder:
                # put both frames side by side
                h1, w1 = hoop_frame.shape[:2]
                h2, w2 = ball_frame.shape[:2]
                # create empty matrix
                vis = np.zeros((max(h1, h2), w1 + w2, 3), np.uint8)
                # combine 2 images
                vis[:h1, :w1, :3] = hoop_frame
                vis[:h2, w1:w1 + w2, :3] = ball_frame
                encoded, buffer = cv2.imencode('.jpg', vis)
                footage_socket.send(buffer)

            elif do_ball_finder and not do_hoop_finder:
                encoded, buffer = cv2.imencode('.jpg', ball_frame)
                footage_socket.send(buffer)

            elif not do_ball_finder and do_hoop_finder:
                encoded, buffer = cv2.imencode('.jpg', hoop_frame)
                footage_socket.send(buffer)

        except KeyboardInterrupt:
            if do_ball_finder:
                ball_camera.release()
            if do_hoop_finder:
                hoop_camera.release()
            cv2.destroyAllWindows()
            print("exiting")
            exit(42069)


if __name__ == "__main__":
    main(do_hoop_finder=True, do_ball_finder=True)
