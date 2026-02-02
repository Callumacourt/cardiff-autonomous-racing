# --- Integration TODOs ---
# TODO: Subscribe to /cone_cloud/local (YOLO output)
# TODO: Subscribe to /odometry/slam (ORB-SLAM3 output)
# TODO: Transform cone detections to global frame using SLAM pose
# TODO: Build and maintain persistent global cone map
# TODO: Implement cone association and duplicate filtering
# TODO: Publish global map to /global_cone_map for path planning
# --- End Integration TODOs ---

from sympy import Point
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from nav_msgs.msg import Odometry, Path
from geometry_msgs.msg import PoseStamped
from visualization_msgs.msg import Marker, MarkerArray
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2

import numpy as np
from scipy.spatial import KDTree
from scipy.spatial.transform import Rotation as R
import time
import math
import json
from typing import List, Tuple, Dict, Optional

# Color constants
BLUE_CONE = 0
YELLOW_CONE = 1  
ORANGE_CONE = 2

class PersistentGlobalMap:
    """Persistent global cone map with adjusted thresholds"""
    
    def __init__(self, confidence_threshold=0.7, min_detections=3):  # Balanced thresholds
        self.global_cones = []
        self.confidence_threshold = confidence_threshold
        self.min_detections = min_detections
        self.cone_id_counter = 0
        
    def try_add_cone(self, cone_data):
        """Try to add a cone to global map if it meets criteria"""
        if (cone_data['confidence'] > self.confidence_threshold and 
            cone_data['detections'] >= self.min_detections):
            
            # Check if already in global map
            for existing in self.global_cones:
                if (existing['color'] == cone_data['color'] and
                    np.linalg.norm([existing['x'] - cone_data['x'], 
                                   existing['y'] - cone_data['y']]) < 1.5):  # Slightly larger tolerance
                    return False  # Already exists
            
            # Add to global map
            self.cone_id_counter += 1
            global_cone = {
                'id': self.cone_id_counter,
                'x': cone_data['x'],
                'y': cone_data['y'], 
                'z': cone_data['z'],
                'color': cone_data['color'],
                'confidence': cone_data['confidence'],
                'detections': cone_data['detections'],
                'added_timestamp': time.time()
            }
            self.global_cones.append(global_cone)
            return True
        return False
    
    def get_global_map(self):
        return self.global_cones.copy()
    
    def get_local_view(self, vehicle_pos, radius=20.0):
        veh_x, veh_y = vehicle_pos
        local_cones = []
        
        for cone in self.global_cones:
            distance = math.sqrt((cone['x'] - veh_x)**2 + (cone['y'] - veh_y)**2)
            if distance <= radius:
                local_cones.append(cone)
        
        return local_cones
    
    def save_to_file(self, filename):
        with open(filename, 'w') as f:
            json.dump(self.global_cones, f, indent=2)
    
    def get_stats(self):
        color_counts = {BLUE_CONE: 0, YELLOW_CONE: 0, ORANGE_CONE: 0}
        for cone in self.global_cones:
            color_counts[cone['color']] += 1
        
        return {
            'total_cones': len(self.global_cones),
            'blue_cones': color_counts[BLUE_CONE],
            'yellow_cones': color_counts[YELLOW_CONE],
            'orange_cones': color_counts[ORANGE_CONE]
        }

class LocalConeBuffer:
    """Sliding window buffer with improved parameters"""
    
    def __init__(self, max_size=200, max_age=6.0):
        self.cones = []
        self.max_size = max_size
        self.max_age = max_age
        self.cone_id_counter = 0
        
    def add_cone_detection(self, x, y, z, color, confidence=1.0):
        """Add detection with distance-based confidence"""
        current_time = time.time()
        
        # Calculate distance for confidence adjustment
        distance = np.sqrt(x*x + y*y + z*z)
        
        # Find matching cone
        matching_idx = self._find_matching_cone(x, y, color)
        
        if matching_idx is not None:
            # Update existing
            cone = self.cones[matching_idx]
            cone['x'] = 0.3 * x + 0.7 * cone['x']  # EMA
            cone['y'] = 0.3 * y + 0.7 * cone['y']
            cone['z'] = 0.3 * z + 0.7 * cone['z']
            
            # Distance-based confidence gain
            confidence_gain = 0.2 if distance < 5.0 else 0.15 if distance < 10.0 else 0.1
            cone['confidence'] = min(1.0, cone['confidence'] + confidence_gain)
            cone['detections'] += 1
            cone['last_seen'] = current_time
        else:
            # Add new cone with distance-based initial confidence
            if distance < 3.0:
                initial_conf = 0.6
            elif distance < 8.0:
                initial_conf = 0.4
            else:
                initial_conf = 0.3
                
            self.cone_id_counter += 1
            self.cones.append({
                'id': self.cone_id_counter,
                'x': x, 'y': y, 'z': z, 'color': color,
                'confidence': initial_conf,
                'detections': 1,
                'first_seen': current_time,
                'last_seen': current_time
            })
    
    def update_frame(self):
        """Update confidence and prune old/low-confidence cones"""
        current_time = time.time()
        
        # Decay confidence for unseen cones
        for cone in self.cones:
            age = current_time - cone['last_seen']
            if age > 0.1:  # Not seen this frame
                cone['confidence'] = max(0.0, cone['confidence'] - 0.04)
        
        # Remove old or low-confidence cones
        self.cones = [cone for cone in self.cones 
                     if (current_time - cone['first_seen'] < self.max_age and
                         cone['confidence'] > 0.15)]
        
        # Limit size
        if len(self.cones) > self.max_size:
            self.cones.sort(key=lambda x: x['confidence'], reverse=True)
            self.cones = self.cones[:self.max_size]
    
    def get_all_cones(self):
        return self.cones.copy()
    
    def get_high_confidence_cones(self, threshold=0.6):  # Lowered threshold
        return [cone for cone in self.cones if cone['confidence'] > threshold]
    
    def _find_matching_cone(self, x, y, color, radius=2.0):  # Increased radius
        candidates = [(i, cone) for i, cone in enumerate(self.cones) 
                     if cone['color'] == color]
        
        if not candidates:
            return None
        
        positions = np.array([[cone['x'], cone['y']] for _, cone in candidates])
        tree = KDTree(positions)
        
        dist, local_idx = tree.query([x, y])
        
        if dist < radius:
            global_idx, _ = candidates[local_idx]
            return global_idx
        
        return None

class ImprovedConeMapperNode(Node):
    """Improved cone mapper with FIXED coordinate transformation"""
    
    def __init__(self):
        super().__init__('improved_cone_mapper')
        
        # Initialize mapping components with better parameters
        self.global_map = PersistentGlobalMap(
            confidence_threshold=0.7,  # Balanced
            min_detections=3          # Reasonable requirement
        )
        self.local_buffer = LocalConeBuffer()
        
        # Vehicle state
        self.latest_pose = None
        self.vehicle_position = (0.0, 0.0)
        
        # Subscriptions
        self.pose_sub = self.create_subscription(
            Odometry, '/odometry/slam', self.pose_callback, 10)
        self.cone_pc_sub = self.create_subscription(
            PointCloud2, '/cone_cloud/local', self.cone_pc_callback, 10)
        
        # Publishers
        self.local_map_pub = self.create_publisher(String, '/cone_map/local', 10)
        self.global_map_pub = self.create_publisher(String, '/cone_map/global', 10)
        self.boundaries_pub = self.create_publisher(Path, '/track/boundaries', 10)
        self.centerline_pub = self.create_publisher(Path, '/track/centerline', 10)
        self.markers_pub = self.create_publisher(MarkerArray, '/cone_map/markers', 10)
        self.diagnostics_pub = self.create_publisher(DiagnosticArray, '/mapping/diagnostics', 10)
        
        # Timers
        self.local_timer = self.create_timer(0.05, self.publish_local_map)
        self.global_timer = self.create_timer(0.5, self.publish_global_map)
        self.diagnostics_timer = self.create_timer(1.0, self.publish_diagnostics)
        self.centerline_timer = self.create_timer(0.5, self.publish_centerline)
        
        # Statistics
        self.stats = {
            'total_detections': 0,
            'global_additions': 0,
            'processing_times': [],
            'coordinate_warnings': 0
        }
        
        self.get_logger().info('Improved Cone Mapper Node initialized with fixed coordinates')
    
    def pose_callback(self, msg):
        """Handle pose updates with validation"""
        pos = msg.pose.pose.position
        ori = msg.pose.pose.orientation
        
        # Validate position
        if (np.isnan(pos.x) or np.isnan(pos.y) or np.isnan(pos.z) or
            np.isinf(pos.x) or np.isinf(pos.y) or np.isinf(pos.z)):
            return
        
        # Validate quaternion
        quat = np.array([ori.x, ori.y, ori.z, ori.w])
        if np.any(np.isnan(quat)) or np.any(np.isinf(quat)) or np.allclose(quat, 0):
            return
        
        # Normalize quaternion
        quat = quat / np.linalg.norm(quat)
        
        self.latest_pose = {
            'position': np.array([pos.x, pos.y, pos.z]),
            'orientation': quat,
            'timestamp': msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        }
        
        self.vehicle_position = (pos.x, pos.y)
    
    def cone_callback(self, pc_msg: PointCloud2):
        """Handle PointCloud2 cone detections (points in camera frame or already in map)."""
        frame_id = getattr(pc_msg.header, 'frame_id', '')
        has_pose = (self.latest_pose is not None)

        # If we don't have a SLAM pose, only accept clouds already in map/odom
        if not has_pose and frame_id not in ('map', 'odom', 'world'):
            self.get_logger().debug("No SLAM pose and cloud not in map/odom; skipping")
            return

        start_time = time.time()
        try:
            # Prepare vehicle/world transform if we have a pose
            if has_pose:
                vehicle_pos = self.latest_pose['position']
                vehicle_quat = self.latest_pose['orientation']
                rot = R.from_quat(vehicle_quat)
                R_world_vehicle = rot.as_matrix()
                t_world_vehicle = vehicle_pos.reshape(3, 1)
            else:
                R_world_vehicle = None
                t_world_vehicle = None

            # Read points from PointCloud2. Prefer 'label' if present, fallback to 'confidence'.
            available_fields = {f.name for f in pc_msg.fields}
            label_field = 'label' if 'label' in available_fields else 'confidence'
            points_iter = point_cloud2.read_points(
                pc_msg,
                field_names=('x', 'y', 'z', label_field),
                skip_nans=True
            )

            valid_detections = 0
            for p in points_iter:
                try:
                    x_cam, y_cam, z_cam, label_f = p
                except Exception:
                    continue

                # Validate inputs
                if not (np.isfinite(x_cam) and np.isfinite(y_cam) and np.isfinite(z_cam)):
                    self.stats['coordinate_warnings'] += 1
                    continue

                # Bounds check
                if abs(x_cam) > 50 or abs(y_cam) > 50 or z_cam < 0.01 or z_cam > 50:
                    self.stats['coordinate_warnings'] += 1
                    continue

                # If cloud already in world/map frame, use values directly
                if frame_id in ('map', 'odom', 'world'):
                    x_world, y_world, z_world = float(x_cam), float(y_cam), float(z_cam)
                else:
                    # require SLAM pose to transform camera->robot->world
                    if not has_pose:
                        continue
                    x_robot = z_cam    # camera Z -> robot X (forward)
                    y_robot = -x_cam   # camera X -> robot -Y (left)
                    z_robot = -y_cam   # camera Y -> robot -Z (up)
                    X_robot = np.array([[x_robot], [y_robot], [z_robot]])
                    X_world = R_world_vehicle @ X_robot + t_world_vehicle
                    x_world, y_world, z_world = float(X_world[0, 0]), float(X_world[1, 0]), float(X_world[2, 0])

                # Label parsing
                try:
                    color = int(label_f)
                except Exception:
                    color = 0

                self.local_buffer.add_cone_detection(x_world, y_world, z_world, color)
                self.stats['total_detections'] += 1
                valid_detections += 1

            if valid_detections > 0:
                self.get_logger().info(f'Processed {valid_detections} valid cone detections')

            # Update buffer and try promote to global map
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

    def cone_pc_callback(self, pc_msg: PointCloud2):
        # wrapper to keep subscription name used in __init__
        self.cone_callback(pc_msg)
    
    def publish_local_map(self):
        """Publish local cone map"""
        local_cones = self.local_buffer.get_all_cones()
        
        if not local_cones:
            return
        
        # Create message
        output_lines = []
        for cone in local_cones:
            output_lines.append(
                f"{cone['x']:.2f},{cone['y']:.2f},{cone['z']:.2f},"
                f"{cone['color']},{cone['confidence']:.2f}")
        
        msg = String()
        msg.data = '\n'.join(output_lines)
        self.local_map_pub.publish(msg)
        
        # Publish visualization
        self.publish_markers(local_cones)
    
    def publish_global_map(self):
        """Publish global cone map"""
        global_cones = self.global_map.get_global_map()
        
        if not global_cones:
            return
        
        # Create message
        output_lines = []
        for cone in global_cones:
            output_lines.append(
                f"{cone['x']:.2f},{cone['y']:.2f},{cone['z']:.2f},{cone['color']}")
        
        msg = String()
        msg.data = '\n'.join(output_lines)
        self.global_map_pub.publish(msg)
        
        # Log stats
        stats = self.global_map.get_stats()
        self.get_logger().info(f'Global map: {stats["total_cones"]} cones total')
    
    def publish_markers(self, cones):
        """Publish RViz markers"""
        marker_array = MarkerArray()
        
        # Clear previous markers
        clear_marker = Marker()
        clear_marker.action = Marker.DELETEALL
        marker_array.markers.append(clear_marker)
        
        colors = {
            BLUE_CONE: [0.0, 0.0, 1.0],
            YELLOW_CONE: [1.0, 1.0, 0.0],
            ORANGE_CONE: [1.0, 0.5, 0.0]
        }
        
        for i, cone in enumerate(cones):
            marker = Marker()
            marker.header.frame_id = 'map'
            marker.header.stamp = self.get_clock().now().to_msg()
            marker.ns = 'local_cones'
            marker.id = i + 1
            marker.type = Marker.CYLINDER
            marker.action = Marker.ADD
            
            # Position
            marker.pose.position.x = cone['x']
            marker.pose.position.y = cone['y']
            marker.pose.position.z = cone['z']
            
            # Size based on confidence
            scale = 0.1 + cone['confidence'] * 0.1
            marker.scale.x = scale
            marker.scale.y = scale
            marker.scale.z = 0.3
            
            # Color and transparency
            color_rgb = colors.get(cone['color'], [0.5, 0.5, 0.5])
            marker.color.r = color_rgb[0]
            marker.color.g = color_rgb[1]
            marker.color.b = color_rgb[2]
            marker.color.a = 0.3 + cone['confidence'] * 0.7
            
            marker_array.markers.append(marker)
        
        # Add global map markers
        global_cones = self.global_map.get_local_view(self.vehicle_position)
        for i, cone in enumerate(global_cones):
            marker = Marker()
            marker.header.frame_id = 'map'
            marker.header.stamp = self.get_clock().now().to_msg()
            marker.ns = 'global_cones'
            marker.id = i + 1000
            marker.type = Marker.CYLINDER
            marker.action = Marker.ADD
            
            marker.pose.position.x = cone['x']
            marker.pose.position.y = cone['y']
            marker.pose.position.z = cone['z']
            
            marker.scale.x = 0.15
            marker.scale.y = 0.15
            marker.scale.z = 0.4
            
            color_rgb = colors.get(cone['color'], [0.5, 0.5, 0.5])
            marker.color.r = color_rgb[0]
            marker.color.g = color_rgb[1]
            marker.color.b = color_rgb[2]
            marker.color.a = 1.0
            
            marker_array.markers.append(marker)
        
        # Add centerline marker
        centerline_marker = Marker()
        centerline_marker.type = Marker.LINE_STRIP
        centerline_marker.header.frame_id = 'map'
        centerline_marker.header.stamp = self.get_clock().now().to_msg()
        centerline_marker.ns = 'centerline'
        centerline_marker.id = 999  # Unique ID
        centerline_marker.action = Marker.ADD
        centerline_marker.color.r, centerline_marker.color.g, centerline_marker.color.b = 0.0, 1.0, 0.0
        centerline_marker.color.a = 1.0
        centerline_marker.scale.x = 0.1  # line width

        # Compute centerline from boundaries (midpoint of left/right cones)
        left_cones = [c for c in global_cones if c['color'] == BLUE_CONE]
        right_cones = [c for c in global_cones if c['color'] == YELLOW_CONE]

        for i in range(min(len(left_cones), len(right_cones))):
            from geometry_msgs.msg import Point
            p = Point()
            p.x = (left_cones[i]['x'] + right_cones[i]['x']) / 2.0
            p.y = (left_cones[i]['y'] + right_cones[i]['y']) / 2.0
            p.z = 0.0
            centerline_marker.points.append(p)

        marker_array.markers.append(centerline_marker)
        
        self.markers_pub.publish(marker_array)
    
    def publish_centerline(self):
        """Publish centerline as a Path message for RViz"""
        global_cones = self.global_map.get_global_map()
        
        # Separate left (blue) and right (yellow) cones
        left_cones = sorted([c for c in global_cones if c['color'] == BLUE_CONE], 
                            key=lambda c: np.sqrt(c['x']**2 + c['y']**2))
        right_cones = sorted([c for c in global_cones if c['color'] == YELLOW_CONE], 
                             key=lambda c: np.sqrt(c['x']**2 + c['y']**2))
        
        if not left_cones or not right_cones:
            self.get_logger().debug("Not enough left/right cones for centerline")
            return
        
        # Calculate centerline as midpoint between left and right
        centerline_path = Path()
        centerline_path.header.frame_id = 'map'
        centerline_path.header.stamp = self.get_clock().now().to_msg()
        
        for i in range(min(len(left_cones), len(right_cones))):
            left = left_cones[i]
            right = right_cones[i]
            
            # Midpoint
            cx = (left['x'] + right['x']) / 2.0
            cy = (left['y'] + right['y']) / 2.0
            cz = (left['z'] + right['z']) / 2.0
            
            pose = PoseStamped()
            pose.header.frame_id = 'map'
            pose.header.stamp = self.get_clock().now().to_msg()
            pose.pose.position.x = cx
            pose.pose.position.y = cy
            pose.pose.position.z = cz
            pose.pose.orientation.w = 1.0
            
            centerline_path.poses.append(pose)
            
            # Log for debugging
            if i % 5 == 0:
                self.get_logger().info(f"Centerline point {i}: ({cx:.2f}, {cy:.2f}, {cz:.2f})")
        
        self.centerline_pub.publish(centerline_path)
    
    def publish_diagnostics(self):
        """Publish system diagnostics"""
        diag_array = DiagnosticArray()
        diag_array.header.stamp = self.get_clock().now().to_msg()
        
        status = DiagnosticStatus()
        status.name = 'cone_mapping'
        status.hardware_id = 'improved_cone_mapper'
        
        # Calculate metrics
        if self.stats['processing_times']:
            avg_time = np.mean(self.stats['processing_times']) * 1000
            max_time = np.max(self.stats['processing_times']) * 1000
        else:
            avg_time = max_time = 0
        
        local_count = len(self.local_buffer.get_all_cones())
        global_count = len(self.global_map.get_global_map())
        
        # Set status
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
        
        # Add metrics
        metrics = {
            'total_detections': self.stats['total_detections'],
            'global_additions': self.stats['global_additions'],
            'local_cone_count': local_count,
            'global_cone_count': global_count,
            'coordinate_warnings': self.stats['coordinate_warnings'],
            'avg_processing_time_ms': avg_time,
            'max_processing_time_ms': max_time
        }
        
        for key, value in metrics.items():
            kv = KeyValue()
            kv.key = key
            kv.value = str(value)
            status.values.append(kv)
        
        diag_array.status.append(status)
        self.diagnostics_pub.publish(diag_array)

def main(args=None):
    rclpy.init(args=args)
    
    node = ImprovedConeMapperNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Save global map on exit
        node.global_map.save_to_file('final_cone_map.json')
        node.get_logger().info('Saved global map to final_cone_map.json')
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()