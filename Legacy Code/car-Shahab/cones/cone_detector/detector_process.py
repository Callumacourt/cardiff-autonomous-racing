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

CMD_INIT_CUDA = 0
CMD_INIT_DETECTOR = 1
CMD_DETECT = 2
CMD_PLAY = 3
CMD_PAUSE = 4
CMD_ABORT = 5


class DetectorProcess(Process):
    def __init__(self, conn, image_buffer, result_buffer):
        Process.__init__(self)
        self.abort_requested = False
        self.conn = conn
        self.image_buffer = image_buffer
        self.result_buffer = result_buffer
        self.detector = None
        

    def init_cuda(self):
        log('Initialising CUDA.\n')
        cuda.init()
        self.context = make_default_context()
        self.device = self.context.get_device()
        self.cudnn_context = libcudnn.cudnnCreate()
        log('CUDA memory: ' + str(cuda.mem_get_info()))

    # @profile
    def run(self):
        # self.prof = LineProfiler()
        # self.prof.add_function(self.act)
        # self.prof.add_function(self.profiled_run)
        # self.prof.add_function(self.detect)
        # self.prof.runcall(self.profiled_run)
        self.profiled_run()
        
    def profiled_run(self):
        try:
            while not self.abort_requested:
                cmd = self.conn.recv()
                self.act(cmd)
        except KeyboardInterrupt:
            log('\nDP: KeyboardInterrupt.')
        finally:
            self.shutdown()
        

    def act(self, cmd):
        if isinstance(cmd, tuple):
            args = cmd[1]
            cmd = cmd[0]
        elif not isinstance(cmd, int):
            log('WARNING: Wrong command format.')

        if cmd == CMD_INIT_CUDA:
            self.init_cuda()
            return
        if cmd == CMD_INIT_DETECTOR:
            self.init_detector(args)
            return
        if cmd == CMD_DETECT:
            self.detect(args)
            return
        if cmd == CMD_ABORT:
            self.abort()
            return
        log('WARNING: Wrong command.')

    def init_detector(self, args):
        log('DP: initialising detector.')
        self.detector = Detector(args['cnn'],
                                 initial_scale=args['initial_scale'],
                                 scale_factor=args['scale_factor'],
                                 num_levels=args['num_levels'],
                                 context=self.context, cudnn_context=self.cudnn_context)
        # self.prof.add_function(self.detector.detect)


    def detect(self, args):
        # log('DP: detecting ' + str(args))
        h = args['height']
        w = args['width']
        N = h * w * 3 # TODO: Variable depth
        im = np.frombuffer(self.image_buffer, dtype=np.uint8, count=N).reshape((h, w, 3))
        self.detector.detect(im)
        result = np.frombuffer(self.result_buffer, dtype=np.uint8, count=N).reshape((h, w, 3))
        np.copyto(result, self.detector.cv_image)
        self.conn.send(0)

    def abort(self):
        log('DP: Abort requested.')
        self.abort_requested = True

    def shutdown(self):
        log('DP: Shutdown.')
        log('Destroying detector')
        del self.detector
        log('DP: Destroyung cuDNN context.')
        libcudnn.cudnnDestroy(self.cudnn_context)
        log('DP: Cleaning up CUDA.\n')
        self.context.pop()
        self.context = None
        clear_context_caches()

        if hasattr(self, 'prof'):
            self.prof.print_stats()

    def __del__(self):
        log('DP: __del__')
