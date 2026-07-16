import os
import sys
from pathlib import Path as pathlib_Path

import matplotlib.pyplot as plt
import numpy as np

# allow imports from the ros_control package root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from MPC.main import Model_Predictive_Control
from model.vehical_model import Vehicle_Input, Vehicle_State
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Header


def make_straight_path(length: int) -> Path:
    poses = []
    for i in range(length):
        pose = PoseStamped()
        pose.pose.position.x = float(i)
        pose.pose.position.y = 0.0
        pose.pose.position.z = 0.0
        poses.append(pose)

    path = Path()
    path.header = Header()
    path.poses = poses
    return path


def plot_cost_heatmap(
    mpc: Model_Predictive_Control,
    initial_state: Vehicle_State,
    required_path: Path,
    velocities: np.ndarray,
    steering_angles: np.ndarray,
    save_path: str = "test_plots/cost_vs_speed_steering.png",
) -> None:
    costs = np.zeros((len(velocities), len(steering_angles)), dtype=float)

    for i, v in enumerate(velocities):
        for j, steer in enumerate(steering_angles):
            state = Vehicle_State(
                x_pos=initial_state.xpos,
                y_pos=initial_state.ypos,
                x_speed=v,
                y_speed=initial_state.perpendicualar_velocity,
                yaw_angle=initial_state.yaw_angle,
                yaw_rate=initial_state.yaw_rate,
                wheel_rpm=initial_state.wheels_rpm,
                steering_angle_rad=steer,
            )

            inputs = [Vehicle_Input(acceleration=0.0, steering_angle=steer)
                      for _ in range(len(required_path.poses))]

            costs[i, j] = mpc.cost_function(state, inputs, required_path)

    plot_dir = pathlib_Path("test_plots")
    plot_dir.mkdir(exist_ok=True)

    S, T = np.meshgrid(steering_angles, velocities)

    fig, ax = plt.subplots()
    heatmap = ax.pcolormesh(
        S,
        T,
        costs,
        shading="auto",
        cmap="viridis",
    )
    cbar = fig.colorbar(heatmap, ax=ax)
    cbar.set_label("Cost")

    ax.set_title("MPC Cost Heatmap: Velocity vs Steering Angle")
    ax.set_xlabel("Steering angle (rad)")
    ax.set_ylabel("Directional velocity (m/s)")
    ax.grid(True, which="both", linestyle="--", linewidth=0.5)

    fig.savefig(plot_dir / pathlib_Path(save_path).name, dpi=120, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    mpc = Model_Predictive_Control(timestep=0.5)
    init_state = Vehicle_State(
        x_pos=0.0,
        y_pos=0.0,
        x_speed=0.0,
        y_speed=0.0,
        yaw_angle=0.0,
        yaw_rate=0.0,
        wheel_rpm=0.0,
        steering_angle_rad=0.0,
    )
    required_path = make_straight_path(10)
    velocities = np.linspace(-5.0, 10.0, 31)
    steering_angles = np.linspace(-0.5, 0.5, 31)
    plot_cost_heatmap(mpc, init_state, required_path, velocities, steering_angles)
    print("Saved cost heatmap to test_plots/cost_vs_speed_steering.png")import os
import sys
from pathlib import Path as pathlib_Path

import matplotlib.pyplot as plt
import numpy as np

# allow imports from the ros_control package root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from MPC.main import Model_Predictive_Control
from model.vehical_model import Vehicle_Input, Vehicle_State
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Header


def make_straight_path(length: int) -> Path:
    poses = []
    for i in range(length):
        pose = PoseStamped()
        pose.pose.position.x = float(i)
        pose.pose.position.y = 0.0
        pose.pose.position.z = 0.0
        poses.append(pose)

    path = Path()
    path.header = Header()
    path.poses = poses
    return path


def plot_cost_vs_velocity(
    mpc: Model_Predictive_Control,
    initial_state: Vehicle_State,
    required_path: Path,
    velocities: np.ndarray,
    save_path: str = "test_plots/cost_vs_velocity.png",
) -> None:
    costs = []

    for v in velocities:
        state = Vehicle_State(
            x_pos=initial_state.xpos,
            y_pos=initial_state.ypos,
            x_speed=v,
            y_speed=initial_state.perpendicualar_velocity,
            yaw_angle=initial_state.yaw_angle,
            yaw_rate=initial_state.yaw_rate,
            wheel_rpm=initial_state.wheels_rpm,
            steering_angle_rad=initial_state.steering_angle_rad,
        )

        inputs = [Vehicle_Input(acceleration=0.0, steering_angle=0.0)
                  for _ in range(len(required_path.poses))]

        cost = mpc.cost_function(state, inputs, required_path)
        costs.append(cost)

    plot_dir = pathlib_Path("test_plots")
    plot_dir.mkdir(exist_ok=True)

    fig, ax = plt.subplots()
    ax.plot(velocities, costs, marker="o", linestyle="-")
    ax.set_title("MPC Cost vs Velocity")
    ax.set_xlabel("Directional velocity (m/s)")
    ax.set_ylabel("Cost")
    ax.set_yscale("log")
    ax.grid(True, which="both", linestyle="--", linewidth=0.5)

    fig.savefig(plot_dir / pathlib_Path(save_path).name, dpi=120, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    mpc = Model_Predictive_Control(timestep=0.5)
    init_state = Vehicle_State(
        x_pos=0.0,
        y_pos=0.0,
        x_speed=0.0,
        y_speed=0.0,
        yaw_angle=0.0,
        yaw_rate=0.0,
        wheel_rpm=0.0,
        steering_angle_rad=0.0,
    )
    required_path = make_straight_path(10)
    velocities = np.linspace(-5.0, 10.0, 31)
    plot_cost_vs_velocity(mpc, init_state, required_path, velocities)
    print("Saved cost-vs-velocity plot to test_plots/cost_vs_velocity.png")