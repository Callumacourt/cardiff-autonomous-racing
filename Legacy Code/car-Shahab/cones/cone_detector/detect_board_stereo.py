#!env python3

import glob
import numpy as np
import cv2
from cv2 import aruco

dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
board = aruco.GridBoard_create(7, 5, 30, 10, dict)
parameters =  aruco.DetectorParameters_create()

camera_matrix_l = np.array([[779.6981,         0,         0],
                           [0,  780.0992,         0],
                           [323.5489,  224.2113,    1.0000]]).transpose()
dist_coeffs_l = np.array([-0.1069, 0.0615, -0.0015, 0.0014, 0.4904]).transpose()

camera_matrix_r = np.array([[548.6055,         0,         0],
                            [0,  547.8158,         0],
                            [305.3728,  227.9431,    1.0000]]).transpose()
dist_coeffs_r = np.array([-0.1204, 0.2374, -0.0028, 0.0025, -0.0707]).transpose()


filenames = sorted(glob.glob('../../data/recording.2310191746/*.jpg'))
rvec_l = cv2.UMat(3, 1, cv2.CV_32F)
tvec_l = cv2.UMat(3, 1, cv2.CV_32F)
rvec_r = cv2.UMat(3, 1, cv2.CV_32F)
tvec_r = cv2.UMat(3, 1, cv2.CV_32F)

with open('out/board.txt', 'w+') as f:
    for fn in filenames:
        print(fn)
        im = cv2.imread(fn)
        width = im.shape[1]
        left = im[:, 0:int(width/2), :]
        right = im[:, int(width/2):, :]
        gray_left = cv2.cvtColor(left, cv2.COLOR_BGR2GRAY)
        gray_right = cv2.cvtColor(right, cv2.COLOR_BGR2GRAY)

        corners_l, ids_l, rejectedImgPoints_l = aruco.detectMarkers(gray_left, dict, parameters=parameters)
        corners_l, ids_l, rejectedImgPoints_l, recovered_l = aruco.refineDetectedMarkers(gray_left, board, corners_l, ids_l, rejectedImgPoints_l, camera_matrix_l, dist_coeffs_l)
        
        corners_r, ids_r, rejectedImgPoints_r = aruco.detectMarkers(gray_right, dict, parameters=parameters)        
        corners_r, ids_r, rejectedImgPoints_r, recovered_r = aruco.refineDetectedMarkers(gray_right, board, corners_r, ids_r, rejectedImgPoints_r, camera_matrix_r, dist_coeffs_r)
        
        retval_l, rvec_l, tvec_l = aruco.estimatePoseBoard(corners_l, ids_l, board,
                                                           camera_matrix_l, dist_coeffs_l, rvec_l, tvec_l)
        retval_r, rvec_r, tvec_r = aruco.estimatePoseBoard(corners_r, ids_r, board,
                                                           camera_matrix_r, dist_coeffs_r, rvec_r, tvec_r)
        rot_l = rvec_l.get()
        trans_l = tvec_l.get()
        rot_r = rvec_r.get()
        trans_r = tvec_r.get()
        f.write('%d %f %f %f %f %f %f %d %f %f %f %f %f %f\n' % (retval_l,
                                        rot_l[0], rot_l[1], rot_l[2],
                                        trans_l[0], trans_l[1], trans_l[2],
                                        retval_r,
                                        rot_r[0], rot_r[1], rot_r[2],
                                        trans_r[0], trans_r[1], trans_r[2]))

