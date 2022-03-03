import cv2
import numpy as np
from socket import *

SCALE = 0.8

def main():
    s = socket(AF_INET, SOCK_DGRAM)
    s.bind(('', 1180))

    while True:
        try:
            data = s.recv(32768)
            print(len(data))
            npimg = np.frombuffer(data, dtype=np.uint8)
            frame = cv2.imdecode(npimg, 1)
            frame = cv2.resize(frame, (int(640 * SCALE), int(480 * 2 * SCALE)), interpolation=cv2.INTER_LINEAR )
            cv2.imshow("Stream", frame)
            cv2.waitKey(1)

        except KeyboardInterrupt:
            print("exiting cuz of keyboard press")
            leave()


def leave():
    cv2.destroyAllWindows()
    exit(69420)


if __name__ == "__main__":
    main()