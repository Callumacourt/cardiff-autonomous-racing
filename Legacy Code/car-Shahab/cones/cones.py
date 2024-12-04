#!env python

# import numpy as np
import cv2

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FPS, 60)

CASC_PATH = 'haar_face.xml'
# CASC_PATH = 'cone_detector_ybsr_pad125.xml'
faceCascade = cv2.CascadeClassifier(CASC_PATH)


while(True):
    # Capture frame-by-frame
    ret, frame = cap.read()

    # Our operations on the frame come here
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = faceCascade.detectMultiScale(
        gray,
        scaleFactor=1.25,
        minNeighbors=5,
        minSize=(32, 24),
        flags = cv2.CASCADE_SCALE_IMAGE
    )
    print(faces)
    # Display the resulting frame
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

    cv2.imshow('frame', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
