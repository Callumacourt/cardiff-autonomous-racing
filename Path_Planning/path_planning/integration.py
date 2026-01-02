#!/usr/bin/env python3
"""
Path Planning Integration Node
Subscribes to YOLO cone detections and implements path planning
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped as PathPose
import numpy as np
from typing import List, Tuple

class PathPlannerNode(Node):
    def __init__(self):
        super().__init__('path_planner')
        
        # Current CAR coordinates - updates due to pose callback
        self.current_pose = (0.0, 0.0)
        self.left_cones = []   # Blue cones (class_id=0, label=0)
        self.right_cones = []  # Yellow cones (class_id=4, label=1)
        self.orange_cones = [] # Orange cones (class_id=1,2, label=2)
        self.centerline = []
        self.last_goal_idx = 0
        
        # Subscribe to car pose (adjust topic name as needed)
        self.create_subscription(PoseStamped, '/car_pose', self.pose_callback, 10)
        
        # Subscribe to YOLO cone detections
        self.create_subscription(String, '/detected_cones', self.yolo_cones_callback, 10)
        
        # Publisher for the planned path
        self.path_pub = self.create_publisher(Path, '/planned_path', 10)
        
        # Timer for main planning loop (5 Hz)
        self.timer = self.create_timer(0.2, self.main_loop)
        
        # Statistics
        self.detection_count = 0
        self.last_detection_time = self.get_clock().now()
        
        self.get_logger().info('Path Planner Node initialized')
        self.get_logger().info('Subscribed to /detected_cones from YOLO')
    
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
        # Clear previous detections for fresh update
        self.left_cones = []
        self.right_cones = []
        self.orange_cones = []
        
        if not msg.data.strip():
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
        
        # Log every 50 detections or every 5 seconds
        if self.detection_count % 50 == 0 or time_diff > 5.0:
            self.get_logger().info(
                f'YOLO Detections #{self.detection_count}: '
                f'{len(self.left_cones)} blue, '
                f'{len(self.right_cones)} yellow, '
                f'{len(self.orange_cones)} orange cones'
            )
            self.last_detection_time = current_time
        
        # Update centerline when we have sufficient cone data
        if len(self.left_cones) > 0 or len(self.right_cones) > 0:
            self.generate_centerline()
    
    def pose_callback(self, msg):
        """Update current vehicle pose"""
        self.current_pose = (
            msg.pose.position.x,
            msg.pose.position.y
        )
    
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
        Implement your path planning algorithm here
        """
        if not self.centerline:
            return
        
        # TODO: Implement your path planning algorithm
        # Example: Pure pursuit, RRT*, MPC, etc.
        
        # Publish the planned path
        path_msg = Path()
        path_msg.header.stamp = self.get_clock().now().to_msg()
        path_msg.header.frame_id = 'map'  # Adjust frame_id as needed
        
        for point in self.centerline:
            pose = PathPose()
            pose.header = path_msg.header
            pose.pose.position.x = point[0]
            pose.pose.position.y = point[1]
            pose.pose.position.z = 0.0
            pose.pose.orientation.w = 1.0  # Neutral orientation
            path_msg.poses.append(pose)
        
        if len(path_msg.poses) > 0:
            self.path_pub.publish(path_msg)
    
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