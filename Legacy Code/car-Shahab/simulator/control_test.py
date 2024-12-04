#!env python3

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.animation import FuncAnimation

#import statsmodels.api as sm


class MassOnSpring:
    def __init__(self, position=0.0, velocity=0.0, mass=1.0, k=0.1, friction=0.1):
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

    def cost(self, N, state, desired_position):
        state_cost = np.zeros(N)
        cumulative_cost = np.zeros(N)
        cost = 0
        for i in range(0, N): 
            state_cost[i] = abs(desired_position-state[0, i])
            cost += state_cost[i]
            cumulative_cost[i] = cost
        return cumulative_cost, state_cost

N = 2000  # Number of simulation steps
predictive_steps = 2000
state = np.zeros((2, N))
control = np.zeros(N)
dt = 0.01
desired_position = 0.5

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

predict = sys.predict(N, predictive_steps, control)

# Plot the results
fig = plt.figure()
fig.set_size_inches(20, 10)
line_position, = plt.plot(t, state[0, :], lw=3, label='Position')
line_velocity, = plt.plot(t, state[1, :], lw=1, label='Velocity')
line_predict, = plt.plot(t, predict[0, :], lw=2, label='Predict Position')
plt.hlines(desired_position, t[0], t[-1], linestyles='dotted')
plt.legend(handles=[line_position, line_velocity, line_predict])


# Controlled with PID
sys = MassOnSpring(position=1.0, velocity=0.0, mass=1.0, k=1.0, friction=0.3)
for i in range(N):  # For each time step
    state[:, i] = sys.state_vector()

    # Determine control (here, PID, for the sake of example)
    error = desired_position - state[0, i]
    error_int += error * dt
    control[i] = kp * error - kd * state[1, i] + ki * error_int

    # Advance the simulation
    sys.advance(dt, control[i])
predict = sys.predict(N, predictive_steps, control)
cumulative_cost, state_cost = sys.cost(N, predict, desired_position)

# Plot the results
fig = plt.figure()
fig.set_size_inches(20, 10)
line_position, = plt.plot(t, state[0, :], lw=3, label='Position')
line_velocity, = plt.plot(t, state[1, :], lw=1, label='Velocity')
line_predict, = plt.plot(t, predict[0, :], lw=2, label='Predict Position')
line_control, = plt.plot(t, control, lw=1, label='Control')
#line_cost, = plt.plot(t, state_cost, lw=2, label='State_Cost')
#line_cumulative, = plt.plot(t, cumulative_cost, lw=2, label='Cumulative_Cost')
plt.hlines(desired_position, t[0], t[-1], linestyles='dotted')
plt.legend(handles=[line_position, line_velocity, line_control, line_predict])
# line_cumulative, line_cost,
plt.show()
