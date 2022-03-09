import cv2
import numpy as np
from socket import *

SCALE = 2


def main():
    no_data_frames = 0
    s = socket(AF_INET, SOCK_DGRAM)
    s.bind(('', 1180))
    s.setblocking(True)
    s.settimeout(1)

    while True:
        try:
            try:
                data = s.recv(32768)
            except error:
                data = None

            if data is not None:
                np_img = np.frombuffer(data, dtype=np.uint8)
                frame = cv2.imdecode(np_img, 1)
                frame = cv2.resize(frame, (int(640 * 2 * SCALE), int(480 * SCALE)), interpolation=cv2.INTER_LINEAR)
                cv2.imshow("Jetson Camera Stream", frame)
                cv2.waitKey(1)
            else:
                text = "FIN :("
                no_data_frames += 1
                frame = np.zeros(shape=(int(640 * 2 * SCALE), int(480 * SCALE), 3))
                cv2.putText(frame, text, (int(420 * SCALE), int(320 * SCALE)), cv2.FONT_HERSHEY_SIMPLEX, 1,
                            (255, 255, 255), 2, 2)
                cv2.imshow("Jetson Camera Stream", frame)
                cv2.waitKey(1)

        except KeyboardInterrupt:
            print("exiting cuz of keyboard press")
            leave()


def leave():
    cv2.destroyAllWindows()
    exit(69420)


if __name__ == "__main__":
    main()
