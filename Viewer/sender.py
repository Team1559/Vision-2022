import cv2
import numpy as np
from socket import *

destination = ('localhost', 5800)

def main():
    cap = cv2.VideoCapture(0)
    s = socket(AF_INET, SOCK_DGRAM)

    while True:
        try:
            ok, frame = cap.read()
            if not ok:
                print("exiting because of camera error")
                break
            cv2.imshow("Source", frame)
            frame = cv2.resize(frame, (160, 120))
            encoded, buffer = cv2.imencode('.jpg', frame)
            print(len(buffer))
            s.sendto(buffer, destination)
            cv2.waitKey(1)

        except KeyboardInterrupt:
            print("exiting cuz of keyboard press")
            leave()


def leave():
    cv2.destroyAllWindows()
    exit(69420)


if __name__ == "__main__":
    main()
