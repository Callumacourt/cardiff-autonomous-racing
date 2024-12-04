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
from mppi import *
from car_simple import CarSimple


class SimulatorThread(Thread):
    def __init__(self, subscriber, simulator):
        Thread.__init__(self)
        self.sim = simulator
        self.subscriber = subscriber
        self.abort_requested = False
        self.FPS = 0
        self.paused = False
        self.mppi = MPPI()

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
        state = self.mppi.start_state(self.sim.car.throttle, self.sim.car.steering, self.sim.car.brakes, dt=0.1, num_timesteps = 2000)
        while True:
            if self.abort_requested:
                return

            if self.paused:
                time.sleep(0.1)
                continue

            x0, state, throttle, brakes, steering = self.mppi.method(state[:, 0], state, self.sim.car.throttle, self.sim.car.steering, self.sim.car.brakes, desired_velocity = 8.8, num_timesteps = 2000, dt = 0.1, number_of_samples = 25, sigma = 0.68, landa = 1)
            self.sim.control(throttle,steering,brakes)
            self.sim.advance()
            state = np.roll(state, -1, axis=1)
            state = self.mppi.current_state(state, self.sim.car.throttle, self.sim.car.steering, self.sim.car.brakes, dt=0.1, num_timesteps = 2000)
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
