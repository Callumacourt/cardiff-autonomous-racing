from threading import Thread        # multui threadding
#basic mathmatical libs
import math
import time
import wx
import cv2      #open cv 2
from image_folder import ImageFolder #self built modules
from log import log
from timer import Timer
from config import config
from CNN import CNN, load_cnn
import numpy as np
import pycuda
from pycuda import gpuarray
from config import config
from tools import round
from kernels import Kernels
# detector = None


class Detector:
    def __init__(self, net_filename, initial_scale=config.CD_INITIAL_SCALE,
                 scale_factor=config.CD_SCALE_FACTOR, num_levels=config.CD_PYRAMID_LEVELS,
                 context=None, cudnn_context=None):
        #initial declerations to help build functoin sturcture
        #Inlcudes data for the cnn and nn refer to cuda documentations 
        self.h = None
        self.w = None
        self.roi_h = None
        # self.roi_w = None
        self.initial_scale = initial_scale
        self.scale_factor = scale_factor
        self.num_levels = int(num_levels)
        self.context = context
        self.cudnn_context = cudnn_context
        self.sizes = None
        self.kernels = Kernels(self.context)
        if self.context is not None:
            self.context.push()
        self.layers = load_cnn(net_filename)
        if self.context is not None:
            self.context.pop()
        self.images = None
        self.tensors = None
        self.roi_image = None
#funstion to set vars to default vals
    def reset(self, h, w, roi_h):
        log('Initialising detector.')
        self.h = h
        self.w = w
        self.roi_h = roi_h
        # self.roi_w = roi_w
        # Compute the scaling factors and the resulting absolute image sizes.
        self.scales = self.initial_scale / \
            np.power(self.scale_factor, np.linspace(
                0, self.num_levels - 1, self.num_levels))
        log('Scales: ' + str(self.scales))

        # For each scale allocate appropriate inputs, outputs, and workspaces
        self.net = [None] * self.scales.size
        self.images = [None] * self.scales.size
        self.tensors = [None] * self.scales.size
        self.detections_gpu = [None] * self.scales.size

        self.sizes = np.zeros((2, self.scales.size), dtype=np.int32)
        for i, scale in enumerate(self.scales):
            self.sizes[0, i] = int(round(self.roi_h * scale))
            self.sizes[1, i] = int(round(self.w * scale))
            self.net[i] = CNN(self.layers, context=self.context,
                              cudnn_context=self.cudnn_context, kernels=self.kernels)
        log('Sizes:\n' + str(self.sizes))
#need a deeper understanding of the following paramters and their effects
        # self.coneness_gpu = gpuarray.empty((h, w), np.float32)
        # self.labels_gpu = gpuarray.empty((h, w), np.uint8)
        # self.vis_gpu = gpuarray.empty((h, w, 3), np.uint8)
        self.coneness_roi_gpu = gpuarray.empty((roi_h, w), np.float32)
        self.labels_roi_gpu = gpuarray.empty((roi_h, w), np.uint8)
        self.vis_roi_gpu = gpuarray.empty((roi_h, w, 3), np.uint8)
#unsure of this command
    @profile
    def detect(self, image):#main cone detection functions
        if self.context:
            self.context.push()

        self.image = image
        # Crop to ROI if necessary
        if config.CD_USE_ROI:
            h, w, c = image.shape
            self.top = int(round(h * config.CD_ROI_TOP * 0.01))
            self.bottom = int(h - round(h * config.CD_ROI_BOTTOM * 0.01))
            self.roi_image = image[self.top:self.bottom, :, :]
        else:
            self.top = 0
            self.roi_image = image

        if ((self.h != self.image.shape[0]) or
            (self.w != self.image.shape[1]) or
                (self.roi_h != self.roi_image.shape[0])):
            # Image size has changed or it is the first iteration
            self.reset(image.shape[0], image.shape[1], self.roi_image.shape[0])

        # Create image pyramid
        # TODO: Is it better to resize on GPU?
        for i in range(self.sizes.shape[1]):
            if not (self.roi_h == self.sizes[0, i] and self.w == self.sizes[1, i]):
                self.images[i] = cv2.resize(
                    self.roi_image, (self.sizes[1, i], self.sizes[0, i]))
            else:  # No need to resize
                self.images[i] = self.roi_image

        # Create NCHW tensors from the image pyramid
        for i in range(self.sizes.shape[1]):
            # TODO: Do it in one shader
            self.tensors[i] = np.ascontiguousarray(np.transpose(
                self.images[i][:, :, :, None], (3, 2, 0, 1))).astype(np.float32)

        # self.detection_gpu.fill(0.0)
        # TODO: allocate only once
        self.detection_gpu = gpuarray.zeros(
            (4, self.roi_h, self.w), dtype=np.float32)

        # Iterate over scales
        for i in range(self.sizes.shape[1]):
            self.detections_gpu[i] = self.net[i].predict(self.tensors[i])
            if self.detections_gpu[i] is None:
                return  # This may happen if the application is being destroyed

            newh = self.detection_gpu.shape[1]
            neww = self.detection_gpu.shape[2]
            block = (16, 16, 1)  # TODO: Optimise block sizes
            gridy = newh // block[0] if newh % block[0] == 1 else newh // block[0] + 1
            gridx = neww // block[1] if neww % block[1] == 1 else neww // block[1] + 1

            oldh = self.detections_gpu[i].shape[2]
            oldw = self.detections_gpu[i].shape[3]
            if (oldh != newh) or (oldw != neww):
                scale_a = oldw / neww
                scale_b = oldh / newh

                # Rescale to original size and take max: result = max(this, result)
                self.kernels.resize_write_max(self.detections_gpu[i], self.detection_gpu,
                                              np.int32(oldh), np.int32(oldw),
                                              np.int32(newh), np.int32(neww),
                                              np.float32(scale_a), np.float32(
                                                  scale_b),
                                              block=block, grid=(gridx, gridy))
            else:
                n = self.detection_gpu.size
                # TODO: Do we need a max here? In a special case when this is the
                # first of the scales we do not. But beware that the initial_scale
                # may not be one.
                self.kernels.write_max(self.detections_gpu[i], self.detection_gpu,
                                       np.int32(n),
                                       block=(256, 1, 1), grid=((n + 255) // 256, 1))

        n = self.detection_gpu.shape[2] * self.detection_gpu.shape[1]
        self.kernels.threshold_max_argmax_label(self.detection_gpu, self.coneness_roi_gpu, self.labels_roi_gpu,
                                                np.int32(n), np.float32(0.5),
                                                block=(256, 1, 1), grid=((n + 255) // 256, 1))
        self.coneness_roi = self.coneness_roi_gpu.get()
        self.labels_roi = self.labels_roi_gpu.get()

        # Visualisation
        # saturation = 0.15
        # brightness = 0.5
        saturation = 1.0
        brightness = 1.0
        alpha = saturation * brightness
        beta = brightness - alpha
        # TODO: Avoid uploading the image again
        im_gpu = gpuarray.to_gpu(self.roi_image)
        self.kernels.visualise_detection(self.detection_gpu, im_gpu, self.vis_roi_gpu, np.int32(n),
                                         np.float32(alpha), np.float32(beta),
                                         block=(256, 1, 1), grid=((n + 255) // 256, 1))
        self.vis_roi = self.vis_roi_gpu.get()
        # self.vis = self.image
        if config.CD_USE_ROI:
            self.coneness = np.zeros((self.h, self.w), dtype=np.float32)
            self.labels = np.zeros((self.h, self.w), dtype=np.uint8)
            # np.zeros((self.h, self.w, 3), dtype=np.uint8)
            self.vis = self.image
            self.coneness[self.top:self.bottom, :] = self.coneness_roi
            self.labels[self.top:self.bottom, :] = self.labels_roi
            self.vis[self.top:self.bottom, :, :] = self.vis_roi
        else:
            self.coneness = self.coneness_roi
            self.labels = self.labels_roi
            self.vis = self.vis_roi

        # self.detection_result = np.ascontiguousarray(np.transpose(
        #     self.detection, (1, 2, 0)))[:, :, 0:3]

        if self.context:
            self.context.pop()
