#!/usr/bin/env python3
"""
Integration example showing how to use RRT* with live perception data
This demonstrates integration with the existing cone detection system
"""

import sys
import os
sys.path.append('/home/dom/cardiff-autonomous-racing/Path Planning')

import rrt_star
from rrt_star import rrt_star, plot
import matplotlib.pyplot as plt


def parse_cone_data(cone_data_string: str):
    """
    Parse cone data from ROS message format
    Returns: (left_cones, right_cones, obstacles)
    """
    left_cones = []
    right_cones = []
    
    if not cone_data_string:
        return left_cones, right_cones, []
    
    lines = cone_data_string.strip().split('\n')
    for line in lines:
        parts = line.strip().split(',')
        if len(parts) >= 4:
            try:
                x, y, z, colour = map(float, parts[:4])
                
                # Based on your test_cone_publisher.py:
                # 0 = orange (right), 1 = blue (left)
                if int(colour) == 0:  # Orange/right cones
                    right_cones.append((x, y))
                elif int(colour) == 1:  # Blue/left cones  
                    left_cones.append((x, y))
            except ValueError:
                continue
    
    # Convert to obstacles with cone radius
    cone_radius = 0.3
    obstacles = []
    for cone in left_cones + right_cones:
        obstacles.append((cone[0], cone[1], cone_radius))
    
    return left_cones, right_cones, obstacles


def generate_centerline(left_cones, right_cones):
    """Generate centerline from left and right cones"""
    if not left_cones or not right_cones:
        return []
    
    centerline = []
    for left_cone in left_cones:
        # Find nearest right cone
        min_dist = float('inf')
        nearest_right = None
        for right_cone in right_cones:
            dist = ((left_cone[0] - right_cone[0])**2 + (left_cone[1] - right_cone[1])**2)**0.5
            if dist < min_dist:
                min_dist = dist
                nearest_right = right_cone
        
        if nearest_right:
            center_x = (left_cone[0] + nearest_right[0]) / 2
            center_y = (left_cone[1] + nearest_right[1]) / 2
            centerline.append((center_x, center_y))
    
    return centerline


def plan_path_with_perception(current_pose, cone_data_string, goal_offset=20.0):
    """
    Main function to plan path using perception data
    
    Args:
        current_pose: (x, y) current vehicle position
        cone_data_string: String with cone data in format "x,y,z,color\n..."
        goal_offset: Distance ahead to set as goal
    """
    
    # Parse cone data
    left_cones, right_cones, obstacles = parse_cone_data(cone_data_string)
    centerline = generate_centerline(left_cones, right_cones)
    
    # Set goal (simple: go forward by goal_offset)
    goal = (current_pose[0] + goal_offset, current_pose[1])
    
    # If we have centerline, use it to set a better goal
    if centerline:
        # Find centerline point closest to goal_offset distance
        for point in centerline:
            if point[0] >= current_pose[0] + goal_offset:
                goal = point
                break
    
    print(f"Current pose: {current_pose}")
    print(f"Goal: {goal}")
    print(f"Found {len(left_cones)} left cones, {len(right_cones)} right cones")
    print(f"Total obstacles: {len(obstacles)}")
    
    # Plan path using RRT*
    result = rrt_star(
        start=current_pose,
        goal=goal,
        obstacles=obstacles,
        x_max=max(100, goal[0] + 10),
        y_max=50,
        max_iter=800,
        max_step=2.0,
        goal_sample_rate=0.1,
        radius=6.0
    )
    
    print(f"Planning result: {result.status}")
    if result.path:
        print(f"Path found with {len(result.path)} waypoints")
    
    # Visualize results
    cone_data = {
        'left_cones': left_cones,
        'right_cones': right_cones,
        'centerline': centerline
    }
    
    plot(
        path=result.path,
        obstacles=obstacles,
        start=current_pose,
        goal=goal,
        tree=result.tree,
        cone_data=cone_data,
        show_tree=False,  # Set to True to see RRT* tree
        x_max=max(100, goal[0] + 10),
        y_max=50
    )
    
    return result


if __name__ == "__main__":
    # Example 1: Using test data from your test_cone_publisher.py
    print("Example 1: Test data from cone publisher")
    current_pose = (0.0, 0.0)
    test_cone_data = "5.0,2.0,0.0,0\n10.0,2.5,0.0,0\n5.0,-2.0,0.0,1\n10.0,-2.5,0.0,1"
    
    result1 = plan_path_with_perception(current_pose, test_cone_data, goal_offset=15.0)
    
    # Example 2: More complex racing scenario
    print("\n" + "="*60)
    print("Example 2: Complex racing scenario")
    
    # Create a more complex cone layout
    complex_cone_data = """10.0,3.0,0.0,0
20.0,3.2,0.0,0
30.0,2.8,0.0,0
40.0,3.5,0.0,0
50.0,3.0,0.0,0
60.0,2.5,0.0,0
70.0,3.2,0.0,0
10.0,-3.0,0.0,1
20.0,-3.2,0.0,1
30.0,-2.8,0.0,1
40.0,-3.5,0.0,1
50.0,-3.0,0.0,1
60.0,-2.5,0.0,1
70.0,-3.2,0.0,1"""
    
    current_pose2 = (5.0, 0.0)
    result2 = plan_path_with_perception(current_pose2, complex_cone_data, goal_offset=50.0)
    
    # Example 3: Show how to use with actual ROS integration
    print("\n" + "="*60)
    print("Example 3: Integration with ROS (simulation)")
    print("In your ROS node, you would call this function in your main loop:")
    print("""
    def main_loop(self):
        # Get current pose from SLAM/odometry
        current_pose = self.current_pose
        
        # Get latest cone data from perception
        cone_data_string = self.latest_cone_data
        
        # Plan path
        result = plan_path_with_perception(current_pose, cone_data_string)
        
        # Publish path to control system
        if result.path:
            self.publish_path(result.path)
    """)
