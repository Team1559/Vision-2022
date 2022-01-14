import cv2
import zmq
import base64
import numpy as np

context = zmq.Context()
footage_socket = context.socket(zmq.SUB)
footage_socket.bind('tcp://*:5555')
footage_socket.setsockopt_string(zmq.SUBSCRIBE, np.compat.unicode(''))

while True:
    try:
        frame = footage_socket.recv()
        npimg = np.frombuffer(frame, dtype=np.uint8)
        #npimg = npimg.reshape(480,640,3)
        source = cv2.imdecode(npimg, 1)
        cv2.imshow("Stream", source)
        cv2.waitKey(1)

    except KeyboardInterrupt:
        cv2.destroyAllWindows()
        print("exiting")
        exit(69420)
