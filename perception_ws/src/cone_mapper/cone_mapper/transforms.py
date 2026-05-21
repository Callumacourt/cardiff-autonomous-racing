"""Coordinate transformation utilities for cone mapping."""
import numpy as np
from scipy.spatial.transform import Rotation as R
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
#  Validation helpers                                                  #
# ------------------------------------------------------------------ #

def validate_point(x: float, y: float, z: float, max_bound: float = 50.0) -> bool:
    """
    Validate camera-frame point: finite, within bounds, positive depth.

    z is expected to be depth (forward distance from camera) so must be > 0.
    """
    if not (np.isfinite(x) and np.isfinite(y) and np.isfinite(z)):
        return False
    if abs(x) > max_bound or abs(y) > max_bound:
        return False
    if z < 0.01 or z > max_bound:
        return False
    return True


def validate_quaternion(quat: np.ndarray) -> bool:
    if quat is None or len(quat) != 4:
        return False
    if np.any(np.isnan(quat)) or np.any(np.isinf(quat)):
        return False
    if np.allclose(quat, 0):
        return False
    return True


def normalize_quaternion(quat: np.ndarray) -> np.ndarray:
    if not validate_quaternion(quat):
        raise ValueError('Invalid quaternion')
    norm = np.linalg.norm(quat)
    if norm < 1e-10:
        raise ValueError('Quaternion norm too small')
    return quat / norm


# ------------------------------------------------------------------ #
#  Camera → base_link                                                  #
# ------------------------------------------------------------------ #

def camera_to_base_link(
    x_cam: float,
    y_cam: float,
    z_cam: float,
    cam_height: float = 0.0,
    cam_forward: float = 0.0,
    cam_lateral: float = 0.0,
) -> Tuple[float, float, float]:
    """
    Transform a point from the camera optical frame to base_link.

    Camera optical convention (ZED, RealSense):
        X → right,  Y → down,  Z → forward (depth)

    ROS body convention (REP-103):
        X → forward, Y → left, Z → up

    cam_height / cam_forward / cam_lateral are the camera origin expressed
    in base_link (metres). For a typical FSAI ZED mount:
        cam_height  ≈ 0.5 m  (camera above base_link ground plane)
        cam_forward ≈ 0.3 m  (camera ahead of base_link origin)
        cam_lateral ≈ 0.0 m  (centred)
    """
    # Rotate: optical → body
    x_base = z_cam + cam_forward    # depth    → forward  + mounting offset
    y_base = -x_cam + cam_lateral   # right    → left     + mounting offset
    z_base = -y_cam + cam_height    # down     → up       + mounting offset
    return x_base, y_base, z_base


# Kept for backward compatibility; prefer camera_to_base_link.
def camera_to_robot_frame(x_cam: float, y_cam: float, z_cam: float) -> np.ndarray:
    """
    Rotate point from camera optical frame to robot body frame (no translation).
    Does NOT account for camera mounting offset; use camera_to_base_link instead.
    """
    return np.array([[z_cam], [-x_cam], [-y_cam]])


# ------------------------------------------------------------------ #
#  base_link → world                                                   #
# ------------------------------------------------------------------ #

def robot_to_world_frame(
    point_robot: np.ndarray,
    vehicle_position: np.ndarray,
    vehicle_quaternion: np.ndarray,
) -> Tuple[float, float, float]:
    """
    Transform a 3×1 point from robot/base_link frame to world/map frame.

    Args:
        point_robot:       3×1 numpy array in base_link frame
        vehicle_position:  (3,) world position of base_link
        vehicle_quaternion: (4,) quaternion [x, y, z, w]
    """
    if point_robot.shape != (3, 1):
        raise ValueError(f'point_robot must be 3×1, got {point_robot.shape}')
    if vehicle_position.shape != (3,):
        raise ValueError(f'vehicle_position must be (3,), got {vehicle_position.shape}')

    quat = normalize_quaternion(vehicle_quaternion)
    rot = R.from_quat(quat)
    R_mat = rot.as_matrix()

    t = vehicle_position.reshape(3, 1)
    X_world = R_mat @ point_robot + t
    return float(X_world[0, 0]), float(X_world[1, 0]), float(X_world[2, 0])


# ------------------------------------------------------------------ #
#  world → base_link (inverse)                                         #
# ------------------------------------------------------------------ #

def world_to_car_frame(
    x_world: float,
    y_world: float,
    z_world: float,
    vehicle_position: np.ndarray,
    vehicle_quaternion: np.ndarray,
) -> Tuple[float, float, float]:
    """
    Transform a point from world/map frame to car (base_link) frame.

    This is the inverse of robot_to_world_frame:
        p_car = R^T * (p_world − t_vehicle)

    Used to publish the accumulated world-frame cone map relative to the
    current car position, so path planning always receives car-centric cones.
    """
    quat = normalize_quaternion(vehicle_quaternion)
    rot = R.from_quat(quat)
    R_mat = rot.as_matrix()

    p_rel = np.array([
        x_world - vehicle_position[0],
        y_world - vehicle_position[1],
        z_world - vehicle_position[2],
    ])
    p_car = R_mat.T @ p_rel
    return float(p_car[0]), float(p_car[1]), float(p_car[2])


# ------------------------------------------------------------------ #
#  Convenience: camera → world in one call                             #
# ------------------------------------------------------------------ #

def camera_to_world_frame(
    x_cam: float,
    y_cam: float,
    z_cam: float,
    vehicle_position: np.ndarray,
    vehicle_quaternion: np.ndarray,
    cam_height: float = 0.0,
    cam_forward: float = 0.0,
    cam_lateral: float = 0.0,
) -> Tuple[float, float, float]:
    x_base, y_base, z_base = camera_to_base_link(
        x_cam, y_cam, z_cam, cam_height, cam_forward, cam_lateral)
    return robot_to_world_frame(
        np.array([[x_base], [y_base], [z_base]]),
        vehicle_position,
        vehicle_quaternion,
    )


# ------------------------------------------------------------------ #
#  Pose extraction                                                     #
# ------------------------------------------------------------------ #

def validate_pose(position: np.ndarray, quaternion: np.ndarray) -> bool:
    if position is None or len(position) != 3:
        return False
    if np.any(np.isnan(position)) or np.any(np.isinf(position)):
        return False
    return validate_quaternion(quaternion)


def extract_pose_from_odometry(odom_msg) -> Optional[dict]:
    """
    Extract and validate pose from nav_msgs/Odometry.

    Returns dict with keys 'position' (np.array), 'orientation' (np.array),
    'timestamp' (float), or None if the message is invalid.
    """
    try:
        pos = odom_msg.pose.pose.position
        ori = odom_msg.pose.pose.orientation

        position = np.array([pos.x, pos.y, pos.z])
        quaternion = np.array([ori.x, ori.y, ori.z, ori.w])

        if not validate_pose(position, quaternion):
            return None

        quaternion = normalize_quaternion(quaternion)
        timestamp = odom_msg.header.stamp.sec + odom_msg.header.stamp.nanosec * 1e-9

        return {'position': position, 'orientation': quaternion, 'timestamp': timestamp}

    except Exception as e:
        logger.error(f'Failed to extract pose from odometry: {e}')
        return None
