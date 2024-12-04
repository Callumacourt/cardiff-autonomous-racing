from math import sin, cos, sqrt, atan2, radians, acos
import random
import time
import glob
# import wx
import numpy as np
from simgeom import point_in_rect, any_point_in_rect, project_points, car_bbox, beam_poly_intersection, sensors_polar
from car_simple import CarSimple
# from log import log
# from agent import AgentNN
from track import Track
from slam import SLAM
from timer import Timer

RESOLUTION = 8
STATE_SIZE = 3

def vnorm(x):
    return sqrt(x[0] * x[0] + x[1] * x[1])

class Simulator:
    def __init__(self, track_fn=None, agent_fn=None):
        self.LENGTH = 2.0 * 2.56
        self.WIDTH = 1.3 * 2.56
        self.AREA = self.LENGTH * self.WIDTH
        self.dead = False
        self.inside = None
        self.agent_fn = agent_fn
        self.reset(track_fn)

        self.RFID = np.hstack((self.track.inner, self.track.outer)).transpose()
        self.slam = SLAM(self.car.position[0], self.car.position[1], self.car.heading)


    def reset(self, track_fn=None):
        if track_fn is None:  # Select a random track
            tracks = glob.glob("data/track*.mat")
            track_fn = random.choice(tracks)
            self.track = Track(track_fn)

        self.last_time = time.time()
        self.fov = radians(75)

        self.car = CarSimple()
        self.car.position[0] = random.random() * 255
        self.car.position[1] = random.random() * 255
        # if random.random() > 0.5:
        # Make sure the car is on track initially
        while self.get_dist(self.car.position[0], self.car.position[1]) < 0:
            self.car.position[0] = random.random() * 255
            self.car.position[1] = random.random() * 255

        fx, fy = self.get_field(self.car.position[0], self.car.position[1])
        # self.car.heading = random.random() * 2 * math.pi  # -math.pi * 0.5
        self.car.heading = atan2(fy, fx)

        self.car.throttle = 0
        self.car.steering = 0
        self.car.brakes = 0

        # self.total_reward = 0
        self.t = 0
        self.sensors_inner = np.zeros(RESOLUTION)
        self.sensors_outer = np.zeros(RESOLUTION)

        n_dist = 16
        n_angle = 16
        self.sensors = np.zeros((n_dist, n_angle))

        self.dead = False
        self.inside = None

        self.agent = None

        # try:
        #     self.agent = AgentNN(self.agent_fn)
        # except:
        #     pass

    def control(self, throttle, steering, brakes, dt=0.01):
        self.car.control(throttle, steering, brakes, dt)

    # @profile
    # def reward(self):
    #     if self.car.position[0] < 0 or self.car.position[0] > 256 or self.car.position[1] < 0 or self.car.position[1] > 256:
    #         self.dead = True
    #         return -200.0
    #     if self.cone_collision():
    #         self.dead = True
    #         return -1000.0
    #     d = self.get_dist(self.car.position[0], self.car.position[1])
    #     if d < 0.0:
    #         if self.inside is None:
    #             pass
    #         elif self.inside:
    #             self.dead = True
    #         self.inside = False
    #         return d * 100 - 100.0
    #     else:
    #         self.inside = True

    #     fx, fy = self.get_field(self.car.position[0], self.car.position[1])
    #     vx = self.car.velocity[0]
    #     vy = self.car.velocity[1]
    #     speed = sqrt(vx * vx + vy * vy)
    #     return (vx * fx + vy * fy) * d + speed * 10.0

    
    def advance(self, dt=None):
        # How much time has elapsed since the last time step.
        # If we are not told, it means we are running in real time mode
        # and will use the clock to find out.
        if dt is None:
            dt = time.time() - self.last_time
            self.last_time = time.time()

        self.car.advance(dt)
        # with Timer('SLAM'):
        self.slam.advance(self.car.velocity[0], self.car.velocity[1], self.car.heading_rate, self.RFID, dt)
        print('CAR:       heading: %.3f, position: %.3f, %.3f' % (self.car.heading, self.car.position[0], self.car.position[1]))
        print('SLAM TRUE: heading: %.3f, position: %.3f, %.3f' % (self.slam.xTrue[2], self.slam.xTrue[0], self.slam.xTrue[1]))
        print('SLAM DR:   heading: %.3f, position: %.3f, %.3f' % (self.slam.xDR[2], self.slam.xDR[0], self.slam.xDR[1]))
        print('SLAM EST:  heading: %.3f, position: %.3f, %.3f' % (self.slam.xEst[2], self.slam.xEst[0], self.slam.xEst[1]))
        print('DIFF:      heading: %.3f, position: %.3f, %.3f\n' % (self.car.heading - self.slam.xTrue[2], self.car.position[0] - self.slam.xTrue[0], self.car.position[1] - self.slam.xTrue[1]))


        # Total elapsed time
        self.t += dt


    def step_agent(self):
        if self.agent is not None:
            speed = self.car.absVel
            accel = sqrt(
                self.car.accel[0] * self.car.accel[0] + self.car.accel[1] * self.car.accel[1])
            yaw_rate = self.car.heading_rate
            bias = 1.0  # Must always provide a dummy 1.0 bias input
            inputs = self.get_sensors() + [speed, accel, yaw_rate, bias]
            throttle, steer, brakes = self.agent.action(inputs)
            dt = 0.05
            self.control(throttle, steer, brakes, dt)

    # @profile
    # def get_sensors(self):
    #     project_points(self.track.inner, self.sensors_inner,
    #                    self.fov, self.car.posx, self.car.posy, self.car.theta)
    #     project_points(self.track.outer, self.sensors_outer,
    #                    self.fov, self.car.posx, self.car.posy, self.car.theta)
    #     return self.sensors_inner.tolist() + self.sensors_outer.tolist()

    # @profile
    def get_sensors_distance(self, poly):
        angle = self.car.heading - self.fov * 0.5
        step = self.fov / RESOLUTION
        x0 = self.car.position[0]
        y0 = self.car.position[1]
        sensors = [0] * (RESOLUTION + 1)
        for i in range(RESOLUTION + 1):
            dx = cos(angle)
            dy = sin(angle)
            d, xi, yi = self.beam_poly(x0, y0, dx, dy, poly)
            if not d is None:
                sensors[i] = 1.0 / max(d, 1.0)
            else:
                sensors[i] = 0.0
            angle += step

        return sensors

    # @profile
    def get_sensors_polar_grid(self, cones):
        sensors_polar(cones, self.sensors, self.fov, self.car.position[0], self.car.position[1], self.car.heading)
        return self.sensors

    # @profile
    def get_sensors(self):
        # return self.get_sensors_distance(self.track.inner) + self.get_sensors_distance(self.track.outer)
        sensors_polar(self.track.inner, self.sensors, self.fov, self.car.position[0], self.car.position[1], self.car.heading)
        sens_inner = self.sensors.flatten().tolist()
        sensors_polar(self.track.outer, self.sensors, self.fov, self.car.position[0], self.car.position[1], self.car.heading)
        sens_outer = self.sensors.flatten().tolist()
        return sens_inner + sens_outer

    # @profile
    def cone_collision(self):
        sxtl, sytl, sxtr, sytr, sxbl, sybl, sxbr, sybr = car_bbox(
            self.car.position[0], self.car.position[1], self.car.heading, self.LENGTH, self.WIDTH)
        if any_point_in_rect(self.track.inner, sxtl, sytl, sxtr, sytr, sxbl, sybl, sxbr, sybr, self.AREA):
            return True
        if any_point_in_rect(self.track.outer, sxtl, sytl, sxtr, sytr, sxbl, sybl, sxbr, sybr, self.AREA):
            return True
        return False

    def get_field(self, x, y):
        x = int(round(x))
        y = int(round(y))
        if x < 0 or x >= self.track.fx.shape[1] or y < 0 or y >= self.track.fx.shape[0]:
            return (0, 0)
        return (self.track.fx[y][x], self.track.fy[y][x])

    def get_dist(self, x, y):
        x = int(round(x))
        y = int(round(y))
        if x < 0 or x >= self.track.dist.shape[1] or y < 0 or y >= self.track.dist.shape[0]:
            return 0
        return self.track.dist[y][x]

    # @profile
    # def beam_segment(self, x0, y0, dx, dy, ax, ay, bx, by):
    #     dxs = bx - ax
    #     dys = by - ay
    #     xs0 = ax
    #     ys0 = ay
    #     denom = (dy * dxs - dys * dx)
    #     if abs(denom) < 0.000001:
    #         return (None, None, None)
    #     t2 = (ys0 * dx - y0 * dx + x0 * dy - xs0 * dy) / denom
    #     if t2 < 0 or t2 > 1:
    #         return (None, None, None)
    #     xi = xs0 + dxs * t2
    #     yi = ys0 + dys * t2
    #     d = (xs0 + t2 * dxs - x0) / dx  # d == t1
    #     if d < 0:
    #         return (None, None, None)
    #     return (d, xi, yi)

    # @profile
    # def beam_poly(self, x0, y0, dx, dy, poly):
    #     found, d, ix, iy = beam_poly_intersection(x0, y0, dx, dy, poly)
    #     if found:
    #         return (d, ix, iy)
    #     else:
    #         return (None, None, None)

    # def get_sensors_cones(self, cones):
    # @profile
    #     MAX_DIST = 100
    #     edges = np.linspace(-self.fov * 0.5, self.fov * 0.5, RESOLUTION + 1)
    #     sensors = [0] * RESOLUTION
    #     xx = self.car.posx
    #     yy = self.car.posy
    #     x2 = math.cos(self.car.theta)
    #     y2 = math.sin(self.car.theta)
    #     for j in range(cones.shape[1]):
    #         x1 = cones[0][j] - xx
    #         y1 = cones[1][j] - yy
    #         d = math.sqrt(x1 * x1 + y1 * y1)
    #         if d <= MAX_DIST:
    #             a = math.atan2(x1 * y2 - y1 * x2, x1 * x2 + y1 * y2)
    #             for i in range(RESOLUTION):
    #                 left = edges[i]
    #                 right = edges[i + 1]
    #                 if a >= left and a < right:
    #                     sensors[len(sensors) - 1 - i] = max(sensors[len(sensors) - 1 - i],
    #                                                         1 - d / MAX_DIST)

    #     return sensors
