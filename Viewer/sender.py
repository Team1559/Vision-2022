import cv2
import numpy as np
from socket import *

destination = ('10.15.59.46', 1180)

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
            frame = cv2.resize(frame, (320, 240))
            encoded, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 30])
            print(len(buffer))
            s.sendto(buffer, destination)
            cv2.waitKey(1)

        except KeyboardInterrupt:
            print("exiting cuz of keyboard press")
            leave()
        except Exception as e:
            print(e)
        except:
            print("Unknown Error")

def leave():
    cv2.destroyAllWindows()
    exit(69420)


if __name__ == "__main__":
    main()
