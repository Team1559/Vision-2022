#!/usr/bin/python
import targetFinder2022
# import HatchFinder2019
import usb
from socket import *
import os
import subprocess
from datetime import datetime

s = socket(AF_INET, SOCK_DGRAM)
# address = ("169.254.210.151", 5801)
# address = ("roborio-1559-frc.local", 5801)
address = ("10.15.59.2", 5801)


def send(data):
    s.sendto(data, address)


def sendErrorValues(found, x, y, angle):
    status = 1 if found else 0
    data = '%3.1f %3.1f %3.1f %d \n' % (x, y, angle, status)
    print(data)
    send(data)


subprocess.check_call(["uvcdynctrl", "-s", "White Balance Temperature, Auto", "0"])
subprocess.check_call(["uvcdynctrl", "-s", "Brightness", "30"])
subprocess.check_call(["uvcdynctrl", "-s", "Exposure, Auto", "1"])
subprocess.check_call(["uvcdynctrl", "-s", "Exposure (Absolute)", "5"])
camera = usb.USBCamera(1, 800, 448)

finder = targetFinder2019.targetFinder(camera)
# finder = HatchFinder2019.hatchFinder(camera)
while 1:
    start = datetime.now()
    result = finder.find()
    end = datetime.now()
    timeElapsed = end - start
    # print timeElapsed.total_seconds()
    # print result
    sendErrorValues(*result)
