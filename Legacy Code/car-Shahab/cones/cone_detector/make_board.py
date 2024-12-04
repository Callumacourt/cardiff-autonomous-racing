#!env python3

import numpy as np
import cv2
from cv2 import aruco

# points = [np.array([(0,0,0),(1,0,0),(1,-1,0),(0,-1,0)],('float32'))]
# arucoDict = aruco.Dictionary_get(aruco.DICT_4X4_50)
# ids = np.array([[0]])
# board = aruco.Board_create(points,arucoDict,ids)

board = aruco.GridBoard_create(7, 5, 30, 10, aruco.getPredefinedDictionary(aruco.DICT_4X4_50))
# print(board)
imboard = board.draw((4000, 2800))
cv2.imwrite("board.png", imboard)

