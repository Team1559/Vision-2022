import cv2
import zmq
import numpy as np
from socket import *


def main(exit_when_stream_dies=True):
    context = zmq.Context()
    s = socket(AF_INET, SOCK_DGRAM)
    s.bind(('localhost', 5554))
    footage_socket = context.socket(zmq.SUB)
    footage_socket.bind('tcp://*:5555')
    footage_socket.setsockopt_string(zmq.SUBSCRIBE, np.compat.unicode(''))

    while True:
        try:

            data = (s.recv(1024).decode('utf8'))
            if data != '1' and exit_when_stream_dies:
                print("exiting cuz the stream died")
                leave()
            old_data = data
            frame = footage_socket.recv()
            npimg = np.frombuffer(frame, dtype=np.uint8)
            # npimg = npimg.reshape(480,640,3)
            source = cv2.imdecode(npimg, 1)
            cv2.imshow("Stream", source)
            cv2.waitKey(1)

        except KeyboardInterrupt:
            print("exiting cuz of keyboard press")
            leave()


def leave():
    cv2.destroyAllWindows()
    exit(69420)


if __name__ == "__main__":
    main(exit_when_stream_dies=True)
