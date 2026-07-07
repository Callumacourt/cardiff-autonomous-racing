"""
Unit tests for landmark_slam.camera_transform — no ROS required.

Run with:
    pytest perception_ws/src/landmark_slam/test/test_camera_transform.py -v
"""

import math

import pytest

from landmark_slam.camera_transform import (
    CameraMount,
    camera_to_robot_2d,
    robot_to_world_2d,
)


# ---------------------------------------------------------------------------
# camera_to_robot_2d
# ---------------------------------------------------------------------------

class TestCameraToRobot:
    """
    Verify the camera → robot transform matches cone_mapper/transforms.py:
        robot_x =  z_cam   (depth → forward)
        robot_y = -x_cam   (right → left)
    """

    def test_cone_ahead_centred(self):
        """Z=5, X=0 → robot (5, 0)."""
        mount = CameraMount()
        rx, ry = camera_to_robot_2d(0.0, 0.0, 5.0, mount)
        assert rx == pytest.approx(5.0)
        assert ry == pytest.approx(0.0)

    def test_cone_right_of_centre(self):
        """X=1 in camera (right) → ry = -1 (robot Y is left)."""
        mount = CameraMount()
        rx, ry = camera_to_robot_2d(1.0, 0.0, 5.0, mount)
        assert rx == pytest.approx(5.0)
        assert ry == pytest.approx(-1.0)

    def test_cone_left_of_centre(self):
        """X=-1 in camera (left) → ry = +1 (robot Y is left)."""
        mount = CameraMount()
        rx, ry = camera_to_robot_2d(-1.0, 0.0, 5.0, mount)
        assert rx == pytest.approx(5.0)
        assert ry == pytest.approx(1.0)

    def test_y_cam_ignored(self):
        """Y_cam (up/down) is height — not used in 2-D, should not affect x/y."""
        mount = CameraMount()
        rx1, ry1 = camera_to_robot_2d(0.0, 0.0, 5.0, mount)
        rx2, ry2 = camera_to_robot_2d(0.0, 2.0, 5.0, mount)
        # robot_x and robot_y must be the same regardless of y_cam
        assert rx1 == pytest.approx(rx2)
        assert ry1 == pytest.approx(ry2)

    def test_forward_offset_applied(self):
        """camera_x_offset=0.35 adds 0.35 m to robot_x."""
        mount = CameraMount(x_offset=0.35)
        rx, ry = camera_to_robot_2d(0.0, 0.0, 5.0, mount)
        assert rx == pytest.approx(5.35)
        assert ry == pytest.approx(0.0)

    def test_lateral_offset_applied(self):
        """camera_y_offset=0.1 adds 0.1 m to robot_y."""
        mount = CameraMount(y_offset=0.1)
        rx, ry = camera_to_robot_2d(0.0, 0.0, 5.0, mount)
        assert rx == pytest.approx(5.0)
        assert ry == pytest.approx(0.1)

    def test_no_offset_matches_cone_mapper(self):
        """
        With zero offset, the output must match cone_mapper/transforms.py
        camera_to_robot_frame() first two elements exactly.
        """
        mount = CameraMount()
        x_cam, y_cam, z_cam = 1.0, 0.5, 5.0
        rx, ry = camera_to_robot_2d(x_cam, y_cam, z_cam, mount)
        # From cone_mapper: robot_x = z_cam, robot_y = -x_cam
        assert rx == pytest.approx(z_cam)
        assert ry == pytest.approx(-x_cam)

    def test_depth_zero(self):
        """Zero depth → robot_x = offset only (no distance)."""
        mount = CameraMount(x_offset=0.0)
        rx, ry = camera_to_robot_2d(0.0, 0.0, 0.0, mount)
        assert rx == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# robot_to_world_2d
# ---------------------------------------------------------------------------

class TestRobotToWorld:
    def test_identity_pose(self):
        """At world origin heading 0, robot frame = world frame."""
        wx, wy = robot_to_world_2d(3.0, 1.0, 0.0, 0.0, 0.0)
        assert wx == pytest.approx(3.0)
        assert wy == pytest.approx(1.0)

    def test_translation_only(self):
        """Vehicle at (10, 5), heading 0.  Point (2, 1) in robot → (12, 6) world."""
        wx, wy = robot_to_world_2d(2.0, 1.0, 10.0, 5.0, 0.0)
        assert wx == pytest.approx(12.0)
        assert wy == pytest.approx(6.0)

    def test_heading_90_forward_is_world_y(self):
        """Heading 90°, 5 m robot-forward → world (0, 5)."""
        wx, wy = robot_to_world_2d(5.0, 0.0, 0.0, 0.0, math.pi / 2)
        assert wx == pytest.approx(0.0, abs=1e-9)
        assert wy == pytest.approx(5.0, abs=1e-9)

    def test_heading_180_forward_is_negative_world_x(self):
        """Heading 180°, 3 m robot-forward → world (−3, 0)."""
        wx, wy = robot_to_world_2d(3.0, 0.0, 0.0, 0.0, math.pi)
        assert wx == pytest.approx(-3.0, abs=1e-9)
        assert wy == pytest.approx(0.0, abs=1e-9)

    def test_heading_minus_90_forward_is_negative_world_y(self):
        """Heading −90°, 4 m robot-forward → world (0, −4)."""
        wx, wy = robot_to_world_2d(4.0, 0.0, 0.0, 0.0, -math.pi / 2)
        assert wx == pytest.approx(0.0, abs=1e-9)
        assert wy == pytest.approx(-4.0, abs=1e-9)

    def test_combined_translation_and_rotation(self):
        """Vehicle at (1, 0), heading 90°.  Robot (1, 0) → world (1, 1)."""
        wx, wy = robot_to_world_2d(1.0, 0.0, 1.0, 0.0, math.pi / 2)
        assert wx == pytest.approx(1.0, abs=1e-9)
        assert wy == pytest.approx(1.0, abs=1e-9)


# ---------------------------------------------------------------------------
# Round-trip test: camera → robot → world
# ---------------------------------------------------------------------------

class TestRoundTrip:
    def test_same_cone_from_two_poses_gives_same_world_position(self):
        """
        The same physical cone observed from two different vehicle poses
        must map to the same world-frame position.
        """
        mount = CameraMount()
        true_cone_world = (6.0, 2.0)

        # --- Pose 1: at origin, heading 0 ---
        vx1, vy1, vth1 = 0.0, 0.0, 0.0
        # Expected robot-frame observation
        dx1 = true_cone_world[0] - vx1
        dy1 = true_cone_world[1] - vy1
        c1, s1 = math.cos(vth1), math.sin(vth1)
        rx1 =  c1 * dx1 + s1 * dy1
        ry1 = -s1 * dx1 + c1 * dy1
        wx1, wy1 = robot_to_world_2d(rx1, ry1, vx1, vy1, vth1)

        # --- Pose 2: at (3, 0), heading 0 ---
        vx2, vy2, vth2 = 3.0, 0.0, 0.0
        dx2 = true_cone_world[0] - vx2
        dy2 = true_cone_world[1] - vy2
        c2, s2 = math.cos(vth2), math.sin(vth2)
        rx2 =  c2 * dx2 + s2 * dy2
        ry2 = -s2 * dx2 + c2 * dy2
        wx2, wy2 = robot_to_world_2d(rx2, ry2, vx2, vy2, vth2)

        assert wx1 == pytest.approx(wx2, abs=1e-9)
        assert wy1 == pytest.approx(wy2, abs=1e-9)
        assert wx1 == pytest.approx(true_cone_world[0])
        assert wy1 == pytest.approx(true_cone_world[1])
