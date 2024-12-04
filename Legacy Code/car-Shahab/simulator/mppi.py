#!env python3
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.animation import FuncAnimation
from car import Car

from slam import pi_2_pi

class MPPI:
    def __init__(self):
        self.car = CarSimple()

    def state_vector(self):
        return np.array([self.car.heading, self.car.position[0], self.car.position[1], self.car.velocity[0], self.car.velocity[1]]).T

    def cost(self, num_timesteps, possible_futures, desired_position, desired_velocity, dt):
        state_cost = np.zeros(num_timesteps)
        cumulative_cost = np.zeros(num_timesteps)
        track_cost = 0.0
        velocity_cost = 0.0
        slip = 0.0
        slip_cost = 0.0
        cost = 0
        for i in range(0, num_timesteps): 
            # weighting penalty yet to be added but that will come with experimentation
            track_cost += math.sqrt((desired_position[i, 0]-possible_futures[1, i])**2 + (desired_position[i, 1]-possible_futures[2, i])**2)
            # velocity cost will need to be editted I figured that there could be something wrong in terms of calculating a couple of things
            velocity_cost += abs(possible_futures[0, i]) * (desired_velocity - possible_futures[3, i])**2
            slip = (possible_futures[4, i]/possible_futures[3, i])**2 
            if np.isnan(slip) == False:
                slip_cost += slip
            cost =  track_cost + velocity_cost + slip_cost
            cumulative_cost[i] = cost
            final_cumulative_cost = cumulative_cost[num_timesteps-1]
        return cumulative_cost, state_cost, final_cumulative_cost

    def Generate_Futures(self, throttle, steering, brakes, num_timesteps, number_of_samples, dt):
        all_possible_futures = np.zeros((number_of_samples, 5, num_timesteps))
        # another possible thing to do is create a control which edits the velocity and steering and see how those trajectories look?
        crash = np.zeros(number_of_samples)
        for i in range(0, number_of_samples):
            possible_future = np.zeros((5, num_timesteps))
            if (i % 2 != 0):
                steering = 0.0 + i*0.01
            else: 
                steering = 0.0 - i*0.01
            for j in range(num_timesteps):  # For each time step
                possible_future[:, j] = mppi.state_vector()
                # Advance the simulation
                mppi.car.control(throttle, steering, brakes, dt)
                mppi.car.advance(dt)
                # if car is outside of the track: 
                #   crash += 1
            all_possible_futures[i] = possible_future
        return all_possible_futures, crash

    def instantaneous_cost(self, possible_futures, num_timesteps, state, desired_position, desired_velocity, number_of_samples, dt):
        predictive_state_costs = np.zeros((number_of_samples,num_timesteps))
        predictive_acumulative_costs = np.zeros((number_of_samples, num_timesteps))
        predictive_final_costs = np.zeros(number_of_samples)
        for i in range(0,number_of_samples):
            predictive_acumulative_costs[i], predictive_state_costs[i], predictive_final_costs[i] = mppi.cost(num_timesteps, possible_futures[i], desired_position, desired_velocity, dt)
        return predictive_acumulative_costs, predictive_state_costs, predictive_final_costs

    def terminal_cost(self, desired_position, possible_futures, predictive_final_costs, number_of_samples, num_timesteps, crash, dt):
        penalty = 0.0
        crash_cost = 0.0
        for i in range(0,number_of_samples):
            penalty = ((desired_position[i, 0]-possible_futures[i, 1])**2 + (desired_position[i, 1]-possible_futures[i, 2])**2)
            predictive_final_costs[i] += penalty[i]
            crash_cost = (0.95**dt)*crash[i]
            predictive_final_costs[i] += crash_cost
            penalty = 0.0
            crash_cost = 0.0
        return predictive_final_costs

    def weighting(self, u, weight, predictive_final_costs, possible_futures, number_of_samples, num_timesteps, sigma, landa):
        normal = 0
        beta = min(predictive_final_costs) # line 9
        # the 2 lines below are line 10
        for a in range(0,number_of_samples):
            normal += math.exp((-1/landa)*(predictive_final_costs[a]-beta))
        for b in range(0,number_of_samples): # line 11
            weight[b] = (1/normal)*math.exp((-1/landa)*(predictive_final_costs[b]-beta)) # line 12
        for s in range(0,num_timesteps): # line 13
            for j in range(0, 5):
                for i in range(1,number_of_samples): 
                    u[j, s] += weight[i]*possible_futures[i, j, s]
        return u

    def action(self, u, throttle, steering, brakes, dt, desired_destination):
        # this refers to line 15 in the paper
        # # Advance the simulation
        displacement = math.sqrt(((desired_destination[0] - u[1, 0])**2) + ((desired_destination[1] - u[2, 0])**2))
        linear_velocity = math.sqrt(((u[3, 0])**2) + ((u[4, 0])**2))
        throttle = (2*(displacement-(linear_velocity*dt))/dt**2)
        steering = u[4, 0]/displacement
        mppi.car.control(throttle, steering, brakes, dt)
        mppi.car.advance(dt)
        return throttle, brakes, steering

    def current_state(self, throttle, steering, brakes, dt, num_timesteps):
        state = np.zeros((5, num_timesteps))
        desired_position_x = np.random.uniform(low = 10, high = 10, size = num_timesteps)
        desired_position_y = np.random.uniform(low = 20, high = 20, size = num_timesteps)
        desired_position = np.array([desired_position_x, desired_position_y]).T
        for i in range(num_timesteps):  # For each time step
            state[:, i] = mppi.state_vector()
            # Advance the simulation
            mppi.car.control(throttle, steering, brakes, dt)
            mppi.car.advance(dt)
        desired_destination = np.array([state[1, 1],state[2, 1]]).T
        return state, desired_destination, desired_position

    #this is referring to the paper with G.Williams et. al.
    def Method(self, x0, u, throttle, steering, brakes, desired_position, desired_destination, dt, desired_velocity, num_timesteps, number_of_samples, sigma, landa):
        # above contains all of the other variables for "x0", "K", "T", "u", "sigma" and "lambda"
        #Sample_Costs = np.zeros(number_of_samples) # intiate "S" from the paper
        weight = np.arange(number_of_samples) # initate "w" from the paper
        #this creates the trajectories and refers to the bit where it creates the sample and sets x0
        possible_futures, crash = mppi.Generate_Futures(throttle, brakes, steering, num_timesteps, number_of_samples, dt)
        predictive_acumulative_costs, predictive_state_cost, predictive_final_costs = mppi.instantaneous_cost(possible_futures, num_timesteps, u, desired_position, desired_velocity, number_of_samples, dt)
        predictive_final_costs = mppi.terminal_cost(desired_position, possible_futures, predictive_final_costs, number_of_samples, num_timesteps, crash, dt)
        u = mppi.weighting(u, weight, predictive_final_costs, possible_futures, number_of_samples, num_timesteps, sigma, landa)
        print(u)
        throttle, brakes, steering = mppi.action(u, throttle, steering, brakes, dt, desired_destination)
        self.car.throttle = throttle
        self.car.brakes = brakes
        self.car.steering = steering
        return x0, u, throttle, brakes, steering# line 18
        #return u

  # Number of simulation steps
throttle = 1
steering = 0
brakes = 0
crash = 3
dt = 0.01

num_timesteps = 2000
t = np.linspace(0, (num_timesteps - 1) * dt, num_timesteps)
# # Open loop control (= no control)
mppi = MPPI()
for i in range(num_timesteps):
    state, desired_destination, desired_position = mppi.current_state(throttle, steering, brakes, dt, num_timesteps = 2000)
    x0, u, throttle, brakes, steering = mppi.Method(state[:, 0], state, throttle, steering, brakes, desired_position, desired_destination, desired_velocity = 8.8, num_timesteps = 2000, dt = 0.01, number_of_samples = 10, sigma = 0.68, landa = 1)
#u = mppi.Method(state[:, 0], state, num_timesteps, dt, desired_position, number_of_samples, sigma, landa)

# Plot the results
fig = plt.figure()
fig.set_size_inches(20, 10)
line_heading, = plt.plot(t, u[0, :], lw=3, label='Heading')
line_x_position, = plt.plot(t, u[1, :], lw=1, label='X_Position')
line_y_position, = plt.plot(t, u[2, :], lw=2, label='Y_Position')
line_x_velocity, = plt.plot(t, u[3, :], lw=1, label='X_Velocity')
line_y_velocity, = plt.plot(t, u[4, :], lw=2, label='Y_Velocity')
# line_control, = plt.plot(t, control, lw=1, label='Control')
#line_cost, = plt.plot(t, state_cost, lw=2, label='State_Cost')
#line_cumulative, = plt.plot(t, cumulative_cost, lw=2, label='Cumulative_Cost')
line_desire_x, = plt.plot(t,desired_position[:, 0], lw=1, label='desired_position_x')
line_desire_y, = plt.plot(t,desired_position[:, 1], lw=1, label='desired_position_y')
plt.legend(handles=[line_heading, line_x_position, line_y_position, line_x_velocity, line_y_velocity, line_desire_x, line_desire_y])
# line_predict, line_control, line_cumulative, line_cost,
plt.show()