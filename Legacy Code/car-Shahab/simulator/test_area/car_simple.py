from math import atan2, sin, cos, sqrt
import numpy as np
from slam import pi_2_pi


def sign(x):
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0


def clamp(x, a, b):
    return min(max(x, a), b)


class CarSimple:
    def __init__(self):
        self.MAX_STEERING = 0.5
        self.heading = 0.0
        self.position = np.array([0.0, 0.0])
        self.speed = 0.0
        self.velocity = np.array([0.0, 0.0])  # m/s in world coords
        self.heading_rate = 0.0
        self.steering = 0.0
        self.steering_angle = 0.0
        self.MAX_SPEED = 3.0
        self.throttle = 0.0
        self.brakes = 0.0


    def control(self, throttle, steering, brakes, dt):
        alpha_steering = 0.9
        alpha_throttle = 0.9
        alpha_brakes = 0.9
        # self.throttle + alpha * (-self.throttle + throttle) / dt
        self.throttle = alpha_throttle * self.throttle + \
            (1.0 - alpha_throttle) * throttle
        self.throttle = min(1.0, max(0.0, self.throttle))
        self.steering = alpha_steering * self.steering + \
            (1.0 - alpha_steering) * steering  # * dt
        self.brakes = alpha_brakes * self.brakes + \
            (1.0 - alpha_brakes) * brakes
        self.brakes = min(0.5, max(0.0, self.brakes))
        self.steering_angle = min(1.0, max(-1.0, self.steering)) * self.MAX_STEERING
        # print(self.throttle, self.steering, self.brakes)

    def advance(self, dt):
        # Pre-calc heading vector
        sn = sin(self.heading)
        cs = cos(self.heading)

        self.heading_rate = self.steering_angle
        if (self.throttle - self.brakes) < 0:
            self.speed = 0
        else:
            self.speed = (self.throttle - self.brakes) * self.MAX_SPEED
        self.velocity[0] = cs * self.speed
        self.velocity[1] = sn * self.speed
        self.heading += self.heading_rate * dt
        self.heading = pi_2_pi(self.heading)
        self.position += self.velocity * dt
