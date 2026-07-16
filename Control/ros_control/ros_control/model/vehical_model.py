import math
import os
import time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

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
    WHEEL_RADIUS_m = 0.253


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
    def __init__(self, timestep:float=0.05, state:Vehicle_State = Vehicle_State(), input:Vehicle_Input = Vehicle_Input(), mass:float = 500.0, F_sideslip_stiffness:float = -100_000, R_sideslip_stiffness:float = -80_000,lf=0.7,lr=0.7,yaw_inertia:float = 1500,matPlotLib:bool=False):
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

    def run_validation_sweep(self, steering_angles, speed=6.0, steps=120):
        """Run a simple open-loop steering sweep and return peak lateral response per steering angle."""
        results = []
        for steering in steering_angles:
            state = Vehicle_State(x_speed=speed, y_speed=0.0)
            model = Dynamics_Model(
                timestep=self.timestep,
                mass=self.mass,
                F_sideslip_stiffness=self.F_sideslip_stiffness,
                R_sideslip_stiffness=self.R_sideslip_stiffness,
                lf=self.lf,
                lr=self.lr,
                yaw_inertia=self.yaw_inertia,
            )
            model.set_state(state)

            peak_lateral_acc = 0.0
            peak_yaw_rate = 0.0

            for _ in range(steps):
                model.calculate_next_state(Vehicle_Input(acceleration=0.0, steering_angle=steering))
                current_state = model.get_state()
                lateral_acc = abs(current_state.yaw_rate * max(current_state.directional_velocity, 1e-6))
                peak_lateral_acc = max(peak_lateral_acc, lateral_acc)
                peak_yaw_rate = max(peak_yaw_rate, abs(current_state.yaw_rate))

            results.append((steering, peak_lateral_acc, peak_yaw_rate))

        return results

    def run_control_sweep(self, steering_angles, acceleration_values, speed=6.0, steps=100):
        """Sweep both steering angle and longitudinal acceleration to test combined vehicle response."""
        results = []
        for steering in steering_angles:
            for acceleration in acceleration_values:
                state = Vehicle_State(x_speed=speed, y_speed=0.0)
                model = Dynamics_Model(
                    timestep=self.timestep,
                    mass=self.mass,
                    F_sideslip_stiffness=self.F_sideslip_stiffness,
                    R_sideslip_stiffness=self.R_sideslip_stiffness,
                    lf=self.lf,
                    lr=self.lr,
                    yaw_inertia=self.yaw_inertia,
                )
                model.set_state(state)

                peak_lateral_acc = 0.0
                peak_yaw_rate = 0.0

                for _ in range(steps):
                    model.calculate_next_state(Vehicle_Input(acceleration=acceleration, steering_angle=steering))
                    current_state = model.get_state()
                    lateral_acc = abs(current_state.yaw_rate * max(current_state.directional_velocity, 1e-6))
                    peak_lateral_acc = max(peak_lateral_acc, lateral_acc)
                    peak_yaw_rate = max(peak_yaw_rate, abs(current_state.yaw_rate))

                results.append((steering, acceleration, peak_lateral_acc, peak_yaw_rate))

        return results

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
    start_time = time.time_ns()
    model = Dynamics_Model(timestep=0.01, matPlotLib=False)
    steering_angles = np.linspace(0.03, 0.35, 12)

    results = model.run_validation_sweep(steering_angles, speed=6.0, steps=140)
    steering_values = np.array([item[0] for item in results])
    lateral_acc_values = np.array([item[1] for item in results])
    yaw_rate_values = np.array([item[2] for item in results])

    plt.figure(figsize=(8, 5))
    plt.plot(steering_values, lateral_acc_values, marker="o", linewidth=2, label="Peak lateral acceleration")
    plt.plot(steering_values, yaw_rate_values, marker="s", linewidth=2, label="Peak yaw rate")
    plt.xlabel("Steering angle (rad)")
    plt.ylabel("Response magnitude")
    plt.title("Validation sweep: steering input vs. vehicle response")
    plt.grid(True, alpha=0.3)
    plt.legend()

    steering_validation_path = os.path.join(os.path.dirname(__file__), "vehicle_validation_plot.png")
    plt.tight_layout()
    plt.savefig(steering_validation_path, dpi=200)
    plt.close()

    acceleration_values = np.array([0.0, 1.0, 2.0, 3.0])
    control_results = model.run_control_sweep(steering_angles, acceleration_values, speed=6.0, steps=100)

    control_grid = np.zeros((len(acceleration_values), len(steering_angles)))
    for steering, acceleration, peak_lateral_acc, _ in control_results:
        accel_index = int(np.where(acceleration_values == acceleration)[0][0])
        steering_index = int(np.where(steering_angles == steering)[0][0])
        control_grid[accel_index, steering_index] = peak_lateral_acc

    plt.figure(figsize=(8, 5))
    plt.imshow(control_grid, aspect="auto", origin="lower", cmap="viridis")
    plt.colorbar(label="Peak lateral acceleration")
    plt.xticks(np.arange(len(steering_angles)), np.round(steering_angles, 3))
    plt.yticks(np.arange(len(acceleration_values)), acceleration_values)
    plt.xlabel("Steering angle (rad)")
    plt.ylabel("Longitudinal acceleration")
    plt.title("Combined control sweep: steering and acceleration")
    plt.tight_layout()

    control_sweep_path = os.path.join(os.path.dirname(__file__), "vehicle_control_sweep.png")
    plt.savefig(control_sweep_path, dpi=200)
    plt.close()

    end_time = time.time_ns()
    print(f"Saved steering validation plot to {steering_validation_path}")
    print(f"Saved control sweep plot to {control_sweep_path}")
    print(f"Simulation time: {(end_time - start_time) / 1e6:.2f} ms")
    print("Interpretation: the response rises quickly and then flattens, which is consistent with a tire-limited cornering regime.")


    # For storing trajectory and velocities
    x_positions = []
    y_positions = []
    speeds = []
    directions = []

    model = Dynamics_Model(timestep=0.01, matPlotLib=False)
    model.set_state(Vehicle_State(x_speed=4.0, y_speed=0.0))

    inputs = [Vehicle_Input(2.5, 0.0) for _ in range(80)] + \
             [Vehicle_Input(-2.0, 0.0) for _ in range(40)] + \
             [Vehicle_Input(0.2, 0.10) for _ in range(120)] + \
             [Vehicle_Input(0.0, -0.12) for _ in range(120)] + \
             [Vehicle_Input(2.0, 0.0) for _ in range(80)]

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

    plt.figure(figsize=(8, 8))
    plot_points = np.column_stack((x, y))
    sc = plt.scatter(plot_points[:, 0], plot_points[:, 1], c=speed, cmap='viridis', s=45, edgecolors='none')

    # Use a thicker line for the path and show a sparse set of clearly visible direction markers.
    sample_stride = 16
    sample_idx = np.arange(0, len(x), sample_stride)
    plt.plot(x[sample_idx], y[sample_idx], color='white', linewidth=1.8, alpha=0.95)

    for i in sample_idx:
        dx, dy = directions[i]
        if np.linalg.norm([dx, dy]) > 1e-6:
            plt.annotate(
                '',
                xy=(x[i] + 0.18 * dx, y[i] + 0.18 * dy),
                xytext=(x[i], y[i]),
                arrowprops=dict(arrowstyle='->', color='#ff4d4d', lw=1.8, mutation_scale=12),
                annotation_clip=False,
            )

    plt.title("Vehicle Trajectory Colored by Speed")
    x_margin = max(0.5, 0.03 * (np.max(x) - np.min(x)))
    y_margin = max(0.5, 0.03 * (np.max(y) - np.min(y)))
    plt.xlim(np.min(x) - x_margin, np.max(x) + x_margin)
    plt.ylim(np.min(y) - y_margin, np.max(y) + y_margin)
    plt.xlabel("X Position (m)")
    plt.ylabel("Y Position (m)")
    plt.grid(True, alpha=0.3)
    plt.gca().set_aspect('equal', adjustable='box')
    cbar = plt.colorbar(sc, label="Speed (m/s)", pad=0.04, shrink=0.9, orientation='horizontal')
    cbar.ax.set_position([0.15, 0.06, 0.7, 0.03])
    plt.tight_layout()
    plt.savefig(os.path.join(os.path.dirname(__file__), "vehicle_trajectory_plot.png"), dpi=200)
    plt.close()
