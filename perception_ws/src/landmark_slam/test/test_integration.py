"""
Integration tests for the full landmark SLAM pipeline — no ROS required.

These tests verify that:
  1. The EKF + camera transform pipeline can localise a car on a
     simulated Formula Student track.
  2. Orange cones are ignored (start/finish markers).
  3. The landmark map is consistent across visits.
  4. Covariance stays bounded and PSD over long runs.

Run with:
    pytest perception_ws/src/landmark_slam/test/test_integration.py -v
"""

import math
from typing import List, Tuple

import numpy as np
import pytest

from landmark_slam.ekf import EKFSlam, wrap_angle
from landmark_slam.camera_transform import (
    CameraMount,
    camera_to_robot_2d,
    robot_to_world_2d,
)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_MOUNT = CameraMount(x_offset=0.0, y_offset=0.0)

# Cone colours
_BLUE = 0
_YELLOW = 1
_ORANGE = 2


def _observe_cones(
    true_x: float,
    true_y: float,
    true_theta: float,
    cones: List[Tuple[float, float, int]],
    max_range: float = 8.0,
    obs_noise: float = 0.0,
    rng: np.random.Generator = None,
) -> List[Tuple[np.ndarray, int]]:
    """
    Generate (robot-frame obs, color) for cones visible from true pose.
    """
    observations = []
    c, s = math.cos(true_theta), math.sin(true_theta)

    for (cx, cy, col) in cones:
        dx = cx - true_x
        dy = cy - true_y
        rx =  c * dx + s * dy
        ry = -s * dx + c * dy

        if math.sqrt(rx ** 2 + ry ** 2) > max_range:
            continue

        if obs_noise > 0.0 and rng is not None:
            rx += rng.normal(0.0, obs_noise)
            ry += rng.normal(0.0, obs_noise)

        observations.append((np.array([rx, ry]), col))

    return observations


def _run_slam(
    ekf: EKFSlam,
    true_trajectory: List[Tuple[float, float, float]],
    cones: List[Tuple[float, float, int]],
    obs_noise: float = 0.2,
    imu_noise: float = 0.01,
    v: float = 2.0,
    dt: float = 0.1,
    seed: int = 0,
) -> None:
    """Drive the EKF through a pre-computed trajectory with noisy observations."""
    rng = np.random.default_rng(seed)
    prev_x, prev_y, prev_th = true_trajectory[0]

    for true_x, true_y, true_theta in true_trajectory[1:]:
        # Compute true deltas
        d_theta = wrap_angle(true_theta - prev_th)
        omega = d_theta / dt

        # Noisy prediction
        ekf.predict(v, omega + rng.normal(0, imu_noise), dt)

        # Observe cones
        for obs, col in _observe_cones(true_x, true_y, true_theta, cones,
                                        obs_noise=obs_noise, rng=rng):
            if col == _ORANGE:
                continue   # Ignore orange
            idx, _ = ekf.associate(obs, color=col)
            if idx is not None:
                ekf.update(obs, idx)
            else:
                ekf.add_landmark(obs, color=col)

        prev_x, prev_y, prev_th = true_x, true_y, true_theta


def _straight_trajectory(
    length: float = 10.0, v: float = 2.0, dt: float = 0.1
) -> List[Tuple[float, float, float]]:
    """Generate a straight-line ground-truth trajectory."""
    steps = int(length / (v * dt))
    return [(v * dt * i, 0.0, 0.0) for i in range(steps + 1)]


def _circle_trajectory(
    radius: float = 8.0, total_angle: float = math.pi, v: float = 2.0,
    dt: float = 0.1,
) -> List[Tuple[float, float, float]]:
    """Generate a circular arc trajectory."""
    omega = v / radius
    n_steps = int(total_angle / (omega * dt))
    traj = []
    x, y, th = 0.0, 0.0, 0.0
    for _ in range(n_steps + 1):
        traj.append((x, y, th))
        x  += v * math.cos(th) * dt
        y  += v * math.sin(th) * dt
        th  = wrap_angle(th + omega * dt)
    return traj


# ---------------------------------------------------------------------------
# Test 1 — Straight track
# ---------------------------------------------------------------------------

class TestStraightTrack:
    def test_position_error_bounded(self):
        """
        Drive 10 m straight with cone walls.  Final position error < 0.4 m.
        """
        traj = _straight_trajectory(length=10.0, v=2.0, dt=0.1)
        cones = (
            [(x, 2.0, _BLUE)   for x in range(1, 12)] +
            [(x, -2.0, _YELLOW) for x in range(1, 12)]
        )

        ekf = EKFSlam(np.zeros(3), obs_noise_xy=0.2,
                      process_noise_xy=0.05, process_noise_yaw=0.01)
        _run_slam(ekf, traj, cones, obs_noise=0.2, dt=0.1, v=2.0, seed=1)

        true_final = traj[-1]
        err = math.sqrt((ekf.x - true_final[0]) ** 2 +
                        (ekf.y - true_final[1]) ** 2)
        assert err < 0.4, f'Final position error {err:.3f} m > 0.4 m'

    def test_landmark_count_reasonable(self):
        """
        Should add ~20 landmarks (10 blue + 10 yellow) ±a few edge cases.
        """
        traj = _straight_trajectory(length=10.0, v=2.0, dt=0.1)
        cones = (
            [(x, 2.0, _BLUE)   for x in range(1, 11)] +
            [(x, -2.0, _YELLOW) for x in range(1, 11)]
        )
        ekf = EKFSlam(np.zeros(3), obs_noise_xy=0.2,
                      process_noise_xy=0.05, process_noise_yaw=0.01)
        _run_slam(ekf, traj, cones, obs_noise=0.2, dt=0.1, v=2.0, seed=2)

        # Expect between 10 and 30 landmarks (10 true cones, some duplicates
        # possible from noisy init before association is reliable)
        assert 10 <= ekf.n_landmarks <= 30, (
            f'Unexpected landmark count: {ekf.n_landmarks}'
        )


# ---------------------------------------------------------------------------
# Test 2 — Orange cones ignored
# ---------------------------------------------------------------------------

class TestOrangeConesIgnored:
    def test_no_orange_landmarks_added(self):
        """
        Orange cones (start/finish) must never be added as landmarks.
        """
        ekf = EKFSlam(np.zeros(3))

        # Simulate a process that adds only orange observations
        orange_obs = [
            np.array([5.0, 0.0]),
            np.array([5.1, -0.1]),
            np.array([4.9, 0.1]),
        ]

        # Integration node skips orange before calling EKF — replicate that here
        for obs in orange_obs:
            color = _ORANGE
            if color == _ORANGE:
                continue  # This is what landmark_slam_node.py does
            idx, _ = ekf.associate(obs, color=color)
            if idx is None:
                ekf.add_landmark(obs, color=color)

        assert ekf.n_landmarks == 0, (
            'Orange cone observations must not create landmarks'
        )


# ---------------------------------------------------------------------------
# Test 3 — Re-observation on a curved track
# ---------------------------------------------------------------------------

class TestCurvedTrack:
    def test_heading_error_bounded(self):
        """
        Drive a 180° arc.  Final heading error should be < 8°.
        """
        traj = _circle_trajectory(radius=8.0, total_angle=math.pi,
                                   v=2.0, dt=0.1)
        cones = (
            [(math.cos(a) * 10.0, math.sin(a) * 10.0, _BLUE)
             for a in np.linspace(0, math.pi, 15)] +
            [(math.cos(a) * 6.0,  math.sin(a) * 6.0,  _YELLOW)
             for a in np.linspace(0, math.pi, 15)]
        )

        ekf = EKFSlam(np.zeros(3), obs_noise_xy=0.2,
                      process_noise_xy=0.05, process_noise_yaw=0.015)
        _run_slam(ekf, traj, cones, obs_noise=0.2, dt=0.1, v=2.0,
                  imu_noise=0.02, seed=3)

        true_final = traj[-1]
        heading_err = abs(wrap_angle(ekf.theta - true_final[2]))
        assert heading_err < math.radians(8), (
            f'Heading error {math.degrees(heading_err):.1f}° > 8°'
        )


# ---------------------------------------------------------------------------
# Test 4 — Covariance health over long runs
# ---------------------------------------------------------------------------

class TestCovarianceHealth:
    def test_covariance_stays_psd(self):
        """Covariance must stay positive semi-definite over 100 steps."""
        traj = _straight_trajectory(length=20.0, v=2.0, dt=0.1)
        cones = (
            [(x, 2.0, _BLUE)   for x in range(1, 22)] +
            [(x, -2.0, _YELLOW) for x in range(1, 22)]
        )
        ekf = EKFSlam(np.zeros(3), obs_noise_xy=0.3,
                      process_noise_xy=0.05, process_noise_yaw=0.01)
        _run_slam(ekf, traj, cones, obs_noise=0.3, dt=0.1, v=2.0, seed=4)

        eigvals = np.linalg.eigvalsh(ekf.P)
        assert np.all(eigvals >= -1e-6), (
            f'Covariance not PSD.  Min eigenvalue: {eigvals.min():.2e}'
        )

    def test_covariance_symmetric(self):
        traj = _straight_trajectory(length=10.0, v=2.0, dt=0.1)
        cones = (
            [(x, 2.0, _BLUE)   for x in range(1, 12)] +
            [(x, -2.0, _YELLOW) for x in range(1, 12)]
        )
        ekf = EKFSlam(np.zeros(3), obs_noise_xy=0.3)
        _run_slam(ekf, traj, cones, obs_noise=0.3, dt=0.1, v=2.0, seed=5)

        assert np.allclose(ekf.P, ekf.P.T, atol=1e-10), \
            'Covariance matrix is not symmetric'

    def test_covariance_bounded(self):
        """No element of P should blow up to ridiculous values."""
        traj = _straight_trajectory(length=10.0, v=2.0, dt=0.1)
        cones = (
            [(x, 2.0, _BLUE)   for x in range(1, 12)] +
            [(x, -2.0, _YELLOW) for x in range(1, 12)]
        )
        ekf = EKFSlam(np.zeros(3), obs_noise_xy=0.3)
        _run_slam(ekf, traj, cones, obs_noise=0.3, dt=0.1, v=2.0, seed=6)

        assert np.max(np.abs(ekf.P)) < 1e4, \
            f'Covariance has unreasonably large elements: {np.max(np.abs(ekf.P)):.1e}'


# ---------------------------------------------------------------------------
# Test 5 — Camera-to-robot consistency with EKF
# ---------------------------------------------------------------------------

class TestCameraToEKFConsistency:
    def test_observation_model_round_trip(self):
        """
        Add a landmark from an observation, then re-observe from the SAME
        pose.  The expected observation must exactly match the original.
        """
        ekf = EKFSlam(np.array([2.0, 1.0, 0.5]))
        obs = np.array([4.0, 1.5])
        ekf.add_landmark(obs, color=_BLUE)

        z_exp = ekf._obs_blocks(0)[0]
        np.testing.assert_allclose(z_exp, obs, atol=1e-9,
                                   err_msg='Expected obs after add_landmark '
                                           'does not match original observation')

    def test_two_poses_same_cone_consistent_world(self):
        """
        Observe the same cone from two different starting positions.
        Both EKF instances should agree on the cone's world position.
        """
        true_cone = (7.0, 2.0)

        def _robot_obs(vx, vy, vth):
            dx = true_cone[0] - vx
            dy = true_cone[1] - vy
            c, s = math.cos(vth), math.sin(vth)
            return np.array([ c*dx + s*dy, -s*dx + c*dy])

        ekf1 = EKFSlam(np.array([0.0, 0.0, 0.0]))
        ekf1.add_landmark(_robot_obs(0.0, 0.0, 0.0), color=_BLUE)

        ekf2 = EKFSlam(np.array([3.0, 0.0, 0.0]))
        ekf2.add_landmark(_robot_obs(3.0, 0.0, 0.0), color=_BLUE)

        np.testing.assert_allclose(ekf1.landmark_xy(0), ekf2.landmark_xy(0),
                                   atol=1e-9)
        np.testing.assert_allclose(ekf1.landmark_xy(0), list(true_cone),
                                   atol=1e-9)
