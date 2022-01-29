import cv2
import numpy as np
import sys


def findCentroid(rectangles):
    centers = np.array([r[0] for r in rectangles])
    centroid = np.mean(centers, axis=0)
    return centroid


class ball_finder(object):

    def __init__(self):
        """Initialize camera"""
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
        self.out = None
        self.minarea = 10  # 100

    def acquireImage(self, data):

        frame = data
        self.height, self.width = frame.shape[:2]
        self.out = frame
        return frame

    def preImageProcessing(self, frame):
        # convert to hsv
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # blur me
        hsv = cv2.blur(hsv, (5, 5))

        thresh = cv2.inRange(hsv, self.hsvl, self.hsvh)
        # erode and dilate
        thresh = cv2.erode(thresh, (14, 14))
        thresh = cv2.dilate(thresh, (14, 14))

        return thresh

    def findTargets(self, frame, thresh):
        filtered = cv2.bitwise_and(frame, frame, mask=thresh)
        if self.show:
            cv2.imshow("Color filtered", filtered)
        cv2.waitKey(1)

        circles = cv2.HoughCircles(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.HOUGH_GRADIENT, 1, 75, param1=90,
                                   param2=20, minRadius=10, maxRadius=200)
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
                print(np.mean(thresh[max(x - r, 0):min(x + r, self.width), max(y - r, 0):min(y + r, self.height)]))
                # > 1*3.141519265357962/4
            if ball is not None:
                cv2.circle(output, (ball[0], ball[1]), ball[2], (0, 255, 0), 4)

        if self.show:
            cv2.imshow("Circles", output)
            cv2.waitKey(1)
        out = output
        return circles, out
        # return rectangles.sort()

    def find(self, data):
        frame = self.acquireImage(data)
        thresh = self.preImageProcessing(frame)

        if self.show:
            cv2.imshow("Thresh", thresh)
            cv2.waitKey(1)
        targets, self.out = self.findTargets(frame, thresh)
        if self.show:
            cv2.imshow("Unfiltered", frame)
            cv2.waitKey(1)
        return (False, 10, 10, 0), self.out


if __name__ == "__main__":
    print("This file is a library please run the correct file to get the output")
    exit(42069)
