#!/usr/bin/env python3
"""
Path Planning Integration Node
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped as PathPose
import numpy as np

# Import TUM optimizer wrapper
try:
    from path_planning.tum_wrapper import TUMTrajectoryOptimizer
    TUM_AVAILABLE = True
except ImportError:
    TUM_AVAILABLE = False

class PathPlannerNode(Node):
    def __init__(self):
        super().__init__('path_planner')
        
        self.current_pose = (0.0, 0.0)
        self.left_cones = []
        self.right_cones = []
        self.orange_cones = []
        self.optimized_trajectory = None
        
        # Initialize TUM optimizer
        self.tum_optimizer = TUMTrajectoryOptimizer(
            vehicle_width=1.5,
            vehicle_length=2.5
        ) if TUM_AVAILABLE else None
        
        # Subscriptions
        self.pose_sub = self.create_subscription(PoseStamped, '/car_pose', self.pose_callback, 10)
        self.cones_sub = self.create_subscription(String, '/detected_cones', self.yolo_cones_callback, 10)
        
        # Publisher
        self.path_pub = self.create_publisher(Path, '/planned_path', 10)
        
        # Timer (5 Hz)
        self.timer = self.create_timer(0.2, self.main_loop)
        
        self.get_logger().info('Path Planner initialized')
    
    def yolo_cones_callback(self, msg):
        """Parse cone data from YOLO: x,y,z,label per line"""
        self.left_cones = []
        self.right_cones = []
        self.orange_cones = []
        
        if not msg.data.strip():
            return
        
        for line in msg.data.strip().split('\n'):
            parts = line.strip().split(',')
            if len(parts) >= 4:
                try:
                    x, y, z, label = map(float, parts[:4])
                    label = int(label)
                    
                    if label == 0:
                        self.left_cones.append((x, y))
                    elif label == 1:
                        self.right_cones.append((x, y))
                    elif label == 2:
                        self.orange_cones.append((x, y))
                except (ValueError, IndexError):
                    continue
        
        # Run optimization if enough cones
        if len(self.left_cones) >= 5 and len(self.right_cones) >= 5:
            self.optimize_trajectory()
    
    def optimize_trajectory(self):
        """Use TUM optimizer to generate racing line"""
        if not self.tum_optimizer:
            return
        
        try:
            reftrack = self.tum_optimizer.cones_to_reftrack(
                self.left_cones,
                self.right_cones,
                min_points=5
            )
            
            if reftrack is not None:
                trajectory = self.tum_optimizer.optimize_trajectory(reftrack, opt_type='mincurv')
                
                if trajectory is not None:
                    self.optimized_trajectory = trajectory
                    self.get_logger().info(f'Optimized path: {len(trajectory)} waypoints')
        except Exception as e:
            self.get_logger().error(f'Optimization failed: {e}')
    
    def pose_callback(self, msg):
        """Update vehicle pose"""
        self.current_pose = (msg.pose.position.x, msg.pose.position.y)
    
    def main_loop(self):
        """Publish path at 5 Hz"""
        if self.optimized_trajectory is None or len(self.optimized_trajectory) == 0:
            return
        
        path_msg = Path()
        path_msg.header.stamp = self.get_clock().now().to_msg()
        path_msg.header.frame_id = 'map'
        
        for pt in self.optimized_trajectory:
            pose = PathPose()
            pose.header.frame_id = 'map'
            pose.pose.position.x = float(pt[0])
            pose.pose.position.y = float(pt[1])
            pose.pose.position.z = 0.0
            pose.pose.orientation.w = 1.0
            path_msg.poses.append(pose)
        
        self.path_pub.publish(path_msg)

def main(args=None):
    rclpy.init(args=args)
    node = PathPlannerNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
    
    def yolo_cones_callback(self, msg):
        """
        Parse cone data directly from YOLO detector
        Message format: "x,y,z,label" per line
        
        Label mapping (from YOLO_cone_detector.py):
        0 = blue cone (left boundary)
        1 = yellow cone (right boundary)  
        2 = orange cone (special markers/boundaries)
        3 = unknown cone
        -1 = invalid
        """
        # Log raw message for debugging
        self.get_logger().debug(f'Received cone data: {msg.data[:100]}...')
        
        # Clear previous detections for fresh update
        self.left_cones = []
        self.right_cones = []
        self.orange_cones = []
        
        if not msg.data.strip():
            self.get_logger().warning('Received empty cone detection message')
            return
        
        lines = msg.data.strip().split('\n')
        valid_detections = 0
        
        for line in lines:
            parts = line.strip().split(',')
            if len(parts) >= 4:
                try:
                    x, y, z, label = map(float, parts[:4])
                    label = int(label)
                    
                    # Filter out invalid and unknown cones
                    if label < 0 or label == 3:
                        continue
                    
                    # Categorize by label
                    if label == 0:  # Blue cone (left boundary)
                        self.left_cones.append((x, y))
                        valid_detections += 1
                        
                    elif label == 1:  # Yellow cone (right boundary)
                        self.right_cones.append((x, y))
                        valid_detections += 1
                        
                    elif label == 2:  # Orange cone (special marker)
                        self.orange_cones.append((x, y))
                        # Decide how to handle orange cones based on your track rules
                        # Option A: Treat as obstacles (add to both boundaries)
                        # Option B: Ignore them
                        # Option C: Special handling for start/finish line
                        # For now, storing separately for flexibility
                        valid_detections += 1
                    
                except (ValueError, IndexError) as e:
                    self.get_logger().warning(f'Failed to parse cone line: "{line}" - {e}')
                    continue
        
        # Update statistics
        self.detection_count += 1
        current_time = self.get_clock().now()
        time_diff = (current_time - self.last_detection_time).nanoseconds / 1e9
        
        # Always log basic stats, detailed every 10 detections
        if self.detection_count % 10 == 0 or time_diff > 2.0:
            self.get_logger().info(
                f'✅ YOLO Detections #{self.detection_count}: '
                f'{len(self.left_cones)} blue, '
                f'{len(self.right_cones)} yellow, '
                f'{len(self.orange_cones)} orange | '
                f'Valid: {valid_detections} cones'
            )
            self.last_detection_time = current_time
        
        # Log first few detections in detail for verification
        if self.detection_count <= 3:
            self.get_logger().info(
                f'🔍 First detections - Blue cones: {self.left_cones[:3]}, '
                f'Yellow cones: {self.right_cones[:3]}'
            )
        
        # Update centerline when we have sufficient cone data
        if len(self.left_cones) > 0 or len(self.right_cones) > 0:
            self.generate_centerline()
            
            # Run TUM optimization if available and enough cones
            if self.tum_optimizer and len(self.left_cones) >= 5 and len(self.right_cones) >= 5:
                self.optimize_trajectory_tum()
    
    def optimize_trajectory_tum(self):
        """Use TUM optimizer to generate optimal racing line"""
        try:
            self.get_logger().info(
                f'🚀 Starting TUM optimization with {len(self.left_cones)} blue, '
                f'{len(self.right_cones)} yellow cones'
            )
            
            # Convert cones to TUM reference track format
            reftrack = self.tum_optimizer.cones_to_reftrack(
                self.left_cones,
                self.right_cones,
                min_points=5
            )
            
            if reftrack is not None:
                self.get_logger().info(f'📊 Generated reftrack with {len(reftrack)} points')
                
                # Run optimization (use 'mincurv' for minimum curvature)
                # Options: 'shortest_path', 'mincurv', or 'mintime'
                trajectory = self.tum_optimizer.optimize_trajectory(
                    reftrack,
                    opt_type='mincurv'
                )
                
                if trajectory is not None:
                    self.optimized_trajectory = trajectory
                    # Calculate some statistics
                    path_length = sum(
                        np.hypot(trajectory[i+1, 0] - trajectory[i, 0],
                                trajectory[i+1, 1] - trajectory[i, 1])
                        for i in range(len(trajectory) - 1)
                    )
                    max_curvature = np.max(np.abs(trajectory[:, 3]))
                    avg_velocity = np.mean(trajectory[:, 4])
                    
                    self.get_logger().info(
                        f'🏁 TUM optimization SUCCESS:\n'
                        f'  - Waypoints: {len(trajectory)}\n'
                        f'  - Path length: {path_length:.2f}m\n'
                        f'  - Max curvature: {max_curvature:.4f} rad/m\n'
                        f'  - Avg velocity: {avg_velocity:.2f} m/s'
                    )
                else:
                    self.get_logger().warning('❌ TUM optimization returned None, using simple centerline')
            else:
                self.get_logger().warning('❌ Failed to create reftrack, using simple centerline')
                    
        except Exception as e:
            self.get_logger().error(f'❌ TUM optimization error: {e}')
            import traceback
            self.get_logger().error(f'Traceback: {traceback.format_exc()}')
            self.optimized_trajectory = None
    
    def pose_callback(self, msg):
        """Update current vehicle pose"""
        self.current_pose = (
            msg.pose.position.x,
            msg.pose.position.y
        )
        self.get_logger().debug(f'Pose updated: {self.current_pose}')
    
    def generate_centerline(self):
        """
        Generate centerline from detected cones
        Implement your centerline generation algorithm here
        """
        # Basic implementation: average of left and right cones
        if not self.left_cones and not self.right_cones:
            self.centerline = []
            return
        
        # Example: Simple midpoint calculation
        # You should replace this with your actual algorithm
        centerline_points = []
        
        # If we have both left and right cones, create midpoints
        if self.left_cones and self.right_cones:
            # Sort cones by x-coordinate (assuming forward direction)
            left_sorted = sorted(self.left_cones, key=lambda p: p[0])
            right_sorted = sorted(self.right_cones, key=lambda p: p[0])
            
            # Simple pairing: match cones by x-coordinate
            for left_cone in left_sorted:
                # Find closest right cone
                closest_right = min(right_sorted, 
                                  key=lambda r: abs(r[0] - left_cone[0]))
                
                # Calculate midpoint
                mid_x = (left_cone[0] + closest_right[0]) / 2
                mid_y = (left_cone[1] + closest_right[1]) / 2
                centerline_points.append((mid_x, mid_y))
        
        # If we only have one side, offset from that side
        elif self.left_cones:
            # Assume track width and offset right
            centerline_points = [(x + 1.5, y) for x, y in self.left_cones]
        elif self.right_cones:
            # Assume track width and offset left
            centerline_points = [(x - 1.5, y) for x, y in self.right_cones]
        
        self.centerline = centerline_points
        
        # Log centerline generation
        if len(centerline_points) > 0:
            self.get_logger().debug(f'Generated centerline with {len(centerline_points)} points')
    
    def main_loop(self):
        """
        Main planning loop - called at 5 Hz
        Publishes optimized trajectory or simple centerline
        """
        # Use TUM optimized trajectory if available, otherwise use simple centerline
        path_points = []
        
        if self.optimized_trajectory is not None and len(self.optimized_trajectory) > 0:
            # Use TUM optimized trajectory: [x, y, heading, curvature, velocity]
            path_points = [(pt[0], pt[1]) for pt in self.optimized_trajectory]
            self.get_logger().debug(f'Using TUM optimized trajectory with {len(path_points)} points')
        elif self.centerline:
            # Fallback to simple centerline
            path_points = self.centerline
            self.get_logger().debug(f'Using simple centerline with {len(path_points)} points')
        else:
            return
        
        # Publish the planned path
        path_msg = Path()
        path_msg.header.stamp = self.get_clock().now().to_msg()
        path_msg.header.frame_id = 'map'
        
        for x, y in path_points:
            pose = PathPose()
            pose.header.frame_id = 'map'
            pose.pose.position.x = float(x)
            pose.pose.position.y = float(y)
            pose.pose.position.z = 0.0
            pose.pose.orientation.w = 1.0  # Neutral orientation
            path_msg.poses.append(pose)
        
        if len(path_msg.poses) > 0:
            self.path_pub.publish(path_msg)
            self.get_logger().debug(f'Published path with {len(path_msg.poses)} poses')

    
    def get_all_obstacles(self, cone_radius: float = 0.3) -> List[Tuple[float, float, float]]:
        """
        Get all cones as obstacles for RRT* or other planning algorithms
        Returns list of (x, y, radius) tuples
        """
        obstacles = []
        
        for x, y in self.left_cones:
            obstacles.append((x, y, cone_radius))
        
        for x, y in self.right_cones:
            obstacles.append((x, y, cone_radius))
        
        for x, y in self.orange_cones:
            obstacles.append((x, y, cone_radius))
        
        return obstacles

def main(args=None):
    rclpy.init(args=args)
    node = PathPlannerNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down Path Planner Node')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()