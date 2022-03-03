from re import T
import cv2
import numpy as np
import sys

FONT = cv2.FONT_HERSHEY_SIMPLEX


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
        self.team = "red"
        # NOOOOOOOO BGR, BGR bad
        self.invalid = np.array((0, 0, 0))
        self.red_low = np.array((90, 130, 45))
        self.red_high = np.array((100, 255, 255))
        self.blue_low = np.array((105, 100, 0))
        self.blue_high = np.array((121, 255, 255))
        self.hsvl = self.invalid
        self.hsvh = self.invalid
        self.show = "show" in sys.argv
        # self.width = 800
        # self.height = 488
        self.width = 0
        self.height = 0

        self.found = False
        self.out = np.zeros(shape=(480, 640, 3))
        self.minarea = 10  # 100
        self.color = (0, 165, 255)
        self.highlightColor = (0, 0)
        self.position = (10, 100)
        self.text = "Invalid"

    def set_color(self, color):
        color_RED = (0, 0, 255)
        color_ORANGE = (0, 165, 255)
        color_BLUE = (255, 0, 0)

        if color == "blue":
            self.hsvh = self.blue_high
            self.hsvl = self.blue_low
            self.color = color_BLUE
            self.highlightColor = color_RED
            self.text = "Blue"

        elif color == "red":
            self.hsvh = self.red_high
            self.hsvl = self.red_low
            self.color = color_RED
            self.highlightColor = color_BLUE
            self.text = "red"
        else:
            self.hsvh = self.invalid
            self.hsvl = self.invalid
            self.color = color_ORANGE
            self.text = "Invalid"

    def acquireImage(self, data):
        frame = data
        self.height, self.width = frame.shape[:2]
        self.out = frame
        return frame

    def preImageProcessing(self, frame):
        # convert to hsv
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        if self.team == "red":
            hsv[:, :, 0] += 90
            hsv[:, :, 0] %= 180
        # blur me
        # hsv = cv2.medianBlur(hsv, 5)
        # hsv =  cv2.blur(hsv, (5,5))

        thresh = cv2.inRange(hsv, self.hsvl, self.hsvh)
        thresh = cv2.medianBlur(thresh, 9)
        # erode and dilate
        # thresh = cv2.erode(thresh, (14, 14))
        # thresh = cv2.dilate(thresh, (14, 14))  # 14

        return thresh

    def findTargets(self, frame, thresh):
        # filtered = cv2.bitwise_and(frame, frame, mask=thresh)
        if self.show:
            # cv2.imshow("Color filtered", filtered)
            pass
        # cv2.waitKey(1)

        circles = cv2.HoughCircles(thresh, cv2.HOUGH_GRADIENT, 1, 75, param1=255, param2=14, minRadius=10,
                                   maxRadius=200)  # bye Ry ry

        # _ ,contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # self.ball = None
        # scale = 0.5
        # maxRadius = 0
        # minAcceptableRadius = 10
        # for contour in contours:
        #     (x,y),r = cv2.minEnclosingCircle(cv2.approxPolyDP(contour, 3, True))

        # if r < minAcceptableRadius and r > maxRadius and cv2.contourArea(contour) > scale *
        # 3.141592653589793238462*r*r:
        #   self.ball = (int(x), int(y), int(r)) maxRadius = r

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

        # if self.show:
        # cv2.imshow("Cargo", output)
        # cv2.waitKey(1)
        return output
        # return rectangles.sort()

    def find(self, data):

        # Return format = (is_there_a_ball, heading, distance, 0), output_frame
        frame = self.acquireImage(data)
        thresh = self.preImageProcessing(frame)

        # if self.show:
        #    cv2.imshow("Thresh", thresh)
        # cv2.imshow("BallCam", frame)
        # cv2.imshow("Ball Thresh", thresh)

        # cv2.waitKey(1)

        self.out = self.findTargets(frame, thresh)

        if not self.ball or self.ball is None:
            return (False, 0, 0, 0), self.out
        distance = self.calculateDistance(self.ball[1])

        if distance < 0.3 or distance > 20:
            return (False, 0, 0, 0), self.out

        cv2.circle(self.out, (self.ball[0], self.ball[1]), self.ball[2], self.highlightColor, 4)
        (text_w, text_h), _ = cv2.getTextSize("{:.1f}ft".format(distance), FONT, 1, 4)
        TEXT_PADDING = 5
        cv2.rectangle(self.out, (0, 0), (TEXT_PADDING * 2 + text_w, TEXT_PADDING * 2 + text_h), (0, 0, 0), -1)
        cv2.putText(self.out, "{:.1f}ft".format(distance), (TEXT_PADDING, TEXT_PADDING + text_h), FONT, 1,
                    (255, 255, 255), 4, cv2.LINE_AA)
        # Text for the current color being targeted
        cv2.putText(self.out, self.text, self.position, cv2.FONT_HERSHEY_SIMPLEX, 1, self.color, 2, 2)

        return (True, self.calculateAngle(self.ball[0]), self.calculateDistance(self.ball[1]),
                0), self.out if True else cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

    def calculateAngle(self, targetPixelX):
        #
        # uses fov to pixel difference ratio to calculate correction angle
        #
        h_fov = 77  # degrees
        imageWidth = 640  # pixels

        pasta = (imageWidth / 2 - targetPixelX)  # postive = right/clockwise

        theta = h_fov * pasta / imageWidth

        return theta

    def calculateDistance(self, targetPixelY):
        # import pdb
        # pdb.set_trace()
        #
        # uses fov to pixel difference ratio to calculate distance
        #
        v_fov = 45.0  # degrees
        imageHeight = 480.0  # pixels
        targetPixelY = imageHeight - targetPixelY  # pixels
        cameraHeight = 2.5416  # feet FIXME: Will need to be adjusted
        targetHeight = 4.75 / 12  # feet
        angularOffset = -39.5  # degrees
        heightDifference = targetHeight - cameraHeight  # feet

        theta = v_fov / imageHeight * targetPixelY + angularOffset
        d = heightDifference / np.tan(theta * 3.14159265 / 180)

        return d


if __name__ == "__main__":
    print("This file is a library please run the correct file to get the output")
    exit(42069)
