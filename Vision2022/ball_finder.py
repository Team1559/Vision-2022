from typing import *
import cv2
import numpy as np
import sys


class ball_finder(object):

    def __init__(self, Camera: cv2.VideoCapture) -> NoReturn:
        """Initialize camera"""
        self.camera = Camera
        # BRIGHTNESS AT 30 for perfect, 85 for driver station
        self.cx = -1
        self.cy = -1
        self.err = -1000
        # NOOOOOOOO BGR, BGR bad
        blue_low = np.array((105, 75, 60))
        blue_high = np.array((115, 250, 255))
        self.hsvl = blue_low
        self.hsvh = blue_high
        self.show = "show" in sys.argv
        # self.width = 800
        # self.height = 488
        self.width = 0
        self.height = 0

        self.found = False

        self.minarea = 10  # 100

    def acquireImage(self) -> np.ndarray:

        success, frame = self.camera.read()
        if not success:
            exit(222)
        self.height, self.width = frame.shape[:2]
        return frame

    def preImageProcessing(self, frame) -> np.ndarray:
        # convert to hsv
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # blur me
        hsv = cv2.blur(hsv, (5, 5))

        thresh = cv2.inRange(hsv, self.hsvl, self.hsvh)
        # erode and dilate
        thresh = cv2.erode(thresh, (14, 14))
        thresh = cv2.dilate(thresh, (14, 14))

        return thresh

    def findTargets(self, frame, thresh) -> np.ndarray:
        filtered = cv2.bitwise_and(frame, frame, mask=thresh)
        if self.show:
            cv2.imshow("Color filtered", filtered)
        cv2.waitKey(1)

        circles = cv2.HoughCircles(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.HOUGH_GRADIENT, 1, 75, param1=90,
                                   param2=20, minRadius=1, maxRadius=100)
        output = frame.copy()
        # ensure at least some circles were found
        if circles is not None:
            # convert the (x, y) coordinates and radius of the circles to integers
            circles = np.round(circles[0, :]).astype("int")
            # loop over the (x, y) coordinates and radius of the circles
            ball = None
            maxRadius = 0
            for (x, y, r) in circles:
                try:
                    if filtered[y][x][2] > 0:
                        if r > maxRadius:
                            ball = (x, y, r)
                            maxRadius = r
                except IndexError:
                    pass
            if ball is not None:
                cv2.circle(output, (ball[0], ball[1]), ball[2], (0, 255, 0), 4)

        if self.show:
            cv2.imshow("Circles", output)
            cv2.waitKey(1)
        return circles
        # return rectangles.sort()

    def findCentroid(self, rectangles) -> np.ndarray:
        centers = np.array([r[0] for r in rectangles])
        centroid = np.mean(centers, axis=0)
        return centroid

    def find(self) -> tuple:
        frame = self.acquireImage()
        thresh = self.preImageProcessing(frame)

        if self.show:
            cv2.imshow("Thresh", thresh)
            cv2.waitKey(1)

        targets = self.findTargets(frame, thresh)
        if self.show:
            cv2.imshow("Unfiltered", frame)
            cv2.waitKey(1)
        return (10, 10, 10, 0), frame


if __name__ == "__main__":
    print("This file is a library please run the correct file to get the output")
    exit(42069)
