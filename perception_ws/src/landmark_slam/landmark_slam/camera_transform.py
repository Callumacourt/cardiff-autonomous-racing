"""
Camera-to-robot-frame coordinate transform.

Conventions match cone_mapper/transforms.py exactly so that both the
landmark SLAM node and the cone mapper interpret the same PointCloud2
observations identically.

Camera optical frame (ZED / RealSense standard):
    X : right
    Y : down
    Z : forward (depth)

Robot body frame (ROS REP-103):
    X : forward
    Y : left
    Z : up

Mapping (rotation only, no translation applied here):
    robot_x =  z_cam   (depth → forward)
    robot_y = -x_cam   (right → -left)
    robot_z = -y_cam   (down  → -up)     ← ignored for 2-D SLAM

Camera mounting offset
----------------------
On the real car the ZED is mounted some distance in front of the car's
reference point (usually the GPS antenna or rear-axle centre).  Use the
*CameraMount* dataclass to capture this offset; the landmark SLAM node
exposes it as ROS parameters so it can be tuned without a rebuild.

NOTE: cone_mapper currently applies NO mounting offset — it treats the
camera origin as coincident with the vehicle reference.  Until the real-car
offset is measured, keep *x_offset* and *y_offset* at 0.0 so that the
SLAM world-frame and the mapper world-frame are identical.
"""

import math
from dataclasses import dataclass, field
from typing import Tuple


@dataclass
class CameraMount:
    """
    Rigid offset from camera optical origin to vehicle reference point.

    Attributes
    ----------
    x_offset : float
        Forward offset (m).  Positive means camera is in front of reference.
    y_offset : float
        Lateral offset (m).  Positive means camera is to the left.
    """
    x_offset: float = 0.0   # set to ~0.35 once measured on real car
    y_offset: float = 0.0


def camera_to_robot_2d(
    x_cam: float,
    y_cam: float,
    z_cam: float,
    mount: CameraMount,
) -> Tuple[float, float]:
    """
    Transform a point from camera optical frame to robot body frame (2-D).

    The height (robot Z) is discarded because the EKF operates in the
    2-D ground plane.

    Parameters
    ----------
    x_cam, y_cam, z_cam : float
        Point in camera frame  (X=right, Y=down, Z=forward/depth).
    mount : CameraMount
        Camera mounting offset relative to vehicle reference.

    Returns
    -------
    (robot_x, robot_y) : float, float
        Point in robot body frame  (X=forward, Y=left).

    Examples
    --------
    >>> mount = CameraMount()
    >>> camera_to_robot_2d(0.0, 0.0, 5.0, mount)
    (5.0, 0.0)          # cone 5 m ahead, dead-centre

    >>> camera_to_robot_2d(1.0, 0.0, 5.0, mount)
    (5.0, -1.0)         # cone 1 m to the right in camera → -1 m Y in robot
    """
    # Matches cone_mapper/transforms.py camera_to_robot_frame exactly.
    robot_x = z_cam + mount.x_offset   # depth   → forward
    robot_y = -x_cam + mount.y_offset  # -right  → left

    return robot_x, robot_y


def robot_to_world_2d(
    robot_x: float,
    robot_y: float,
    vehicle_x: float,
    vehicle_y: float,
    vehicle_theta: float,
) -> Tuple[float, float]:
    """
    Rotate and translate a point from robot body frame to world/map frame.

    Parameters
    ----------
    robot_x, robot_y : float
        Point in robot body frame.
    vehicle_x, vehicle_y, vehicle_theta : float
        Current vehicle pose in world frame.

    Returns
    -------
    (world_x, world_y) : float, float

    Examples
    --------
    >>> robot_to_world_2d(5.0, 0.0, 0.0, 0.0, 0.0)
    (5.0, 0.0)

    >>> import math; robot_to_world_2d(5.0, 0.0, 0.0, 0.0, math.pi / 2)
    (0.0, 5.0)      # heading 90°, forward becomes world-Y
    """
    c = math.cos(vehicle_theta)
    s = math.sin(vehicle_theta)
    world_x = vehicle_x + robot_x * c - robot_y * s
    world_y = vehicle_y + robot_x * s + robot_y * c
    return world_x, world_y
