from video_source import VideoSource
from config import config
import cv2
import numpy as np


class Camera(VideoSource):
    def __init__(self, device_id, image_buffer):
        self.device_id = device_id
        self.image_buffer = image_buffer
        self.image = None
        self.paused = True
        self.cap = cv2.VideoCapture(self.device_id)
        self.cap.set(cv2.CAP_PROP_FPS, 50)

    def play(self):
        self.paused = False

    def pause(self):
        self.paused = True

    @profile
    def get(self):
        # with Timer('Loading image'):
        if (not self.paused):
            if self.image is None:
                ret, self.image = self.cap.read()
            else:
                self.cap.read(self.image)
            self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
            # TODO: Avoid copying by capturing directly into the buffer?
            N = self.image.shape[0] * self.image.shape[1] * self.image.shape[2]
            buf = np.frombuffer(self.image_buffer, dtype=np.uint8, count=N)
            buf = buf.reshape((self.image.shape[0], self.image.shape[1], self.image.shape[2]))
            np.copyto(buf, self.image)
            self.image = buf
