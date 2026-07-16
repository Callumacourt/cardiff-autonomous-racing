"""Main ROS2 node for cone mapping."""
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from nav_msgs.msg import Odometry
from visualization_msgs.msg import MarkerArray
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2

import numpy as np
import time
from typing import Optional

from .map_data import PersistentGlobalMap, LocalConeBuffer
from .constants import ConeColor
from .transforms import (
    validate_point,
    extract_pose_from_odometry,
    camera_to_robot_frame,
    robot_to_world_frame
)
from .visualisation import ConeVisualizer


class ConeMapperNode(Node):
    """
    ROS2 node for building persistent cone map from detections and SLAM.

    Subscribes to:
        /cone_cloud/local: PointCloud2 detections from YOLO
        /odometry/slam: Vehicle pose from SLAM

    Publishes:
        /cone_map/local: Local cone buffer (String)
        /cone_map/global: Persistent global map (String)
        /cone_map/markers: RViz visualization (MarkerArray)
        /mapping/diagnostics: System health (DiagnosticArray)
    """
    
    # Cones below this confidence are held back from /cone_map/local so the
    # planner never plans around a cone seen only once or twice.
    LOCAL_PUBLISH_MIN_CONF = 0.3

    # Ignore detections deeper than this (camera-frame metres): depth
    # accuracy degrades with range and long-range errors put cones
    # metres from their true spot. Matches landmark_slam's max_cone_range.
    MAX_DETECTION_RANGE = 15.0

    # Physical plausibility band for a cone's world-frame height (m).
    # A bad depth sample (e.g. road surface in front of a distant cone)
    # back-projects to below ground level — provably not a cone.
    MIN_CONE_Z = -0.15
    MAX_CONE_Z = 1.2

    def __init__(self):
        super().__init__('cone_mapper')

        # Node clock (follows sim time when use_sim_time is set) so buffer
        # aging matches the world the node is running in.
        ros_now = lambda: self.get_clock().now().nanoseconds * 1e-9

        # Initialize mapping components
        self.global_map = PersistentGlobalMap(
            confidence_threshold=0.7,
            min_detections=3,
            now_fn=ros_now
        )
        self.local_buffer = LocalConeBuffer(max_size=200, max_age=6.0, now_fn=ros_now)
        
        # Initialize visualizer
        self.visualizer = ConeVisualizer(frame_id='map')
        
        # Vehicle state
        self.latest_pose: Optional[dict] = None
        self.vehicle_position = (0.0, 0.0)
        
        # Setup ROS interfaces
        self._setup_subscribers()
        self._setup_publishers()
        self._setup_timers()
        
        # Statistics
        self.stats = {
            'total_detections': 0,
            'global_additions': 0,
            'processing_times': [],
            'coordinate_warnings': 0
        }
        
        self.get_logger().info('Cone Mapper initialized')
    
    def _setup_subscribers(self):
        """Create ROS subscriptions."""
        self.pose_sub = self.create_subscription(
            Odometry, '/odometry/slam', self._pose_callback, 10)
        self.cone_pc_sub = self.create_subscription(
            PointCloud2, '/cone_cloud/local', self._cone_callback, 10)
    
    def _setup_publishers(self):
        """Create ROS publishers."""
        self.local_map_pub = self.create_publisher(String, '/cone_map/local', 10)
        self.global_map_pub = self.create_publisher(String, '/cone_map/global', 10)
        self.markers_pub = self.create_publisher(MarkerArray, '/cone_map/markers', 10)
        self.diagnostics_pub = self.create_publisher(DiagnosticArray, '/mapping/diagnostics', 10)

    def _setup_timers(self):
        """Create periodic timers."""
        self.create_timer(0.05, self._publish_local_map)
        self.create_timer(0.5, self._publish_global_map)
        self.create_timer(1.0, self._publish_diagnostics)
        self.create_timer(0.1, self._publish_visualisation)
    
    def _pose_callback(self, msg: Odometry):
        """
        Handle incoming vehicle pose updates from SLAM.
        
        Uses transforms.extract_pose_from_odometry for validation.
        """
        pose = extract_pose_from_odometry(msg)
        
        if pose is None:
            self.get_logger().warning("Received invalid pose from SLAM")
            return
        
        self.latest_pose = pose
        self.vehicle_position = (pose['position'][0], pose['position'][1])
    
    def _cone_callback(self, msg: PointCloud2):
        """
        Handle incoming cone detections from PointCloud2.
        
        Uses transforms module for coordinate transformations.
        """
        frame_id = msg.header.frame_id
        has_pose = (self.latest_pose is not None)

        # If we don't have SLAM pose, only accept clouds in map/odom frame
        if not has_pose and frame_id not in ('map', 'odom', 'world'):
            self.get_logger().warning(
                f"Rejecting cloud: no SLAM pose and frame_id={frame_id}",
                throttle_duration_sec=5.0)
            return
        
        start_time = time.time()
        
        try:
            # cone_detector publishes x, y, z, label (+ confidence since v0.2)
            available = {f.name for f in msg.fields}
            if 'label' not in available:
                self.get_logger().warning(
                    "Cone cloud has no 'label' field — dropping message",
                    throttle_duration_sec=5.0)
                return
            has_conf = 'confidence' in available
            fields = ('x', 'y', 'z', 'label', 'confidence') if has_conf else \
                     ('x', 'y', 'z', 'label')

            points_iter = point_cloud2.read_points(
                msg, field_names=fields, skip_nans=True)

            valid_detections = 0

            for p in points_iter:
                try:
                    x_cam, y_cam, z_cam, label_f = p[0], p[1], p[2], p[3]
                    det_conf = float(p[4]) if has_conf else 1.0
                except Exception:
                    continue
                
                # Validate point using transforms module
                if not validate_point(x_cam, y_cam, z_cam, max_bound=50.0):
                    self.stats['coordinate_warnings'] += 1
                    continue
                
                # Transform to world frame
                if frame_id in ('map', 'odom', 'world'):
                    # Already in world frame
                    x_world, y_world, z_world = float(x_cam), float(y_cam), float(z_cam)
                else:
                    # Need to transform from camera to world
                    if not has_pose:
                        continue

                    # Camera-frame z is depth: gate out long-range detections
                    if z_cam > self.MAX_DETECTION_RANGE:
                        continue
                    
                    # Camera -> Robot frame
                    point_robot = camera_to_robot_frame(x_cam, y_cam, z_cam)
                    
                    # Robot -> World frame
                    x_world, y_world, z_world = robot_to_world_frame(
                        point_robot,
                        self.latest_pose['position'],
                        self.latest_pose['orientation']
                    )
                
                # Reject physically impossible cone heights (bad depth)
                if not (self.MIN_CONE_Z <= z_world <= self.MAX_CONE_Z):
                    self.stats['coordinate_warnings'] += 1
                    continue

                # Parse color label
                try:
                    color = int(label_f)
                except Exception:
                    color = ConeColor.BLUE  # Default
                
                # Add to local buffer
                self.local_buffer.add_cone_detection(
                    x_world, y_world, z_world, color, confidence=det_conf)
                self.stats['total_detections'] += 1
                valid_detections += 1
            
            if valid_detections > 0:
                self.get_logger().debug(
                    f'Processed {valid_detections} valid cone detections from frame {frame_id}')

            # Update buffer and promote high-confidence cones to global map
            self.local_buffer.update_frame()

            for cone in self.local_buffer.get_high_confidence_cones():
                if self.global_map.try_add_cone(cone):
                    self.stats['global_additions'] += 1
                    self.get_logger().debug(
                        f'Added cone {cone["id"]} to global map at '
                        f'({cone["x"]:.1f}, {cone["y"]:.1f}) with confidence {cone["confidence"]:.2f}'
                    )
            
            # Track processing time
            self.stats['processing_times'].append(time.time() - start_time)
            if len(self.stats['processing_times']) > 100:
                self.stats['processing_times'] = self.stats['processing_times'][-100:]
        
        except Exception as e:
            self.get_logger().error(f'Error processing cone pointcloud: {e}')
    
    def _publish_local_map(self):
        """Publish local cone map as String message."""
        local_cones = [c for c in self.local_buffer.get_all_cones()
                       if c['confidence'] >= self.LOCAL_PUBLISH_MIN_CONF]

        if not local_cones:
            self.get_logger().debug("No local cones to publish")
            return

        # Format: x,y,z,color,confidence
        output_lines = []
        for cone in local_cones:
            output_lines.append(
                f"{cone['x']:.2f},{cone['y']:.2f},{cone['z']:.2f},"
                f"{cone['color']},{cone['confidence']:.2f}"
            )
        
        msg = String()
        msg.data = '\n'.join(output_lines)
        self.local_map_pub.publish(msg)
    
    def _publish_global_map(self):
        """Publish global cone map as String message."""
        global_cones = self.global_map.get_global_map()
        
        if not global_cones:
            self.get_logger().debug("No global cones to publish")
            return
        
        # Format: x,y,z,color
        output_lines = []
        for cone in global_cones:
            output_lines.append(
                f"{cone['x']:.2f},{cone['y']:.2f},{cone['z']:.2f},{cone['color']}"
            )
        
        msg = String()
        msg.data = '\n'.join(output_lines)
        self.global_map_pub.publish(msg)

        stats = self.global_map.get_stats()
        self.get_logger().info(
            f'Global map: {stats["total_cones"]} cones '
            f'(B:{stats["blue_cones"]} Y:{stats["yellow_cones"]} O:{stats["orange_cones"]})',
            throttle_duration_sec=10.0
        )
    
    def _publish_visualisation(self):
        """Publish RViz cone markers."""
        local_cones = self.local_buffer.get_all_cones()
        global_cones = self.global_map.get_local_view(
            self.vehicle_position,
            radius=20.0
        )

        if not local_cones and not global_cones:
            return

        marker_array = self.visualizer.create_marker_array(
            local_cones,
            global_cones,
            self.get_clock().now()
        )
        self.markers_pub.publish(marker_array)

    def _publish_diagnostics(self):
        """Publish system diagnostics."""
        diag_array = DiagnosticArray()
        diag_array.header.stamp = self.get_clock().now().to_msg()
        
        status = DiagnosticStatus()
        status.name = 'cone_mapping'
        status.hardware_id = 'cone_mapper'
        
        # Calculate metrics
        if self.stats['processing_times']:
            avg_time = np.mean(self.stats['processing_times']) * 1000  # ms
            max_time = np.max(self.stats['processing_times']) * 1000
        else:
            avg_time = max_time = 0
        
        local_count = len(self.local_buffer.get_all_cones())
        global_count = len(self.global_map.get_global_map())
        
        # Set status level based on health checks
        if self.stats['coordinate_warnings'] > 50:
            status.level = DiagnosticStatus.WARN
            status.message = 'High coordinate warning count'
        elif avg_time > 20:
            status.level = DiagnosticStatus.WARN
            status.message = 'High processing time'
        elif local_count > 150:
            status.level = DiagnosticStatus.WARN
            status.message = 'High local cone count'
        else:
            status.level = DiagnosticStatus.OK
            status.message = 'System healthy'
        
        # Add metrics as key-value pairs
        metrics = {
            'total_detections': self.stats['total_detections'],
            'global_additions': self.stats['global_additions'],
            'local_cone_count': local_count,
            'global_cone_count': global_count,
            'coordinate_warnings': self.stats['coordinate_warnings'],
            'avg_processing_time_ms': f'{avg_time:.2f}',
            'max_processing_time_ms': f'{max_time:.2f}',
            'has_slam_pose': str(self.latest_pose is not None)
        }
        
        for key, value in metrics.items():
            kv = KeyValue()
            kv.key = key
            kv.value = str(value)
            status.values.append(kv)
        
        diag_array.status.append(status)
        self.diagnostics_pub.publish(diag_array)


def main(args=None):
    """Main entry point for cone mapper node."""
    rclpy.init(args=args)
    
    node = ConeMapperNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Save global map on exit
        try:
            node.global_map.save_to_file('final_cone_map.json')
            node.get_logger().info('Saved global map to final_cone_map.json')
        except Exception as e:
            node.get_logger().error(f'Failed to save global map: {e}')
        
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()