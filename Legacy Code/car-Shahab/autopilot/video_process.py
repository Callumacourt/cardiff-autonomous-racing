from multiprocessing import Process
# import time
from log import log
# import numpy as np
from line_profiler import LineProfiler
from ipc import *

CMD_GET = 0
CMD_ABORT = 1
CMD_SET_SOURCE = 2

class VideoProcess(Process):
    def __init__(self, conn):     #passes in video process conn feedback.
        Process.__init__(self)
        self.abort_requested = False     #stops process from being aborted.
        self.conn = conn                 #sets the object's conn to conn.
        self.video_source = None         #object has no video source.

    # @profile
    def run(self):       #calls the profiled_run function.
        # self.prof = LineProfiler()
        # self.prof.add_function(self.act)
        # self.prof.add_function(self.profiled_run)
        # self.prof.add_function(self.detect)
        # self.prof.runcall(self.profiled_run)
        self.profiled_run()

    def profiled_run(self):
        try:
            while not self.abort_requested:               #tries while abort_requested is False
                cmd = self.conn.recv()                    #sets cmd to received feedback from video process conn
                self.act(cmd)                             #calls act function
        except KeyboardInterrupt:                         #error catch for interrupt triggered via keyboard, e.g. alt + f4
            log('\Video process: KeyboardInterrupt.')     #updates the log with the interrupt
        finally:
            self.shutdown()       #shuts down system, either after interrupt or when while loop finishes.

    def act(self, cmd):
        if isinstance(cmd, tuple):     #if cmd is a tuple
            args = cmd[1]
            cmd = cmd[0]
        elif not isinstance(cmd, int):      #checks if cmd is not an int, error catch
            log('WARNING: Wrong command format.')
        if cmd == CMD_GET:       #CMD_GET defined at the top. 
            self.get(args)       #gets the arguements from self
            return               #exits function
        if cmd == CMD_ABORT:     #handles abort call
            self.abort()
            return               #exits function
        log('WARNING: Wrong command.')      #logs incorrect command

    def get(self, args):    # Notify the main process that the detection is complete
        self.conn.send(0)

    def abort(self):       #logs abort request and sets abort variable to true
        log('Video process: Normal abort requested.')
        self.abort_requested = True

    def shutdown(self):
        if hasattr(self, 'prof'):
            self.prof.print_stats()      #prints out statistics
        log('Video process: Shutting down.')     #logs shutdown
