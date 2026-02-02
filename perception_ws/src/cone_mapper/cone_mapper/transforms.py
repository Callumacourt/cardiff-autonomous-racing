"""Coordinate transformation utilities for cone mapping."""
import numpy as np
from scipy.spatial.transform import Rotation as R
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def validate_point(x: float, y: float, z: float, max_bound: float = 50.0) -> bool:
    """
    Validate point coordinates are finite and within bounds.
    
    Args:
        x, y, z: Point coordinates
        max_bound: Maximum absolute coordinate value
        
    Returns:
        True if point is valid, False otherwise
        
    Example:
        >>> validate_point(5.0, 3.0, 2.0)
        True
        >>> validate_point(np.nan, 3.0, 2.0)
        False
        >>> validate_point(100.0, 3.0, 2.0, max_bound=50.0)
        False
    """
    # Check for NaN or infinity
    if not (np.isfinite(x) and np.isfinite(y) and np.isfinite(z)):
        return False
    
    # Check bounds
    if abs(x) > max_bound or abs(y) > max_bound:
        return False
    
    # Check depth is reasonable (positive and within range)
    if z < 0.01 or z > max_bound:
        return False
    
    return True


def validate_quaternion(quat: np.ndarray) -> bool:
    """
    Validate quaternion is finite and non-zero.
    
    Args:
        quat: Quaternion as numpy array [x, y, z, w]
        
    Returns:
        True if valid, False otherwise
    """
    if quat is None or len(quat) != 4:
        return False
    
    # Check for NaN/inf
    if np.any(np.isnan(quat)) or np.any(np.isinf(quat)):
        return False
    
    # Check not all zeros
    if np.allclose(quat, 0):
        return False
    
    return True


def normalize_quaternion(quat: np.ndarray) -> np.ndarray:
    """
    Normalize quaternion to unit length.
    
    Args:
        quat: Quaternion [x, y, z, w]
        
    Returns:
        Normalized quaternion
        
    Raises:
        ValueError: If quaternion is invalid
    """
    if not validate_quaternion(quat):
        raise ValueError("Invalid quaternion provided")
    
    norm = np.linalg.norm(quat)
    if norm < 1e-10:
        raise ValueError("Quaternion norm too small")
    
    return quat / norm


def camera_to_robot_frame(x_cam: float, y_cam: float, z_cam: float) -> np.ndarray:
    """
    Transform point from camera frame to robot/base_link frame.
    
    Camera frame conventions (typical for ZED, RealSense):
        X: Right
        Y: Down  
        Z: Forward (depth)
    
    Robot frame conventions (ROS REP-103):
        X: Forward
        Y: Left
        Z: Up
    
    Args:
        x_cam: Camera X coordinate (right)
        y_cam: Camera Y coordinate (down)
        z_cam: Camera Z coordinate (forward/depth)
        
    Returns:
        3x1 numpy array [x_robot, y_robot, z_robot]
        
    Example:
        >>> point_cam = camera_to_robot_frame(1.0, 0.5, 5.0)
        >>> print(point_cam)
        [[5.0], [-1.0], [-0.5]]
    """
    x_robot = z_cam     # Camera forward (Z) -> Robot forward (X)
    y_robot = -x_cam    # Camera right (X) -> Robot left (-Y)
    z_robot = -y_cam    # Camera down (Y) -> Robot up (-Z)
    
    return np.array([[x_robot], [y_robot], [z_robot]])


def robot_to_world_frame(
    point_robot: np.ndarray,
    vehicle_position: np.ndarray,
    vehicle_quaternion: np.ndarray
) -> Tuple[float, float, float]:
    """
    Transform point from robot frame to world/map frame using vehicle pose.
    
    Args:
        point_robot: 3x1 point in robot frame [x, y, z]
        vehicle_position: 3D position of vehicle in world [x, y, z]
        vehicle_quaternion: Quaternion [x, y, z, w] for vehicle orientation
        
    Returns:
        Tuple of (x_world, y_world, z_world)
        
    Raises:
        ValueError: If inputs are invalid
        
    Example:
        >>> point = np.array([[5.0], [0.0], [0.0]])  # 5m forward
        >>> pos = np.array([10.0, 20.0, 0.0])
        >>> quat = np.array([0.0, 0.0, 0.0, 1.0])  # No rotation
        >>> x, y, z = robot_to_world_frame(point, pos, quat)
        >>> print(x, y, z)
        15.0 20.0 0.0
    """
    # Validate inputs
    if point_robot.shape != (3, 1):
        raise ValueError(f"point_robot must be 3x1, got {point_robot.shape}")
    
    if vehicle_position.shape != (3,):
        raise ValueError(f"vehicle_position must be (3,), got {vehicle_position.shape}")
    
    # Normalize quaternion
    quat_normalized = normalize_quaternion(vehicle_quaternion)
    
    # Build rotation matrix from quaternion
    rot = R.from_quat(quat_normalized)
    R_world_vehicle = rot.as_matrix()
    
    # Transform: X_world = R_world_vehicle * X_robot + t_world_vehicle
    t_world_vehicle = vehicle_position.reshape(3, 1)
    X_world = R_world_vehicle @ point_robot + t_world_vehicle
    
    return float(X_world[0, 0]), float(X_world[1, 0]), float(X_world[2, 0])


def camera_to_world_frame(
    x_cam: float,
    y_cam: float,
    z_cam: float,
    vehicle_position: np.ndarray,
    vehicle_quaternion: np.ndarray
) -> Tuple[float, float, float]:
    """
    Transform point directly from camera frame to world frame.
    
    Convenience function combining camera_to_robot_frame and robot_to_world_frame.
    
    Args:
        x_cam, y_cam, z_cam: Point in camera frame
        vehicle_position: Vehicle position in world frame
        vehicle_quaternion: Vehicle orientation quaternion
        
    Returns:
        Tuple of (x_world, y_world, z_world)
        
    Example:
        >>> x, y, z = camera_to_world_frame(
        ...     1.0, 0.5, 5.0,
        ...     np.array([10.0, 20.0, 0.0]),
        ...     np.array([0.0, 0.0, 0.0, 1.0])
        ... )
    """
    # First transform to robot frame
    point_robot = camera_to_robot_frame(x_cam, y_cam, z_cam)
    
    # Then transform to world frame
    return robot_to_world_frame(point_robot, vehicle_position, vehicle_quaternion)


def validate_pose(position: np.ndarray, quaternion: np.ndarray) -> bool:
    """
    Validate a complete pose (position + orientation).
    
    Args:
        position: 3D position vector
        quaternion: Quaternion [x, y, z, w]
        
    Returns:
        True if pose is valid
    """
    # Validate position
    if position is None or len(position) != 3:
        return False
    
    if np.any(np.isnan(position)) or np.any(np.isinf(position)):
        return False
    
    # Validate quaternion
    return validate_quaternion(quaternion)


def extract_pose_from_odometry(odom_msg) -> Optional[dict]:
    """
    Extract and validate pose from ROS Odometry message.
    
    Args:
        odom_msg: nav_msgs/Odometry message
        
    Returns:
        Dictionary with 'position' (np.array) and 'orientation' (np.array),
        or None if invalid
        
    Example:
        >>> pose = extract_pose_from_odometry(odom_msg)
        >>> if pose:
        ...     print(pose['position'])
        ...     print(pose['orientation'])
    """
    try:
        pos = odom_msg.pose.pose.position
        ori = odom_msg.pose.pose.orientation
        
        position = np.array([pos.x, pos.y, pos.z])
        quaternion = np.array([ori.x, ori.y, ori.z, ori.w])
        
        # Validate
        if not validate_pose(position, quaternion):
            return None
        
        # Normalize quaternion
        quaternion = normalize_quaternion(quaternion)
        
        # Extract timestamp
        timestamp = odom_msg.header.stamp.sec + odom_msg.header.stamp.nanosec * 1e-9
        
        return {
            'position': position,
            'orientation': quaternion,
            'timestamp': timestamp
        }
        
    except Exception as e:
        logger.error(f"Failed to extract pose from odometry: {e}")
        return None