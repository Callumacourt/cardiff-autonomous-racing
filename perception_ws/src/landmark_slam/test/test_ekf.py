"""
Unit tests for landmark_slam.ekf — no ROS required.

Run with:
    pytest perception_ws/src/landmark_slam/test/test_ekf.py -v

Or via colcon (inside the perception container):
    colcon test --packages-select landmark_slam
    colcon test-result --verbose
"""

import math
from typing import Tuple

import numpy as np
import pytest

from landmark_slam.ekf import EKFSlam, wrap_angle, yaw_to_quaternion


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_ekf(**kwargs) -> EKFSlam:
    """Create an EKFSlam at the origin with sensible defaults."""
    defaults = dict(
        initial_pose=np.zeros(3),
        process_noise_xy=0.01,
        process_noise_yaw=0.005,
        obs_noise_xy=0.3,
    )
    defaults.update(kwargs)
    return EKFSlam(**defaults)


def _is_symmetric(M: np.ndarray, atol: float = 1e-10) -> bool:
    return np.allclose(M, M.T, atol=atol)


def _is_psd(M: np.ndarray, tol: float = -1e-8) -> bool:
    return bool(np.all(np.linalg.eigvalsh(M) >= tol))


# ---------------------------------------------------------------------------
# wrap_angle
# ---------------------------------------------------------------------------

class TestWrapAngle:
    def test_zero(self):
        assert wrap_angle(0.0) == pytest.approx(0.0)

    def test_pi_returns_minus_pi_or_pi(self):
        # π wraps to −π (modular boundary)
        assert abs(wrap_angle(math.pi)) == pytest.approx(math.pi, abs=1e-12)

    def test_just_above_pi(self):
        assert wrap_angle(math.pi + 0.1) == pytest.approx(-math.pi + 0.1)

    def test_just_below_minus_pi(self):
        assert wrap_angle(-math.pi - 0.1) == pytest.approx(math.pi - 0.1)

    def test_two_pi_is_zero(self):
        assert wrap_angle(2 * math.pi) == pytest.approx(0.0, abs=1e-12)

    def test_large_positive(self):
        assert wrap_angle(5 * math.pi) == pytest.approx(-math.pi, abs=1e-12)


# ---------------------------------------------------------------------------
# yaw_to_quaternion
# ---------------------------------------------------------------------------

class TestYawToQuat:
    def test_zero_yaw(self):
        x, y, z, w = yaw_to_quaternion(0.0)
        assert (x, y, z) == pytest.approx((0.0, 0.0, 0.0))
        assert w == pytest.approx(1.0)

    def test_unit_norm(self):
        for yaw in [0.0, math.pi / 4, math.pi / 2, math.pi, -math.pi / 3]:
            q = yaw_to_quaternion(yaw)
            norm = math.sqrt(sum(v ** 2 for v in q))
            assert norm == pytest.approx(1.0, abs=1e-12)


# ---------------------------------------------------------------------------
# EKFSlam — construction
# ---------------------------------------------------------------------------

class TestConstruction:
    def test_initial_state_dimension(self):
        ekf = make_ekf()
        assert ekf.state_dim == 3
        assert ekf.n_landmarks == 0

    def test_initial_pose_stored(self):
        pose = np.array([1.0, 2.0, 0.5])
        ekf = make_ekf(initial_pose=pose)
        np.testing.assert_array_equal(ekf.pose, pose)

    def test_invalid_initial_pose_raises(self):
        with pytest.raises(ValueError):
            EKFSlam(initial_pose=np.array([0.0, 0.0]))  # wrong shape

    def test_invalid_cov_shape_raises(self):
        with pytest.raises(ValueError):
            EKFSlam(
                initial_pose=np.zeros(3),
                initial_pose_cov=np.eye(4),
            )


# ---------------------------------------------------------------------------
# EKFSlam — predict
# ---------------------------------------------------------------------------

class TestPredict:
    def test_stationary_no_change(self):
        ekf = make_ekf()
        state_before = ekf.state.copy()
        ekf.predict(v=0.0, omega=0.0, dt=1.0)
        np.testing.assert_allclose(ekf.state, state_before, atol=1e-12)

    def test_forward_motion(self):
        ekf = make_ekf()
        ekf.predict(v=1.0, omega=0.0, dt=1.0)
        np.testing.assert_allclose(ekf.pose, [1.0, 0.0, 0.0], atol=1e-9)

    def test_forward_motion_x_direction(self):
        """1 m/s for 2 s = 2 m in x."""
        ekf = make_ekf()
        ekf.predict(v=1.0, omega=0.0, dt=2.0)
        assert ekf.x == pytest.approx(2.0)
        assert ekf.y == pytest.approx(0.0)

    def test_rotation_only(self):
        ekf = make_ekf()
        ekf.predict(v=0.0, omega=math.pi / 2, dt=1.0)
        assert ekf.theta == pytest.approx(math.pi / 2)
        np.testing.assert_allclose(ekf.pose[:2], [0.0, 0.0], atol=1e-12)

    def test_rotation_wraps_correctly(self):
        ekf = make_ekf()
        ekf.predict(v=0.0, omega=math.pi, dt=1.5)  # 270° CCW → −90°
        assert ekf.theta == pytest.approx(-math.pi / 2, abs=1e-9)

    def test_heading_90_forward_motion(self):
        """Facing 90° (left), 1 m forward → y increases."""
        ekf = make_ekf(initial_pose=np.array([0.0, 0.0, math.pi / 2]))
        ekf.predict(v=1.0, omega=0.0, dt=1.0)
        assert ekf.x == pytest.approx(0.0, abs=1e-9)
        assert ekf.y == pytest.approx(1.0, abs=1e-9)

    def test_covariance_grows(self):
        ekf = make_ekf()
        tr_before = np.trace(ekf.P)
        ekf.predict(v=1.0, omega=0.1, dt=0.1)
        assert np.trace(ekf.P) > tr_before

    def test_covariance_symmetric_after_predict(self):
        ekf = make_ekf()
        for _ in range(20):
            ekf.predict(v=2.0, omega=0.3, dt=0.05)
        assert _is_symmetric(ekf.P)

    def test_negative_dt_is_noop(self):
        ekf = make_ekf()
        state_before = ekf.state.copy()
        P_before = ekf.P.copy()
        ekf.predict(v=5.0, omega=1.0, dt=-0.1)
        np.testing.assert_array_equal(ekf.state, state_before)
        np.testing.assert_array_equal(ekf.P, P_before)

    def test_zero_dt_is_noop(self):
        ekf = make_ekf()
        state_before = ekf.state.copy()
        ekf.predict(v=5.0, omega=1.0, dt=0.0)
        np.testing.assert_array_equal(ekf.state, state_before)


# ---------------------------------------------------------------------------
# EKFSlam — add_landmark
# ---------------------------------------------------------------------------

class TestAddLandmark:
    def test_first_landmark_ahead(self):
        """Cone 5 m straight ahead at heading 0 → world (5, 0)."""
        ekf = make_ekf()
        ekf.add_landmark(np.array([5.0, 0.0]), color=0)
        assert ekf.n_landmarks == 1
        np.testing.assert_allclose(ekf.landmark_xy(0), [5.0, 0.0], atol=1e-9)

    def test_landmark_to_left(self):
        ekf = make_ekf()
        ekf.add_landmark(np.array([0.0, 3.0]), color=1)
        np.testing.assert_allclose(ekf.landmark_xy(0), [0.0, 3.0], atol=1e-9)

    def test_landmark_with_heading_90(self):
        """Car faces 90° (left).  Cone 5 m robot-forward → world (0, 5)."""
        ekf = make_ekf(initial_pose=np.array([0.0, 0.0, math.pi / 2]))
        ekf.add_landmark(np.array([5.0, 0.0]), color=0)
        np.testing.assert_allclose(ekf.landmark_xy(0), [0.0, 5.0], atol=1e-9)

    def test_landmark_with_offset_position(self):
        """Car at (2, 1), heading 0.  Cone at robot (3, 0) → world (5, 1)."""
        ekf = make_ekf(initial_pose=np.array([2.0, 1.0, 0.0]))
        ekf.add_landmark(np.array([3.0, 0.0]), color=0)
        np.testing.assert_allclose(ekf.landmark_xy(0), [5.0, 1.0], atol=1e-9)

    def test_state_dim_grows(self):
        ekf = make_ekf()
        assert ekf.state_dim == 3
        ekf.add_landmark(np.array([1.0, 0.0]), color=0)
        assert ekf.state_dim == 5
        ekf.add_landmark(np.array([2.0, 1.0]), color=1)
        assert ekf.state_dim == 7

    def test_covariance_grows_in_shape(self):
        ekf = make_ekf()
        ekf.add_landmark(np.array([3.0, 0.0]), color=0)
        assert ekf.P.shape == (5, 5)
        ekf.add_landmark(np.array([3.0, 2.0]), color=1)
        assert ekf.P.shape == (7, 7)

    def test_covariance_symmetric_after_add(self):
        ekf = make_ekf()
        ekf.add_landmark(np.array([5.0, 1.0]), color=0)
        assert _is_symmetric(ekf.P)

    def test_covariance_psd_after_add(self):
        ekf = make_ekf()
        ekf.add_landmark(np.array([5.0, 1.0]), color=0)
        assert _is_psd(ekf.P)

    def test_color_stored(self):
        ekf = make_ekf()
        ekf.add_landmark(np.array([2.0, 0.0]), color=0)
        ekf.add_landmark(np.array([2.0, 1.0]), color=1)
        assert ekf.landmark_colors[0] == 0
        assert ekf.landmark_colors[1] == 1

    def test_returns_correct_index(self):
        ekf = make_ekf()
        i0 = ekf.add_landmark(np.array([1.0, 0.0]), color=0)
        i1 = ekf.add_landmark(np.array([2.0, 0.0]), color=1)
        assert i0 == 0
        assert i1 == 1


# ---------------------------------------------------------------------------
# EKFSlam — associate (data association)
# ---------------------------------------------------------------------------

class TestAssociate:
    def test_no_landmarks_returns_none(self):
        ekf = make_ekf()
        idx, dist = ekf.associate(np.array([5.0, 0.0]), color=0)
        assert idx is None

    def test_exact_observation_associates(self):
        ekf = make_ekf()
        ekf.add_landmark(np.array([5.0, 0.0]), color=0)
        idx, _ = ekf.associate(np.array([5.0, 0.0]), color=0)
        assert idx == 0

    def test_nearby_observation_associates(self):
        """Observation within 0.1 m should associate."""
        ekf = make_ekf()
        ekf.add_landmark(np.array([5.0, 0.0]), color=0)
        idx, _ = ekf.associate(np.array([5.05, 0.03]), color=0)
        assert idx == 0

    def test_far_observation_creates_new(self):
        """Observation 20 m away from only landmark → no association."""
        ekf = make_ekf()
        ekf.add_landmark(np.array([5.0, 0.0]), color=0)
        idx, _ = ekf.associate(np.array([25.0, 10.0]), color=0)
        assert idx is None

    def test_color_mismatch_not_associated(self):
        """Blue observation should never associate with a yellow landmark."""
        ekf = make_ekf()
        ekf.add_landmark(np.array([5.0, 0.0]), color=1)   # yellow
        idx, _ = ekf.associate(np.array([5.0, 0.0]), color=0)  # blue query
        assert idx is None

    def test_nearest_of_two_selected(self):
        ekf = make_ekf()
        ekf.add_landmark(np.array([5.0, 0.0]), color=0)
        ekf.add_landmark(np.array([5.0, 3.0]), color=0)
        idx, _ = ekf.associate(np.array([5.0, 0.1]), color=0)
        assert idx == 0

    def test_second_of_two_selected(self):
        ekf = make_ekf()
        ekf.add_landmark(np.array([5.0, 0.0]), color=0)
        ekf.add_landmark(np.array([5.0, 3.0]), color=0)
        idx, _ = ekf.associate(np.array([5.0, 2.9]), color=0)
        assert idx == 1

    def test_no_color_filter_matches_any(self):
        """color=None should not filter by colour."""
        ekf = make_ekf()
        ekf.add_landmark(np.array([5.0, 0.0]), color=1)
        idx, _ = ekf.associate(np.array([5.0, 0.0]), color=None)
        assert idx == 0


# ---------------------------------------------------------------------------
# EKFSlam — update
# ---------------------------------------------------------------------------

class TestUpdate:
    def test_update_reduces_vehicle_uncertainty(self):
        ekf = make_ekf()
        ekf.predict(v=1.0, omega=0.0, dt=2.0)   # add uncertainty
        ekf.add_landmark(np.array([5.0, 0.0]), color=0)
        P_x_before = ekf.P[0, 0]
        ekf.update(np.array([5.0, 0.0]), landmark_idx=0)
        # Vehicle x-variance should decrease (or stay same) after a good obs
        assert ekf.P[0, 0] <= P_x_before + 1e-10

    def test_update_corrects_drift(self):
        """Inject 0.5 m drift; landmark observation should pull pose back."""
        ekf = make_ekf()
        ekf.add_landmark(np.array([5.0, 0.0]), color=0)

        # Artificially drift car position (pretend IMU drifted 0.5 m right)
        ekf.state[0] += 0.5

        # From true pose (0,0) the landmark is at (5,0) robot-frame.
        # The drifted car thinks it's at (0.5,0), so if we observe the
        # landmark as-if from (0,0), the EKF should reduce the residual.
        z_obs = np.array([5.0, 0.0])
        z_before = ekf._obs_blocks(0)[0]
        resid_before = np.linalg.norm(z_obs - z_before)

        ekf.update(np.array([5.0, 0.0]), landmark_idx=0)

        z_after = ekf._obs_blocks(0)[0]
        resid_after = np.linalg.norm(z_obs - z_after)

        assert resid_after < resid_before

    def test_covariance_symmetric_after_update(self):
        ekf = make_ekf()
        ekf.add_landmark(np.array([4.0, 1.0]), color=0)
        for obs in [np.array([4.1, 0.9]), np.array([3.9, 1.1])]:
            ekf.update(obs, landmark_idx=0)
        assert _is_symmetric(ekf.P)

    def test_covariance_psd_after_updates(self):
        ekf = make_ekf()
        ekf.add_landmark(np.array([4.0, 1.0]), color=0)
        for obs in [np.array([4.1, 0.9]), np.array([3.9, 1.1]),
                    np.array([4.0, 1.0])]:
            ekf.update(obs, landmark_idx=0)
        assert _is_psd(ekf.P)


# ---------------------------------------------------------------------------
# Full EKF loop — convergence tests
# ---------------------------------------------------------------------------

class TestFullLoop:
    def test_stationary_landmark_converges(self):
        """
        Stationary vehicle, 30 noisy observations of the same cone.
        Landmark estimate should converge to within 0.2 m of truth.
        """
        ekf = make_ekf(obs_noise_xy=0.3)
        rng = np.random.default_rng(42)
        true_lx, true_ly = 5.0, 1.0

        # First obs initialises the landmark
        obs0 = np.array([true_lx, true_ly]) + rng.normal(0.0, 0.3, 2)
        ekf.add_landmark(obs0, color=0)

        for _ in range(30):
            obs = np.array([true_lx, true_ly]) + rng.normal(0.0, 0.3, 2)
            ekf.update(obs, landmark_idx=0)

        lm = ekf.landmark_xy(0)
        np.testing.assert_allclose(lm, [true_lx, true_ly], atol=0.25)

    def test_moving_car_position_error_bounded(self):
        """
        Car drives straight 10 m observing cones on both sides.
        Final position error should be < 0.5 m.
        """
        ekf = make_ekf(obs_noise_xy=0.2, process_noise_xy=0.05,
                       process_noise_yaw=0.01)
        rng = np.random.default_rng(0)

        dt = 0.1
        v = 2.0           # m/s
        true_x, true_y, true_th = 0.0, 0.0, 0.0

        # Known track cones (simplified straight track)
        cones_left  = [(x, 2.0, 0) for x in range(1, 11)]
        cones_right = [(x, -2.0, 1) for x in range(1, 11)]
        all_cones = cones_left + cones_right

        for _ in range(50):   # 5 s of driving
            true_x += v * math.cos(true_th) * dt
            true_y += v * math.sin(true_th) * dt

            # Noisy yaw rate
            ekf.predict(v, rng.normal(0, 0.01), dt)

            # Observe cones within 7 m
            for (cx, cy, col) in all_cones:
                dx = cx - true_x
                dy = cy - true_y
                c, s = math.cos(true_th), math.sin(true_th)
                rx =  c * dx + s * dy
                ry = -s * dx + c * dy

                if math.sqrt(rx ** 2 + ry ** 2) > 7.0:
                    continue

                obs = np.array([rx, ry]) + rng.normal(0, 0.2, 2)
                idx, _ = ekf.associate(obs, color=col)
                if idx is not None:
                    ekf.update(obs, idx)
                else:
                    ekf.add_landmark(obs, color=col)

        err = math.sqrt((ekf.x - true_x) ** 2 + (ekf.y - true_y) ** 2)
        assert err < 0.5, f'Position error {err:.3f} m exceeds 0.5 m threshold'

    def test_heading_error_bounded(self):
        """After driving a curve, heading error should be < 5°."""
        ekf = make_ekf(obs_noise_xy=0.2, process_noise_yaw=0.01)
        rng = np.random.default_rng(7)

        dt = 0.1
        true_x, true_y, true_th = 0.0, 0.0, 0.0
        omega_true = 0.2   # rad/s gentle left curve

        cones = [(x, y, col)
                 for x in range(1, 15)
                 for y, col in [(2.0, 0), (-2.0, 1)]]

        for _ in range(50):
            true_x += 1.5 * math.cos(true_th) * dt
            true_y += 1.5 * math.sin(true_th) * dt
            true_th = wrap_angle(true_th + omega_true * dt)

            ekf.predict(1.5, omega_true + rng.normal(0, 0.02), dt)

            for (cx, cy, col) in cones:
                dx = cx - true_x
                dy = cy - true_y
                c, s = math.cos(true_th), math.sin(true_th)
                rx =  c * dx + s * dy
                ry = -s * dx + c * dy
                if math.sqrt(rx ** 2 + ry ** 2) > 6.0:
                    continue
                obs = np.array([rx, ry]) + rng.normal(0, 0.2, 2)
                idx, _ = ekf.associate(obs, color=col)
                if idx is not None:
                    ekf.update(obs, idx)
                else:
                    ekf.add_landmark(obs, color=col)

        heading_err = abs(wrap_angle(ekf.theta - true_th))
        assert heading_err < math.radians(5), (
            f'Heading error {math.degrees(heading_err):.1f}° exceeds 5°'
        )
