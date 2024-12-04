#!/usr/bin/env python
import sys, time
import cv2
import roslib
import rospy
from cv_bridge import CvBridge, CvBridgeError
from sensor_msgs.msg import Image

VERBOSE=False


CASC_PATH = 'haar_face.xml'
faceCascade = cv2.CascadeClassifier(CASC_PATH)

class image_feature:

    def __init__(self):
        '''Initialize ros publisher, ros subscriber'''
        # topic where we
        # self.cones_pub = rospy.Publisher("/output/cones", String)
        # self.bridge = CvBridge()

        # subscribed Topic
        self.subscriber = rospy.Subscriber("/camera",
            Image, self.callback, queue_size = 1)
        self.bridge = CvBridge()
        
        if VERBOSE :
            print("subscribed to /camera/image/compressed")


    def callback(self, ros_data):
        if VERBOSE :
            print('received image of type: "%s"' % ros_data.format)
        try:
            cv_image = self.bridge.imgmsg_to_cv2(ros_data, desired_encoding="passthrough")
        except CvBridgeError as e:
            print(e)        

        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
    
        faces = faceCascade.detectMultiScale(
            gray,
            scaleFactor=2.0,
            minNeighbors=5,
            minSize=(30, 30),
            flags = cv2.CASCADE_SCALE_IMAGE
        )

        for (x, y, w, h) in faces:
            cv2.rectangle(cv_image, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.imshow('cv_img', cv_image)


        cv2.waitKey(1)


def main(args):
    '''Initializes and cleanup ros node'''
    ic = image_feature()
    rospy.init_node('image_feature', anonymous=True)
    try:
        rospy.spin()
    except KeyboardInterrupt:
        print("Shutting down ROS Image feature detector module")
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main(sys.argv)
