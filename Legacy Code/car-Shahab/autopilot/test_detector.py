#!env python3
import builtins
try:
    builtins.profile
except AttributeError:
    # No line profiler, provide a pass-through version
    def profile(func): return func
    builtins.profile = profile
from multiprocessing import Pipe, RawArray
import cv2
import numpy as np
from detector import Detector
import pycuda.autoinit
import pycuda.driver as drv
import libcudnn
from timer import Timer


fn = '000015.png';

cudnn_context = libcudnn.cudnnCreate()

detector = Detector('cnn/net-8-6-6-6-4-do00-bn.mat', cudnn_context=cudnn_context)
im = cv2.imread(fn)
im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)

with Timer('Detection'):
    for i in range(100):
        detector.detect(im)

cv2.imwrite('out.png', cv2.cvtColor(detector.vis, cv2.COLOR_BGR2RGB))



libcudnn.cudnnDestroy(cudnn_context)

