#!env python3
import pygame
from simulator import Simulator
import time
import csv
from math import sqrt, sin, cos
from airsim.utils import to_eularian_angles
from random import random

sim = Simulator()
sim.client.enableApiControl(True)
pygame.init()
pygame.display.set_mode((640, 480))


t0 = time.time()
t = t0
frame = 0
cmd_throttle = 0.0
cmd_steering = 0.0
new_throttle = 0.0
new_steering = 0.0

cmd_brake = 0.0
DT = 0.050
dt = 0

key_up = False
key_down = False
key_left = False
key_right = False
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sim.client.enableApiControl(False)
            pygame.quit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                key_up = True
            if event.key == pygame.K_DOWN:
                key_down = True
            if event.key == pygame.K_LEFT:
                key_left = True
            if event.key == pygame.K_RIGHT:
                key_right = True
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_UP:
                key_up = False
            if event.key == pygame.K_DOWN:
                key_down = False
            if event.key == pygame.K_LEFT:
                key_left = False
            if event.key == pygame.K_RIGHT:
                key_right = False

    # print(key_up, key_down)
    alpha = 0.1
    if key_up:
        cmd_throttle += 0.2 * dt
    # else:
    #     cmd_throttle = (1.0 - alpha) * cmd_throttle
    if key_down:
        cmd_brake += 0.2 * dt
    # else:
    #     cmd_brake = (1.0 - alpha) * cmd_brake
    if abs(cmd_brake) < 0.01:
        cmd_brake = 0.0

    cmd_throttle = max(0.0, min(1.0, cmd_throttle))
    cmd_brake = max(0.0, min(1.0, cmd_brake))

    alpha_steering = 0.07
    if key_left:
        cmd_steering -= 1.0 * dt
    if key_right:
        cmd_steering += 1.0 * dt
    # if not (key_left or key_right):
    #     cmd_steering = (1.0 - alpha_steering) * cmd_steering
    cmd_steering = max(-1.0, min(1.0, cmd_steering))

    while time.time() < t + DT:
        time.sleep(0.001)
    now = time.time()
    dt = now - t
    t = now

    if random() > 0.99:
        new_steering = 2.0 * random() - 1.0
    if random() > 0.99:
        new_throttle = random() * 0.5
    cmd_steering = alpha_steering * new_steering + \
        (1.0 - alpha_steering) * cmd_steering
    cmd_throttle = alpha * new_throttle + (1.0 - alpha) * cmd_throttle

    sim.control(cmd_steering, cmd_throttle, cmd_brake)

    st = sim.state()
    kin = sim.client.simGetGroundTruthKinematics()
    # print(kin)
    ctr = sim.client.getCarControls()
    timestamp = st.timestamp

    # Controls
    gear = st.gear
    steering = ctr.steering
    throttle = ctr.throttle
    brake = ctr.brake

    # Kinematics
    # kin = sim.client.getImuData()
    x = kin.position.x_val
    y = kin.position.y_val
    z = kin.position.z_val
    wx = kin.angular_velocity.x_val
    wy = kin.angular_velocity.y_val
    wz = kin.angular_velocity.z_val
    # # ang_acc = kin.angular_acceleration.z_val
    vx = kin.linear_velocity.x_val
    vy = kin.linear_velocity.y_val
    vz = kin.linear_velocity.z_val
    ax = kin.linear_acceleration.x_val
    ay = kin.linear_acceleration.y_val
    az = kin.linear_acceleration.z_val
    # vz = kin.linear_velocity.z_val
    q = kin.orientation
    pitch, roll, yaw = to_eularian_angles(q)

    # fwdx = cos(theta)
    # fwdy = sin(theta)

    # sdex = sin(theta)
    # sdey = -cos(theta)

    # lin_vel = fwdx * vx + fwdy * vy
    # lin_acc = fwdx * ax + fwdy * ay

    # lin_vel_side = sdex * vx + sdey * vy
    # lin_acc_side = sdex * ax + sdey * ay

    speed = st.speed
    # print("%.2f %.2f %.4f" % (speed, lin_vel, speed - lin_vel))
    # print("% .2f % .2f % .2f \t%.2f %.2f %.2f" % (vx, vy, vz, lin_vel, speed, speed - lin_vel))

    # print(inert)
    # print("% .2f % .2f" % (x, y))
    with open('id.csv', 'a') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, cmd_steering, cmd_throttle, brake,
                         x, y, z, vx, vy, vz, ax, ay, az,
                         q.w_val, q.x_val, q.y_val, q.z_val,
                         pitch, roll, yaw,
                         wx, wy, wz])

    frame += 1

