"""Coordinate transformation utilities for cone mapping."""
import logging
from typing import Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


def validate_point(x: float, y: float, z: float, max_bound: float = 50.0) -> bool:
    """
    Validate point coordinates are finite and within bounds.

    z is the camera depth, so it must additionally be positive.
    """
    if not (np.isfinite(x) and np.isfinite(y) and np.isfinite(z)):
        return False
    if abs(x) > max_bound or abs(y) > max_bound:
        return False
    if z < 0.01 or z > max_bound:
        return False
    return True


def camera_to_robot_frame(x_cam: float, y_cam: float, z_cam: float) -> np.ndarray:
    """
    Transform point from camera optical frame to robot/base_link frame.

    Camera frame (ZED / RealSense standard):  X right, Y down, Z forward.
    Robot frame (ROS REP-103):                X forward, Y left, Z up.

    Must match landmark_slam/camera_transform.py so both nodes interpret
    the same PointCloud2 observations identically.

    Returns
    -------
    ndarray, shape (3, 1)
    """
    return np.array([[z_cam], [-x_cam], [-y_cam]])


def _quat_to_rotation_matrix(q: np.ndarray) -> np.ndarray:
    """Rotation matrix from a unit quaternion [x, y, z, w]."""
    x, y, z, w = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w),     2 * (x * z + y * w)],
        [2 * (x * y + z * w),     1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w),     2 * (y * z + x * w),     1 - 2 * (x * x + y * y)],
    ])


def robot_to_world_frame(
    point_robot: np.ndarray,
    vehicle_position: np.ndarray,
    vehicle_quaternion: np.ndarray,
) -> Tuple[float, float, float]:
    """
    Transform a point from robot frame to world/map frame using the
    vehicle pose:  X_world = R·X_robot + t.

    Parameters
    ----------
    point_robot : ndarray, shape (3, 1)
    vehicle_position : ndarray, shape (3,)
    vehicle_quaternion : ndarray, shape (4,)  — unit [x, y, z, w]
    """
    R = _quat_to_rotation_matrix(vehicle_quaternion)
    X_world = R @ point_robot + vehicle_position.reshape(3, 1)
    return float(X_world[0, 0]), float(X_world[1, 0]), float(X_world[2, 0])


def extract_pose_from_odometry(odom_msg) -> Optional[dict]:
    """
    Extract and validate pose from a nav_msgs/Odometry message.

    Returns
    -------
    dict with 'position' (ndarray (3,)), 'orientation' (unit quaternion
    ndarray (4,)) and 'timestamp' (float seconds), or None if the message
    contains NaNs / a zero quaternion.
    """
    pos = odom_msg.pose.pose.position
    ori = odom_msg.pose.pose.orientation

    position = np.array([pos.x, pos.y, pos.z])
    quaternion = np.array([ori.x, ori.y, ori.z, ori.w])

    if not (np.all(np.isfinite(position)) and np.all(np.isfinite(quaternion))):
        return None
    norm = np.linalg.norm(quaternion)
    if norm < 1e-6:
        return None

    return {
        'position': position,
        'orientation': quaternion / norm,
        'timestamp': odom_msg.header.stamp.sec + odom_msg.header.stamp.nanosec * 1e-9,
    }
