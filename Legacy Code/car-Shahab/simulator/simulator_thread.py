import os
from threading import *
import math
import time
import wx
# import neat
from log import log
from config import config
from log import log
from simulator import *


class SimulatorThread(Thread):
    def __init__(self, subscriber, simulator):
        Thread.__init__(self)
        self.sim = simulator
        self.subscriber = subscriber
        self.abort_requested = False
        self.FPS = 0
        self.paused = False

    def play(self):
        self.paused = False

    def pause(self):
        self.paused = True

    def notify(self):
        try:
            wx.CallAfter(self.subscriber)
        except:
            pass

    # @profile
    def run(self):
        # self.train()
        frame = 0
        total_frames = 0
        t = time.time()
        while True:
            if self.abort_requested:
                return

            if self.paused:
                time.sleep(0.1)
                continue

            # self.sim.control(1.0, 0.5, 0.0)
            self.sim.advance()
            time.sleep(0.05)

            frame += 1
            total_frames += 1

            dt = time.time() - t
            if dt > 1.0:
                self.FPS = float(frame) / dt
                frame = 0
                t = time.time()

            self.notify()

    def abort(self):
        self.abort_requested = True
