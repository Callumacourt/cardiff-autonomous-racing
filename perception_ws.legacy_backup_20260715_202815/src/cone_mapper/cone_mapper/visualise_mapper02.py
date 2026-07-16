#!/usr/bin/env python3
"""
Improved Real-time 2D visualization with better zoom and clarity
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from nav_msgs.msg import Odometry, Path
from geometry_msgs.msg import PoseStamped

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from collections import deque
import threading
import time

class ConeMapVisualizer(Node):
    """Improved cone map visualizer with better zoom control"""
    
    def __init__(self):
        super().__init__('cone_map_visualizer')
        
        # Data storage
        self.local_cones = {'blue': [], 'yellow': [], 'orange': []}
        self.global_cones = {'blue': [], 'yellow': [], 'orange': []}
        self.vehicle_position = [0.0, 0.0]
        self.vehicle_heading = 0.0
        self.vehicle_path = deque(maxlen=50)  # Reduced path length for clarity
        self.track_boundaries = []
        self.centerline = []
        
        # Thread lock for data safety
        self.data_lock = threading.Lock()
        
        # Visualization parameters
        self.zoom_level = 15.0  # Default zoom (meters around vehicle)
        self.auto_zoom = True
        
        # Subscriptions
        self.local_sub = self.create_subscription(
            String, '/cone_map/local', self.local_cone_callback, 10)
        self.global_sub = self.create_subscription(
            String, '/cone_map/global', self.global_cone_callback, 10)
        self.pose_sub = self.create_subscription(
            Odometry, '/ground_truth/odom', self.pose_callback, 10)
        self.boundary_sub = self.create_subscription(
            Path, '/track/boundaries', self.boundary_callback, 10)
        self.centerline_sub = self.create_subscription(
            Path, '/track/centerline', self.centerline_callback, 10)
        
        # Statistics
        self.stats = {
            'local_cone_count': 0,
            'global_cone_count': 0,
            'last_update': time.time()
        }
        
        self.get_logger().info('Improved Cone Map Visualizer initialized')
    
    def local_cone_callback(self, msg):
        """Handle local cone map updates"""
        with self.data_lock:
            self.local_cones = {'blue': [], 'yellow': [], 'orange': []}
            
            if not msg.data.strip():
                return
                
            lines = msg.data.strip().split('\n')
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) >= 4:
                    try:
                        x, y, z, color = float(parts[0]), float(parts[1]), float(parts[2]), int(parts[3])
                        confidence = float(parts[4]) if len(parts) > 4 else 1.0
                        
                        color_name = {0: 'blue', 1: 'yellow', 2: 'orange'}.get(color, 'blue')
                        self.local_cones[color_name].append({'x': x, 'y': y, 'confidence': confidence})
                    except (ValueError, IndexError):
                        continue
            
            self.stats['local_cone_count'] = sum(len(cones) for cones in self.local_cones.values())
            self.stats['last_update'] = time.time()
    
    def global_cone_callback(self, msg):
        """Handle global cone map updates"""
        with self.data_lock:
            self.global_cones = {'blue': [], 'yellow': [], 'orange': []}
            
            if not msg.data.strip():
                return
                
            lines = msg.data.strip().split('\n')
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) >= 4:
                    try:
                        x, y, z, color = float(parts[0]), float(parts[1]), float(parts[2]), int(parts[3])
                        
                        color_name = {0: 'blue', 1: 'yellow', 2: 'orange'}.get(color, 'blue')
                        self.global_cones[color_name].append({'x': x, 'y': y})
                    except (ValueError, IndexError):
                        continue
            
            self.stats['global_cone_count'] = sum(len(cones) for cones in self.global_cones.values())
    
    def pose_callback(self, msg):
        """Handle vehicle pose updates"""
        with self.data_lock:
            pos = msg.pose.pose.position
            ori = msg.pose.pose.orientation
            
            self.vehicle_position = [pos.x, pos.y]
            
            # Calculate heading from quaternion (yaw only)
            siny_cosp = 2 * (ori.w * ori.z + ori.x * ori.y)
            cosy_cosp = 1 - 2 * (ori.y * ori.y + ori.z * ori.z)
            self.vehicle_heading = np.arctan2(siny_cosp, cosy_cosp)
            
            # Add to path
            self.vehicle_path.append([pos.x, pos.y])
    
    def boundary_callback(self, msg):
        """Handle track boundary updates"""
        with self.data_lock:
            self.track_boundaries = []
            for pose in msg.poses:
                self.track_boundaries.append([pose.pose.position.x, pose.pose.position.y])
    
    def centerline_callback(self, msg):
        """Handle centerline updates"""
        with self.data_lock:
            self.centerline = []
            for pose in msg.poses:
                self.centerline.append([pose.pose.position.x, pose.pose.position.y])
    
    def get_plot_data(self):
        """Thread-safe data retrieval for plotting"""
        with self.data_lock:
            return {
                'local_cones': {k: v.copy() for k, v in self.local_cones.items()},
                'global_cones': {k: v.copy() for k, v in self.global_cones.items()},
                'vehicle_position': self.vehicle_position.copy(),
                'vehicle_heading': self.vehicle_heading,
                'vehicle_path': list(self.vehicle_path),
                'track_boundaries': self.track_boundaries.copy(),
                'centerline': self.centerline.copy(),
                'stats': self.stats.copy()
            }

def create_realtime_plot():
    """Create and run real-time plotting with improved visualization"""
    
    # Initialize ROS2
    rclpy.init()
    visualizer = ConeMapVisualizer()
    
    # Start ROS2 in separate thread
    ros_thread = threading.Thread(target=lambda: rclpy.spin(visualizer))
    ros_thread.daemon = True
    ros_thread.start()
    
    # Set up matplotlib with improved styling
    plt.style.use('dark_background')  # Better contrast
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3, linewidth=0.5)
    ax.set_xlabel('X (m)', fontsize=12)
    ax.set_ylabel('Y (m)', fontsize=12)
    ax.set_title('Real-time Cone Map Visualization', fontsize=14, fontweight='bold')
    
    def update_plot(frame):
        # Get latest data
        data = visualizer.get_plot_data()
        
        # Clear previous plots
        ax.clear()
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3, linewidth=0.5)
        ax.set_xlabel('X (m)', fontsize=12)
        ax.set_ylabel('Y (m)', fontsize=12)
        
        # Update title with stats and timestamp
        stats = data['stats']
        title = (f'Cone Map - Local: {stats["local_cone_count"]} | '
                f'Global: {stats["global_cone_count"]} | '
                f'{time.strftime("%H:%M:%S")}')
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        # Get vehicle position for centering
        vx, vy = data['vehicle_position'] if data['vehicle_position'] else [0, 0]
        
        # Plot global cones first (background layer)
        for color, cones in data['global_cones'].items():
            if cones:
                x_coords = [cone['x'] for cone in cones]
                y_coords = [cone['y'] for cone in cones]
                
                # Use different markers for global vs local
                ax.scatter(x_coords, y_coords, c=color, s=120, alpha=0.9, 
                          marker='o', label=f'Global {color}', 
                          edgecolors='white', linewidth=2)
        
        # Plot local cones (foreground layer)
        local_cone_count = 0
        for color, cones in data['local_cones'].items():
            if cones:
                x_coords = [cone['x'] for cone in cones]
                y_coords = [cone['y'] for cone in cones]
                confidences = [cone['confidence'] for cone in cones]
                
                # Create size array based on confidence
                sizes = [30 + conf * 50 for conf in confidences]
                
                # Plot with varying size and alpha based on confidence
                scatter = ax.scatter(x_coords, y_coords, c=color, s=sizes, 
                                   alpha=0.8, marker='^', 
                                   label=f'Local {color}', 
                                   edgecolors='gray', linewidth=1)
                
                # Add confidence text for high-confidence cones
                for x, y, conf in zip(x_coords, y_coords, confidences):
                    if conf > 0.7:  # Only show text for high confidence
                        ax.annotate(f'{conf:.1f}', (x, y), 
                                  xytext=(5, 5), textcoords='offset points',
                                  fontsize=8, alpha=0.8, color='white')
                
                local_cone_count += len(cones)
        
        # Plot vehicle position and heading
        if data['vehicle_position']:
            # Vehicle position (larger, more visible)
            ax.scatter(vx, vy, c='red', s=300, marker='s', 
                      label='Vehicle', edgecolors='white', linewidth=3, zorder=10)
            
            # Vehicle heading arrow (longer, more visible)
            heading = data['vehicle_heading']
            arrow_length = 3.0
            dx = arrow_length * np.cos(heading)
            dy = arrow_length * np.sin(heading)
            ax.arrow(vx, vy, dx, dy, head_width=0.8, head_length=0.5, 
                    fc='red', ec='white', linewidth=3, zorder=10)
            
            # Add coordinate text
            ax.text(vx, vy - 2, f'({vx:.1f}, {vy:.1f})', 
                   ha='center', va='top', fontsize=10, 
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='red', alpha=0.7))
        
        # Plot vehicle path
        if len(data['vehicle_path']) > 1:
            path_array = np.array(data['vehicle_path'])
            ax.plot(path_array[:, 0], path_array[:, 1], 'r--', alpha=0.6, 
                   linewidth=2, label='Vehicle Path')
        
        # Plot track boundaries
        if data['track_boundaries']:
            boundary_array = np.array(data['track_boundaries'])
            ax.plot(boundary_array[:, 0], boundary_array[:, 1], 'k-', 
                   linewidth=4, label='Track Boundary', alpha=0.8)
        
        # Plot centerline
        if data['centerline']:
            centerline_array = np.array(data['centerline'])
            ax.plot(centerline_array[:, 0], centerline_array[:, 1], 'g-', 
                   linewidth=3, label='Centerline', alpha=0.9)
        
        # Smart zoom control
        if data['vehicle_position']:
            # Calculate zoom based on cone distribution
            all_cone_positions = []
            for color_cones in data['local_cones'].values():
                for cone in color_cones:
                    all_cone_positions.append([cone['x'], cone['y']])
            
            if all_cone_positions:
                cone_array = np.array(all_cone_positions)
                # Calculate distances from vehicle
                distances = np.sqrt((cone_array[:, 0] - vx)**2 + (cone_array[:, 1] - vy)**2)
                max_distance = np.max(distances) if len(distances) > 0 else 10
                
                # Adaptive zoom: show all cones plus some margin
                zoom_margin = min(20, max(8, max_distance * 1.3))
            else:
                zoom_margin = 12  # Default zoom when no cones
            
            # Set limits centered on vehicle
            ax.set_xlim(vx - zoom_margin, vx + zoom_margin)
            ax.set_ylim(vy - zoom_margin, vy + zoom_margin)
            
            # Add compass rose
            compass_x = vx + zoom_margin * 0.8
            compass_y = vy + zoom_margin * 0.8
            ax.arrow(compass_x, compass_y, 0, 2, head_width=0.5, head_length=0.3, 
                    fc='cyan', ec='cyan', alpha=0.7)
            ax.text(compass_x, compass_y + 3, 'N', ha='center', fontsize=12, 
                   color='cyan', fontweight='bold')
        else:
            # Default view when no vehicle position
            ax.set_xlim(-10, 10)
            ax.set_ylim(-10, 10)
        
        # Create legend with better positioning
        legend_elements = []
        if any(len(cones) > 0 for cones in data['global_cones'].values()):
            legend_elements.extend([plt.Line2D([0], [0], marker='o', color='w', 
                                             markerfacecolor=color, markersize=10, 
                                             markeredgecolor='white', markeredgewidth=2,
                                             label=f'Global {color}', linestyle='None')
                                  for color in ['blue', 'yellow', 'orange'] 
                                  if len(data['global_cones'][color]) > 0])
        
        if any(len(cones) > 0 for cones in data['local_cones'].values()):
            legend_elements.extend([plt.Line2D([0], [0], marker='^', color='w', 
                                             markerfacecolor=color, markersize=8, 
                                             markeredgecolor='gray',
                                             label=f'Local {color}', linestyle='None')
                                  for color in ['blue', 'yellow', 'orange'] 
                                  if len(data['local_cones'][color]) > 0])
        
        if data['vehicle_position']:
            legend_elements.append(plt.Line2D([0], [0], marker='s', color='w', 
                                            markerfacecolor='red', markersize=12,
                                            markeredgecolor='white', markeredgewidth=2,
                                            label='Vehicle', linestyle='None'))
        
        if legend_elements:
            ax.legend(handles=legend_elements, loc='upper left', 
                     bbox_to_anchor=(0.02, 0.98), fontsize=10, framealpha=0.9)
        
        # Add information panel
        info_text = []
        if data['vehicle_position']:
            info_text.append(f'Vehicle: ({vx:.1f}, {vy:.1f})')
            info_text.append(f'Heading: {np.degrees(data["vehicle_heading"]):.1f}°')
        
        info_text.append(f'Local cones: {local_cone_count}')
        info_text.append(f'Global cones: {sum(len(cones) for cones in data["global_cones"].values())}')
        
        # Position info panel
        ax.text(0.98, 0.02, '\n'.join(info_text), transform=ax.transAxes, 
               verticalalignment='bottom', horizontalalignment='right',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='black', alpha=0.8),
               fontsize=10, color='white')
    
    def on_key(event):
        """Handle keyboard events for zoom control"""
        if event.key == '+' or event.key == '=':
            visualizer.zoom_level *= 0.8  # Zoom in
        elif event.key == '-':
            visualizer.zoom_level *= 1.25  # Zoom out
        elif event.key == 'r':
            visualizer.auto_zoom = not visualizer.auto_zoom
            print(f"Auto zoom: {'ON' if visualizer.auto_zoom else 'OFF'}")
    
    # Connect keyboard events
    fig.canvas.mpl_connect('key_press_event', on_key)
    
    # Add instructions
    fig.text(0.02, 0.02, 'Controls: +/- to zoom, R to toggle auto-zoom', 
             fontsize=10, alpha=0.7)
    
    # Create animation with improved update rate
    ani = animation.FuncAnimation(fig, update_plot, interval=50, cache_frame_data=False)
    
    try:
        plt.show()
    except KeyboardInterrupt:
        pass
    finally:
        visualizer.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    create_realtime_plot()