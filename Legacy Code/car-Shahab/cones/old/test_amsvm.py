#!env python3

import cv2
import numpy as np
import scipy.io as sio
import amsvm

# im = cv2.imread('../../lenna.png')
# buf = np.ndarray(shape=(512, 512, 3), dtype=np.single, order='F')
# print(buf.strides)
# amsvm.getwnd(buf, im, 0, 0, im.shape[1], im.shape[0])

# cv2.imwrite('buf.png', (buf));

im = cv2.cvtColor(cv2.imread('../data/local/amz/000210.png'),
                  cv2.COLOR_BGR2RGB)


class AM(object):
    def __init__(self, fn):
        am = sio.loadmat(fn, squeeze_me=True)
        self.name = am['name']
        self.colour = bool(am['colour'])
        self.B = am['B']
        self.ev = am['ev']
        self.avg = am['avg']
        self.keep = am['keep']
        self.cw = am['cw']
        self.ch = am['ch']
        self.a = am['a']
        self.b = am['b']
        self.sd = am['sd']
        self.svm_alphas = am['svm_alphas']
        self.svm_vectors = am['svm_vectors']
        self.svm_bias = am['svm_bias']

        self.buf = None

    def allocate_buf(self, h, w, d):
        if ((self.buf is None) or self.buf.shape[0] != h or
            self.buf.shape[1] != w or self.buf.shape[2] != d):
            self.buf = np.ndarray(shape=(h, w, d), dtype=np.single, order='F')

    # @profile
    def eval_bbox(self, im, x, y, w, h):
        self.allocate_buf(am.ch, am.cw, im.shape[2])
        amsvm.getwnd(self.buf, im, x, y, w, h)

        # Project buffer into eigenpace
        # proj = (self.B.T @ (self.buf.flatten(order='F') - self.avg)) * self.a + self.b
        # SVM predicion
        # pred = self.svm_pred(proj)

        return amsvm.am_project_svm(self.buf,
                                    self.B, self.avg, self.a, self.b, self.sd,
                                    self.svm_vectors, self.svm_alphas, self.svm_bias)

    def height2width(self, h):
        return 0.7946 * h + 0.4918;

    def eval_bbox_multiscale(self, im, cx, cy, h0):
        # h_space = np.linspace(0.25 * h0, 1.5 * h0, 8)
        h_space = [16, 27, 46, 80]
        best_score = -1e6
        for i in range(len(h_space)):
            h = h_space[i]
            w = self.height2width(h)
            x = cx - (w - 1) * 0.5;
            y = cy - (h - 1) * 0.5;
            score = self.eval_bbox(im, x, y, w, h)
            if score > best_score:
                best_score = score

        return best_score
            

    def svm_pred(self, x):
        diff = self.svm_vectors - x[:, None]
        return (np.sum(self.svm_alphas *
                       np.exp(-np.sum(diff * diff, axis=0))) + self.svm_bias)


am = AM('am_y_vs_bg_26x21_90_rgb.mat')


w = 21.0;
h = 26.0;


C = np.ndarray(shape=(im.shape[0], im.shape[1]), dtype=np.single)
tic = cv2.getTickCount()
for cy in range(im.shape[0]):
    print(cy)
    # y = cy - (h - 1) * 0.5
    for cx in range(im.shape[1]):
        # x = cx - (w - 1) * 0.5
        C[cy, cx] = max(0.0, am.eval_bbox_multiscale(im, cx, cy, 16 * 4))

toc = cv2.getTickCount()
print((toc - tic) / cv2.getTickFrequency())

C = C - np.min(C)
C = C / np.max(C)

cv2.imwrite('C_.png', C * 255)
