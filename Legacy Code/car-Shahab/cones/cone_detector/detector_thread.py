from threading import Thread
import math
import time
import wx
import cv2
from image_folder import ImageFolder
from camera import Camera
from log import log
from timer import Timer
from config import config
import numpy as np
import detector_process


class DetectorThread(Thread):
    def __init__(self, subscriber, conn, image_buffer, result_buffer):
        Thread.__init__(self)

        # self.video = ImageFolder('../../../car_data/cones/amz', image_buffer)
        self.video = ImageFolder('../../../car_data/test_days/2019-12-11/recording0_flipped', image_buffer)
        # self.video = ImageFolder('../../../car_data/cones/ka-raceing-240919/every10')
        # self.video = ImageFolder('../../../car_data/cones/office.261019')
        # self.video = ImageFolder('../../../car_data/local/fs2019_track1_fixed')
        # self.video = ImageFolder('../fsuk 2019 recordings/track1')
        # self.video = ImageFolder('../../data/recording.2310191746')
        # self.video = ImageFolder('../../data/local/recording')
        # self.video = ImageFolder('../../data/cones/single_lap')
        # log('Found %d image files.' % (self.video.N))

        # self.video = Camera(0, image_buffer)

        self.conn = conn
        self.image_buffer = image_buffer
        self.result_buffer = result_buffer
        self.im_result = None

        self.subscriber = subscriber
        self.abort_requested = False
        self.FPS = 0
        self.paused = True

    def play(self):
        self.paused = False
        self.video.play()

    def pause(self):
        self.paused = True
        self.video.pause()

    def notify(self):
        try:
            wx.CallAfter(self.subscriber)
        except:
            pass

    @profile
    def run(self):
        frame = 0
        t = time.time()
        while True:
            if self.abort_requested:
                return

            if self.paused:
                if self.video.image is None:
                    self.video.get()
                time.sleep(0.1)
                continue

            if config.CD_ENABLE and (self.video.image is not None):
                self.conn.send((detector_process.CMD_DETECT,
                                {'height': self.video.image.shape[0],
                                 'width': self.video.image.shape[1]}))
                self.video.get()
                self.conn.recv()  # Blocking
            else:
                self.video.get()
            # else:
                # self.bboxes = []

            frame += 1

            dt = time.time() - t
            if dt > 1.0:
                self.FPS = float(frame) / dt
                frame = 0
                t = time.time()

            N = self.video.image.shape[0] * self.video.image.shape[1] * self.video.image.shape[2]
            self.im_result = np.frombuffer(self.result_buffer, dtype=np.uint8, count=N)
            self.im_result = self.im_result.reshape(self.video.image.shape)

            self.notify()

    def abort(self):
        self.abort_requested = True
