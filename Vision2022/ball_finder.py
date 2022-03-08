import cv2
import numpy as np
import sys

FONT = cv2.FONT_HERSHEY_SIMPLEX


def findCentroid(rectangles):
    centers = np.array([r[0] for r in rectangles])
    centroid = np.mean(centers, axis=0)
    return centroid


def calculateDistance(targetPixelY):
    # import pdb
    # pdb.set_trace()
    #
    # uses fov to pixel difference ratio to calculate distance
    #
    v_fov = 45.0  # degrees
    imageHeight = 480.0  # pixels
    targetPixelY = imageHeight - targetPixelY  # pixels
    cameraHeight = 28.0 / 12.0  # feet FIXME: Will need to be adjusted
    targetHeight = 4.75 / 12.0  # feet
    angularOffset = -17 - v_fov / 2  # degrees
    heightDifference = targetHeight - cameraHeight  # feet

    theta = v_fov / imageHeight * targetPixelY + angularOffset
    d = heightDifference / np.tan(theta * 3.14159265 / 180)

    return d


def calculateAngle(targetPixelX):
    #
    # uses fov to pixel difference ratio to calculate correction angle
    #
    h_fov = 77  # degrees
    imageWidth = 640  # pixels

    pasta = (imageWidth / 2 - targetPixelX)  # positive = right/clockwise

    theta = h_fov * pasta / imageWidth

    return theta


class ball_finder(object):

    def __init__(self):
        """Initialize camera"""
        # BRIGHTNESS AT 30 for perfect, 85 for driver station
        self.cx = -1
        self.cy = -1
        self.err = -1000
        self.ball = None
        # NO BGR, BGR bad
        self.invalid = np.array((0, 0, 0))
        # self.red_low = np.array((80, 130, 45))
        # self.red_high = np.array((110, 255, 255))
        self.red_low = np.array((0, 30, 20))
        self.red_high = np.array((10, 255, 255))
        # self.blue_low = np.array((105, 100, 20))
        # self.blue_high = np.array((121, 255, 255))
        tighten = 3
        self.blue_low = np.array((105 + tighten, 120, 20))
        self.blue_high = np.array((121 + tighten, 255, 255))
        self.hsv_l = self.invalid
        self.hsv_h = self.invalid
        self.show = "show" in sys.argv
        self.width = 0
        self.height = 0

        self.found = False
        self.out = None
        self.min_area = 10  # 100
        self.color = (0, 165, 255)
        self.highlightColor = (0, 0)
        self.position = (10, 100)
        self.text = "Invalid"

    def set_color(self, color):
        color_RED = (0, 0, 255)
        color_BLACK = (0, 0, 0)
        color_BLUE = (255, 0, 0)

        if color == "blue":
            self.hsv_h = self.blue_high
            self.hsv_l = self.blue_low
            self.color = color_BLUE
            self.highlightColor = color_RED
            self.text = "Blue"

        elif color == "red":
            self.hsv_h = self.red_high
            self.hsv_l = self.red_low
            self.color = color_RED
            self.highlightColor = color_BLUE
            self.text = "Red"
        else:
            self.hsv_h = self.invalid
            self.hsv_l = self.invalid
            self.color = color_BLACK
            self.text = "Invalid"

    def acquireImage(self, data):
        frame = data
        self.height, self.width = frame.shape[:2]
        self.out = frame
        return frame

    def preImageProcessing(self, frame):
        # convert to hsv
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        if self.text == "Red":
            # if True:
            hsv[:, :, 0] += 90
            hsv[:, :, 0] %= 180

        thresh = cv2.inRange(hsv, self.hsv_l, self.hsv_h)
        thresh = cv2.medianBlur(thresh, 9)
        return thresh

    def findTargets(self, frame, thresh):
        if self.show:
            pass

        circles = cv2.HoughCircles(thresh, cv2.HOUGH_GRADIENT, 1, 75, param1=255, param2=14, minRadius=10,
                                   maxRadius=200)  # bye Ry ry
        output = frame.copy()
        # ensure at least some circles were found
        if circles is not None:
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
        return output

    def find(self, data):
        # print(self.hsv_l, self.hsv_h)
        frame = self.acquireImage(data)
        thresh = self.preImageProcessing(frame)

        # self.out = self.findTargets(frame, thresh)
        output = self.out if True else cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

        valid_result = self.ball and self.ball is not None

        distance = calculateDistance(self.ball[1]) if valid_result else 0
        distance_valid = 0.3 < distance <= 20
        # distance_valid = True
        distance_display = distance if distance_valid else 0

        TEXT_PADDING = 5
        (text_w, text_h), _ = cv2.getTextSize("{:.1f}ft".format(distance_display), FONT, 1, 4)

        cv2.rectangle(self.out, (0, 0), (TEXT_PADDING * 2 + text_w, TEXT_PADDING * 2 + text_h), self.color, -1)
        cv2.putText(self.out, "{:.1f}ft".format(distance_display), (TEXT_PADDING, TEXT_PADDING + text_h), FONT, 1,
                    (255, 255, 255), 4, cv2.LINE_AA)

        if not valid_result or not distance_valid:
            return (False, 0, 0, 0), output

        cv2.circle(self.out, (self.ball[0], self.ball[1]), self.ball[2], self.highlightColor, 4)
        # Text for the current color being targeted

        return (True, calculateAngle(self.ball[0]), calculateDistance(self.ball[1]),
                0), output


if __name__ == "__main__":
    print("This file is a library please run the correct file to get the output")
    exit(42069)
