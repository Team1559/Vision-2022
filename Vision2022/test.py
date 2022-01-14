import numpy as np
import cv2

captureDevice = cv2.VideoCapture(0) #captureDevice = camera

while True:
    ret, frame = captureDevice.read()

    cv2.imshow('my frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

captureDevice.release()
cv2.destroyAllWindows()