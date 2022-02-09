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
        self.ball = None
        self.team = "blue"
        # NOOOOOOOO BGR, BGR bad
        red_low = np.array((80, 100, 45))
        red_high = np.array((100, 255, 255))
        blue_low = np.array((105, 0, 20))
        blue_high = np.array((121, 255, 255))
        self.hsvl = blue_low if self.team == "blue" else red_low
        self.hsvh = blue_high if self.team == "blue" else red_high
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
        if self.team == "red":
            hsv[:,:,0] += 90
            hsv[:,:,0] %= 180
        # blur me
        hsv = cv2.blur(hsv, (5, 5))

        thresh = cv2.inRange(hsv, self.hsvl, self.hsvh)
        # erode and dilate
        thresh = cv2.erode(thresh, (9, 9))
        thresh = cv2.dilate(thresh, (9, 9))  # 14

        return thresh

    def findTargets(self, frame, thresh):
        # filtered = cv2.bitwise_and(frame, frame, mask=thresh)
        if self.show:
            # cv2.imshow("Color filtered", filtered)
            pass
        # cv2.waitKey(1)

        circles = cv2.HoughCircles(thresh, cv2.HOUGH_GRADIENT, 1, 75, param1=255, param2=14, minRadius=10, maxRadius=200) # bye Ry ry

        # _ ,contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # self.ball = None
        # scale = 0.5
        # maxRadius = 0
        # minAcceptableRadius = 10
        # for contour in contours:
        #     (x,y),r = cv2.minEnclosingCircle(cv2.approxPolyDP(contour, 3, True))

        #     if r < minAcceptableRadius and r > maxRadius and cv2.contourArea(contour) > scale * 3.141592653589793238462*r*r:
        #         self.ball = (int(x), int(y), int(r))
        #         maxRadius = r

        output = frame.copy()
        # ensure at least some circles were found
        if circles is not None:
            # print("cirlces" , len(circles))
            # convert the (x, y) coordinates and radius of the circles to integers
            circles = np.round(circles[0, :]).astype("int")
            # loop over the (x, y) coordinates and radius of the circles
            self.ball = None
            maxRadius = 0
            for (x, y, r) in circles:
                try:
                    if thresh[y][x] > 0:
                        if r > maxRadius:
                            self.ball = (x, y, r)
                            maxRadius = r
                except IndexError:
                    pass
                # print(np.mean(thresh[max(x - r, 0):min(x + r, self.width), max(y - r, 0):min(y + r, self.height)]))
                # > 1*3.141519265357962/4
        if self.ball is not None:
            cv2.circle(output, (self.ball[0], self.ball[1]), self.ball[2], (0, 255, 0), 4)

        #if self.show:
        #cv2.imshow("Cargo", output)
            # cv2.waitKey(1)
        return output
        # return rectangles.sort()

    def find(self, data):
        frame = self.acquireImage(data)
        thresh = self.preImageProcessing(frame)

        #if self.show:
        #    cv2.imshow("Thresh", thresh)

        if self.show:
            pass
            # cv2.imshow("BallCam", frame)
            # cv2.waitKey(1)    
        self.out = self.findTargets(frame, thresh)
        if self.show:
            pass
            # cv2.imshow("Ball Thresh", thresh)

            #cv2.waitKey(1)
        #return (False, 10, 10, 0), self.out
        return (self.ball is not None, self.calculateAngle(self.ball[0]) if self.ball is not None else 0, 0, 0), self.out

    def calculateAngle(self, targetPixelX):
        #
        # uses fov to pixel difference ratio to calculate correction angle
        #
        h_fov = 77  # degrees
        imageWidth = 640  # pixels

        pasta = (imageWidth / 2 - targetPixelX)  # postive = right/clockwise

        theta = h_fov * pasta / imageWidth

        return theta


if __name__ == "__main__":
    print("This file is a library please run the correct file to get the output")
    exit(42069)
