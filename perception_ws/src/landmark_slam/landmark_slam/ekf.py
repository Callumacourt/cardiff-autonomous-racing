"""
EKF-SLAM implementation for Formula Student cone landmark SLAM.

Pure Python / NumPy — zero ROS dependencies so this module is fully
unit-testable in isolation.

State vector layout
-------------------
x = [x_r, y_r, θ_r,  x_L0, y_L0,  x_L1, y_L1,  ...]
     ──── vehicle ────  ─── landmark 0 ───  ─── L1 ───

All positions in metres (2-D ground plane), angles in radians, wrapped
to (−π, π].

Motion model
------------
Unicycle (constant heading during dt):
    x_r' = x_r + v·cos(θ)·dt
    y_r' = y_r + v·sin(θ)·dt
    θ_r' = θ_r + ω·dt

Observation model
-----------------
Cone i at world position (lx_i, ly_i) is observed in robot body frame as:
    obs_x =  cos(θ)·(lx_i − x_r) + sin(θ)·(ly_i − y_r)
    obs_y = −sin(θ)·(lx_i − x_r) + cos(θ)·(ly_i − y_r)

Data association
----------------
Mahalanobis distance with chi-squared threshold (2 DOF, p=0.01 → 9.21).
Observations with distance > threshold create a new landmark.
"""

import math
from typing import List, Optional, Tuple

import numpy as np


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def wrap_angle(angle: float) -> float:
    """Wrap *angle* (rad) to (−π, π]."""
    return float((angle + math.pi) % (2.0 * math.pi) - math.pi)


def yaw_to_quaternion(yaw: float) -> Tuple[float, float, float, float]:
    """Return (x, y, z, w) quaternion for a pure yaw rotation."""
    half = yaw * 0.5
    return (0.0, 0.0, math.sin(half), math.cos(half))


# ---------------------------------------------------------------------------
# EKF-SLAM
# ---------------------------------------------------------------------------

class EKFSlam:
    """
    Extended Kalman Filter SLAM with a growing landmark state vector.

    Landmarks are 2-D cone positions (x, y) in the world/map frame.
    Cone colour is stored alongside each landmark and used during data
    association so that blue and yellow cones are never confused.

    Parameters
    ----------
    initial_pose : ndarray, shape (3,)
        Starting vehicle pose [x, y, θ].
    initial_pose_cov : ndarray, shape (3, 3), optional
        Initial vehicle covariance.  Defaults to a small diagonal.
    process_noise_xy : float
        Std-dev (m/√s) of position noise in the motion model.
    process_noise_yaw : float
        Std-dev (rad/√s) of heading noise in the motion model.
    obs_noise_xy : float
        Std-dev (m) of each cone observation coordinate.
    mahal_thresh : float
        Mahalanobis-distance threshold for landmark association.
        chi-squared(2 DOF) 99th-percentile = 9.21 (default).
    """

    def __init__(
        self,
        initial_pose: np.ndarray,
        initial_pose_cov: Optional[np.ndarray] = None,
        process_noise_xy: float = 0.1,
        process_noise_yaw: float = 0.05,
        obs_noise_xy: float = 0.5,
        mahal_thresh: float = 9.21,
    ) -> None:
        if initial_pose.shape != (3,):
            raise ValueError("initial_pose must be shape (3,)")

        self.state: np.ndarray = initial_pose.astype(float).copy()

        if initial_pose_cov is None:
            self.P: np.ndarray = np.diag([0.01, 0.01, 0.001])
        else:
            if initial_pose_cov.shape != (3, 3):
                raise ValueError("initial_pose_cov must be shape (3, 3)")
            self.P = initial_pose_cov.astype(float).copy()

        # Process noise — scaled by dt inside predict()
        self._Q_rate = np.diag([
            process_noise_xy ** 2,
            process_noise_xy ** 2,
            process_noise_yaw ** 2,
        ])

        # Observation noise covariance (2×2, fixed per observation)
        self.R: np.ndarray = np.diag([obs_noise_xy ** 2, obs_noise_xy ** 2])

        self.mahal_thresh: float = float(mahal_thresh)
        self.n_landmarks: int = 0
        self.landmark_colors: List[int] = []   # per-landmark colour label

    # -----------------------------------------------------------------------
    # Read-only properties
    # -----------------------------------------------------------------------

    @property
    def state_dim(self) -> int:
        """Total state-vector dimension: 3 + 2·N_landmarks."""
        return 3 + 2 * self.n_landmarks

    @property
    def pose(self) -> np.ndarray:
        """Current vehicle pose [x, y, θ] as a copy."""
        return self.state[:3].copy()

    @property
    def x(self) -> float:
        return float(self.state[0])

    @property
    def y(self) -> float:
        return float(self.state[1])

    @property
    def theta(self) -> float:
        return float(self.state[2])

    def landmark_xy(self, i: int) -> np.ndarray:
        """Return world-frame (x, y) of landmark *i* as a copy."""
        idx = 3 + 2 * i
        return self.state[idx: idx + 2].copy()

    def pose_covariance_3x3(self) -> np.ndarray:
        """Return the 3×3 vehicle-pose covariance block as a copy."""
        return self.P[:3, :3].copy()

    # -----------------------------------------------------------------------
    # Prediction step
    # -----------------------------------------------------------------------

    def predict(self, v: float, omega: float, dt: float) -> None:
        """
        EKF prediction using the unicycle motion model.

        Parameters
        ----------
        v : float
            Forward velocity (m/s).  Positive = forward.
        omega : float
            Yaw rate (rad/s).  Positive = counter-clockwise (left turn).
        dt : float
            Time step (s).  Call is a no-op if dt ≤ 0.
        """
        if dt <= 0.0:
            return

        x, y, theta = self.state[0], self.state[1], self.state[2]
        c = math.cos(theta)
        s = math.sin(theta)

        # Predicted vehicle pose
        self.state[0] = x + v * c * dt
        self.state[1] = y + v * s * dt
        self.state[2] = wrap_angle(theta + omega * dt)

        # Jacobian of motion model w.r.t. vehicle state (3×3)
        Fx = np.array([
            [1.0, 0.0, -v * s * dt],
            [0.0, 1.0,  v * c * dt],
            [0.0, 0.0,  1.0],
        ])

        # Covariance prediction: P = F·P·Fᵀ + Q.
        # F is identity except the top-left pose block, so only the pose
        # rows/columns of P change — O(n) instead of building the full
        # n×n Jacobian (which is O(n³) and stalls the node once the
        # landmark count grows).
        self.P[:3, :3] = Fx @ self.P[:3, :3] @ Fx.T + self._Q_rate * dt
        if self.n_landmarks > 0:
            self.P[:3, 3:] = Fx @ self.P[:3, 3:]
            self.P[3:, :3] = self.P[:3, 3:].T

    # -----------------------------------------------------------------------
    # Internal: expected observation + Jacobian
    # -----------------------------------------------------------------------

    def _obs_blocks(
        self, landmark_idx: int
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Expected observation of landmark *i* in robot body frame plus the
        non-zero blocks of the Jacobian H = ∂h/∂x and the innovation
        covariance S.

        H is zero everywhere except the pose block A = ∂h/∂[x_r, y_r, θ]
        (2×3) and the landmark block B = ∂h/∂[lx_i, ly_i] (2×2), so S and
        the Kalman gain can be computed from covariance sub-blocks without
        ever building the full 2×n matrix (which made every cone update
        O(n³) and stalled the node as the landmark count grew).

        Observation model:
            obs_x =  cos(θ)·dx + sin(θ)·dy
            obs_y = −sin(θ)·dx + cos(θ)·dy
        where dx = lx_i − x_r, dy = ly_i − y_r.

        Returns
        -------
        (z_exp, A, B, S)
        """
        x_r, y_r, theta = self.state[0], self.state[1], self.state[2]
        li = 3 + 2 * landmark_idx
        lx, ly = self.state[li], self.state[li + 1]

        dx = lx - x_r
        dy = ly - y_r
        c = math.cos(theta)
        s = math.sin(theta)

        z_exp = np.array([c * dx + s * dy, -s * dx + c * dy])

        A = np.array([
            [-c, -s, -s * dx + c * dy],
            [ s, -c, -c * dx - s * dy],
        ])
        B = np.array([[c, s], [-s, c]])

        P_vv = self.P[:3, :3]
        P_vl = self.P[:3, li:li + 2]
        P_ll = self.P[li:li + 2, li:li + 2]

        S = (A @ P_vv @ A.T + A @ P_vl @ B.T
             + (A @ P_vl @ B.T).T + B @ P_ll @ B.T + self.R)

        return z_exp, A, B, S

    # -----------------------------------------------------------------------
    # Data association
    # -----------------------------------------------------------------------

    def associate(
        self,
        obs_robot: np.ndarray,
        color: Optional[int] = None,
    ) -> Tuple[Optional[int], float]:
        """
        Nearest-neighbour Mahalanobis data association.

        Parameters
        ----------
        obs_robot : ndarray, shape (2,)
            Observed cone position in robot body frame (x_fwd, y_left).
        color : int, optional
            Cone colour label.  When provided, landmarks of a different colour
            are skipped — blue cones never match yellow landmarks.

        Returns
        -------
        (landmark_idx, mahal_distance)
            *landmark_idx* is ``None`` if no landmark is within the threshold.
        """
        best_idx: Optional[int] = None
        best_dist: float = self.mahal_thresh

        for i in range(self.n_landmarks):
            if color is not None and self.landmark_colors[i] != color:
                continue

            z_exp, _, _, S = self._obs_blocks(i)
            innov = obs_robot - z_exp

            try:
                d = float(innov @ np.linalg.solve(S, innov))
            except np.linalg.LinAlgError:
                continue

            if d < best_dist:
                best_dist = d
                best_idx = i

        return best_idx, best_dist

    # -----------------------------------------------------------------------
    # EKF update step
    # -----------------------------------------------------------------------

    def update(self, obs_robot: np.ndarray, landmark_idx: int) -> None:
        """
        EKF measurement update.

        Parameters
        ----------
        obs_robot : ndarray, shape (2,)
            Observed cone position in robot body frame.
        landmark_idx : int
            Index of the associated landmark in the state vector.
        """
        z_exp, A, B, S = self._obs_blocks(landmark_idx)
        innov = obs_robot - z_exp

        # P·Hᵀ from the two non-zero blocks of H — O(n) instead of O(n²)
        li = 3 + 2 * landmark_idx
        PHt = self.P[:, :3] @ A.T + self.P[:, li:li + 2] @ B.T   # (n × 2)
        K = PHt @ np.linalg.inv(S)                               # (n × 2)

        self.state = self.state + K @ innov
        self.state[2] = wrap_angle(self.state[2])

        # Joseph form expanded:  (I−KH)P(I−KH)ᵀ + KRKᵀ
        #   = P − K·(HP) − (HP)ᵀ·Kᵀ + K·S·Kᵀ        (HP = PHtᵀ, P symmetric)
        # Every term is a rank-2 product → O(n²), no dense n×n matmuls.
        self.P = self.P - K @ PHt.T - PHt @ K.T + K @ S @ K.T
        # Enforce symmetry
        self.P = 0.5 * (self.P + self.P.T)

    # -----------------------------------------------------------------------
    # Add new landmark
    # -----------------------------------------------------------------------

    def add_landmark(self, obs_robot: np.ndarray, color: int = -1) -> int:
        """
        Initialise a new landmark from the current observation and vehicle pose.

        The inverse observation model transforms *obs_robot* (in body frame)
        to world frame, appends it to the state vector, and augments the
        covariance matrix consistently.

        Parameters
        ----------
        obs_robot : ndarray, shape (2,)
            Observed cone position in robot body frame.
        color : int
            Cone colour label (BLUE=0, YELLOW=1, ORANGE=2).

        Returns
        -------
        int
            Index of the newly created landmark.
        """
        x_r, y_r, theta = self.state[0], self.state[1], self.state[2]
        obs_x, obs_y = float(obs_robot[0]), float(obs_robot[1])
        c = math.cos(theta)
        s = math.sin(theta)

        # Inverse observation: robot frame → world frame
        lx = x_r + obs_x * c - obs_y * s
        ly = y_r + obs_x * s + obs_y * c

        n_old = self.state_dim          # dimension before adding landmark
        new_idx = self.n_landmarks

        # Augment state vector
        self.state = np.append(self.state, [lx, ly])
        self.n_landmarks += 1
        self.landmark_colors.append(color)

        n_new = self.state_dim          # = n_old + 2

        # --- Covariance augmentation (standard EKF-SLAM) ---
        #
        # Jacobian of inverse obs w.r.t. vehicle pose (2×3)
        Jv = np.array([
            [1.0, 0.0, -obs_x * s - obs_y * c],
            [0.0, 1.0,  obs_x * c - obs_y * s],
        ])

        # Jacobian of inverse obs w.r.t. observation (2×2)
        Jo = np.array([[c, -s], [s, c]])

        P_old = self.P.copy()
        P_vv = P_old[:3, :3]

        # New landmark covariance block
        P_ll = Jv @ P_vv @ Jv.T + Jo @ self.R @ Jo.T

        # Cross-covariance: entire old state ↔ new landmark (n_old × 2)
        P_xl = P_old[:n_old, :3] @ Jv.T

        # Assemble augmented covariance
        P_new = np.zeros((n_new, n_new))
        P_new[:n_old, :n_old] = P_old
        P_new[n_old:, n_old:] = P_ll
        P_new[:n_old, n_old:] = P_xl
        P_new[n_old:, :n_old] = P_xl.T

        self.P = P_new
        return new_idx
