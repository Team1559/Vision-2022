import cv2
import numpy as np
import sys

FONT = cv2.FONT_HERSHEY_SIMPLEX

frameCount = 0

class ball_finder(object):

    def __init__(self):
        pass

    def set_color(self, color):
        pass

    def acquireImage(self, data):
        frame = data
        self.height, self.width = frame.shape[:2]
        return frame

    def find(self, data):
        frame = self.acquireImage(data)
        # global frameCount
        # frameCount += 1
        # if frameCount % 100 == 0:
        #     cv2.imwrite("/home/frc1559/frames/ball{}.jpg".format(frameCount), frame)
        return (False, 0, 0, 0), output


if __name__ == "__main__":
    print("This file is a library please run the main.py to get the output")
    exit(42069)
