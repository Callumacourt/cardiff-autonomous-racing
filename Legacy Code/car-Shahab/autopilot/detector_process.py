from multiprocessing import Process
import time
import libcudnn
import pycuda
import pycuda.driver as cuda
from pycuda.tools import make_default_context, clear_context_caches
from log import log
from detector import Detector
import numpy as np
from line_profiler import LineProfiler
from ipc import *

CMD_INIT_CUDA = 0
CMD_INIT_DETECTOR = 1
CMD_DETECT = 2
CMD_PLAY = 3
CMD_PAUSE = 4
CMD_ABORT = 5


class DetectorProcess(Process):
    def __init__(self, conn):     #initialises object.
        Process.__init__(self)
        self.abort_requested = False
        self.conn = conn
        self.detector = None
        

    def init_cuda(self):          #initialises CUDA
        log('Initialising CUDA.\n')       #logs CUDA initialisation
        cuda.init()
        self.context = make_default_context()         #sets default context from pycuda
        self.device = self.context.get_device()
        self.cudnn_context = libcudnn.cudnnCreate()
        log('CUDA memory: ' + str(cuda.mem_get_info()))       #logs CUDA memory

    # @profile
    def run(self):                   #calls run profiled_run function
        # self.prof = LineProfiler()
        # self.prof.add_function(self.act)
        # self.prof.add_function(self.profiled_run)
        # self.prof.add_function(self.detect)
        # self.prof.runcall(self.profiled_run)
        self.profiled_run()
        
    def profiled_run(self):
        try:
            while not self.abort_requested:     #tries while abort_requested is False
                cmd = self.conn.recv()          #sets cmd to received feedback from detector process conn
                self.act(cmd)                   
        except KeyboardInterrupt:               #error catch for interrupt triggered via keyboard, e.g. alt + f4
            log('\nDetector process: KeyboardInterrupt.')       #updates the log with the interrupt
        finally:
            self.shutdown()       #shuts down system, either after interrupt or when while loop finishes.

    def act(self, cmd):
        if isinstance(cmd, tuple):          #if cmd is a tuple
            args = cmd[1]
            cmd = cmd[0]
        elif not isinstance(cmd, int):        #checks if cmd is not an int, error catch
            log('WARNING: Wrong command format.')             #logs warning

        if cmd == CMD_INIT_CUDA:       #initialises CUDA
            self.init_cuda()
            return
        if cmd == CMD_INIT_DETECTOR:      #initialises detector
            self.init_detector(args)
            return
        if cmd == CMD_DETECT:       #detects
            self.detect(args)
            return
        if cmd == CMD_ABORT:        #aborts
            self.abort()
            return
        log('WARNING: Wrong command.')        #logs incorrect command.

    def init_detector(self, args):             #initialises detector
        log('Detector process: initialising detector.')
        self.detector = Detector(args['cnn'],           #sets default values for detector
                                 initial_scale=args['initial_scale'],
                                 scale_factor=args['scale_factor'],
                                 num_levels=args['num_levels'],
                                 context=self.context, cudnn_context=self.cudnn_context)
        # if hasattr(self, 'prof'):
            # self.prof.add_function(self.detector.detect)


    def detect(self, args):
        # log('Detector process: detecting ' + str(args))
        h = args['height']         #gets height of detected object
        w = args['width']          #gets width of detected object
        N = h * w * 3 # TODO: Variable depth       #calculates depth
        image_lock.acquire()
        im_l = np.frombuffer(image_buffer_l, dtype=np.uint8, count=N).reshape((h, w, 3)).copy()      #sets image as seen from left camera
        im_r = np.frombuffer(image_buffer_r, dtype=np.uint8, count=N).reshape((h, w, 3)).copy()      #sets image as seen from right camera
        image_lock.release()          #releases lock, so cameras can find next object

        # TODO: Check if some of the operations can be done more efficiently on both images at once.
        
        self.detector.detect(im_l)                     #sets results from the left camera
        result_l = np.frombuffer(result_buffer_l,        
                                    dtype=np.float32, count=N).reshape((h, w, 3))
        coneness_l = np.frombuffer(coneness_buffer_l,
                                    dtype=np.float32, count=h * w).reshape((h, w))
        labels_l = np.frombuffer(labels_buffer_l,
                                    dtype=np.uint8, count=h * w).reshape((h, w))
        vis_l = np.frombuffer(vis_buffer_l,
                                    dtype=np.uint8, count=h * w * 3).reshape((h, w, 3))
        
        result_lock.acquire()
        # np.copyto(result_l, self.detector.detection_result)
        np.copyto(coneness_l, self.detector.coneness)
        np.copyto(labels_l, self.detector.labels)
        np.copyto(vis_l, self.detector.vis)
        result_lock.release()

        self.detector.detect(im_r)                #sets results from the right camera
        result_r = np.frombuffer(result_buffer_r,
                                     dtype=np.float32, count=N).reshape((h, w, 3))
        coneness_r = np.frombuffer(coneness_buffer_r,
                                    dtype=np.float32, count=h * w).reshape((h, w))
        labels_r = np.frombuffer(labels_buffer_r,
                                    dtype=np.uint8, count=h * w).reshape((h, w))
        vis_r = np.frombuffer(vis_buffer_r,
                                    dtype=np.uint8, count=h * w * 3).reshape((h, w, 3))
        result_lock.acquire()
        # np.copyto(result_r, self.detector.detection_result)
        np.copyto(coneness_r, self.detector.coneness)
        np.copyto(labels_r, self.detector.labels)
        np.copyto(vis_r, self.detector.vis)
        result_lock.release()

        # Notify the main process that the detection is complete
        self.conn.send(0)

    def abort(self):        #aborts the detection process
        log('Detector process: Normal abort requested.')
        self.abort_requested = True
 
    def shutdown(self):              #shutsdown the detection process and logs it
        if hasattr(self, 'prof'):
            self.prof.print_stats()
        log('Detector process: Initiating shutdown.')         #initiates shutdown.
        log('Destroying detector')
        if hasattr(self, 'detector'):
            del self.detector
        log('Detector process: Destroying cuDNN context.')        #destroys cuDNN context
        libcudnn.cudnnDestroy(self.cudnn_context)
        log('Detector process: Cleaning up CUDA.\n')       #cleans up CUDA
        self.context.pop()
        self.context = None
        clear_context_caches()     #clears caches.


    # def __del__(self):
        # log('Detector process: __del__')
