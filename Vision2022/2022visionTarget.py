#!/usr/bin/python
import cv2
import platform
import targetFinder2022
# import HatchFinder2019

from socket import *
import os
import subprocess
from datetime import datetime
import base64
import zmq
import numpy as np
import time
is_jetson = False
cpuArch = platform.uname()[4]
if cpuArch != "x86_64" and cpuArch != "AMD64":
    is_jetson = True

context = zmq.Context()
footage_socket = context.socket(zmq.PUB)
if is_jetson:
    footage_socket.connect('tcp://10.15.59.2:5555')
else:
    footage_socket.connect('tcp://localhost:5555')




s = socket(AF_INET, SOCK_DGRAM)
# address = ("169.254.210.151", 5801)
# address = ("roborio-1559-frc.local", 5801)
address = ("10.15.59.2", 5801)
localhost = ("localhost", 5801)


def send(data):
    if is_jetson:
        s.sendto(bytes(data, 'utf-8'), address)
    else:
        s.sendto(bytes(data, 'utf-8'), localhost)
    print(data)


def send_data(found, x, y, angle):
    status = 1 if found else 0
    data = '%3.1f %3.1f %3.1f %d \n' % (x, y, angle, status)
    print(data)
    send(data)


# subprocess.check_call(["uvcdynctrl", "-s", "White Balance Temperature, Auto", "0"])
# subprocess.check_call(["uvcdynctrl", "-s", "Brightness", "30"])
# subprocess.check_call(["uvcdynctrl", "-s", "Exposure, Auto", "1"])
# subprocess.check_call(["uvcdynctrl", "-s", "Exposure (Absolute)", "5"])
camera = cv2.VideoCapture(0)

finder = targetFinder2022.targetFinder(camera)
# finder = HatchFinder2019.hatchFinder(camera)
print(camera.set(cv2.CAP_PROP_XI_MANUAL_WB, 1))
while 1:

    try:
        start = datetime.now()
        result, frame = finder.find()
        end = datetime.now()
        timeElapsed = end - start
        # print timeElapsed.total_seconds()
        # print(result)
        send_data(*result)

        encoded, buffer = cv2.imencode('.jpg', frame)
        footage_socket.send(buffer)

    except KeyboardInterrupt:
        camera.release()
        cv2.destroyAllWindows()
        break
