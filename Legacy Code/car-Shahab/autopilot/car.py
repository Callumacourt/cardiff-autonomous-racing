"""
Mechanical model of the car
"""
from math import atan2, sin, cos, sqrt
import numpy as np
import scipy.io as sio


def sign(x):
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0


def clamp(x, a, b):
    return min(max(x, a), b)


class Car:
    def __init__(self):
        cfg = sio.loadmat('car_model.mat')['cfg'][:, 0]          #array of 13 parameters from 'car_model.mat'
        
        # print(cfg)
        
        self.weight_transfer = cfg[0];                           #dividing array into individual variables
        self.cg_height = cfg[1];
        self.cg_to_front_axle = cfg[2];
        self.cg_to_rear_axle = cfg[3];
        self.max_steering = cfg[4];
        self.tire_grip = cfg[5];
        self.corner_stiffness_front = cfg[6];
        self.corner_stiffness_rear = cfg[7];
        self.engine_force = cfg[8];
        self.roll_resistance = cfg[9];
        self.air_resistance = cfg[10];
        self.inertia = cfg[11];
        self.ahdg_damping = cfg[12];

        self.mass = 2500.0 
        self.gravity = 9.81

        #self.lockGrip = 0.7  # % of grip available when wheel is locked
        self.wheel_base = self.cg_to_front_axle + self.cg_to_rear_axle          #more variables being defined
        self.weight_ratio_front = self.cg_to_rear_axle / \
            self.wheel_base  # // % car weight on the front axle
        self.weight_ratio_rear = self.cg_to_front_axle / \
            self.wheel_base  # // % car weight on the rear axle

        self.brakes = 0                                                         #more variables being defined
        self.ebrake = 0

    # def control(self, throttle, steering, brakes, dt):
    #     alpha_steering = 0.9
    #     alpha_throttle = 0.9
    #     # self.throttle + alpha * (-self.throttle + throttle) / dt
    #     self.throttle = alpha_throttle * self.throttle + \
    #         (1.0 - alpha_throttle) * throttle
    #     self.throttle = min(1.0, max(0.0, self.throttle))
    #     self.steering = alpha_steering * self.steering + \
    #         (1.0 - alpha_steering) * steering  # * dt
    #     self.brakes = brakes

        # self.steering_angle = min(1.0, max(-1.0, self.steering)) * self.max_steering
        # print(self.throttle, self.steering, self.brakes)

    def advance(self, X, ctr, dt):
        x = X[0]                                                                #dividing X array into individual variables
        y = X[1]
        vx = X[2]
        vy = X[3]
        ax = X[4]
        ay = X[5]
        hdg = X[6]
        hdgv = X[7]
        hdga = X[8]

        speed = sqrt(vx * vx + vy * vy)                                          #vehicle calculations
        speed_c = 0.0017268 * speed * speed - 0.0800304 * speed + 0.9791562
        steering_angle = min(1.0, max(-1.0, ctr[0])) * self.max_steering * speed_c
        throttle = min(1.0, max(0.0, ctr[1])) * self.engine_force

        # print(self.max_steering, ctr[0], ctr[1])

        # Pre-calc heading vector
        sn = sin(hdg)
        cs = cos(hdg)

        # Get velocity in local car coordinates
        vxc = cs * vx + sn * vy
        vyc = cs * vy - sn * vx
        axc = cs * ax + sn * ay
        ayc = cs * ay - sn * ax

        # Weight on axles based on centre of gravity and weight shift due to forward/reverse acceleration
        axle_weight_front = self.mass * (self.weight_ratio_front * self.gravity -
                                       self.weight_transfer * axc * self.cg_height / self.wheel_base)
        axle_weight_rear = self.mass * (self.weight_ratio_rear * self.gravity +
                                      self.weight_transfer * axc * self.cg_height / self.wheel_base)

        # Resulting velocity of the wheels as result of the yaw rate of the car body.
        # v = yawrate * r where r is distance from axle to CG and heading_rate (angular velocity) in rad/s.
        yaw_speed_front = self.cg_to_front_axle * hdgv
        yaw_speed_rear = -self.cg_to_rear_axle * hdgv

        # Calculate slip angles for front and rear wheels (a.k.a. alpha)
        slip_angle_front = atan2(vyc + yaw_speed_front, abs(vxc)) - sign(vxc) * steering_angle
        slip_angle_rear = atan2(vyc + yaw_speed_rear, abs(vxc))

        tire_grip_front = self.tire_grip
        tire_grip_rear = self.tire_grip

        
        motion = min(1.0, max(0, (speed - 0.1) / (5.0 - 0.1)))
        friction_force_front_cy = clamp(-self.corner_stiffness_front *
                                        slip_angle_front * motion, -tire_grip_front, tire_grip_front) * axle_weight_front
        friction_force_rear_cy = clamp(-self.corner_stiffness_rear *
                                       slip_angle_rear * motion, -tire_grip_rear, tire_grip_rear) * axle_weight_rear

        #  Get amount of brake/throttle from our inputs
        brake = 0
        

        #  Resulting force in local car coordinates.
        #  This is implemented as a RWD car only.
        traction_force_cx = throttle - brake * sign(vxc)
        traction_force_cy = 0

        drag_force_cx = -self.roll_resistance * vxc - self.air_resistance * vxc * abs(vxc)
        drag_force_cy = -self.roll_resistance * vyc - self.air_resistance * vyc * abs(vyc)

        # total force in car coordinates
        total_force_cx = drag_force_cx + traction_force_cx
        total_force_cy = drag_force_cy + traction_force_cy + cos(steering_angle) * friction_force_front_cy + friction_force_rear_cy

        # acceleration along car axes
        axc = total_force_cx / self.mass  # forward/reverse accel
        ayc = total_force_cy / self.mass  # sideways accel

        # acceleration in world coordinates
        ax = cs * axc - sn * ayc
        ay = sn * axc + cs * ayc

        # update velocity
        vx += ax * dt
        vy += ay * dt

        # calculate rotational forces
        angular_torque = (friction_force_front_cy + traction_force_cy) * \
            self.cg_to_front_axle - friction_force_rear_cy * self.cg_to_rear_axle
        # print('torque', angular_torque, 'inertia', self.inertia)

        # hdga = angular_torque / (self.mass * self.inertia)
        hdga = self.ahdg_damping * (angular_torque / (self.mass * self.inertia)) + (1 - self.ahdg_damping) * hdga;
        hdgv += hdga * dt
        hdg += hdgv * dt
        x += vx * dt
        y += vy * dt

        X = np.array([x, y, vx, vy, ax, ay, hdg, hdgv, hdga])
        # print(X)
        return X
