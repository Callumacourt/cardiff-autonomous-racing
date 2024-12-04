from video_source import VideoSource
from config import config
import cv2
import numpy as np
import airsim
from timer import Timer as timer

class SimulatorCamera(VideoSource):
    
    def __init__(self, sim, image_buffer_l, image_buffer_r, image_lock):      #initialises object with default and passed variables
        self.image_buffer_l = image_buffer_l
        self.image_buffer_r = image_buffer_r
        self.image_lock = image_lock
        self.image_l = None
        self.image_r = None
        self.image_l_prev = None
        self.image_r_prev = None
        self.paused = True
        self.sim = sim
        self.frame = 0
        self.requests = [airsim.ImageRequest("0", airsim.ImageType.Scene, False, False),
                         airsim.ImageRequest("1", airsim.ImageType.Scene, False, False)]         #not sure what this does?

    def play(self):
        self.paused = False

    def pause(self):
        self.paused = True

    # @profile
    def get(self):                        #reads/gets the image?
        # with Timer('Loading image'):
        if (not self.paused):
            # if self.image is None:
            #     ret, self.image = self.cap.read()
            # else:
            #     self.cap.read(self.image)
            # self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
            
            # TODO: Avoid copying by capturing directly into the buffer?
            # N = self.image.shape[0] * self.image.shape[1] * self.image.shape[2]
            # buf = np.frombuffer(self.image_buffer, dtype=np.uint8, count=N)
            # buf = buf.reshape((self.image.shape[0], self.image.shape[1], self.image.shape[2]))
            # np.copyto(buf, self.image)
            # self.image = buf
            if self.image_l is not None:
                self.image_l_prev = self.image_l.copy()
                self.image_r_prev = self.image_r.copy()

            # with timer('Get images'):
            responses = self.sim.client.simGetImages(self.requests)                            #not sure
            self.image_l = np.frombuffer(responses[0].image_data_uint8, dtype=np.uint8)
            self.image_l = self.image_l.reshape(responses[0].height, responses[0].width, 3)
            self.image_l = cv2.cvtColor(self.image_l, cv2.COLOR_BGR2RGB)
            self.image_r = np.frombuffer(responses[1].image_data_uint8, dtype=np.uint8)
            self.image_r = self.image_r.reshape(responses[1].height, responses[1].width, 3)
            self.image_r = cv2.cvtColor(self.image_r, cv2.COLOR_BGR2RGB)
            
            # both = cv2.cvtColor(np.concatenate((self.image_l, self.image_r), axis=1), cv2.COLOR_BGR2RGB)
            # cv2.imwrite("out/%06d.png" % self.frame, both) 
            self.frame += 1

            self.image_lock.acquire()                                                           #not sure
            N = self.image_l.shape[0] * self.image_l.shape[1] * self.image_l.shape[2]
            buf_l = np.frombuffer(self.image_buffer_l, dtype=np.uint8, count=N)
            buf_l = buf_l.reshape((self.image_l.shape[0], self.image_l.shape[1], self.image_l.shape[2]))
            np.copyto(buf_l, self.image_l)
            buf_r = np.frombuffer(self.image_buffer_r, dtype=np.uint8, count=N)
            buf_r = buf_r.reshape((self.image_r.shape[0], self.image_r.shape[1], self.image_r.shape[2]))
            np.copyto(buf_r, self.image_r)
            self.image_lock.release()

