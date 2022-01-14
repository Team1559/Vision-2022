import cv2
import numpy as np
import Gst
import os


class USBCamera(object):

    # index is what usb port its plugged into
    def __init__(self, index, width, height):

        Gst.init(None)

        # for usb
        # OLD PATH
        # path = "v4l2src ! video/x-raw, height=%d, width=%d,format=(string)BGR ! appsink name=sink%d" %(height,width,index)
        path = "v4l2src ! video/x-raw, width=800,height=448,framerate=20/1 ! tee name=t t. ! queue ! videoconvert ! video/x-raw, format=(string)BGR ! appsink name=sink1 t. ! queue ! nvvidconv ! nvjpegenc ! rtpjpegpay ! udpsink host=10.15.59.46 port=5802"

        print(path)
        self.pipe = Gst.parse_launch(path)

        self.index = index
        self.width = width
        self.height = height

        # for CSI
        # path = "nvcamerasrc device=/dev/video0 ! video/x-raw-yuv,width=720,height=480,framerate=20/1 ! appsink name=sink"+str(index)

        # self.pipe = Gst.parse_launch(path)
        self.pipe.set_state(Gst.State.PLAYING)

        self.appsink = self.pipe.get_by_name("sink" + str(index))
        # self.appsink = self.pipe.get_by_name("appsink0")
        self.appsink.set_property("emit-signals", True)
        self.appsink.set_property("sync", False)
        self.appsink.set_property("max-buffers", 1)
        self.appsink.set_property("drop", True)

        self.index = index

        ##Use this when gstreamer doesnt work##
        # self.cap = cv2.VideoCapture(index)

        self.frame = np.zeros((width, height, 3), np.uint8)

    # set the camera to manual exposure
    # os.system("v4l2-ctl -c exposure_auto=1 -d /dev/video0")

    def updateFrame(self):

        try:
            sample = self.appsink.emit("pull-sample")

            buf = sample.get_buffer()
            caps = sample.get_caps()

            self.frame = np.ndarray(
                (caps.get_structure(0).get_value('height'), caps.get_structure(0).get_value('width'), 3),
                buffer=buf.extract_dup(0, buf.get_size()), dtype=np.uint8)
        except:
            pass

    # _,self.frame = self.cap.read()

    def setExposure(self, value):

        os.system("v4l2-ctl -c exposure_absolute=" + str(value) + " -d /dev/video0")

    def stopCamera(self):

        self.pipe.set_state(Gst.State.PAUSED)

    def setStreaming(self):

        self.pipe = Gst.parse_launch(
            "v4l2src ! video/x-raw,width=320,height=240,framerate=15/1 ! jpegenc ! rtpjpegpay ! udpsink host=10.15.59.5 port=5802")

        self.pipe.set_state(Gst.State.PLAYING)
