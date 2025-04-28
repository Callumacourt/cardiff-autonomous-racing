import math
import matplotlib.pyplot as plt
import time


class Vehicle_State():
    def __init__(self,x_pos=0, y_pos=0, x_speed=0, y_speed=0, yaw_angle=0, yaw_rate=0):
        # 2D position
        self.xpos = x_pos
        self.ypos = y_pos

        # 2D velocity
        self.directional_velocity = x_speed
        self.perpendicualar_velocity = y_speed

        self.yaw_angle = yaw_angle
        self.yaw_rate = yaw_rate
    
    def __str__(self):
        return f"X pos: {self.xpos}\nY pos: {self.ypos}\nDirectional velocity: {self.directional_velocity}\nPerpendicular velocity: {self.perpendicualar_velocity}\nYaw angle: {self.yaw_angle}\nYaw rate: {self.yaw_rate}"



class Vehicle_Input():
    def __init__(self, acceleration=0,steering_angle=0):
        self.acceleration = acceleration
        self.steering_angle = steering_angle


class Dynamics_Model():
    """ timestep: the time between 2 consecutive states (s)
        mass: (kg)
        F_sideslip_stiffness: (N/rad)
        R_sideslip_stiffness: (N/rad)
        lf: distance from centre of gravity to front axel (m)
        lr: distance from centre of gravity to rear axel (m)
        yaw_inertia: lateral inertia of the vehicle (kgm^2)"""
    def __init__(self, timestep:float=0.1, state:Vehicle_State = Vehicle_State(), input:Vehicle_Input = Vehicle_Input(), mass:float = 500, F_sideslip_stiffness:float = -100_000, R_sideslip_stiffness:float = -80_000,lf=0.7,lr=0.7,yaw_inertia:float = 1500):
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
        x_positions.append(self.state.xpos)
        y_positions.append(self.state.ypos)

    

    def calc_front_lateral_force(self,steering_angle):
        if self.state.directional_velocity==0:
            self.state.directional_velocity=0.01
        result = self.F_sideslip_stiffness * ((self.state.perpendicualar_velocity + self.lf * self.state.yaw_rate)/self.state.directional_velocity - steering_angle)

        self.state.directional_velocity = 0
        
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

        self.state = next_state
        self.timestep_count+=1

        x_positions.append(self.state.xpos)
        y_positions.append(self.state.ypos)


# testing purposes

x_positions = []
y_positions = []

model = Dynamics_Model(timestep=0.01)
#generate some inputs
inputs = [Vehicle_Input(3,0) for x in range(500)] + [Vehicle_Input(0,0.3) for x in range(50)] + [Vehicle_Input(3,0) for x in range(100)] + [Vehicle_Input(0,0.3) for x in range(50)] + [Vehicle_Input(0,0) for x in range(200)]

startTime = time.time_ns()
for i in range(len(inputs)-1):
    #print the state for debug purposes
    #print(model.state)
    model.calculate_next_state(inputs[i])
    #print(model.timestep_count)
    #print()

endTime = time.time_ns()
print(model.state)

print("Time taken: "+str(endTime-startTime)+"ns")

plt.plot(x_positions,y_positions)
plt.xlim(-100,100)
plt.ylim(-100,100)
plt.show()


#TODO:
#plot this on a matplotlib graph, where the color of each dot represents what time it was recorded at, to beter show speed and direction of travel
