#!env python3
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.animation import FuncAnimation

#import statsmodels.api as sm


class MassOnSpring:
    def __init__(self, position=0.0, velocity=0.0, mass=1.0, k=0.1, friction=0.1):
        # From my understanding this is F
        self.position = position
        self.velocity = velocity
        self.mass = mass
        self.k = k
        self.friction = friction

    def advance(self, dt, control):
        force = -self.k * self.position - self.velocity * self.friction + control
        accel = force / self.mass
        self.velocity += accel * dt
        self.position += self.velocity * dt

    def state_vector(self):
        return np.array([self.position, self.velocity]).T

    def predict(self, N, step, control):
        predict = np.zeros((2,N))
        for i in range(N, N+step):  # For each time step ahead of N for "predictive steps" steps
            predict[:, i-N] = sys.state_vector()

            # Advance the simulation
            sys.advance(dt, control[i-N])
        return predict

    def cost(self, N, possible_futures, desired_position):
        state_cost = np.zeros(N)
        cumulative_cost = np.zeros(N)
        cost = 0
        for i in range(0, N): 
            state_cost[i] = abs(desired_position-possible_futures[i])
            cost += state_cost[i]
            cumulative_cost[i] = cost
        final_cumulative_cost = cumulative_cost[N-1]
        return cumulative_cost, state_cost, final_cumulative_cost

    def Generate_Futures(self, N, number_of_samples):
        # this is function F for all trajectories (line 4-6)
        all_possible_futures = np.zeros((number_of_samples, 2, N))
        for i in range(0, number_of_samples):
            possible_future = np.zeros((2, N))
            #generates the samples (line 4)
            sys = MassOnSpring(position=1.0, velocity=0.0, mass=1.0, k=1.0, friction=0.3)
            if (i % 2 != 0):     
                test_control = np.ones(N)*i
            else:
                test_control = np.ones(N)*-i
            for j in range(N):  # For each time step
                possible_future[:, j] = sys.state_vector()
                # Advance the simulation
                sys.advance(dt, test_control[j])
            all_possible_futures[i] = possible_future
        return all_possible_futures

    def instantaneous_cost(self, possible_futures, N, state, desired_position, number_of_samples):
        # this function is the S(e) += q(x at t)... (line 7)
        predictive_state_costs = np.zeros((number_of_samples,N))
        predictive_acumulative_costs = np.zeros((number_of_samples, N))
        predictive_final_costs = np.zeros(number_of_samples)
        for i in range(0,number_of_samples):
            predictive_acumulative_costs[i], predictive_state_costs[i], predictive_final_costs[i] = sys.cost(N, possible_futures[i,0], desired_position)
        return predictive_acumulative_costs, predictive_state_costs, predictive_final_costs

    def terminal_cost(self, desired_position, predictive_state_cost, predictive_final_costs, number_of_samples, N):
        # this function is the S(e) += terminal cost (line 8)
        penalty = 0
        for i in range(0,number_of_samples):
            penalty = abs(predictive_state_cost[i, N-1] - desired_position)
            predictive_final_costs[i] += penalty
            penalty = 0
        return predictive_final_costs

    def weighting(self, u, weight, predictive_final_costs, possible_futures, number_of_samples, num_timesteps, sigma, landa):
        normal = 0
        control = np.zeros((num_timesteps))
        beta = min(predictive_final_costs) # line 9
        # the 2 lines below are line 10
        for a in range(0,number_of_samples):
            normal += math.exp((-1/landa)*(predictive_final_costs[a]-beta))
        for b in range(0,number_of_samples): # line 11
            weight[b] = (1/normal)*math.exp((-1/landa)*(predictive_final_costs[b]-beta)) # line 12
        for s in range(0,num_timesteps): # line 13
            # the 2 lines below are line 14, I added control for the sake of tracking how the future might look but personally I am not too sure about that.
            for j in range(0, 2):
                for i in range(1,number_of_samples): 
                    u[j, s] += weight[i]*possible_futures[i, j, s]
                    control[s] += weight[i]*possible_futures[i, j, s]
        return u, control

    #this is referring to the paper with G.Williams et. al.
    def Method(self, x0, u, num_timesteps, dt, desired_position, number_of_samples, sigma = 0.68, landa = 1):
        # above contains all of the other variables for "x0", "K", "T", "u", "sigma" and "lambda"
        weight = np.arange(number_of_samples) # initate "w" from the paper
        possible_futures = sys.Generate_Futures(N, number_of_samples)
        predictive_acumulative_costs, predictive_state_cost, predictive_final_costs = sys.instantaneous_cost(possible_futures, N, state, desired_position, number_of_samples)
        predictive_final_costs = sys.terminal_cost(desired_position, predictive_state_cost, predictive_final_costs, number_of_samples, N)
        u, control = sys.weighting(u, weight, predictive_final_costs, possible_futures, number_of_samples, num_timesteps, sigma, landa)
        #action u[0] movement #line 15 I leave these commented out for now since the full controls are in another part of the program
        #u = np.delete(u, 0) # line 16 and 17
        return u, control # line 18

N = 2000  # Number of simulation steps
predictive_steps = 2000
state = np.zeros((2, N))
control = np.zeros(N)
dt = 0.01
desired_position = 0.5
number_of_samples = 10

error_int = 0.0
# kp = 40.0
# kd = 10.0
# ki = 5.0

kp = 10.0
kd = 5.0
ki = 2.0

t = np.linspace(0, (N - 1) * dt, N)
# Open loop control (= no control)
sys = MassOnSpring(position=1.0, velocity=0.0, mass=1.0, k=1.0, friction=0.3)
for i in range(N):  # For each time step
    state[:, i] = sys.state_vector()

    control[i] = 0.0
    # Advance the simulation
    sys.advance(dt, control[i])

# predict = sys.predict(N, predictive_steps, control)
# # Plot the results
# fig = plt.figure()
# fig.set_size_inches(20, 10)
# line_position, = plt.plot(t, state[0, :], lw=3, label='Position')
# line_velocity, = plt.plot(t, state[1, :], lw=1, label='Velocity')
# line_predict, = plt.plot(t, predict[0, :], lw=2, label='Predict Position')
# plt.hlines(desired_position, t[0], t[-1], linestyles='dotted')
# plt.legend(handles=[line_position, line_velocity, line_predict])


# Controlled with PID
# sys = MassOnSpring(position=1.0, velocity=0.0, mass=1.0, k=1.0, friction=0.3)
# for i in range(N):
#     control_state[:, i] = sys.state_vector()
#     # Determine control (here, PID, for the sake of example)
#     # error = desired_position - state[0, i]
#     # error_int += error * dt
#     # control[i] = kp * error - kd * state[1, i] + ki * error_int
#     #Determine control using MPPI
    
#     # Advance the simulation
#     sys.advance(dt, control[i])
state, control = sys.Method(state[:, i], state, N, dt, desired_position, number_of_samples, sigma = 0.68, landa = 1)
predict = sys.predict(N, predictive_steps, control)
print(state[0,:])
print(state[1,:])
print(predict[0,:])
print(control)
# sys = MassOnSpring(position=1.0, velocity=0.0, mass=1.0, k=1.0, friction=0.3)
# possible_futures = sys.Generate_Futures(N, number_of_samples)
# predictive_acumulative_costs, predictive_state_cost, predictive_final_costs = sys.instantaneous_cost(possible_futures, N, state, desired_position, number_of_samples)
# predictive_final_costs = sys.terminal_cost(desired_position, predictive_state_cost, predictive_final_costs, number_of_samples, N)
# weight = np.arange(number_of_samples)
# sigma = 0.68
# landa = 1
# u = sys.weighting(state, weight, predictive_final_costs, number_of_samples, N, sigma, landa)

# # Plot the results
fig = plt.figure()
fig.set_size_inches(20, 10)
line_position, = plt.plot(t, state[0, :], lw=3, label='Position')
line_velocity, = plt.plot(t, state[1, :], lw=1, label='Velocity')
line_predict, = plt.plot(t, predict[0, :], lw=2, label='Predict Position')
line_control, = plt.plot(t, control, lw=1, label='Control')
#line_cost, = plt.plot(t, state_cost, lw=2, label='State_Cost')
#line_cumulative, = plt.plot(t, cumulative_cost, lw=2, label='Cumulative_Cost')
plt.hlines(desired_position, t[0], t[-1], linestyles='dotted')
plt.legend(handles=[line_position, line_velocity, line_predict, line_control])
# line_cumulative, line_cost,
plt.show()
