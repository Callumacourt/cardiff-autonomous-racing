#!/usr/bin/env python3
"""
Enhanced visualization for RRT* path planning with perception obstacles
Demonstrates how to visualize paths with different types of obstacles and cone data
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from typing import List, Tuple, Optional
import rrt_star
from rrt_star import Node, rrt_star, PathResult, PathStatus


def plot_with_perception_obstacles(
    path: Optional[List[Tuple[float, float]]], 
    obstacles: List[Tuple[float, float, float]],
    start: Tuple[float, float], 
    goal: Tuple[float, float], 
    tree: Optional[List[Node]] = None,
    left_cones: Optional[List[Tuple[float, float]]] = None,
    right_cones: Optional[List[Tuple[float, float]]] = None,
    centerline: Optional[List[Tuple[float, float]]] = None,
    x_max: float = 100, 
    y_max: float = 100,
    show_tree: bool = True,
    title: str = "RRT* Path Planning with Perception Data"
) -> None:
    """
    Enhanced plotting function that shows:
    - RRT* tree (optional)
    - Planned path
    - Perception obstacles (cones)
    - Different cone types (left/right)
    - Centerline reference
    """
    
    plt.figure(figsize=(12, 10))
    
    # Set the plot limits with some padding
    plt.xlim(-5, x_max + 5)
    plt.ylim(-20, y_max + 5)
    
    # Plot obstacles as red circles
    for ox, oy, radius in obstacles:
        circle = plt.Circle((ox, oy), radius, color='red', alpha=0.6, label='Obstacles' if obstacles.index((ox, oy, radius)) == 0 else "")
        plt.gca().add_patch(circle)
    
    # Plot left cones (blue - typically left side of track)
    if left_cones:
        left_x = [cone[0] for cone in left_cones]
        left_y = [cone[1] for cone in left_cones]
        plt.scatter(left_x, left_y, c='blue', marker='s', s=80, alpha=0.8, label='Left Cones (Blue)', edgecolors='darkblue')
    
    # Plot right cones (yellow/orange - typically right side of track)
    if right_cones:
        right_x = [cone[0] for cone in right_cones]
        right_y = [cone[1] for cone in right_cones]
        plt.scatter(right_x, right_y, c='orange', marker='s', s=80, alpha=0.8, label='Right Cones (Orange)', edgecolors='darkorange')
    
    # Plot centerline reference
    if centerline:
        center_x = [point[0] for point in centerline]
        center_y = [point[1] for point in centerline]
        plt.plot(center_x, center_y, '--', color='gray', linewidth=2, alpha=0.7, label='Centerline Reference')
        plt.scatter(center_x, center_y, c='gray', marker='x', s=40, alpha=0.7)
    
    # Plot the RRT* tree if provided and requested
    if tree and show_tree:
        tree_plotted = False
        for node in tree:
            if node.parent:
                plt.plot([node.x, node.parent.x], [node.y, node.parent.y], 'c-', alpha=0.3, linewidth=0.5)
                if not tree_plotted:
                    plt.plot([node.x, node.parent.x], [node.y, node.parent.y], 'c-', alpha=0.3, linewidth=0.5, label='RRT* Tree')
                    tree_plotted = True
    
    # Plot the planned path if found
    if path:
        path_x = [x for x, y in path]
        path_y = [y for x, y in path]
        plt.plot(path_x, path_y, '-g', linewidth=3, label='Planned Path', zorder=5)
        plt.scatter(path_x, path_y, c='green', marker='o', s=30, zorder=6, alpha=0.8)
        
        # Add arrows to show direction
        for i in range(0, len(path) - 1, max(1, len(path) // 10)):
            dx = path[i+1][0] - path[i][0]
            dy = path[i+1][1] - path[i][1]
            plt.arrow(path[i][0], path[i][1], dx*0.5, dy*0.5, 
                     head_width=1, head_length=0.5, fc='darkgreen', ec='darkgreen', alpha=0.7)
    else:
        plt.text(x_max/2, y_max/2, "No path found", fontsize=16, ha='center', 
                bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
    
    # Plot start and goal with distinct markers
    plt.scatter(start[0], start[1], c='blue', marker='o', s=150, label='Start', 
               edgecolors='darkblue', linewidth=2, zorder=10)
    plt.scatter(goal[0], goal[1], c='purple', marker='*', s=200, label='Goal', 
               edgecolors='darkred', linewidth=2, zorder=10)
    
    # Add coordinate text for start and goal
    plt.annotate(f'Start\n({start[0]:.1f}, {start[1]:.1f})', 
                xy=start, xytext=(start[0]+2, start[1]+2),
                fontsize=10, ha='left')
    plt.annotate(f'Goal\n({goal[0]:.1f}, {goal[1]:.1f})', 
                xy=goal, xytext=(goal[0]+2, goal[1]+2),
                fontsize=10, ha='left')
    
    # Customize the plot
    plt.grid(True, alpha=0.3)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlabel('X Position (m)', fontsize=12)
    plt.ylabel('Y Position (m)', fontsize=12)
    plt.axis('equal')
    plt.tight_layout()
    plt.show()


def example_racing_scenario():
    """
    Example showing how to use the visualization with racing cone data
    """
    
    # Define racing track with cones
    left_cones = [
        (10, -2), (20, -2.5), (30, -3), (40, -2.8), (50, -2.2),
        (60, -1.8), (70, -2.5), (80, -3.2), (90, -2.9)
    ]
    
    right_cones = [
        (10, 2), (20, 2.5), (30, 3), (40, 2.8), (50, 2.2),
        (60, 1.8), (70, 2.5), (80, 3.2), (90, 2.9)
    ]
    
    # Generate centerline
    centerline = []
    for i in range(min(len(left_cones), len(right_cones))):
        center_x = (left_cones[i][0] + right_cones[i][0]) / 2
        center_y = (left_cones[i][1] + right_cones[i][1]) / 2
        centerline.append((center_x, center_y))
    
    # Convert cones to obstacles (with radius)
    cone_radius = 0.3
    obstacles = []
    for cone in left_cones + right_cones:
        obstacles.append((cone[0], cone[1], cone_radius))
    
    # Add some additional obstacles (debris, barriers, etc.)
    additional_obstacles = [
        (35, 0.5, 1.0),  # Debris
        (65, -0.8, 0.8),  # Barrier
    ]
    obstacles.extend(additional_obstacles)
    
    # Define start and goal
    start = (5.0, 0.0)
    goal = (95.0, 0.0)
    
    # Run RRT* planning
    print("Running RRT* path planning...")
    result = rrt_star(
        start=start,
        goal=goal,
        obstacles=obstacles,
        x_max=100,
        y_max=20,
        max_iter=1000,
        max_step=3.0,
        goal_sample_rate=0.1,
        radius=8.0
    )
    
    # Display results
    print(f"Planning status: {result.status}")
    if result.path:
        print(f"Path length: {len(result.path)} waypoints")
        print(f"Tree size: {len(result.tree)} nodes")
    
    # Visualize the results
    plot_with_perception_obstacles(
        path=result.path,
        obstacles=obstacles,
        start=start,
        goal=goal,
        tree=result.tree,
        left_cones=left_cones,
        right_cones=right_cones,
        centerline=centerline,
        x_max=100,
        y_max=20,
        show_tree=True,
        title="RRT* Path Planning - Racing Scenario"
    )


def example_with_ros_data(cone_data_string: str, current_pose: Tuple[float, float]):
    """
    Example showing how to use cone data from ROS messages
    
    Args:
        cone_data_string: String in format "x,y,z,color,confidence\n..." 
        current_pose: Current vehicle position (x, y)
    """
    
    left_cones = []
    right_cones = []
    
    # Parse cone data (similar to integration.py)
    if cone_data_string:
        lines = cone_data_string.strip().split('\n')
        for line in lines:
            parts = line.strip().split(',')
            if len(parts) >= 4:
                x, y, z, colour = map(float, parts[:4])
                
                # 0 = blue (left), 1 = yellow/orange (right)
                if int(colour) == 0:
                    left_cones.append((x, y))
                elif int(colour) == 1:
                    right_cones.append((x, y))
    
    # Convert to obstacles
    cone_radius = 0.3
    obstacles = []
    for cone in left_cones + right_cones:
        obstacles.append((cone[0], cone[1], cone_radius))
    
    # Define goal (example: 20 meters ahead)
    goal = (current_pose[0] + 20, current_pose[1])
    
    # Run planning
    result = rrt_star(
        start=current_pose,
        goal=goal,
        obstacles=obstacles,
        x_max=current_pose[0] + 30,
        y_max=20,
        max_iter=500,
        max_step=2.0,
        goal_sample_rate=0.15
    )
    
    # Visualize
    plot_with_perception_obstacles(
        path=result.path,
        obstacles=obstacles,
        start=current_pose,
        goal=goal,
        tree=result.tree,
        left_cones=left_cones,
        right_cones=right_cones,
        show_tree=False,  # Don't show tree for cleaner view
        title="RRT* with Live Perception Data"
    )
    
    return result


if __name__ == "__main__":
    # Run the racing scenario example
    example_racing_scenario()
    
    # Example with simulated ROS data
    print("\n" + "="*50)
    print("Running example with simulated ROS cone data...")
    
    # Simulate cone data string (format: x,y,z,color,confidence)
    sample_cone_data = """10.0,2.0,0.0,1,0.9
15.0,2.2,0.0,1,0.8
20.0,1.8,0.0,1,0.9
10.0,-2.0,0.0,0,0.9
15.0,-2.2,0.0,0,0.8
20.0,-1.8,0.0,0,0.9"""
    
    current_car_pose = (5.0, 0.0)
    result = example_with_ros_data(sample_cone_data, current_car_pose)
