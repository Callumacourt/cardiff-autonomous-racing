"""
Mechanical model of the car
"""
from math import atan2, sin, cos, sqrt
import numpy as np


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
        self.heading = 0.0
        self.position = np.array([0.0, 0.0])
        self.velocity = np.array([0.0, 0.0])  # m/s in world coords
        # m/s in local car coords (x is forward, y is sideways)
        self.velocity_c = np.array([0.0, 0.0])
        self.accel = np.array([0.0, 0.0])  # acceleration in world coords
        self.accel_c = np.array([0.0, 0.0])  # accleration in local car coords
        self.abs_vel = 0.0  # absolute velocity m/s
        self.heading_rate = 0.0  # angular velocity in radians
        self.steer = 0.0   # amount of steering input (-1.0..1.0)
        # actual front wheel steer angle (-maxSteer..maxSteer)
        self.steering_angle = 0.0


        self.gravity = 9.81  # m/s^2
        self.mass = 1000.0  # kg
        self.half_width = 0.8  # Centre to side of chassis (metres)
        self.cg_to_front = 2.0  # Centre of gravity to front of chassis (metres)
        self.cg_to_rear = 2.0  # Centre of gravity to rear of chassis
        self.cg_to_front_axle = 1.25  # Centre gravity to front axle
        self.cg_to_rear_axle = 1.25  # Centre gravity to rear axle
        self.cg_height = 0.55  # Centre gravity height
        # Includes tire (also represents height of axle)
        self.tire_grip = 2.0  # How much grip tires have
        self.lockGrip = 0.7  # % of grip available when wheel is locked
        self.engineForce = 3000.0
        self.brake_force = 10000.0
        self.e_brake_force = self.brake_force / 2.5
        self.weight_transfer = 0.2  # How much weight is transferred during acceleration/braking
        self.max_steering = 0.3  # Maximum steering angle in radians
        self.corner_stiffness_front = 5.0
        self.corner_stiffness_rear = 5.2
        self.air_resistance = 2.5  # air resistance (* vel)
        self.roll_resistance = 8.0  # rolling resistance force (* vel)

        self.inertia = self.mass

        self.wheel_base = self.cg_to_front_axle + self.cg_to_rear_axle
        self.weight_ratio_front = self.cg_to_rear_axle / \
            self.wheel_base  # // % car weight on the front axle
        self.weight_ratio_rear = self.cg_to_front_axle / \
            self.wheel_base  # // % car weight on the rear axle

        self.brakes = 0
        self.ebrake = 0

    def control(self, throttle, steering, brakes, dt):
        alpha_steering = 0.9
        alpha_throttle = 0.9
        # self.throttle + alpha * (-self.throttle + throttle) / dt
        self.throttle = alpha_throttle * self.throttle + \
            (1.0 - alpha_throttle) * throttle
        self.throttle = min(1.0, max(0.0, self.throttle))
        self.steering = alpha_steering * self.steering + \
            (1.0 - alpha_steering) * steering  # * dt
        self.brakes = brakes

        self.steering_angle = min(1.0, max(-1.0, self.steering)) * self.max_steering
        # print(self.throttle, self.steering, self.brakes)

    def advance(self, dt):
        # Pre-calc heading vector
        sn = sin(self.heading)
        cs = cos(self.heading)

        # Get velocity in local car coordinates
        self.velocity_c[0] = cs * self.velocity[0] + sn * self.velocity[1]
        self.velocity_c[1] = cs * self.velocity[1] - sn * self.velocity[0]
        self.accel_c[0] = cs * self.accel[0] + sn * self.accel[1]
        self.accel_c[1] = cs * self.accel[1] - sn * self.accel[0]

        # Weight on axles based on centre of gravity and weight shift due to forward/reverse acceleration
        axle_weight_front = self.mass * (self.weight_ratio_front * self.gravity -
                                       self.weight_transfer * self.accel_c[0] * self.cg_height / self.wheel_base)
        axle_weight_rear = self.mass * (self.weight_ratio_rear * self.gravity +
                                      self.weight_transfer * self.accel_c[0] * self.cg_height / self.wheel_base)

        # Resulting velocity of the wheels as result of the yaw rate of the car body.
        # v = yawrate * r where r is distance from axle to CG and heading_rate (angular velocity) in rad/s.
        yaw_speed_front = self.cg_to_front_axle * self.heading_rate
        yaw_speed_rear = -self.cg_to_rear_axle * self.heading_rate

        # Calculate slip angles for front and rear wheels (a.k.a. alpha)
        slip_angle_front = atan2(self.velocity_c[1] + yaw_speed_front,
                                 abs(self.velocity_c[0])) - sign(self.velocity_c[0]) * self.steering_angle
        slip_angle_rear = atan2(self.velocity_c[1] + yaw_speed_rear,
                                abs(self.velocity_c[0]))


        tire_grip_front = self.tire_grip
        # reduce rear grip when ebrake is on
        tire_grip_rear = self.tire_grip * \
            (1.0 - self.ebrake * (1.0 - self.lockGrip))

        def edge(t, a, b):
            return min(1.0, max(0, (t - a) / (b - a)))

        motion = edge(self.abs_vel, 0.1, 5)
        friction_force_front_cy = clamp(-self.corner_stiffness_front *
                                        slip_angle_front * motion, -tire_grip_front, tire_grip_front) * axle_weight_front
        friction_force_rear_cy = clamp(-self.corner_stiffness_rear *
                                       slip_angle_rear * motion, -tire_grip_rear, tire_grip_rear) * axle_weight_rear

        #  Get amount of brake/throttle from our inputs
        brake = min(self.brakes * self.brake_force +
                    self.ebrake * self.e_brake_force, self.brake_force)
        throttle = self.throttle * self.engineForce

        #  Resulting force in local car coordinates.
        #  This is implemented as a RWD car only.
        traction_force_cx = throttle - brake * sign(self.velocity_c[0])
        traction_force_cy = 0

        drag_force_cx = -self.roll_resistance * \
            self.velocity_c[0] - self.air_resistance * \
            self.velocity_c[0] * abs(self.velocity_c[0])
        drag_force_cy = -self.roll_resistance * \
            self.velocity_c[1] - self.air_resistance * \
            self.velocity_c[1] * abs(self.velocity_c[1])

        # total force in car coordinates
        total_force_cx = drag_force_cx + traction_force_cx
        total_force_cy = drag_force_cy + traction_force_cy + \
            cos(self.steering_angle) * friction_force_front_cy + \
            friction_force_rear_cy

        # print(total_force_cx, total_force_cy)

        # acceleration along car axes
        self.accel_c[0] = total_force_cx / self.mass  # forward/reverse accel
        self.accel_c[1] = total_force_cy / self.mass  # sideways accel

        # acceleration in world coordinates
        self.accel[0] = cs * self.accel_c[0] - sn * self.accel_c[1]
        self.accel[1] = sn * self.accel_c[0] + cs * self.accel_c[1]

        # update velocity
        self.velocity += self.accel * dt

        self.abs_vel = sqrt(
            self.velocity[0] * self.velocity[0] + self.velocity[1] * self.velocity[1])

        # calculate rotational forces
        angular_torque = (friction_force_front_cy + traction_force_cy) * \
            self.cg_to_front_axle - friction_force_rear_cy * self.cg_to_rear_axle

        angular_accel = angular_torque / self.inertia
        self.heading_rate += angular_accel * dt

        #  Sim gets unstable at very slow speeds, so just stop the car
        # print(self.abs_vel)
        # if abs(self.abs_vel) < 2.0 and self.throttle < 0.1:
        #     self.accel_c[0] = 0
        #     self.accel_c[1] = 0
        #     self.accel[0] = 0
        #     self.accel[1] = 0
        #     self.velocity[0] = 0
        #     self.velocity[1] = 0
        #     self.abs_vel = 0
        #     angular_torque = 0
        #     self.heading_rate = 0

        # print('Throttle: %.2f, yaw_rate: %.2f' % (self.throttle, self.heading_rate))
        self.heading += self.heading_rate * dt
        # print(self.heading)

        #  finally we can update position
        self.position += self.velocity * dt
        # print(self.position)
