#!env python3

import cv2
import numpy as np
import amsvm

im = cv2.cvtColor(cv2.imread('../../data/local/amz/000001.png'),
                  cv2.COLOR_BGR2RGB)


from am import AM

am = AM('../am_yb_vs_bg_26x21_90_c_rgb.mat')


w = 21.0;
h = 26.0;


C = np.ndarray(shape=(im.shape[0], im.shape[1]), dtype=np.single)
tic = cv2.getTickCount()
for cy in range(im.shape[0]):
    print(cy)
    for cx in range(im.shape[1]):
        score, _ = am.eval_bbox_multiscale(im, cx, cy, 16 * 4)
        C[cy, cx] = max(0.0, score)

toc = cv2.getTickCount()
print((toc - tic) / cv2.getTickFrequency())

# C[C > 0] = 2.0 * C[C > 0]
C = C - np.nanmin(C)
C = C / np.nanmax(C)

cv2.imwrite('C_2c.png', C * 255)
