import math
import matplotlib.pyplot as plt
import time
import numpy as np

class Vehicle_Constants():
    #milimetres
    LENGTH = 2815
    WIDTH = 1430
    HEIGHT = 664
    WHEELBASE = 1530
    FRONT_TRACK = 1201
    REAR_TRACK = 1201
    #kilograms
    WEIGHT = 300
    WEIGHT_FRONT = 150
    WEIGHT_REAR = 166
    #radians
    MAX_STEERING_ANGLE = 0.41999998688697815


class Vehicle_State():
    def __init__(self,x_pos=0, y_pos=0, x_speed=0, y_speed=0, yaw_angle=0, yaw_rate=0, wheel_rpm=0,steering_angle_rad=0):
        # 2D position
        self.xpos = x_pos
        self.ypos = y_pos

        # 2D velocity
        self.directional_velocity = x_speed
        self.perpendicualar_velocity = y_speed

        self.yaw_angle = yaw_angle
        self.yaw_rate = yaw_rate

        self.wheels_rpm = wheel_rpm#current average rpm of all 4 wheels
        self.steering_angle_rad = steering_angle_rad#current steering angle of wheels in radians (+ is left)
    
    def __str__(self):
        return f"X pos: {self.xpos}\nY pos: {self.ypos}\nDirectional velocity: {self.directional_velocity}\nPerpendicular velocity: {self.perpendicualar_velocity}\nYaw angle: {self.yaw_angle}\nYaw rate: {self.yaw_rate}"



class Vehicle_Input():
    def __init__(self, acceleration=0, steering_angle=0):
        self.acceleration = acceleration # pedal
        self.steering_angle = steering_angle # steer


class Dynamics_Model():
    """ timestep: the time between 2 consecutive states (s)
        mass: (kg)
        F_sideslip_stiffness: (N/rad)
        R_sideslip_stiffness: (N/rad)
        lf: distance from centre of gravity to front axel (m)
        lr: distance from centre of gravity to rear axel (m)
        yaw_inertia: lateral inertia of the vehicle (kgm^2)"""
    def __init__(self, timestep:float=0.1, state:Vehicle_State = Vehicle_State(), input:Vehicle_Input = Vehicle_Input(), mass:float = 500.0, F_sideslip_stiffness:float = -100_000, R_sideslip_stiffness:float = -80_000,lf=0.7,lr=0.7,yaw_inertia:float = 1500,matPlotLib:bool=False):
        self.matPlotLib = matPlotLib
        self.state = state
        #self.input = input
        
        self.mass = mass
        self.F_sideslip_stiffness = F_sideslip_stiffness
        self.R_sideslip_stiffness = R_sideslip_stiffness
        self.lf = lf
        self.lr = lr
        self.yaw_inertia = yaw_inertia
        self.timestep = timestep

        self.timestep_count=0


        # for matplotlib
        if self.matPlotLib:
            x_positions.append(self.state.xpos)
            y_positions.append(self.state.ypos)

    def set_state(self, state:Vehicle_State):
        self.state = state
    def get_state(self):
        return self.state

    def calc_front_lateral_force(self,steering_angle):
        if self.state.directional_velocity==0:
            self.state.directional_velocity=0.01
        result = self.F_sideslip_stiffness * ((self.state.perpendicualar_velocity + self.lf * self.state.yaw_rate)/self.state.directional_velocity - steering_angle)
        
        return result

    def calc_rear_lateral_force(self):
        if self.state.directional_velocity==0:
            self.state.directional_velocity=0.01

        result = self.R_sideslip_stiffness * (self.state.perpendicualar_velocity + self.lr * self.state.yaw_rate)/self.state.directional_velocity

        return result

    
    def calculate_next_state(self,input:Vehicle_Input):
        next_state = Vehicle_State()

        next_state.xpos = self.state.xpos + self.timestep * (self.state.directional_velocity * math.cos(self.state.yaw_angle) - self.state.perpendicualar_velocity * math.sin(self.state.yaw_angle))
        next_state.ypos = self.state.ypos + self.timestep * (self.state.perpendicualar_velocity * math.cos(self.state.yaw_angle) + self.state.directional_velocity * math.sin(self.state.yaw_angle))

        next_state.yaw_angle = self.state.yaw_angle + self.timestep * self.state.yaw_rate

        next_state.directional_velocity = self.state.directional_velocity + self.timestep * input.acceleration
        
        next_state.perpendicualar_velocity = (self.mass*self.state.directional_velocity*self.state.perpendicualar_velocity + self.timestep*(self.lf*self.F_sideslip_stiffness - self.lr*self.R_sideslip_stiffness)*self.state.yaw_rate - self.timestep*self.F_sideslip_stiffness*input.steering_angle*self.state.directional_velocity - self.timestep*self.mass*self.state.directional_velocity*self.state.directional_velocity*self.state.yaw_rate)/(self.mass*self.state.directional_velocity - self.timestep*(self.F_sideslip_stiffness+self.R_sideslip_stiffness))

        next_state.yaw_rate = (self.yaw_inertia*self.state.directional_velocity*self.state.yaw_rate + self.timestep*(self.lf*self.F_sideslip_stiffness - self.lr*self.R_sideslip_stiffness)*self.state.perpendicualar_velocity - self.timestep*self.lf*self.F_sideslip_stiffness*input.steering_angle*self.state.directional_velocity)/(self.yaw_inertia*self.state.directional_velocity - self.timestep*(self.lf*self.lf*self.F_sideslip_stiffness + self.lr*self.lr*self.R_sideslip_stiffness))


        next_state.wheels_rpm = (next_state.directional_velocity / 0.253) * 60

        next_state.steering_angle_rad = input.steering_angle


        self.state = next_state
        self.timestep_count+=1

        if self.matPlotLib:
            x_positions.append(self.state.xpos)
            y_positions.append(self.state.ypos)

if __name__ == "__main__":
    # For storing trajectory and velocities
    x_positions = []
    y_positions = []
    speeds = []
    directions = []

    model = Dynamics_Model(timestep=0.01, matPlotLib=False)

    inputs = [Vehicle_Input(3,0) for x in range(500)] + \
             [Vehicle_Input(0,0.3) for x in range(50)] + \
             [Vehicle_Input(3,0) for x in range(100)] + \
             [Vehicle_Input(0,0.3) for x in range(50)] + \
             [Vehicle_Input(0,0) for x in range(200)]

    startTime = time.time_ns()
    for i in range(len(inputs)-1):
        model.calculate_next_state(inputs[i])
        state = model.get_state()
        x_positions.append(state.xpos)
        y_positions.append(state.ypos)
        vx = state.directional_velocity * math.cos(state.yaw_angle) - state.perpendicualar_velocity * math.sin(state.yaw_angle)
        vy = state.perpendicualar_velocity * math.cos(state.yaw_angle) + state.directional_velocity * math.sin(state.yaw_angle)
        speeds.append(math.sqrt(vx**2 + vy**2))
        directions.append((vx, vy))
    endTime = time.time_ns()

    print(model.state)
    print("Time taken: "+str(endTime-startTime)+"ns")

    # Convert lists to numpy arrays
    x = np.array(x_positions)
    y = np.array(y_positions)
    speed = np.array(speeds)
    directions = np.array(directions)

    plt.figure(figsize=(10, 10))
    sc = plt.scatter(x, y, c=speed, cmap='viridis', s=10)
    plt.colorbar(sc, label="Speed (m/s)")

    # Draw direction arrows every N steps
    N = 20
    for i in range(0, len(x), N):
        dx, dy = directions[i]
        plt.arrow(x[i], y[i], dx * 0.2, dy * 0.2, head_width=0.5, color='red')

    plt.title("Vehicle Trajectory Colored by Speed with Direction Arrows")
    plt.xlim(-100, 100)
    plt.ylim(-100, 100)
    plt.xlabel("X Position (m)")
    plt.ylabel("Y Position (m)")
    plt.grid(True)
    plt.show()


