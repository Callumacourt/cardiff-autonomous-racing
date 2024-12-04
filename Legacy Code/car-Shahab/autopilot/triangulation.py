#!env python3
import numpy as np
import scipy.io as sio
from skimage import measure
import cv2
from timer import Timer as timer
from scipy import stats, optimize
import math

THR_SOFT = 0.5

det_l = sio.loadmat('Cl.mat')['Cl']
det_r = sio.loadmat('Cr.mat')['Cr']
P1 = sio.loadmat('P1.mat')['P1']
P2 = sio.loadmat('P2.mat')['P2']


def triangulate(P1, P2, left, right):
    X = cv2.triangulatePoints(P1, P2, left, right)
    X = X / X[3]

    reproj_left = P1 @ X
    reproj_left = reproj_left / reproj_left[2]
    reproj_right = P2 @ X
    reproj_right = reproj_right / reproj_right[2]
    err = [np.linalg.norm((left - reproj_left[0:2].T).T),
           np.linalg.norm((right - reproj_right[0:2].T).T)]

    return X[0:3], err

def cone_centroids(det):
    lab = np.argmax(det, axis=2)
    soft = np.amax(det, axis=2)

    _, soft_thr = cv2.threshold(soft, THR_SOFT, 1, cv2.THRESH_BINARY)
    n_cc, cc_labels = cv2.connectedComponents(
        soft_thr.astype(np.uint8))

    cones = np.zeros((3, n_cc - 1))

    # TODO: Merge nerby connected components
    for i in range(n_cc - 1):
        row, col = np.where(cc_labels == i + 1)
        val = soft[row, col]
        den = np.sum(val)
        cones[0, i] = np.sum(col * val) / den + 1.0;
        cones[1, i] = np.sum(row * val) / den + 1.0;
        cones[2, i] = stats.mode(lab[row, col])[0]

    return cones

# TODO: Filter those below the hard threshold
cones_l = cone_centroids(det_l)
cones_r = cone_centroids(det_r)
# print(cones_l.shape)
# print(cones_r.shape)

G = np.zeros((cones_l.shape[1], cones_r.shape[1]))
W = np.zeros((cones_l.shape[1], cones_r.shape[1], 3))
for i in range(cones_l.shape[1]):
    for j in range(cones_r.shape[1]):
        p3d, err = triangulate(P1, P2, cones_l[0:2, i], cones_r[0:2, j])
        err = np.max(err)
        W[i, j, :] = p3d.flatten()
        if err > 5.0 or p3d[2] < 0.0 or cones_l[2, i] != cones_r[2, j]:
            G[i, j] = 10000
        else:
            G[i, j] = err

# print(G)
row, col = optimize.linear_sum_assignment(G)
print(row, col)
edge_cost = G[row, col]
print(edge_cost)
# cv2.imwrite('cc_l.png', labels_im * 15)
