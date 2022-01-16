#!/usr/bin/python
import subprocess
import cv2
import platform
from socket import *
from datetime import datetime
import zmq
from Vision2022 import ball_finder


def main():

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

    if is_jetson:
        subprocess.check_call(["uvcdynctrl", "-s", "White Balance Temperature, Auto", "0"])
        subprocess.check_call(["uvcdynctrl", "-s", "Brightness", "30"])
        subprocess.check_call(["uvcdynctrl", "-s", "Exposure, Auto", "1"])
        subprocess.check_call(["uvcdynctrl", "-s", "Exposure (Absolute)", "5"])
    if is_jetson:
        camera = cv2.VideoCapture(1)
    else:
        camera = cv2.VideoCapture(0)

    finder = ball_finder.ball_finder(camera)
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
            print("exiting")
            exit(42069)
        # # except Exception as e:
        # #     print(e)
        # except BaseException as e:
        #     print(e)
        #     break


if __name__ == "__main__":
    main()
