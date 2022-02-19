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
import sys

CAMERA_PATH = "/dev/v4l/by-path/"

BALL_CAMERA_ID = CAMERA_PATH + "platform-70090000.xusb-usb-0:4.4:1.0-video-index0"
HOOP_CAMERA_ID = CAMERA_PATH + "platform-70090000.xusb-usb-0:4.3:1.0-video-index0"

def init():
    global is_jetson
    global cpuArch
    global ball_camera
    global hoop_camera
    try:
        ball_camera = cv2.VideoCapture(0)
    except:
        print("Ball camera not found")
    hoop_camera = None
def get_ball(ball_frame):
    ball = ball_finder.ball_finder()
    bd, bf = ball.find(ball_frame)
    return bd, bf

def main():
    global ball_camera
    hoop_frame = np.zeros(shape=(480, 640, 3))
    ball_frame = np.zeros(shape=(480, 640, 3))

    while True:
        try:
            hoop_result = None
            ball_result = None
            elapsed = ""

            if True: # find ball
                ball_cam_status, ball_cam_frame = ball_camera.read()
                if not ball_cam_status:
                    print("ball camera error")
                if ball_cam_frame is None:
                    ball_cam_frame = np.zeros(shape=(480, 640, 3))
                start_time = time.time()
                end_time = time.time()
                elapsedBall = " " + str(round(1000 * (end_time - start_time), 1))

                ball_result, ball_frame = get_ball(ball_cam_frame.astype('uint8'))
                
            if ball_result is not None:
                if ball_result[0]:
                    print("Ball--> " + str(ball_result) + elapsedBall)

            if "show" in sys.argv:
                cv2.imshow("DriverStation", ball_frame)

            cv2.waitKey(1)
        except KeyboardInterrupt:
            time.sleep(0.25)
            cv2.destroyAllWindows()
            print("exiting")
            exit(69420)

try:
    init()
    main()
except KeyboardInterrupt:
    # status(-1)
    time.sleep(0.25)
    cv2.destroyAllWindows()
    print("exiting")
    exit(69420)
