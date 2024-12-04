# import psutil
from video_source import VideoSource
from util import glob_files, memory
from config import config
# from image import *
import numpy as np
import cv2
# from timer import Timer


class ImageFolder(VideoSource):
    def __init__(self, path, image_buffer, memory_threshold=1024):
        self.path = path
        self.image_buffer = image_buffer
        self.memory_threshold = memory_threshold
        self.fn = sorted(glob_files(self.path, config.IMAGE_EXT))
        self.N = len(self.fn)
        self.idx = 0
        self.image = None
        self.cache = {}
        self.paused = True

    def play(self):
        self.paused = False

    def pause(self):
        self.paused = True

    def load_image(self, fn):
        if fn in self.cache:
            return self.cache[fn]
        else:
            im = cv2.cvtColor(cv2.imread(fn), cv2.COLOR_BGR2RGB)
            # print "Loaded %dx%dx%d image" % (
            # im.shape[0], im.shape[1], im.shape[2])
            if memory() > self.memory_threshold:
                # print "Memory: %d, caching image." % memory()
                self.cache[fn] = im
            return im

    @profile
    def get(self):
        # with Timer('Loading image'):
        if (not self.paused) or (self.image is None):
            self.image = self.load_image(self.fn[self.idx])
            self.idx = (self.idx + 1) % self.N

            N = self.image.shape[0] * self.image.shape[1] * self.image.shape[2]
            buf = np.frombuffer(self.image_buffer, dtype=np.uint8, count=N)
            buf = buf.reshape((self.image.shape[0], self.image.shape[1], self.image.shape[2]))
            np.copyto(buf, self.image)
            self.image = buf

