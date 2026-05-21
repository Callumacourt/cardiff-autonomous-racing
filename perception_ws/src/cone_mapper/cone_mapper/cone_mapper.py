"""
Cone mapper ROS2 node.

Coordinate frame design
-----------------------
Inputs
  /cone_cloud/local   PointCloud2 in camera optical frame (from YOLO)
  /odometry/slam      nav_msgs/Odometry  (or any topic set via odom_topic param)

Primary outputs  (always available, even without SLAM)
  /cone_map/car_frame PointCloud2 in base_link  — cone observations for
                      the path planner and future landmark SLAM
  /cone_map/local     String CSV  x,y,z,color,conf  in base_link  (path planner)
  /cone_map/orange    PointCloud2 in base_link  — start/finish line cones only

Secondary outputs  (require odometry)
  /cone_map/global    String CSV  x,y,z,color  in odom/map frame
  /cone_map/markers   MarkerArray in odom/map frame  (RViz)
  /track/centerline   nav_msgs/Path  in odom/map frame  (RViz)

Republished for downstream
  /car_pose           geometry_msgs/PoseStamped  (path planner)
  /mapping/diagnostics DiagnosticArray
"""

import time
from typing import Optional

import numpy as np
import rclpy
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry, Path
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2, PointField
from sensor_msgs_py import point_cloud2
from std_msgs.msg import Header, String
from visualization_msgs.msg import MarkerArray

from .constants import ConeColor
from .map_data import LocalConeBuffer, PersistentGlobalMap
from .transforms import (
    camera_to_base_link,
    extract_pose_from_odometry,
    robot_to_world_frame,
    validate_point,
    world_to_car_frame,
)
from .visualisation import ConeVisualizer


class ConeMapperNode(Node):

    def __init__(self):
        super().__init__('cone_mapper')

        # --- Parameters ---
        odom_topic = self.declare_parameter('odom_topic', '/odometry/slam').get_parameter_value().string_value
        # Camera mounting in base_link (metres)
        self.cam_height  = self.declare_parameter('cam_height',  0.5).get_parameter_value().double_value
        self.cam_forward = self.declare_parameter('cam_forward', 0.3).get_parameter_value().double_value
        self.cam_lateral = self.declare_parameter('cam_lateral', 0.0).get_parameter_value().double_value

        # --- Mapping state ---
        self.global_map = PersistentGlobalMap(confidence_threshold=0.7, min_detections=3)
        self.local_buffer = LocalConeBuffer(max_size=200, max_age=6.0)
        self.visualizer = ConeVisualizer(frame_id='odom')

        self.latest_pose: Optional[dict] = None
        self.vehicle_position = (0.0, 0.0)

        # --- ROS interfaces ---
        self._setup_subscribers(odom_topic)
        self._setup_publishers()
        self._setup_timers()

        # --- Stats ---
        self.stats = {
            'total_detections': 0,
            'global_additions': 0,
            'processing_times': [],
            'coordinate_warnings': 0,
        }

        self.get_logger().info(
            f'Cone Mapper started | odom={odom_topic} | '
            f'cam offset: fwd={self.cam_forward} lat={self.cam_lateral} h={self.cam_height}'
        )

    # ------------------------------------------------------------------ #
    #  Setup                                                               #
    # ------------------------------------------------------------------ #

    def _setup_subscribers(self, odom_topic: str):
        self.pose_sub = self.create_subscription(
            Odometry, odom_topic, self._pose_callback, 10)
        self.cone_pc_sub = self.create_subscription(
            PointCloud2, '/cone_cloud/local', self._cone_callback, 10)

    def _setup_publishers(self):
        # Primary (car frame — always available)
        self.car_frame_pc_pub  = self.create_publisher(PointCloud2, '/cone_map/car_frame', 10)
        self.orange_pub        = self.create_publisher(PointCloud2, '/cone_map/orange',    10)
        self.local_map_pub     = self.create_publisher(String,      '/cone_map/local',     10)
        # Secondary (world frame — require odometry)
        self.global_map_pub    = self.create_publisher(String,      '/cone_map/global',    10)
        self.centerline_pub    = self.create_publisher(Path,        '/track/centerline',   10)
        self.markers_pub       = self.create_publisher(MarkerArray, '/cone_map/markers',   10)
        # Relay for path planner
        self.car_pose_pub      = self.create_publisher(PoseStamped, '/car_pose',           10)
        self.diagnostics_pub   = self.create_publisher(DiagnosticArray, '/mapping/diagnostics', 10)

    def _setup_timers(self):
        self.create_timer(0.05,  self._publish_local_map)       # 20 Hz  — car frame CSV
        self.create_timer(0.1,   self._publish_visualisation)   # 10 Hz  — markers
        self.create_timer(0.2,   self._update_buffer)           #  5 Hz  — confidence decay
        self.create_timer(0.5,   self._publish_global_map)      #  2 Hz  — world frame CSV
        self.create_timer(0.5,   self._publish_centerline)      #  2 Hz  — centerline Path
        self.create_timer(1.0,   self._publish_diagnostics)     #  1 Hz  — health

    # ------------------------------------------------------------------ #
    #  Callbacks                                                           #
    # ------------------------------------------------------------------ #

    def _pose_callback(self, msg: Odometry):
        pose = extract_pose_from_odometry(msg)
        if pose is None:
            self.get_logger().warning('Received invalid pose from odometry', throttle_duration_sec=5.0)
            return
        self.latest_pose = pose
        self.vehicle_position = (pose['position'][0], pose['position'][1])

        # Republish as PoseStamped so path planner can consume /car_pose
        ps = PoseStamped()
        ps.header = msg.header
        ps.pose = msg.pose.pose
        self.car_pose_pub.publish(ps)

    def _cone_callback(self, msg: PointCloud2):
        t0 = time.time()

        available_fields = {f.name for f in msg.fields}
        label_field = 'label' if 'label' in available_fields else 'confidence'

        try:
            points_iter = point_cloud2.read_points(
                msg, field_names=('x', 'y', 'z', label_field), skip_nans=True)
        except Exception as e:
            self.get_logger().error(f'Failed to read PointCloud2: {e}')
            return

        # ---- 1. Parse raw camera-frame points ----
        car_frame_points   = []  # (x, y, z, label) in base_link
        world_frame_points = []  # (x, y, z, label) in odom/map — only when pose known

        has_pose = self.latest_pose is not None

        for p in points_iter:
            try:
                x_cam, y_cam, z_cam, label_f = p
            except Exception:
                continue

            if not validate_point(x_cam, y_cam, z_cam):
                self.stats['coordinate_warnings'] += 1
                continue

            label = int(label_f)

            # Camera optical → base_link  (always possible)
            x_base, y_base, z_base = camera_to_base_link(
                float(x_cam), float(y_cam), float(z_cam),
                self.cam_height, self.cam_forward, self.cam_lateral,
            )
            car_frame_points.append((x_base, y_base, z_base, label))

            # base_link → world  (only when odometry available; skip orange)
            if has_pose and label != ConeColor.ORANGE:
                try:
                    pt = np.array([[x_base], [y_base], [z_base]])
                    x_w, y_w, z_w = robot_to_world_frame(
                        pt,
                        self.latest_pose['position'],
                        self.latest_pose['orientation'],
                    )
                    world_frame_points.append((x_w, y_w, z_w, label))
                except Exception:
                    pass

        if not car_frame_points:
            return

        # ---- 2. Publish car-frame observations immediately ----
        self._publish_car_frame_pc(car_frame_points, msg.header.stamp)

        # ---- 3. Separate orange cones (start/finish line) ----
        orange = [(x, y, z, l) for x, y, z, l in car_frame_points if l == ConeColor.ORANGE]
        if orange:
            self._publish_pc(orange, msg.header.stamp, 'base_link', self.orange_pub)

        # ---- 4. No-SLAM fallback: publish single-frame car-frame cones to /cone_map/local ----
        # When no odometry is available (landmark SLAM not yet running, or sim testing)
        # the path planner still gets cone positions relative to the car — just from the
        # current frame rather than an accumulated map.
        if not has_pose:
            boundary = [(x, y, z, l) for x, y, z, l in car_frame_points
                        if l != ConeColor.ORANGE]
            if boundary:
                lines = [f'{x:.2f},{y:.2f},{z:.2f},{l},1.00'
                         for x, y, z, l in boundary]
                fallback = String()
                fallback.data = '\n'.join(lines)
                self.local_map_pub.publish(fallback)
            return  # Skip world-frame accumulation without pose

        # ---- 5. Accumulate boundary cones in world-frame buffer ----
        for x_w, y_w, z_w, label in world_frame_points:
            self.local_buffer.add_cone_detection(x_w, y_w, z_w, label)
            self.stats['total_detections'] += 1

        # ---- 5. Promote high-confidence cones to global map ----
        promoted = 0
        for cone in self.local_buffer.get_high_confidence_cones():
            if self.global_map.try_add_cone(cone):
                self.stats['global_additions'] += 1
                promoted += 1

        if promoted:
            self.get_logger().debug(f'Promoted {promoted} cones to global map')

        self.stats['processing_times'].append(time.time() - t0)
        if len(self.stats['processing_times']) > 100:
            self.stats['processing_times'] = self.stats['processing_times'][-100:]

    # ------------------------------------------------------------------ #
    #  Timer callbacks                                                     #
    # ------------------------------------------------------------------ #

    def _update_buffer(self):
        """Decay and prune local buffer at 5 Hz (independent of camera rate)."""
        self.local_buffer.update_frame()

    def _publish_local_map(self):
        """
        Publish accumulated boundary cones in car (base_link) frame as CSV.
        If no odometry is available, publish nothing here — the raw
        /cone_map/car_frame PointCloud2 is always available from the callback.
        """
        local_cones = self.local_buffer.get_all_cones()
        if not local_cones or self.latest_pose is None:
            return

        lines = []
        for cone in local_cones:
            try:
                x_c, y_c, z_c = world_to_car_frame(
                    cone['x'], cone['y'], cone['z'],
                    self.latest_pose['position'],
                    self.latest_pose['orientation'],
                )
            except Exception:
                continue
            lines.append(
                f"{x_c:.2f},{y_c:.2f},{z_c:.2f},{cone['color']},{cone['confidence']:.2f}"
            )

        if lines:
            msg = String()
            msg.data = '\n'.join(lines)
            self.local_map_pub.publish(msg)

    def _publish_global_map(self):
        """Publish persistent global map in world frame as CSV."""
        global_cones = self.global_map.get_global_map()
        if not global_cones:
            return

        lines = [
            f"{c['x']:.2f},{c['y']:.2f},{c['z']:.2f},{c['color']}"
            for c in global_cones
        ]
        msg = String()
        msg.data = '\n'.join(lines)
        self.global_map_pub.publish(msg)

        stats = self.global_map.get_stats()
        self.get_logger().info(
            f"Global map: {stats['total_cones']} cones "
            f"(B:{stats['blue_cones']} Y:{stats['yellow_cones']} O:{stats['orange_cones']})"
        )

    def _publish_centerline(self):
        global_cones = self.global_map.get_global_map()
        left  = [c for c in global_cones if c['color'] == ConeColor.BLUE]
        right = [c for c in global_cones if c['color'] == ConeColor.YELLOW]

        if not left or not right:
            return

        ts = self.get_clock().now()
        path = self.visualizer.create_centerline_path(left, right, ts)
        self.centerline_pub.publish(path)

    def _publish_visualisation(self):
        local_cones = self.local_buffer.get_all_cones()
        global_cones = self.global_map.get_local_view(self.vehicle_position, radius=20.0)

        if not local_cones and not global_cones:
            return

        ts = self.get_clock().now()
        marker_array = self.visualizer.create_marker_array(local_cones, global_cones, ts)

        left  = [c for c in global_cones if c['color'] == ConeColor.BLUE]
        right = [c for c in global_cones if c['color'] == ConeColor.YELLOW]
        if left and right:
            marker_array.markers.append(
                self.visualizer.create_centerline_marker(left, right, ts))
            marker_array.markers.extend(
                self.visualizer.create_boundary_markers(left, right, ts))

        self.markers_pub.publish(marker_array)

    def _publish_diagnostics(self):
        diag = DiagnosticArray()
        diag.header.stamp = self.get_clock().now().to_msg()

        status = DiagnosticStatus()
        status.name = 'cone_mapping'
        status.hardware_id = 'cone_mapper'

        if self.stats['processing_times']:
            avg_ms = np.mean(self.stats['processing_times']) * 1000
            max_ms = np.max(self.stats['processing_times']) * 1000
        else:
            avg_ms = max_ms = 0.0

        local_count  = len(self.local_buffer.get_all_cones())
        global_count = len(self.global_map.get_global_map())

        if self.stats['coordinate_warnings'] > 50:
            status.level = DiagnosticStatus.WARN
            status.message = 'High coordinate warning count'
        elif avg_ms > 20:
            status.level = DiagnosticStatus.WARN
            status.message = 'High processing time'
        elif local_count > 150:
            status.level = DiagnosticStatus.WARN
            status.message = 'High local cone count'
        else:
            status.level = DiagnosticStatus.OK
            status.message = 'System healthy'

        for key, val in {
            'total_detections':     self.stats['total_detections'],
            'global_additions':     self.stats['global_additions'],
            'local_cone_count':     local_count,
            'global_cone_count':    global_count,
            'coordinate_warnings':  self.stats['coordinate_warnings'],
            'avg_processing_ms':    f'{avg_ms:.2f}',
            'max_processing_ms':    f'{max_ms:.2f}',
            'has_slam_pose':        str(self.latest_pose is not None),
        }.items():
            kv = KeyValue(key=key, value=str(val))
            status.values.append(kv)

        diag.status.append(status)
        self.diagnostics_pub.publish(diag)

    # ------------------------------------------------------------------ #
    #  Publish helpers                                                     #
    # ------------------------------------------------------------------ #

    def _publish_car_frame_pc(self, points, stamp):
        """Publish raw car-frame cone observations as PointCloud2."""
        self._publish_pc(points, stamp, 'base_link', self.car_frame_pc_pub)

    def _publish_pc(self, points, stamp, frame_id: str, publisher):
        """Generic PointCloud2 publisher for (x, y, z, label) point lists."""
        if not points:
            return
        header = Header()
        header.stamp = stamp
        header.frame_id = frame_id
        fields = [
            PointField(name='x',     offset=0,  datatype=PointField.FLOAT32, count=1),
            PointField(name='y',     offset=4,  datatype=PointField.FLOAT32, count=1),
            PointField(name='z',     offset=8,  datatype=PointField.FLOAT32, count=1),
            PointField(name='label', offset=12, datatype=PointField.FLOAT32, count=1),
        ]
        pc = point_cloud2.create_cloud(
            header, fields, [(x, y, z, float(l)) for x, y, z, l in points])
        publisher.publish(pc)


# ------------------------------------------------------------------ #
#  Entry point                                                         #
# ------------------------------------------------------------------ #

def main(args=None):
    rclpy.init(args=args)
    node = ConeMapperNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            node.global_map.save_to_file('final_cone_map.json')
            node.get_logger().info('Saved global map to final_cone_map.json')
        except Exception as e:
            node.get_logger().error(f'Failed to save global map: {e}')
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
