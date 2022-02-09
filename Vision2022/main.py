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

s = socket(AF_INET, SOCK_DGRAM)

address = ("10.15.59.2", 5801)

do_ball_finder = do_hoop_finder = True

def init():
    global is_jetson
    global cpuArch
    is_jetson = False
    cpuArch = platform.uname()[4]
    if cpuArch != "x86_64" and cpuArch != "AMD64":
        is_jetson = True

    if is_jetson:
        # brightness not set for ball camera?
        # CAP_PROP_SATURATION not set for either camera?
        ball_camera_props = {
            "CAP_PROP_EXPOSURE": 1800,
            "CAP_PROP_WB_TEMPERATURE": 4659
        }
        both = {
            "CAP_PROP_SHARPNESS": 128,
            "CAP_PROP_CONTRAST": 128,
            "CAP_PROP_AUTO_EXPOSURE": 2,
            "CAP_PROP_AUTO_WB": 0
        }
        hoop_camera_props = {
            "CAP_PROP_EXPOSURE": 5,
            "CAP_PROP_WB_TEMPERATURE": 6500,
            "CAP_PROP_BRIGHTNESS": 1
        }
        for prop, value in both.items():
            ball_camera.set(prop, value)
            hoop_camera.set(prop, value)
        for prop, value in ball_camera_props.items(): # may need to be adjusted for python2
            ball_camera.set(prop, value)
        for prop, value in hoop_camera_props.items():
            hoop_camera.set(prop, value)

        # Both cameras
        # subprocess.check_call(["uvcdynctrl", "-s", "Sharpness", "128"])
        # subprocess.check_call(["uvcdynctrl", "-s", "Contrast", "128"])
        # subprocess.check_call(["uvcdynctrl", "-s", "Exposure, Auto", "2"])
        # subprocess.check_call(["uvcdynctrl", "-s", "White Balance Temperature, Auto", "0"])

        # Hoop stuff
        # subprocess.check_call(["uvcdynctrl", "-s", "White Balance Temperature", "6500"])
        # subprocess.check_call(["uvcdynctrl", "-s", "Brightness", "1"])
        # subprocess.check_call(["uvcdynctrl", "-s", "Exposure (Absolute)", "5"])

        # Ball stuff
        # subprocess.check_call(["uvcdynctrl", "-s", "White Balance Temperature", "4659"])
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

    ball_camera = None
    try:
        ball_camera = cv2.VideoCapture(BALL_CAMERA_ID)
    except:
        print("Ball camera not found")
    hoop_camera = None
    try:
        hoop_camera = cv2.VideoCapture(HOOP_CAMERA_ID)
    except:
        print("Hoop camera not found")
    hoop_frame = np.zeros(shape=(480, 640, 3))
    ball_frame = np.zeros(shape=(480, 640, 3))

    while True:
        try:
            hoop_result = None
            ball_result = None
            elapsed = ""

            if do_ball_finder: # find ball
                ball_cam_status, ball_cam_frame = ball_camera.read()
                if not ball_cam_status:
                    print("ball camera error")
                if ball_cam_frame is None:
                    ball_cam_frame = np.zeros(shape=(480, 640, 3))
                start_time = time.time()
                ball_data = get_ball(ball_cam_frame.astype('uint8'))
                end_time = time.time()
                elapsedBall = " " + str(round(1000 * (end_time - start_time), 1))

                ball_result, ball_frame = ball_data

            if do_hoop_finder: # find hoop
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
                hoop_result, hoop_frame = hoop_data

            # Print and send depending on which results we got, probably should change
            if hoop_result is not None and ball_result is not None:
                print(str(hoop_result) + elapsedHoop + " <-- Hoop, Ball--> " + str(ball_result) + elapsedBall)
                send_data(hoop_result[0], hoop_result[1], hoop_result[2], 0, ball_result[0], ball_result[1], ball_result[2], ball_result[3], 0)
                # Python 3:send_data(*hoop_result[:3], 0, *ball_result[:4], 0)
            elif ball_result is not None:
                if ball_result[0]:
                    print("Ball--> " + str(ball_result) + elapsedBall)
                send_data(False, 0, 0, 0, ball_result[0], ball_result[1], ball_result[2], ball_result[3], 0)
            elif hoop_result is not None:
                print(str(hoop_result) + elapsedHoop + " <-- Hoop")
                send_data(hoop_result[0], hoop_result[1], hoop_result[2], 0, False, 0, 0, 0, 0)

            #stream images depending on result, also should change
            if hoop_result is not None and ball_result is not None:
                imageHeight = 480
                imageWidth = 640
                THICKNESS = 4
                HOOP_COLOR = (255, 255, 0)
                BALL_COLOR = (0, 215, 255)
                cv2.line(hoop_frame, ((imageWidth/2)-20, imageHeight/2), (imageWidth/2+20, imageHeight/2), HOOP_COLOR, THICKNESS)
                cv2.line(hoop_frame, ((imageWidth/2), imageHeight/2-20), (imageWidth/2, imageHeight/2+20), HOOP_COLOR, THICKNESS)
                cv2.line(ball_frame, ((imageWidth/2)-20, imageHeight/2), (imageWidth/2+20, imageHeight/2), BALL_COLOR, THICKNESS)
                cv2.line(ball_frame, ((imageWidth/2), imageHeight/2-20), (imageWidth/2, imageHeight/2+20), BALL_COLOR, THICKNESS)
                vis = np.vstack((cv2.resize(hoop_frame, None, fx=0.25, fy=0.25), cv2.resize(ball_frame, None, fx=0.25, fy=0.25)))
                if "show" in sys.argv:
                    cv2.imshow("DriverStation", np.vstack((hoop_frame, ball_frame)))
                encoded, buffer = cv2.imencode('.jpg', vis.astype('uint8'))
                # footage_socket.send(buffer)
                # status(1)
            elif ball_result is not None:
                encoded, buffer = cv2.imencode('.jpg', ball_frame.astype('uint8'))
                # footage_socket.send(buffer)
                # status(1)
            elif hoop_result is not None:
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


# Data sending stuff
def send(data):
    s.sendto(data.encode('utf-8'), address)
def send_data(hoop_found, hoop_x, hoop_y, hoop_angle, ball_found, ball_x, ball_y, ball_angle, wait_for_other_robot):
    data = '%3.1f %3.1f %3.1f %3.1f %3.1f %3.1f %d %d %d \n' % (hoop_x, hoop_y, hoop_angle, ball_x, ball_y, ball_angle, 1 if ball_found else 0, 1 if hoop_found else 0, wait_for_other_robot)
    send(data)
def status(data): #What does this do?
    if is_jetson:
        laptop_address = ("10.15.59.2", 5554)
    else:
        laptop_address = ("localhost", 5554)
        s.sendto(data.encode('utf-8'), laptop_address)


if __name__ == "__main__":
    try:
        init()
        main()
    except KeyboardInterrupt:
        # status(-1)
        time.sleep(0.25)
        cv2.destroyAllWindows()
        print("exiting")
        exit(69420)
