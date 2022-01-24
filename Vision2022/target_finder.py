from typing import *
import cv2
import numpy as np
import sys


def calculateDistance(centroid_y) -> tuple:
    fov = 45  # degrees
    imageHeight = 480  # pixels
    targetPixelY = centroid_y  # pixels
    cameraHeight = 3  # feet
    targetHeight = 8.67  # feet
    angularOffset = 25  # degrees
    heightDifference = targetHeight - cameraHeight  # feet

    theta = fov / imageHeight * targetPixelY + angularOffset
    d = heightDifference / np.tan(theta)

    return d


def findCentroid(rectangles) -> np.ndarray:
    centers = np.array([r[0] for r in rectangles])
    centroid = np.median(centers, axis=0)
    # print("centroid : " , centroid)
    return centroid


def targetRectangles(rectangles) -> list:
    candidates = []
    for i in range(len(rectangles)):
        target_rectangles = [rectangles[i]]
        ex = abs(findCentroid(target_rectangles)[0])
        candidates.append((ex, target_rectangles))
    # check for candidates then sort by distance from center
    if not candidates:
        return []
    else:
        candidates.sort()
        return [c[1][0] for c in candidates]


class target_finder(object):

    def __init__(self) -> NoReturn:
        """Initialize camera"""
        # BRIGHTNESS AT 30 for perfect, 85 for driver station
        self.color = 0
        self.cx = -1
        self.cy = -1
        self.err = -1000
        # self.hsvl = np.array((70, 50, 60))
        # self.hsvh = np.array((80, 255, 255))
        green_low = np.array([0, 100, 0])
        green_high = np.array([10, 255, 10])
        np.array((20, 0, 0))
        # colors are in the BGR color space
        self.hsvl = green_low
        self.hsvh = green_high
        self.show = "show" in sys.argv
        # self.width = 800
        # self.height = 488
        self.width = 0
        self.height = 0
        self.found = False

        self.minarea = 10  # 100

    def acquireImage(self, data: np.ndarray) -> np.ndarray:

        frame = data
        # exit(222)
        self.height, self.width = frame.shape[:2]
        return frame

    def preImageProcessing(self, frame) -> np.ndarray:
        # convert to hsv
        # hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hsv = frame
        # blur me
        hsv = cv2.blur(hsv, (5, 5))

        thresh = cv2.inRange(hsv, self.hsvl, self.hsvh)

        # erode and dilate
        thresh = cv2.erode(thresh, (7, 7))
        thresh = cv2.dilate(thresh, (7, 7))
        return thresh

    def findTargets(self, thresh) -> tuple:
        # find some contours
        # im2 is useless and used as a filler value
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # grab both min area rectangles

        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:4]
        rectangles = []
        # areas = [cv2.contourArea(c) for c in contours]
        if len(contours) > 0:
            for cnt in contours:
                # max_index = np.argmax(areas)
                # cnt = contours[max_index]

                # check for min area
                if cv2.contourArea(cnt) >= self.minarea:
                    rect = cv2.minAreaRect(cnt)
                    rectangles.append(rect)

        def xpos(r):
            return r[0][0]

        return tuple(sorted(rectangles, key=xpos))
        # return rectangles.sort()

    def find(self, data: np.ndarray) -> tuple:
        frame = self.acquireImage(data)
        thresh = self.preImageProcessing(frame)

        if self.show:
            cv2.imshow("Filtered", thresh)
            cv2.waitKey(1)

        targets = self.findTargets(thresh)
        rectangles = targetRectangles(targets)

        # print("rectangles" , rectangles)

        # found, x, y, angle
        result = (False, 0, 0, 0)

        if len(rectangles) > 0:
            cx, cy = findCentroid(rectangles).astype(np.int32)

            self.err = cx - (self.width / 2)
            cv2.circle(frame, (cx, cy), 10, (0, 255, 255), 5)

            distance = calculateDistance(cy)

            print("distance :", distance)

        else:
            self.err = -1000
        if self.show:
            cv2.imshow("Unfiltered", frame)
            cv2.waitKey(1)
        return result, frame


if __name__ == "__main__":
    print("This file is a library please run the correct file to get the output")
    exit(42069)
