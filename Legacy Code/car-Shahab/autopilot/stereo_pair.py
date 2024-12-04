import numpy as np
import scipy.io as sio
import cv2

def project_point(P, X):
    proj = P @ X
    return proj / proj[2]

class StereoPair:
    def __init__(self):
        # recieving incoming data from camera
        
        cam = sio.loadmat('cam.mat')
        self.P1 = cam['P1']
        self.P2 = cam['P2']
        self.I1 = cam['I1']
        self.I2 = cam['I2']
        self.coeffs1 = cam['coeffs1']
        self.coeffs2 = cam['coeffs2']
        # self.GtoC = cam['GtoC']
        # self.CtoG = cam['CtoG']

    # @profile
    def project(self, X):
        # Making two distinct images for each camera
        proj_left = project_point(self.P1, X)
        proj_right = project_point(self.P2, X)
        return proj_left, proj_right

    # @profile
    def triangulate(self, left, right):
        #Triangulate linear points between the two images from cameras
        
        # TODO: Port non-linear triangulation.
        X = cv2.triangulatePoints(self.P1, self.P2, left, right)
        X = X / X[3]
        reproj_left, reproj_right = self.project(X)
        err = [np.linalg.norm((left - reproj_left[0:2].T).T),
               np.linalg.norm((right - reproj_right[0:2].T).T)]
        return X[0:3], err
