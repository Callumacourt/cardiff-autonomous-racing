#!env python3
import cv2
import numpy as np
import time

NUM_CAMERAS = 2 #edit this dependant on the number of cameras your laptop is holding don't forget about the in-built camera
cap = [None] * NUM_CAMERAS
for i in range(NUM_CAMERAS):
    cap[i] = cv2.VideoCapture(i)
    cap[i].set(cv2.CAP_PROP_FPS, 60)

FPS = 0
t = time.time()
frame_num = 0
while(True):
    ret = [None] * NUM_CAMERAS
    frame = [None] * NUM_CAMERAS
    for i in range(NUM_CAMERAS):
        ret[i], frame[i] = cap[i].read()

    both = np.concatenate((frame[0], frame[1]), axis=1) # edit the number inside the square bracket to change which camera it is referencing
        
    # for i in range(NUM_CAMERAS):
    #     cv2.imshow(str(i), frame[i])
    cv2.imshow("STEREO", both)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    cv2.imwrite("recording/%06d.jpg" % (frame_num), both)

    frame_num += 1
    FPS += 1
    new_t = time.time()
    if new_t - t > 1:
        print("FPS: " + str(FPS))
        FPS = 0
        t = new_t

    print(str(frame_num))

for i in range(NUM_CAMERAS):
    cap[i].release()

cv2.destroyAllWindows()
