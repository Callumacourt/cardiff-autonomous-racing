#!env python3
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.animation import FuncAnimation
from car_simple import CarSimple
from simulator import Simulator
from slam import pi_2_pi

class Generate_Futures:
    def __init__(self):
        self.sim = Simulator()

    def state_vector(self):
        return np.array([self.sim.car.heading, self.sim.car.position[0], self.sim.car.position[1], self.sim.car.velocity[0], self.sim.car.velocity[1]]).T

    def generate(self, throttle, steering, brakes, num_timesteps, number_of_samples, dt):
        crash_count = 0
        possible_future = np.zeros((5, num_timesteps))
        for j in range(0, num_timesteps):  # For each time step
            possible_future[:, j] = self.state_vector()
            # Advance the simulation
            self.sim.car.control(throttle, steering, brakes, dt)
            self.sim.car.advance(dt)
            if self.sim.get_dist(self.sim.car.position[0], self.sim.car.position[1]) <= 0.0:
                crash_count += 1
        return possible_future, crash_count