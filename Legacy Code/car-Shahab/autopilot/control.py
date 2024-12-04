import math
import wx
import numpy as np
import math

def clamp(x, a, b):                                             # returning maximum values of paramters
    return max(a, min(x, b))


class Controller:
    def __init__(self, sim):                                    # defining parameters for controller           
        self.sim = sim
        # self.speed_err_int = 0.0
        self.speed_prev = 0.0
        self.throttle_cmd = 0.0
        self.steering_prev = 0.0

    def control(self, dt, kbd_steering, kbd_throttle, cones_y, cones_b, target):  
        # car_state = self.sim.client.getCarState()
        
        # speed_cmd = kbd_throttle * 20.0#3.0 # for trackdrive

        # speed_err = speed_cmd - car_state.speed
        # accel_max = 0.5
        # accel_cmd = clamp(speed_err * 0.2, -accel_max, accel_max)

        # accel = (car_state.speed - self.speed_prev) / dt
        # self.speed_prev = car_state.speed

        # accel_err = accel_cmd - accel
        
        # self.throttle_cmd += accel_err * 0.2 * dt
        # if self.throttle_cmd > 0.0:
        #     throttle = self.throttle_cmd * 1.0
        #     brake = 0.0
        # else:
        #     throttle = 0.0
        #     brake = -self.throttle_cmd * 0.5
            
        

        angle = math.degrees(math.atan2(target[0], target[1]))       #calculate angle between two points

        steering = angle * 0.07                                      #for trackdrive
        if kbd_steering != 0.0:                                      #angle of steer if its zero
            steering = kbd_steering

        steering = kbd_steering                                      #defining steering 
        throttle = kbd_throttle                                      #defining throttle
        

        # alpha_steering = 0.7
        # steering = alpha_steering * self.steering_prev + (1.0 - alpha_steering) * steering
        # self.steering_prev = steering
        self.sim.control(steering, throttle, brake)                  #Unknown what it does

