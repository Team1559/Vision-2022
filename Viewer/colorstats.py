import numpy as np
import cv2


def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        exit()

    while True:
        ret, image = cap.read()
        if not ret:
            raise Exception("Can't receive frame (stream end?). Exiting ...")

        # display the image and wait for a keypress
        cv2.imshow("image", image)
        key = cv2.waitKey(1) & 0xFF
        if key in (10, 13):
            break

    clone = image.copy()

    refPt = []
    cropping = False

    cv2.namedWindow("image")

    def click_and_crop(event, x, y, flags, param):
        # grab references to the global variables
        global refPt, cropping
        # if the left mouse button was clicked, record the starting
        # (x, y) coordinates and indicate that cropping is being
        # performed
        if event == cv2.EVENT_LBUTTONDOWN:
            refPt = [(x, y)]
            cropping = True
        # check to see if the left mouse button was released
        elif event == cv2.EVENT_LBUTTONUP:
            # record the ending (x, y) coordinates and indicate that
            # the cropping operation is finished
            cropping = False
            if (x, y) == refPt[0]:
                refPt = []
            else:
                refPt.append((x, y))
                # draw a rectangle around the region of interest
                cv2.rectangle(image, refPt[0], refPt[1], (0, 255, 0), 2)
                cv2.imshow("image", image)

    cv2.setMouseCallback("image", click_and_crop)

    while True:
        # display the image and wait for a keypress
        cv2.imshow("image", image)
        key = cv2.waitKey(1) & 0xFF
        # if the 'r' key is pressed, reset the cropping region
        if key == ord("r"):
            image = clone.copy()
        # press enter to complete the selection
        elif key in (10, 13):
            break
        elif key == ord("q"):
            cv2.destroyAllWindows()
            exit()

    def print_stats(image):
        print("min", np.min(image, (0, 1)))
        print("med", np.median(image, (0, 1)).astype(np.uint8))
        print("max", np.max(image, (0, 1)))

    # if there are two reference points, then crop the region of interest
    # from the image and display it
    if len(refPt) == 2:
        roi = clone[refPt[0][1]: refPt[1][1], refPt[0][0]: refPt[1][0]]
        cv2.imshow("ROI", roi)
        print("rgb")
        print_stats(roi)
        print("\nhsv")
        print_stats(cv2.cvtColor(roi, cv2.COLOR_BGR2HSV))
        cv2.waitKey(0)

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
