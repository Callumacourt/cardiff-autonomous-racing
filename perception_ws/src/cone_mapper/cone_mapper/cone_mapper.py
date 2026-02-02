"""Main ROS2 node for cone mapping."""
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from nav_msgs.msg import Odometry, Path
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
        /odometry/slam: Vehicle pose from ORB-SLAM3
    
    Publishes:
        /cone_map/local: Local cone buffer (String)
        /cone_map/global: Persistent global map (String)
        /cone_map/markers: RViz visualization (MarkerArray)
        /track/centerline: Centerline path (Path)
        /mapping/diagnostics: System health (DiagnosticArray)
    """
    
    def __init__(self):
        super().__init__('cone_mapper')
        
        # Initialize mapping components
        self.global_map = PersistentGlobalMap(
            confidence_threshold=0.7,
            min_detections=3
        )
        self.local_buffer = LocalConeBuffer(max_size=200, max_age=6.0)
        
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
        self.centerline_pub = self.create_publisher(Path, '/track/centerline', 10)
        self.markers_pub = self.create_publisher(MarkerArray, '/cone_map/markers', 10)
        self.diagnostics_pub = self.create_publisher(DiagnosticArray, '/mapping/diagnostics', 10)
    
    def _setup_timers(self):
        """Create periodic timers."""
        self.create_timer(0.05, self._publish_local_map)
        self.create_timer(0.5, self._publish_global_map)
        self.create_timer(1.0, self._publish_diagnostics)
        self.create_timer(0.5, self._publish_centerline)
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
        
        self.get_logger().info(f"Received PointCloud2: frame_id={frame_id}, has_pose={has_pose}")
        
        # If we don't have SLAM pose, only accept clouds in map/odom frame
        if not has_pose and frame_id not in ('map', 'odom', 'world'):
            self.get_logger().warning(f"Rejecting cloud: no SLAM pose and frame_id={frame_id}")
            return
        
        start_time = time.time()
        
        try:
            # Read points from PointCloud2
            available_fields = {f.name for f in msg.fields}
            label_field = 'label' if 'label' in available_fields else 'confidence'
            
            points_iter = point_cloud2.read_points(
                msg,
                field_names=('x', 'y', 'z', label_field),
                skip_nans=True
            )
            
            valid_detections = 0
            
            for p in points_iter:
                try:
                    x_cam, y_cam, z_cam, label_f = p
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
                    
                    # Camera -> Robot frame
                    point_robot = camera_to_robot_frame(x_cam, y_cam, z_cam)
                    
                    # Robot -> World frame
                    x_world, y_world, z_world = robot_to_world_frame(
                        point_robot,
                        self.latest_pose['position'],
                        self.latest_pose['orientation']
                    )
                
                # Parse color label
                try:
                    color = int(label_f)
                except Exception:
                    color = ConeColor.BLUE  # Default
                
                # Add to local buffer
                self.local_buffer.add_cone_detection(x_world, y_world, z_world, color)
                self.stats['total_detections'] += 1
                valid_detections += 1
            
            if valid_detections > 0:
                self.get_logger().info(f'Processed {valid_detections} valid cone detections from frame {frame_id}')
            
            # Update buffer and promote high-confidence cones to global map
            self.local_buffer.update_frame()
            promoted_count = 0
            
            for cone in self.local_buffer.get_high_confidence_cones():
                if self.global_map.try_add_cone(cone):
                    self.stats['global_additions'] += 1
                    promoted_count += 1
                    self.get_logger().info(
                        f'Added cone {cone["id"]} to global map at '
                        f'({cone["x"]:.1f}, {cone["y"]:.1f}) with confidence {cone["confidence"]:.2f}'
                    )
            
            if promoted_count > 0:
                self.get_logger().info(f'Promoted {promoted_count} cones to global map')
            
            # Track processing time
            self.stats['processing_times'].append(time.time() - start_time)
            if len(self.stats['processing_times']) > 100:
                self.stats['processing_times'] = self.stats['processing_times'][-100:]
        
        except Exception as e:
            self.get_logger().error(f'Error processing cone pointcloud: {e}')
    
    def _publish_local_map(self):
        """Publish local cone map as String message."""
        local_cones = self.local_buffer.get_all_cones()
        
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
        
        # Log stats periodically
        stats = self.global_map.get_stats()
        self.get_logger().info(
            f'Global map: {stats["total_cones"]} cones '
            f'(B:{stats["blue_cones"]} Y:{stats["yellow_cones"]} O:{stats["orange_cones"]})'
        )
    
    def _publish_visualisation(self):
        """
        Publish RViz markers using visualisation module.
        """
        local_cones = self.local_buffer.get_all_cones()
        global_cones = self.global_map.get_local_view(
            self.vehicle_position, 
            radius=20.0
        )
        
        if not local_cones and not global_cones:
            self.get_logger().debug("No cones to visualize")
            return
        
        timestamp = self.get_clock().now()
        
        # Create marker array with all cones
        marker_array = self.visualizer.create_marker_array(
            local_cones,
            global_cones,
            timestamp
        )
        
        # Add centerline marker
        left_cones = [c for c in global_cones if c['color'] == ConeColor.BLUE]
        right_cones = [c for c in global_cones if c['color'] == ConeColor.YELLOW]
        
        if left_cones and right_cones:
            centerline_marker = self.visualizer.create_centerline_marker(
                left_cones,
                right_cones,
                timestamp
            )
            marker_array.markers.append(centerline_marker)
            
            # Optionally add boundary markers
            boundary_markers = self.visualizer.create_boundary_markers(
                left_cones,
                right_cones,
                timestamp
            )
            marker_array.markers.extend(boundary_markers)
        
        self.markers_pub.publish(marker_array)
    
    def _publish_centerline(self):
        """
        Publish centerline as Path message using visualisation module.
        """
        global_cones = self.global_map.get_global_map()
        
        # Separate left (blue) and right (yellow) cones
        left_cones = [c for c in global_cones if c['color'] == ConeColor.BLUE]
        right_cones = [c for c in global_cones if c['color'] == ConeColor.YELLOW]
        
        if not left_cones or not right_cones:
            self.get_logger().debug("Not enough left/right cones for centerline")
            return
        
        timestamp = self.get_clock().now()
        
        # Use visualizer to create centerline path
        centerline_path = self.visualizer.create_centerline_path(
            left_cones,
            right_cones,
            timestamp
        )
        
        self.centerline_pub.publish(centerline_path)
        
        # Log for debugging
        if len(centerline_path.poses) > 0:
            self.get_logger().info(
                f"Published centerline with {len(centerline_path.poses)} points"
            )
    
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