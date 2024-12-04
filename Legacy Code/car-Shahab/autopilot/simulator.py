import numpy as np
import airsim
from log import log
from tools import quaternion_to_euler
from math import sin, cos


class Simulator:
    def __init__(self):
        self.connected = False
        self.client = airsim.CarClient()     #sets the client to the airsim CarClient
        self.connect()

    def connect(self):                      #connects to AirSim
        log('Connecting to AirSim...')
        try:
            self.client.confirmConnection()             #confirms connection
            self.connected = True
            self.client.enableApiControl(True)          #enables API control
            self.car_controls = airsim.CarControls()
            self.car_controls.is_manual_gear = False
            log('Connected.')
        except:                                #exception in case of failure
            log('Connection failed.')
            self.connected = False

    def state(self):                          #returns the state of the car
        return self.client.getCarState()
    
    def state_vector_c(self):                   #returns array of state vector values?
        X = np.zeros(9)                         #sets variable values
        kin = self.client.simGetGroundTruthKinematics()
        x = kin.position.x_val
        y = kin.position.y_val
        q = kin.orientation
        _, _, hdg = quaternion_to_euler(
            np.array([q.w_val, q.x_val, q.y_val, q.z_val]))
        sn = sin(hdg)
        cs = cos(hdg)
        vx = kin.linear_velocity.x_val
        vy = kin.linear_velocity.y_val
        ax = kin.linear_acceleration.x_val
        ay = kin.linear_acceleration.y_val
        # TODO: Check if we need angular velocity and acceleration in car-centric frame?
        return np.array((0, 0, cs * vx + sn * vy, cs * vy - sn * vx,
                         cs * ax + sn * ay, cs * ay - sn * ax,
                         0, kin.angular_velocity.z_val, kin.angular_acceleration.z_val))

    def control(self, steering, throttle, brake=0):        #sets car's controls to the given values, with brake value = 0 (not sure why)
        self.car_controls.steering = steering
        self.car_controls.throttle = throttle
        self.car_controls.brake = brake
        self.client.setCarControls(self.car_controls)

    def disconnect(self):           #disconnects from AirSim
        try:
            self.control(0.0, 0.0, 1.0)
            self.client.enableApiControl(False)
        except:
            pass
