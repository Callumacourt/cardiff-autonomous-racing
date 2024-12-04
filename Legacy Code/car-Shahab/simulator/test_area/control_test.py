#!env python3
import numpy
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
            predict[:, i-N] = self.state_vector()
            
            indices = [i-10, i-9, i-8, i-7, i-6, i-5, i-4, i-3, i-2, i-1]
            control[i] = (control[indices].sum())/10

            # Advance the simulation
            self.advance(dt, control[i])
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
control = np.zeros(N + predictive_steps)
dt = 0.01
desired_position = 0.5

error_int = 0.0
# kp = 40.0
# kd = 10.0
# ki = 5.0

kp = 10.0
kd = 5.0
ki = 2.0

t = np.linspace(0, (N + predictive_steps - 1) * dt, N + predictive_steps)

# Open loop control (= no control)
default = MassOnSpring(position=1.0, velocity=0.0, mass=1.0, k=1.0, friction=0.3)
for i in range(N):  # For each time step
    state[:, i] = default.state_vector()

    control[i] = 0.0
    # Advance the simulation
    default.advance(dt, control[i])

predict_default = default.predict(N, predictive_steps, control)

full_position = np.concatenate([state[0, :], predict_default[0, :]])
full_velocity = np.concatenate([state[1, :], predict_default[1, :]])

# Plot the results
fig = plt.figure()
fig.set_size_inches(20, 10)
line_position, = plt.plot(t, full_position, lw=3, label='Position')
line_velocity, = plt.plot(t, full_velocity, lw=1, label='Velocity')
predict_position, = plt.scatter(N*dt, predict_default[0, 0], marker = 'o', color = 'g')
predict_velocity, = plt.scatter(N*dt, predict_default[1, 0], marker = 'o', color = 'r')
plt.hlines(desired_position, t[0], t[-1], linestyles='dotted')
plt.legend(handles=[line_position, line_velocity])
#plt.legend((predict_position, predict_velocity), ('predict_position', 'predict_velocity'))
plt.title('Mass On a Spring System with no control')
plt.xlabel('Time')
plt.ylabel('Position and Velocity')


# Controlled with PID
control = np.zeros(N + predictive_steps)
controlsys = MassOnSpring(position=1.0, velocity=0.0, mass=1.0, k=1.0, friction=0.3)
for i in range(N):  # For each time step
    state[:, i] = controlsys.state_vector()

    # Determine control (here, PID, for the sake of example)
    error = desired_position - state[0, i]
    error_int += error * dt
    control[i] = kp * error - kd * state[1, i] + ki * error_int

    # Advance the simulation
    controlsys.advance(dt, control[i])

predictsys = controlsys.predict(N, predictive_steps, control)
cumulative_cost, state_cost = controlsys.cost(N, predictsys, desired_position)

full_position_pid = np.concatenate([state[0, :], predictsys[0, :]])
full_velocity_pid = np.concatenate([state[1, :], predictsys[1, :]])

# Plot the results
fig = plt.figure()
fig.set_size_inches(20, 10)
line_position, = plt.plot(t, full_position_pid, lw=3, label='Position')
line_velocity, = plt.plot(t, full_velocity_pid, lw=1, label='Velocity')
line_control, = plt.plot(t, control, lw=1, label='Control')
plt.scatter(N*dt, predictsys[0, 0], marker = 'o', color = 'g')
plt.scatter(N*dt, predictsys[1, 0], marker = 'o', color = 'r')
#line_cost, = plt.plot(t, state_cost, lw=2, label='State_Cost')
#line_cumulative, = plt.plot(t, cumulative_cost, lw=2, label='Cumulative_Cost')
plt.hlines(desired_position, t[0], t[-1], linestyles='dotted')
plt.legend(handles=[line_position, line_velocity, line_control])
#plt.legend((predict_position, predict_velocity), ('predict_position', 'predict_velocity'))
plt.title('Mass On a Spring System with PID control')
plt.xlabel('Time')
plt.ylabel('Position and Velocity')
plt.show()
