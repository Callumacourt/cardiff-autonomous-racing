#!env python3

import datetime
# import numpy as np
import cv2
from cv2 import aruco


cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FPS, 50)

# CASC_PATH = 'haar_face.xml'
# CASC_PATH = 'cone_detector_ybsr_pad125.xml'
# faceCascade = cv2.CascadeClassifier(CASC_PATH)

aruco_dict = aruco.Dictionary_get(aruco.DICT_4X4_50)
parameters =  aruco.DetectorParameters_create()

while(True):
    # Capture frame-by-frame
    ret, frame = cap.read()

    # Our operations on the frame come here
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    t = datetime.datetime.now()
    corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
    print('%.3f' % ((datetime.datetime.now() - t).total_seconds() * 1000.0))

    frame_markers = aruco.drawDetectedMarkers(frame.copy(), corners, ids)


    cv2.imshow('frame', frame_markers)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
