# import psutil
from video_source import VideoSource
from tools import glob_files, memory
from config import config
# from image import *
import numpy as np
import cv2
# from timer import Timer
from ipc import image_buffer_l, image_buffer_r

def split_stereo(im):                                                 #splitting raw input image
    width = int(im.shape[1] / 2)
    left = im[:, 0:width, :]
    right = im[:, width:, :]
    return left, right


class ImageFolder(VideoSource):
    def __init__(self, path, stereo, start=0, memory_threshold=1024):
        self.path = path                                                #obtaining path for image input 
        self.stereo = stereo
        self.memory_threshold = memory_threshold
        self.fn = sorted(glob_files(self.path, config.IMAGE_EXT))

        self.N = len(self.fn)
        self.idx = start
        self.image = None
        self.image_l = None
        self.image_r = None
        self.image_l_prev = None
        self.image_r_prev = None
        self.cache = {}
        self.paused = True

    def play(self):                                                     #pass operation for image or video
        self.paused = False

    def pause(self):
        self.paused = True

    def load_image(self, fn):                                           # loading image from input data
        if fn in self.cache:
            return self.cache[fn]
        else:
            im = cv2.cvtColor(cv2.imread(fn), cv2.COLOR_BGR2RGB)        #converting image colour from BGR to RGB 
            # print "Loaded %dx%dx%d image" % (
            # im.shape[0], im.shape[1], im.shape[2])
            if memory() > self.memory_threshold:
                # print "Memory: %d, caching image." % memory()
                self.cache[fn] = im
            return im

    def rectify(self):                                                   #ajust input images for reduction in distrosion 
        # print(self.stereo.coeffs1.T)
        # print(self.stereo.I1)
        self.image_l = cv2.undistort(self.image_l, self.stereo.I1, self.stereo.coeffs1)
        self.image_r = cv2.undistort(self.image_r, self.stereo.I2, self.stereo.coeffs2)
        # cv2.imwrite('rectified_l.png', cv2.cvtColor(self.image_l, cv2.COLOR_BGR2RGB))
        
    # @profile
    def get(self):                                          #function which gets images input from video           
        # with Timer('Loading image'):
        if (not self.paused) or (self.image is None):
            if self.image_l is not None:
                self.image_l_prev = self.image_l.copy()
                self.image_r_prev = self.image_r.copy()

            # Load the next image from file or get it from memory cache
            self.image = self.load_image(self.fn[self.idx])
            # Split it into the left and the right halves
            self.image_l, self.image_r = split_stereo(self.image)        #splitting image input
            # self.rectify()
            
            # Increment frame counter
            self.idx = (self.idx + 1) % self.N

            N = self.image_l.shape[0] * self.image_l.shape[1] * self.image_l.shape[2]
            
            buf_l = np.frombuffer(image_buffer_l, dtype=np.uint8, count=N)
            buf_l = buf_l.reshape((self.image_l.shape[0], self.image_l.shape[1], self.image_l.shape[2]))
            np.copyto(buf_l, self.image_l)
            buf_r = np.frombuffer(image_buffer_r, dtype=np.uint8, count=N)
            buf_r = buf_r.reshape((self.image_r.shape[0], self.image_r.shape[1], self.image_r.shape[2]))
            np.copyto(buf_r, self.image_r)
            # self.image = buf

