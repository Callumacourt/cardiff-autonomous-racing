#!env python3

import datetime
import numpy as np
import cv2
from cv2 import aruco


cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FPS, 50)
dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
board = aruco.GridBoard_create(7, 5, 30, 10, dict)
parameters =  aruco.DetectorParameters_create()

aruco_marker_length_meters = 100

camera_matrix = np.array([[775.1396, 0, 0], [0.1312, 775.1908, 0], [326.0607, 226.0587, 1.0000]])
dist_coeffs = np.array([-0.1309, 0.3687, -0.0016, 0.0019, -0.4446]).transpose()
rvec = cv2.UMat(3, 1, cv2.CV_32F)
tvec = cv2.UMat(3, 1, cv2.CV_32F)

while(True):
    # Capture frame-by-frame
    ret, frame_markers = cap.read()

    # Our operations on the frame come here
    gray = cv2.cvtColor(frame_markers, cv2.COLOR_BGR2GRAY)

    t = datetime.datetime.now()
    corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, dict, parameters=parameters)
    print('%.3f' % ((datetime.datetime.now() - t).total_seconds() * 1000.0))

    # frame_markers = aruco.drawDetectedMarkers(frame.copy(), corners, ids)

    retval, rvec, tvec = aruco.estimatePoseBoard(corners, ids, board, camera_matrix, dist_coeffs, rvec, tvec)
    print(retval, rvec.get(), tvec.get())
    
    frame_markers = aruco.drawAxis(frame_markers, camera_matrix, dist_coeffs, rvec, tvec, aruco_marker_length_meters)
    # frame_markers = aruco.drawDetectedMarkers(frame_markers, corners, ids)


    cv2.imshow('frame', frame_markers)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()

