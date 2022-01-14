import math
import sys

import cv2
import numpy as np


class targetFinder(object):

    def __init__(self, Camera):
        '''Initialize camera'''
        self.camera = Camera
        # BRIGHTNESS AT 30 for perfect, 85 for driver station
        self.cx = -1
        self.cy = -1
        self.err = -1000
        green_low = np.array([0, 20, 0])
        green_high = np.array([100, 255, 100])
        blue_low = np.array((60, 0, 0))
        blue_high = np.array((255, 80, 80))
        # colors are in the BGR color space
        self.hsvl = blue_low
        self.hsvh = blue_high
        self.show = True # "show" in sys.argv
        # self.width = 800
        # self.height = 488
        self.width = 0
        self.height = 0

        self.found = False

        self.minarea = 50  # 100

    def acquireImage(self):

        success, frame = self.camera.read()
        if not success:
            exit(222)
        self.height, self.width = frame.shape[:2]
        return frame

    def preImageProcessing(self, frame):
        # convert to hsv
        hsv = frame  # cv2.cvtColor(frame, cv2.COLOR_BGR2BGR)
        # blur me
        hsv = cv2.blur(hsv, (5, 5))

        thresh = cv2.inRange(hsv, self.hsvl, self.hsvh)

        # erode and dilate
        thresh = cv2.erode(thresh, (14, 14))
        thresh = cv2.dilate(thresh, (14, 14))
        return thresh

    def findTargets(self, thresh):
        # find some contours
        # im2 is useless and used as a filler value
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # grab both min area rectangles

        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:4]
        rectangles = []

        for cnt in contours:
            # check for min area
            if cv2.contourArea(cnt) < self.minarea:
                break
            # check for quadrilateral
            perimeter = cv2.arcLength(cnt, True)
            polygon = cv2.approxPolyDP(cnt, 0.04 * perimeter, True)
            # check for num of contours did not work
            # if len(polygon)!=4:
            #    continue

            rect = cv2.minAreaRect(cnt)
            rectangles.append(rect)

        def xpos(r):
            return r[0][0]

        return tuple(sorted(rectangles, key=xpos))

    def targetRectangles(self, rectangles):
        def findAngle(r):
            if r[1][1] > r[1][0]:
                angle = r[2]
            else:
                angle = r[2] + 90
            return angle

        candidates = []
        for i in range(len(rectangles) - 1):
            angle1 = findAngle(rectangles[i])
            angle2 = findAngle(rectangles[i + 1])
            # print(angle1,angle2)
            if True:  # angle1 > 0 and angle2 < 0:
                targetRectangles = [rectangles[i], rectangles[i + 1]]
                ex = abs(self.findCentroid(targetRectangles)[0] - self.width / 2)
                candidates.append((ex, targetRectangles))
        # check for candidates then sort by distance from center
        if not candidates:
            return []
        else:
            candidates.sort()
            return candidates[0][1]

    def findCentroid(self, rectangles):

        centers = np.array([r[0] for r in rectangles])
        centroid = np.mean(centers, axis=0)
        return centroid

    def calculateDistance(self, rectangles):
        # NEW
        dims = np.array([r[1] for r in rectangles])
        tapeHeights = np.max(dims, axis=1)
        # tapeHeight = np.mean(tapeHeights)
        distances = 3009.30724995 * np.power(tapeHeights, -0.94923256)
        distance = np.mean(distances)
        # print distance

        # OLD
        # actualTapeDistance = tapeXDistance / math.cos(angle)
        # distance = 6846.93489125*math.pow(actualTapeDistance,-1.03994056)
        # print distance, angle * 180/math.pi
        return distance, distances

    def calculateAngle(self, distance, distances, rectangles):
        leftTapePoint = np.max(cv2.boxPoints(rectangles[0]), axis=0)[0]
        rightTapePoint = np.min(cv2.boxPoints(rectangles[1]), axis=0)[0]
        averageTapePoint = (leftTapePoint + rightTapePoint) / 2
        xError = (self.width / 2) - averageTapePoint
        angle = -math.atan(xError / 700.0)

        # OLD CODE
        widthBetweenTapes = rightTapePoint - leftTapePoint
        expectedWidth = 4875.64456729 * np.power(distance, -0.96150127)
        if abs(widthBetweenTapes) > expectedWidth:
            viewAngle = 0
        else:
            viewAngle = math.acos(widthBetweenTapes / expectedWidth)
        if distances[0] < distances[1]:
            viewAngle = -viewAngle
        return angle, viewAngle

    def XOffset(self, distance, rectangles):
        a = rectangles[0][1][0] * rectangles[0][1][1]
        b = rectangles[1][1][0] * rectangles[1][1][1]

        if a > b:
            ratio = -math.sqrt(a / b - 1)
        else:
            ratio = math.sqrt(b / a - 1)
        return ratio * 50

        # print distance, angle, viewAngle
        # return distance*math.sin(angle+viewAngle)

        # OLD CODE
        FOV = 60 * math.pi / 180
        radiansPerPixel = FOV / self.width
        centerOfImage = self.width / 2
        XoffsetAngle = radiansPerPixel * (cx - centerOfImage)
        Xoffset = math.tan(XoffsetAngle) * distance
        return Xoffset

    def aspectRatioUNUSED(self, rectangles):

        # new code
        dims = np.array([r[1] for r in rectangles])
        tapeHeights = np.max(dims, axis=1)
        leftTapePoint = np.max(cv2.boxPoints(rectangles[0]), axis=0)[0]
        rightTapePoint = np.min(cv2.boxPoints(rectangles[1]), axis=0)[0]
        tapeDistance = rightTapePoint - leftTapePoint
        aspectRatio = tapeDistance / np.mean(tapeHeights)
        # print tapeDistance, tapeHeights, aspectRatio
        print
        np.mean(tapeHeights)
        # old code
        # dims = np.array([r[1] for r in rectangles])
        # aspectRatios = np.max(dims, axis = 1)/np.min(dims, axis=1)
        # aspectRatio = np.mean(aspectRatios)
        return aspectRatio, tapeDistance,

    def angleOLD(self, rectangles, aspectRatio):
        # aspect ratio depends on the height of the target relative to the camera frame
        base_ratio = 1.44
        # base_ratio = 3.17
        # print aspectRatio
        if aspectRatio > base_ratio:
            aspectRatio = base_ratio
        angle = math.acos(aspectRatio / base_ratio)
        areas = [r[1][0] * r[1][1] for r in rectangles]
        if areas[0] < areas[1]:
            angle = -angle
        if angle == 0:
            pass
            # pdb.set_trace()
        # print aspectRatio, angle*(180/math.pi)
        return angle

    def find(self):
        frame = self.acquireImage()
        thresh = self.preImageProcessing(frame)

        if self.show:
            cv2.imshow("Filtered", thresh)
            cv2.waitKey(1)

        targets = self.findTargets(thresh)
        rectangles = self.targetRectangles(targets)
        # rectangles = self.findMatchingPair(rectangles)

        self.color = 0

        # found, x, y, angle
        result = (False, 0, 0, 0)

        if len(rectangles) != 0:
            cx, cy = self.findCentroid(rectangles).astype(np.int32)
            self.err = cx - (self.width / 2)
            cv2.circle(frame, (cx, cy), 5, 255, -1)

            # NEW
            distance, distances = self.calculateDistance(rectangles)
            angle, viewAngle = self.calculateAngle(distance, distances, rectangles)
            XOffset = self.XOffset(distance, rectangles)
            result = (True, XOffset, distance, angle * 180 / math.pi)

            # print distance, angle*180/math.pi, XOffset
            # ratio, tapeXDistance = self.aspectRatio(rectangles)
            # angle = self.angle(rectangles, ratio)
            # result = (True, 0, 0, angle * 180/math.pi)

            # OLD
            # ratio, tapeXDistance = self.aspectRatio(rectangles)
            # angle = self.angle(rectangles, ratio)
            # self.calculateDistance(tapeXDistance, angle)
            # result = (True, 0, 0, angle * 180/math.pi)

            # print(cx,cy)
            # print ratio, angle*180/math.pi
        else:
            self.err = -1000
        if self.show:
            cv2.imshow("Unfiltered", frame)
            cv2.waitKey(1)
        return result
