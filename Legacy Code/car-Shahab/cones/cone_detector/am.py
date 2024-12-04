import numpy as np
import scipy.io as sio
import amsvm
from timer import Timer
import math

SD_THRESHOLD = 3.2

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
        self.svm_scale = 1.0 / (am['svm_scale'] * am['svm_scale'])
        self.bsvm_alphas = am['bsvm_alphas']
        self.bsvm_vectors = am['bsvm_vectors']
        self.bsvm_bias = am['bsvm_bias']
        self.bsvm_scale = 1.0 / (am['bsvm_scale'] * am['bsvm_scale'])
        # self.lda_B = am['lda_B']
        # self.lda_avg = am['lda_avg']

        self.buf = None
        if self.colour:
            self.allocate_buf(self.ch, self.cw, 3)
        else:
            self.allocate_buf(self.ch, self.cw)

        print(self.svm_vectors.shape)

        self.sd_max = (self.sd * SD_THRESHOLD + (self.B.T @ self.avg)) * self.a
        self.sd_min = (-self.sd * SD_THRESHOLD + (self.B.T @ self.avg)) * self.a

        self.B_original = self.B

        # print(self.B)
        self.B = self.B * self.a.T
        # print(self.B)
        
        # print(self.svm_vectors[0, :])
        # print(self.svm_vectors - self.b[:, None])
        self.svm_vectors = (self.svm_vectors - self.b[:, None] + self.B.T @ self.avg[:, None])

        
        self.bsvm_vectors = (self.bsvm_vectors - self.b[:, None] + self.B.T @ self.avg[:, None])

        # print(self.B.T @ self.avg[:, None])

        print(self.svm_vectors)
        print(self.svm_alphas)
        print(self.svm_bias)
        print(self.svm_scale)
        # print(self.svm_vectors.shape)
        # print(fn)
        # self.B = self.B / self.svm_scale
        # self.svm_vectors /= self.svm_scale

        # self.csvm_vectors -= (self.b - self.B.T @ self.avg)[:, None]

        

    def allocate_buf(self, h, w, d):
        if ((self.buf is None) or self.buf.shape[0] != h or
                self.buf.shape[1] != w or self.buf.shape[2] != d):
            self.buf = np.ndarray(shape=(h, w, d), dtype=np.single, order='F')

    def eval_bbox(self, im, x, y, w, h):
        amsvm.getwndnn(self.buf, im, x, y, w, h)
        return amsvm.am_project_svm(self.buf,
                                    self.B, self.sd_min, self.sd_max,
                                    self.svm_vectors, self.svm_alphas, self.svm_bias, self.svm_scale)

    def eval_bbox2(self, im, x, y, w, h):
        amsvm.getwndnn(self.buf, im, x, y, w, h)
        return amsvm.am_project_svm2(self.buf,
                                    self.B, self.sd_min, self.sd_max,
                                     self.svm_vectors, self.svm_alphas, self.svm_bias, self.svm_scale,
                                     self.bsvm_vectors, self.bsvm_alphas, self.bsvm_bias, self.bsvm_scale)

    def height2width(self, h):
        return 0.7902 * h

    def eval_bbox_multiscale(self, im, cx, cy, h0):
        h_space = np.linspace(0.75 * h0, 1.25 * h0, 5)
        # h_space = [0.7500 * h0, 0.8522 * h0, 0.9682 * h0, 1.1001 * h0, 1.2500 * h0]
        # h_space = [0.7500 * h0,    0.8068 * h0,   0.8679 * h0,
                   # 0.9336 * h0,   1.0042 * h0,  1.0803 * h0,  1.1620 * h0, 1.2500]
        # print("h_space = ", h_space)
        # h_space = [16, 27, 46, 80]
        best_score = float('-inf')
        best_bbox = []
        for i in range(len(h_space)):
            h = h_space[i]
            w = self.height2width(h)
            x = cx - (w - 1) * 0.5
            y = cy - (h - 1) * 0.5
            score = self.eval_bbox(im, x, y, w, h)
            # score1, score2 = self.eval_bbox2(im, x, y, w, h)
            # print(score1, score2)
            # score = max(score1, score2)
            # score = score1 + score2
            if score > best_score:
                best_score = score
                best_bbox = [x, y, w, h]

        if math.isinf(best_score):
            best_score = float('nan')

        return best_score, best_bbox

    def svm_pred(self, x):
        diff = self.svm_vectors - x[:, None]
        return (np.sum(self.svm_alphas *
                       np.exp(-np.sum(diff * diff, axis=0))) + self.svm_bias)

    def classify(self, im, x, y, w, h):
        return 0
        
        amsvm.getwndnn(self.buf, im, x, y, w, h)
        score =  amsvm.am_project_svm(self.buf,
                                    self.B, self.sd_min, self.sd_max,
                                    self.csvm_vectors, self.csvm_alphas, self.csvm_bias)
        # proj = (self.B_original.T @ (self.buf.flatten(order='F') - self.avg))
        # score = (self.lda_B.T @ (proj - self.lda_avg))
        if score > 0:
            return 1
        else:
            return 0
