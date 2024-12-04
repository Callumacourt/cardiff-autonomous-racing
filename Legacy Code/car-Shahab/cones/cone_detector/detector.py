from threading import Thread
import math
import time
import wx
import cv2
from image_folder import ImageFolder
from log import log
from timer import Timer
from config import config
from CNN import CNN, load_cnn
import numpy as np
import pycuda
from pycuda import gpuarray
from config import config

detector = None

class Detector:
    def __init__(self, net_filename, initial_scale=config.CD_INITIAL_SCALE,
                 scale_factor=config.CD_SCALE_FACTOR, num_levels=config.CD_PYRAMID_LEVELS,
                 context=None, cudnn_context=None):
        self.bboxes = []
        self.bboxesf = []
        self.h = None
        self.w = None
        self.initial_scale = initial_scale
        self.scale_factor = scale_factor
        self.num_levels = int(num_levels)
        self.context = context
        self.cudnn_context = cudnn_context
        self.sizes = None
        if self.context is not None:
            self.context.push()
        self.layers = load_cnn(net_filename)
        if self.context is not None:
            self.context.pop()
        self.images = None
        self.tensors = None
        self.cv_image = None
        with open('resize_max.cu', 'r') as f:
            resize_max_src = f.read()

        resize_max_kernel = pycuda.compiler.SourceModule(resize_max_src) # , options=['-ccbin', '/usr/bin/gcc-8']
        # TODO: Make it an option
        self.resize_write_max = resize_max_kernel.get_function(
            "resize_nn_write_max")
        self.write_max = resize_max_kernel.get_function("write_max")
        self.threshold = resize_max_kernel.get_function("threshold")

    def reset(self, h, w):
        log('Initialising detector.')
        self.h = h
        self.w = w
        self.scales = self.initial_scale / \
            np.power(self.scale_factor, np.linspace(
                0, self.num_levels - 1, self.num_levels))
        log('Scales: ' + str(self.scales))
        self.net = [None] * self.scales.size
        self.images = [None] * self.scales.size
        self.tensors = [None] * self.scales.size
        # self.detections = [None] * self.scales.size
        self.detections_gpu = [None] * self.scales.size
        self.sizes = np.zeros((2, self.scales.size), dtype=np.int)
        for i, scale in enumerate(self.scales):
            self.sizes[0, i] = int(round(self.h * scale))
            self.sizes[1, i] = int(round(self.w * scale))
            self.net[i] = CNN(self.layers, context=self.context, cudnn_context=self.cudnn_context)
        log('Sizes:\n' + str(self.sizes))

    # @profile
    def detect(self, image):
        if self.context:
            self.context.push()

        if (self.h != image.shape[0]) or (self.w != image.shape[1]):
            # Image size has changed or it is the first iteration
            self.reset(image.shape[0], image.shape[1])

        # Copy the image from the video source and crop to ROI if necessary
        if config.CD_USE_ROI:
            h, w, c = image.shape
            self.top = int(round(h * config.CD_ROI_TOP * 0.01))
            self.bottom = int(h - round(h * config.CD_ROI_BOTTOM * 0.01))
            self.cv_image = image[self.top:self.bottom, :, :]
        else:
            self.top = 0
            self.cv_image = image

        # Create image pyramid
        for i in range(self.sizes.shape[1]):
            if not (self.h == self.sizes[0, i] and self.w == self.sizes[1, i]):
                self.images[i] = cv2.resize(
                    self.cv_image, (self.sizes[1, i], self.sizes[0, i]))
            else:
                self.images[i] = self.cv_image

        # Create NCHW tensors from the image pyramid
        for i in range(self.sizes.shape[1]):
            # TODO: Do it in one shader
            self.tensors[i] = np.ascontiguousarray(np.transpose(
                self.images[i][:, :, :, None], (3, 2, 0, 1))).astype(np.float32)

        # Grayscale version of the original image for display
        self.cv_image_gray = cv2.cvtColor(
            self.cv_image, cv2.COLOR_RGB2GRAY) * 0.5

        # Perform cone detection
        # self.detection = np.zeros((self.h, self.w, 4), dtype=np.float32)

        # self.detection_gpu.fill(0.0)
        self.detection_gpu = gpuarray.zeros(
            (4, self.h, self.w), dtype=np.float32)
        # TODO: allocate only once
        for i in range(self.sizes.shape[1]):
            # self.detections[i] = self.net[i].predict(self.tensors[i]).get()
            # print(self.tensors[i].shape)
            self.detections_gpu[i] = self.net[i].predict(self.tensors[i])
            if self.detections_gpu[i] is None:
                return  # This may happen if the application is being destroyed
            # self.detections[i] = np.ascontiguousarray(np.transpose(self.detections[i], (0, 2, 3, 1)))
            # self.detections[i] = cv2.resize(self.detections[i][0, :, :, :], (self.w, self.h))
            # self.detection = np.maximum(self.detection, self.detections[i])

            newh = self.detection_gpu.shape[1]
            neww = self.detection_gpu.shape[2]
            block = (16, 16, 1)
            gridy = newh // block[0] if newh % block[0] == 1 else newh // block[0] + 1
            gridx = neww // block[1] if neww % block[1] == 1 else neww // block[1] + 1

            # print(newh, neww)
            # print(self.detections_gpu[i].shape)
            # print(gridx, gridy)
            oldh = self.detections_gpu[i].shape[2]
            oldw = self.detections_gpu[i].shape[3]
            if (oldh != newh) or (oldw != neww):
                scale_a = oldw / neww
                scale_b = oldh / newh

                self.resize_write_max(self.detections_gpu[i], self.detection_gpu,
                                      np.int32(oldh), np.int32(oldw),
                                      np.int32(newh), np.int32(neww),
                                      np.float32(scale_a), np.float32(scale_b),
                                      block=block, grid=(gridx, gridy))
            else:
                n = self.detection_gpu.size
                self.write_max(self.detections_gpu[i], self.detection_gpu,
                               np.int32(n),
                               block=(256, 1, 1), grid=((n + 255) // 256, 1))

        n = self.detection_gpu.size
        self.threshold(self.detection_gpu, np.int32(n), np.float32(config.CD_ABS_THRESHOLD),
                       block=(256, 1, 1), grid=((n + 255) // 256, 1))
        self.detection_gpu = self.detection_gpu.get()
        # self.detection[self.detection < config.CD_ABS_THRESHOLD] = 0

        self.detection_cv = (np.ascontiguousarray(np.transpose(
            self.detection_gpu, (1, 2, 0)))[:, :, 0:3] * 255.0).astype(np.uint8)

        # self.cv_image = np.maximum(self.cv_image, image)

        # self.cv_image = np.zeros((self.h, self.w, 3), dtype=np.uint8)
        # self.cv_image[:, :, 0] = self.cv_image_gray
        # self.cv_image[:, :, 1] = self.cv_image_gray
        # self.cv_image[:, :, 2] = self.cv_image_gray

        self.cv_image = image.copy()
        # print(self.cv_image.shape, self.cv_image_gray.shape, self.detection_cv.shape)

        self.cv_image[:, :, 0] = np.maximum(
            self.cv_image_gray, self.detection_cv[:, :, 0])
        self.cv_image[:, :, 1] = np.maximum(
            self.cv_image_gray, self.detection_cv[:, :, 0])
        self.cv_image[:, :, 2] = np.maximum(
            self.cv_image_gray, self.detection_cv[:, :, 1])

        # self.bboxesf = []
        # bw = (self.detection_gpu[0, :, :] > 0).astype(np.uint8)
        # num, labels, stats, centroids = cv2.connectedComponentsWithStats(bw)
        # for i in range(1, num):
        #     self.bboxesf.append(
        #         [stats[i, 0], stats[i, 1], stats[i, 2], stats[i, 3], 0])
        # bw = (self.detection_gpu[1, :, :] > 0).astype(np.uint8)
        # num, labels, stats, centroids = cv2.connectedComponentsWithStats(bw)
        # for i in range(1, num):
        #     self.bboxesf.append(
        #         [stats[i, 0], stats[i, 1], stats[i, 2], stats[i, 3], 1])

        if self.context:
            self.context.pop()
