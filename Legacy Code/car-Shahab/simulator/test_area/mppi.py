#!env python3
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.animation import FuncAnimation
from car_simple import CarSimple
from simulator import Simulator
from generate_futures import Generate_Futures

from slam import pi_2_pi

class MPPI:
    def __init__(self):
        self.sim = Simulator()
        self.gen = Generate_Futures()

    def state_vector(self):
        return np.array([self.sim.car.heading, self.sim.car.position[0], self.sim.car.position[1], self.sim.car.velocity[0], self.sim.car.velocity[1]]).T

    def cost(self, num_timesteps, possible_futures, desired_velocity, c1, c2, c3, dt):
        state_cost = np.zeros(num_timesteps)
        cumulative_cost = np.zeros(num_timesteps)
        track_cost = 0.0
        velocity_cost = 0.0
        slip = 0.0
        slip_cost = 0.0
        cost = 0
        for i in range(0, num_timesteps-1): 
            if self.sim.get_dist(possible_futures[1, i], possible_futures[2, i]) > 0:
                track_cost += self.sim.get_dist(possible_futures[1, i], possible_futures[2, i])
            else:
                track_cost += 10000000000000000000000
            velocity_cost += abs(desired_velocity - (math.sqrt((possible_futures[4, i])**2 + (possible_futures[3, i])**2)))
            slip = (possible_futures[4, i]/possible_futures[3, i])**2 
            if np.isnan(slip) == False:
                slip_cost += slip
            cost = c1*track_cost + c2*velocity_cost + c3*slip_cost
            cumulative_cost[i] = cost
        final_cumulative_cost = cumulative_cost[num_timesteps-1]
        return cumulative_cost, state_cost, final_cumulative_cost

    def generate_futures(self, throttle, steering, brakes, num_timesteps, number_of_samples, dt):
        all_possible_futures = np.zeros((number_of_samples, 5, num_timesteps))
        crash = np.zeros(number_of_samples)
        for i in range(0, number_of_samples):
            temp_throttle = self.sim.car.throttle
            temp_brakes = self.sim.car.brakes
            if (i % 2 != 0):
                steering = 0.0 + i*0.02
            else: 
                steering = 0.0 - i*0.02
            all_possible_futures[i], crash[i] = self.gen.generate(temp_throttle, steering, temp_brakes, num_timesteps, number_of_samples, dt)
        return all_possible_futures, crash

    def instantaneous_cost(self, possible_futures, num_timesteps, state, desired_velocity, number_of_samples, c1, c2, c3, dt):
        predictive_state_costs = np.zeros((number_of_samples,num_timesteps))
        predictive_acumulative_costs = np.zeros((number_of_samples, num_timesteps))
        predictive_final_costs = np.zeros(number_of_samples)
        for i in range(0,number_of_samples):
            predictive_acumulative_costs[i], predictive_state_costs[i], predictive_final_costs[i] = self.cost(num_timesteps, possible_futures[i], desired_velocity, c1, c2, c3, dt)
        return predictive_acumulative_costs, predictive_state_costs, predictive_final_costs

    def terminal_cost(self, possible_futures, predictive_final_costs, number_of_samples, num_timesteps, c4, crash, dt):
        for i in range(0,number_of_samples):
            crash_cost = (c4**dt)*crash[i]
            predictive_final_costs[i] += crash_cost
        return predictive_final_costs

    def weighting(self, u, predictive_final_costs, possible_futures, number_of_samples, num_timesteps, sigma, landa):
        weight = np.zeros(number_of_samples) # initate "w" from the paper
        normal = 0
        #print(predictive_final_costs)
        beta = min(predictive_final_costs) # line 9
        #print(beta)
        # the 2 lines below are line 10
        for a in range(0,number_of_samples):
            normal += math.exp((-1/landa)*(predictive_final_costs[a]-beta))
        #print(normal)
        for b in range(0,number_of_samples): # line 11
            weight[b] = (1/normal)*math.exp((-1/landa)*(predictive_final_costs[b]-beta)) # line 12
        #print(weight)
        for s in range(0,num_timesteps): # line 13
            for j in range(0, 5):
                for i in range(0,number_of_samples): 
                    u[j, s] += weight[i]*possible_futures[i, j, s]
        #print(u)
        return u

    def action(self, v, throttle, steering, brakes, dt):
        # this refers to line 15 in the paper
        # # Advance the simulation
        #print(v)
        displacement = math.sqrt(((v[1, 0] - self.sim.car.position[0])**2) + ((v[2, 0] - self.sim.car.position[1])**2))
        linear_velocity = math.sqrt(((v[3, 0])**2) + ((v[4, 0])**2))
        #displacement = math.sqrt(((v[1, 1] - v[1, 0])**2) + ((v[2, 1] - v[2, 0])**2))
        #linear_velocity = math.sqrt(((v[3, 1] - v[3, 0])**2) + ((v[4, 1] - v[4, 0])**2))
        throttle = (2*(displacement-(linear_velocity*dt))/dt**2)
        steering = v[0, 0] - self.sim.car.heading
        # if steering > 1 or steering < 1:
        #     brakes = (abs(steering) - 0.5)
        # else:
        #     brakes = 0
        #print(throttle, steering, brakes)
        self.sim.car.control(throttle,steering,brakes, dt)
        self.sim.car.advance(dt)
        return throttle, brakes, steering

    def start_state(self, throttle, steering, brakes, dt, num_timesteps):
        state = np.zeros((5, num_timesteps))
        for i in range(num_timesteps):  # For each time step
            state[:, i] = self.state_vector()
            self.sim.car.control(throttle,steering,brakes, dt)
            self.sim.car.advance(dt)
        return state

    def current_state(self, state, throttle, steering, brakes, dt, num_timesteps):
        for i in range(num_timesteps):  # For each time step
            state[:, i] = self.state_vector()
            self.sim.car.control(throttle,steering,brakes, dt)
            self.sim.car.advance(dt)
        return state

    #this is referring to the paper with G.Williams et. al.
    def method(self, x0, u, throttle, steering, brakes, dt, desired_velocity, num_timesteps, number_of_samples, sigma, landa):
        # above contains all of the other variables for "x0", "K", "T", "u", "sigma" and "lambda"
        #Sample_Costs = np.zeros(number_of_samples) # intiate "S" from the paper
        #here are the cost penalty costs for the various inflictions:
        c1 = 100
        c2 = 2.5
        c3 = 50
        c4 = 100000000000000000000
        #this creates the trajectories and refers to the bit where it creates the sample and sets x0
        possible_futures, crash = self.generate_futures(throttle, brakes, steering, num_timesteps, number_of_samples, dt)
        predictive_acumulative_costs, predictive_state_cost, predictive_final_costs = self.instantaneous_cost(possible_futures, num_timesteps, u, desired_velocity, number_of_samples, c1, c2, c3, dt)
        predictive_final_costs = self.terminal_cost(possible_futures, predictive_final_costs, number_of_samples, num_timesteps, c4, crash, dt)
        u = self.weighting(u, predictive_final_costs, possible_futures, number_of_samples, num_timesteps, sigma, landa)
        throttle, brakes, steering = self.action(u, throttle, steering, brakes, dt)
        return x0, u, throttle, brakes, steering# line 18
        #return u

  # Number of simulation steps
#throttle = 1
#steering = 0
#brakes = 0
# crash = 3
#dt = 0.01

# num_timesteps = 2000
# t = np.linspace(0, (num_timesteps - 1) * dt, num_timesteps)
# # Open loop control (= no control)
# state, desired_destination, desired_position = sys.current_state(throttle, steering, brakes, dt, num_timesteps = 2000)
# x0, u, throttle, brakes, steering = sys.method(state[:, 0], state, throttle, steering, brakes, desired_position, desired_destination, desired_velocity = 8.8, num_timesteps = 2000, dt = 0.01, number_of_samples = 10, sigma = 0.68, landa = 1)
# #u = sys.method(state[:, 0], state, num_timesteps, dt, desired_position, number_of_samples, sigma, landa)

# # Plot the results
# fig = plt.figure()
# fig.set_size_inches(20, 10)
# line_heading, = plt.plot(t, u[0, :], lw=3, label='Heading')
# line_x_position, = plt.plot(t, u[1, :], lw=1, label='X_Position')
# line_y_position, = plt.plot(t, u[2, :], lw=2, label='Y_Position')
# line_x_velocity, = plt.plot(t, u[3, :], lw=1, label='X_Velocity')
# line_y_velocity, = plt.plot(t, u[4, :], lw=2, label='Y_Velocity')
# # line_control, = plt.plot(t, control, lw=1, label='Control')
# #line_cost, = plt.plot(t, state_cost, lw=2, label='State_Cost')
# #line_cumulative, = plt.plot(t, cumulative_cost, lw=2, label='Cumulative_Cost')
# line_desire_x, = plt.plot(t,desired_position[:, 0], lw=1, label='desired_position_x')
# line_desire_y, = plt.plot(t,desired_position[:, 1], lw=1, label='desired_position_y')
# plt.legend(handles=[line_heading, line_x_position, line_y_position, line_x_velocity, line_y_velocity, line_desire_x, line_desire_y])
# # line_predict, line_control, line_cumulative, line_cost,
# plt.show()