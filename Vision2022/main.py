#!/usr/bin/python
import cv2
import platform
from socket import *
import numpy as np
import ball_finder
import target_finder
import time
import sys

TEAM = "red"

CAMERA_PATH = "/dev/v4l/by-path/"
# With hub
# BALL_CAMERA_ID = CAMERA_PATH + "platform-3530000.xhci-usb-0:2.4:1.0-video-index0"
# HOOP_CAMERA_ID = CAMERA_PATH + "platform-3530000.xhci-usb-0:2.3:1.0-video-index0"

# Without hub
BALL_CAMERA_ID = CAMERA_PATH + "platform-3530000.xhci-usb-0:2:1.0-video-index0"
HOOP_CAMERA_ID = CAMERA_PATH + "platform-3530000.xhci-usb-0:3:1.0-video-index0"

s = socket(AF_INET, SOCK_DGRAM)

address = ("10.15.59.2", 5801)

do_ball_finder = do_hoop_finder = True
elapsedBall = 0
elapsedHoop = 0
UDP_PORT = 5005
sock = socket(AF_INET, SOCK_DGRAM)
sock.bind(("", UDP_PORT))
sock.setblocking(False)

color = "Invalid"

is_jetson = False
cpuArch = platform.uname()[4]
if cpuArch != "x86_64" and cpuArch != "AMD64":
    is_jetson = True

if is_jetson:
    # Brightness not set for ball camera?
    # CAP_PROP_SATURATION not set for either camera?
    ball_camera = None
    try:
        ball_camera = cv2.VideoCapture(BALL_CAMERA_ID)
    except error:
        print("Ball camera not found")
    hoop_camera = None
    try:
        hoop_camera = cv2.VideoCapture(HOOP_CAMERA_ID)
    except error:
        print("Hoop camera not found")

    ball_camera_props = {
        cv2.CAP_PROP_TEMPERATURE: 4659,
        cv2.CAP_PROP_AUTO_EXPOSURE: 0,
        cv2.CAP_PROP_BRIGHTNESS: 96,
    }

    both = {
        cv2.CAP_PROP_CONTRAST: 128,
        cv2.CAP_PROP_AUTO_WB: 0
    }

    hoop_camera_props = {
        cv2.CAP_PROP_EXPOSURE: 5,
        cv2.CAP_PROP_AUTO_EXPOSURE: 2,
        cv2.CAP_PROP_TEMPERATURE: 6500,
        cv2.CAP_PROP_BRIGHTNESS: 1
    }
    for prop, value in both.items():
        ball_camera.set(prop, value)
        hoop_camera.set(prop, value)
    for prop, value in ball_camera_props.items():
        ball_camera.set(prop, value)
    for prop, value in hoop_camera_props.items():
        hoop_camera.set(prop, value)

hoop_locator = target_finder.target_finder()


def get_hoop(hoop_frame):
    hd, hf = hoop_locator.find(hoop_frame)
    return hd, hf


ball_locator = ball_finder.ball_finder()


def get_ball(ball_frame):
    ball_locator.set_color(color)
    bd, bf = ball_locator.find(ball_frame)
    return bd, bf


def main():
    global ball_camera, elapsedHoop, elapsedBall
    global hoop_camera
    hoop_frame = np.zeros(shape=(480, 640, 3))
    ball_frame = np.zeros(shape=(480, 640, 3))

    while True:
        receive()
        try:
            hoop_result = None
            ball_result = None
            if do_ball_finder:  # find ball
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

            if do_hoop_finder:  # find hoop
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
                # print(str(hoop_result) + elapsedHoop + " <-- Hoop, Ball--> " + str(ball_result) + elapsedBall)
                send_data(hoop_result[0], hoop_result[1], hoop_result[2], 0, ball_result[0], ball_result[1],
                          ball_result[2], ball_result[3], 0)
                # Python 3:send_data(*hoop_result[:3], 0, *ball_result[:4], 0)
            elif ball_result is not None:
                if ball_result[0]:
                    #  print("Ball--> " + str(ball_result) + elapsedBall)
                    send_data(False, 0, 0, 0, ball_result[0], ball_result[1], ball_result[2], ball_result[3], 0)
            elif hoop_result is not None:
                # print(str(hoop_result) + elapsedHoop + " <-- Hoop")
                send_data(hoop_result[0], hoop_result[1], hoop_result[2], 0, False, 0, 0, 0, 0)

            # stream images depending on result, also should change
            imageHeight = 480
            imageWidth = 640
            THICKNESS = 6
            HOOP_COLOR = (255, 255, 255)
            BALL_COLOR = (255, 255, 255)
            cv2.line(hoop_frame, ((imageWidth / 2) - 20, imageHeight * 1 / 3),
                     (imageWidth / 2 + 20, imageHeight * 1 / 3),
                     HOOP_COLOR, THICKNESS)
            cv2.line(hoop_frame, ((imageWidth / 2), imageHeight * 1 / 3 - 20),
                     (imageWidth / 2, imageHeight * 1 / 3 + 20),
                     HOOP_COLOR, THICKNESS)
            cv2.line(ball_frame, ((imageWidth / 2) - 20, imageHeight * 4 / 5),
                     (imageWidth / 2 + 20, imageHeight * 4 / 5),
                     BALL_COLOR, THICKNESS)
            cv2.line(ball_frame, ((imageWidth / 2), imageHeight * 4 / 5 - 20),
                     (imageWidth / 2, imageHeight * 4 / 5 + 20),
                     BALL_COLOR, THICKNESS)
            vis = np.hstack(
                (cv2.resize(hoop_frame, None, fx=0.5, fy=0.5), cv2.resize(ball_frame, None, fx=0.5, fy=0.5)))
            if "show" in sys.argv:
                cv2.imshow("DriverStation", np.hstack((hoop_frame, ball_frame)))
            encoded, buffer = cv2.imencode('.jpg', vis, [cv2.IMWRITE_JPEG_QUALITY, 22])
            s.sendto(buffer, ("10.15.59.46", 1180))

            cv2.waitKey(1)
        except KeyboardInterrupt:
            time.sleep(0.25)
            cv2.destroyAllWindows()
            print("exiting")
            exit(69420)


# Data sending stuff
def send_data(hoop_found, hoop_x, hoop_y, hoop_angle, ball_found, ball_x, ball_y, ball_angle, wait_for_other_robot):
    data = '%3.1f %3.1f %3.1f %3.1f %3.1f %3.1f %d %d %d \n' % (
        hoop_x, hoop_y, hoop_angle, ball_x, ball_y, ball_angle, int(hoop_found), int(ball_found), wait_for_other_robot)

    s.sendto(data.encode('utf-8'), address)
# def send_data(one, two, three, four, five, six, seven, eight, nine):
#     data = '%3.1f %3.1f %3.1f %3.1f %3.1f %3.1f %d %d %d \n' % (
#         two, three, four, six, seven, eight, int(one), int(five), nine)

#     s.sendto(data.encode('utf-8'), address)


def receive():
    global color
    global sock
    try:
        data, sender = sock.recvfrom(1024)  # buffer size is 1024 bytes
        if data is not None:
            color = data.decode('utf-8')
    except error:
        pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # status(-1)
        time.sleep(0.25)
        sock.close()
        cv2.destroyAllWindows()
        print("exiting")
        exit(69420)
# This is a update for the software testing
# We attempted to try and measure the distance from the shooter to the camera but we are failing a lot.
# we went to
