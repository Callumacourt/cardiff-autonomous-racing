#!/usr/bin/env python3
"""
Comprehensive Path Planning GUI for Cardiff Autonomous Racing
Interactive testing and visualization tool for TUM trajectory optimization

Features:
- Interactive cone placement (left/right/orange)
- Multiple test scenarios (straight, curve, chicane, etc.)
- Real-time trajectory optimization
- Vehicle position simulation
- Statistics display
- Save/Load scenarios
- ROS 2 topic publishing (optional)
- Multiple optimization modes
"""

import sys
import os
import json
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List, Tuple, Optional
import threading

# Add path_planning to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import TUM wrapper
try:
    from path_planning.tum_wrapper import TUMTrajectoryOptimizer
    TUM_AVAILABLE = True
except ImportError:
    TUM_AVAILABLE = False
    print("Warning: TUM optimizer not available")

# Try to import ROS 2 (optional)
try:
    import rclpy
    from std_msgs.msg import String
    from geometry_msgs.msg import PoseStamped
    from nav_msgs.msg import Path as NavPath
    from geometry_msgs.msg import PoseStamped as PathPose
    ROS_AVAILABLE = True
except ImportError:
    ROS_AVAILABLE = False
    print("Warning: ROS 2 not available - publishing disabled")


class PathPlanningGUI:
    """Main GUI application for path planning visualization and testing"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Cardiff Autonomous Racing - Path Planning Tester")
        self.root.geometry("1600x900")
        
        # Data storage
        self.left_cones = []  # Blue cones
        self.right_cones = []  # Yellow cones
        self.orange_cones = []  # Orange cones
        self.car_position = (0.0, 0.0)
        self.car_heading = 0.0
        self.optimized_trajectory = None
        self.reftrack = None
        
        # GUI state
        self.placing_mode = None  # 'left', 'right', 'orange', 'car'
        self.selected_scenario = "Custom"
        self.optimization_running = False
        
        # TUM Optimizer
        self.optimizer = TUMTrajectoryOptimizer(
            vehicle_width=1.5,
            vehicle_length=2.5
        ) if TUM_AVAILABLE else None
        
        # ROS 2 Node (optional)
        self.ros_node = None
        self.ros_thread = None
        
        # Setup GUI
        self.setup_ui()
        self.setup_plot()
        self.update_plot()
        
        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_ui(self):
        """Setup the user interface"""
        
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Controls
        left_panel = ttk.Frame(main_frame, width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        left_panel.pack_propagate(False)
        
        # Right panel - Plot
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # === LEFT PANEL SECTIONS ===
        
        # 1. Scenario Selection
        scenario_frame = ttk.LabelFrame(left_panel, text="Test Scenarios", padding=10)
        scenario_frame.pack(fill=tk.X, pady=(0, 10))
        
        scenarios = [
            "Custom",
            "Straight Track",
            "Simple Curve",
            "S-Curve (Chicane)",
            "Hairpin Turn",
            "Oval Track",
            "Figure-8",
            "Slalom Course"
        ]
        
        self.scenario_var = tk.StringVar(value="Custom")
        for scenario in scenarios:
            ttk.Radiobutton(
                scenario_frame,
                text=scenario,
                variable=self.scenario_var,
                value=scenario,
                command=self.load_scenario
            ).pack(anchor=tk.W)
        
        # 2. Cone Placement
        placement_frame = ttk.LabelFrame(left_panel, text="Place Cones", padding=10)
        placement_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(
            placement_frame,
            text="🔵 Place Blue Cones (Left)",
            command=lambda: self.set_placing_mode('left')
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            placement_frame,
            text="🟡 Place Yellow Cones (Right)",
            command=lambda: self.set_placing_mode('right')
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            placement_frame,
            text="🟠 Place Orange Cones",
            command=lambda: self.set_placing_mode('orange')
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            placement_frame,
            text="🚗 Place Car",
            command=lambda: self.set_placing_mode('car')
        ).pack(fill=tk.X, pady=2)
        
        ttk.Separator(placement_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        ttk.Button(
            placement_frame,
            text="Clear All Cones",
            command=self.clear_all_cones
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            placement_frame,
            text="Clear Last Cone",
            command=self.clear_last_cone
        ).pack(fill=tk.X, pady=2)
        
        # 3. Optimization Settings
        opt_frame = ttk.LabelFrame(left_panel, text="Optimization", padding=10)
        opt_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(opt_frame, text="Optimization Type:").pack(anchor=tk.W)
        self.opt_type_var = tk.StringVar(value="mincurv")
        opt_types = [
            ("Minimum Curvature", "mincurv"),
            ("Shortest Path", "shortest_path")
        ]
        for text, value in opt_types:
            ttk.Radiobutton(
                opt_frame,
                text=text,
                variable=self.opt_type_var,
                value=value
            ).pack(anchor=tk.W)
        
        ttk.Separator(opt_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        ttk.Label(opt_frame, text="Vehicle Width (m):").pack(anchor=tk.W)
        self.vehicle_width_var = tk.StringVar(value="1.5")
        ttk.Entry(opt_frame, textvariable=self.vehicle_width_var, width=10).pack(anchor=tk.W)
        
        ttk.Separator(opt_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        self.optimize_button = ttk.Button(
            opt_frame,
            text="🚀 Run Optimization",
            command=self.run_optimization
        )
        self.optimize_button.pack(fill=tk.X, pady=5)
        
        self.status_label = ttk.Label(opt_frame, text="Ready", foreground="green")
        self.status_label.pack(fill=tk.X)
        
        # 4. Display Options
        display_frame = ttk.LabelFrame(left_panel, text="Display Options", padding=10)
        display_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.show_reftrack_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            display_frame,
            text="Show Reference Track",
            variable=self.show_reftrack_var,
            command=self.update_plot
        ).pack(anchor=tk.W)
        
        self.show_centerline_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            display_frame,
            text="Show Centerline",
            variable=self.show_centerline_var,
            command=self.update_plot
        ).pack(anchor=tk.W)
        
        self.show_trajectory_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            display_frame,
            text="Show Optimized Path",
            variable=self.show_trajectory_var,
            command=self.update_plot
        ).pack(anchor=tk.W)
        
        self.show_grid_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            display_frame,
            text="Show Grid",
            variable=self.show_grid_var,
            command=self.update_plot
        ).pack(anchor=tk.W)
        
        # 5. Statistics
        stats_frame = ttk.LabelFrame(left_panel, text="Statistics", padding=10)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.stats_text = tk.Text(stats_frame, height=8, width=30, font=("Courier", 9))
        self.stats_text.pack(fill=tk.BOTH)
        self.update_statistics()
        
        # 6. File Operations
        file_frame = ttk.LabelFrame(left_panel, text="File Operations", padding=10)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(
            file_frame,
            text="💾 Save Scenario",
            command=self.save_scenario
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            file_frame,
            text="📂 Load Scenario",
            command=self.load_scenario_from_file
        ).pack(fill=tk.X, pady=2)
        
        ttk.Button(
            file_frame,
            text="📸 Export Plot",
            command=self.export_plot
        ).pack(fill=tk.X, pady=2)
        
        # 7. ROS 2 Integration (if available)
        if ROS_AVAILABLE:
            ros_frame = ttk.LabelFrame(left_panel, text="ROS 2 Integration", padding=10)
            ros_frame.pack(fill=tk.X, pady=(0, 10))
            
            self.ros_enabled_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(
                ros_frame,
                text="Enable ROS 2 Publishing",
                variable=self.ros_enabled_var,
                command=self.toggle_ros
            ).pack(anchor=tk.W)
            
            ttk.Button(
                ros_frame,
                text="📡 Publish Cones",
                command=self.publish_cones
            ).pack(fill=tk.X, pady=2)
            
            ttk.Button(
                ros_frame,
                text="📡 Publish Path",
                command=self.publish_path
            ).pack(fill=tk.X, pady=2)
        
        # === RIGHT PANEL - PLOT ===
        self.plot_frame = right_panel
    
    def setup_plot(self):
        """Setup matplotlib plot"""
        self.fig = Figure(figsize=(12, 8), dpi=100)
        self.ax = self.fig.add_subplot(111)
        
        self._colorbar = None   # track active colorbar so we can replace it

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.draw()
        
        # Toolbar
        toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        toolbar.update()
        
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Connect click event
        self.canvas.mpl_connect('button_press_event', self.on_plot_click)
    
    def update_plot(self):
        """Update the visualization"""
        # Remove stale colorbar before clearing axes, otherwise it orphans
        if self._colorbar is not None and self.optimized_trajectory is None:
            self._colorbar.remove()
            self._colorbar = None
        self.ax.clear()
        
        # Set limits
        x_min, x_max = -5, 50
        y_min, y_max = -15, 15
        
        # Adjust limits based on data
        all_x = []
        all_y = []
        
        for cones in [self.left_cones, self.right_cones, self.orange_cones]:
            if cones:
                all_x.extend([c[0] for c in cones])
                all_y.extend([c[1] for c in cones])
        
        if all_x:
            x_min = min(min(all_x) - 5, x_min)
            x_max = max(max(all_x) + 5, x_max)
            y_min = min(min(all_y) - 5, y_min)
            y_max = max(max(all_y) + 5, y_max)
        
        self.ax.set_xlim(x_min, x_max)
        self.ax.set_ylim(y_min, y_max)
        self.ax.set_aspect('equal', adjustable='box')
        
        # Grid
        if self.show_grid_var.get():
            self.ax.grid(True, alpha=0.3)
        
        # Plot cones
        if self.left_cones:
            left_x = [c[0] for c in self.left_cones]
            left_y = [c[1] for c in self.left_cones]
            self.ax.scatter(left_x, left_y, c='blue', marker='s', s=100, 
                          alpha=0.8, label='Left Cones (Blue)', edgecolors='darkblue', linewidth=2)
        
        if self.right_cones:
            right_x = [c[0] for c in self.right_cones]
            right_y = [c[1] for c in self.right_cones]
            self.ax.scatter(right_x, right_y, c='orange', marker='s', s=100, 
                          alpha=0.8, label='Right Cones (Yellow)', edgecolors='darkorange', linewidth=2)
        
        if self.orange_cones:
            orange_x = [c[0] for c in self.orange_cones]
            orange_y = [c[1] for c in self.orange_cones]
            self.ax.scatter(orange_x, orange_y, c='red', marker='s', s=100, 
                          alpha=0.8, label='Orange Cones', edgecolors='darkred', linewidth=2)
        
        # Plot reference track (centerline)
        if self.show_centerline_var.get() and self.reftrack is not None:
            center_x = self.reftrack[:, 0]
            center_y = self.reftrack[:, 1]
            self.ax.plot(center_x, center_y, '--', color='gray', linewidth=2, 
                       alpha=0.5, label='Reference Track')
        
        # Plot track boundaries (if reftrack available)
        if self.show_reftrack_var.get() and self.reftrack is not None:
            cx = self.reftrack[:, 0]
            cy = self.reftrack[:, 1]
            w_right = self.reftrack[:, 2]
            w_left  = self.reftrack[:, 3]

            # Perpendicular normals from the track tangent
            dx   = np.gradient(cx)
            dy   = np.gradient(cy)
            norm = np.maximum(np.sqrt(dx ** 2 + dy ** 2), 1e-8)
            nx   = -dy / norm   # left-pointing normal
            ny   =  dx / norm

            left_bound_x  = cx + w_left  * nx
            left_bound_y  = cy + w_left  * ny
            right_bound_x = cx - w_right * nx
            right_bound_y = cy - w_right * ny

            self.ax.plot(left_bound_x,  left_bound_y,  '-', color='blue',   linewidth=1.5, alpha=0.7, label='Left Boundary')
            self.ax.plot(right_bound_x, right_bound_y, '-', color='#FFD700', linewidth=1.5, alpha=0.7, label='Right Boundary')

            # Safety margins: dashed lines inset by half the vehicle width
            if self.optimizer:
                half_vw = self.optimizer.vehicle_width / 2
                self.ax.plot(cx + (w_left  - half_vw) * nx,
                             cy + (w_left  - half_vw) * ny,
                             '--', color='blue', linewidth=1, alpha=0.35, label='Safe Margin')
                self.ax.plot(cx - (w_right - half_vw) * nx,
                             cy - (w_right - half_vw) * ny,
                             '--', color='#FFD700', linewidth=1, alpha=0.35)

        # Plot optimized trajectory
        if self.show_trajectory_var.get() and self.optimized_trajectory is not None:
            traj_x = self.optimized_trajectory[:, 0]
            traj_y = self.optimized_trajectory[:, 1]
            self.ax.plot(traj_x, traj_y, '-', color='green', linewidth=3, 
                       label='Optimized Path', zorder=5)
            
            # Add velocity visualisation — remove any previous colorbar first
            if self.optimized_trajectory.shape[1] >= 5:
                if self._colorbar is not None:
                    self._colorbar.remove()
                    self._colorbar = None
                velocities = self.optimized_trajectory[:, 4]
                scatter = self.ax.scatter(traj_x, traj_y, c=velocities, cmap='plasma',
                                          s=30, zorder=6, alpha=0.8)
                self._colorbar = self.fig.colorbar(scatter, ax=self.ax,
                                                   label='Velocity (m/s)')
        
        # Plot car as a scaled rectangle with a direction arrow
        car_x, car_y = self.car_position
        half_l = (self.optimizer.vehicle_length if self.optimizer else 2.5) / 2
        half_w = (self.optimizer.vehicle_width  if self.optimizer else 1.5) / 2
        cos_h, sin_h = np.cos(self.car_heading), np.sin(self.car_heading)

        corners = np.array([[-half_l, -half_w],
                             [ half_l, -half_w],
                             [ half_l,  half_w],
                             [-half_l,  half_w],
                             [-half_l, -half_w]])
        rect_x = corners[:, 0] * cos_h - corners[:, 1] * sin_h + car_x
        rect_y = corners[:, 0] * sin_h + corners[:, 1] * cos_h + car_y

        self.ax.fill(rect_x, rect_y, color='purple', alpha=0.25, zorder=10)
        self.ax.plot(rect_x, rect_y, '-', color='purple', linewidth=2, zorder=10, label='Car')
        # Direction arrow from centre to nose
        self.ax.annotate(
            '', xy=(car_x + half_l * cos_h, car_y + half_l * sin_h),
            xytext=(car_x, car_y),
            arrowprops=dict(arrowstyle='->', color='darkviolet', lw=2),
            zorder=11
        )
        
        # Labels and title
        self.ax.set_xlabel('X Position (m)', fontsize=12)
        self.ax.set_ylabel('Y Position (m)', fontsize=12)
        self.ax.set_title(f'Path Planning Visualization - {self.selected_scenario}', fontsize=14, fontweight='bold')
        self.ax.legend(loc='upper right')
        
        # Mode indicator
        if self.placing_mode:
            mode_text = {
                'left': '[Blue] Placing Blue Cones (Click to place)',
                'right': '[Yellow] Placing Yellow Cones (Click to place)',
                'orange': '[Orange] Placing Orange Cones (Click to place)',
                'car': '[Car] Placing Car (Click to place)'
            }
            self.ax.text(0.5, 0.98, mode_text.get(self.placing_mode, ''), 
                       transform=self.ax.transAxes, ha='center', va='top',
                       bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8),
                       fontsize=11, fontweight='bold')
        
        self.canvas.draw()
    
    def on_plot_click(self, event):
        """Handle click on plot"""
        if event.inaxes != self.ax or not self.placing_mode:
            return
        
        x, y = event.xdata, event.ydata
        
        if self.placing_mode == 'left':
            self.left_cones.append((x, y))
        elif self.placing_mode == 'right':
            self.right_cones.append((x, y))
        elif self.placing_mode == 'orange':
            self.orange_cones.append((x, y))
        elif self.placing_mode == 'car':
            self.car_position = (x, y)
            self.placing_mode = None  # Only place one car
        
        self.update_plot()
        self.update_statistics()
    
    def set_placing_mode(self, mode):
        """Set cone placing mode"""
        self.placing_mode = mode
        self.update_plot()
    
    def clear_all_cones(self):
        """Clear all cones"""
        if messagebox.askyesno("Confirm", "Clear all cones?"):
            self.left_cones = []
            self.right_cones = []
            self.orange_cones = []
            self.optimized_trajectory = None
            self.reftrack = None
            self.update_plot()
            self.update_statistics()
    
    def clear_last_cone(self):
        """Clear the last placed cone"""
        if self.placing_mode == 'left' and self.left_cones:
            self.left_cones.pop()
        elif self.placing_mode == 'right' and self.right_cones:
            self.right_cones.pop()
        elif self.placing_mode == 'orange' and self.orange_cones:
            self.orange_cones.pop()
        
        self.update_plot()
        self.update_statistics()
    
    def run_optimization(self):
        """Run TUM trajectory optimization"""
        if not TUM_AVAILABLE:
            messagebox.showerror("Error", "TUM optimizer not available. Install trajectory-planning-helpers.")
            return

        if len(self.left_cones) < 5 or len(self.right_cones) < 5:
            messagebox.showwarning("Warning", "Need at least 5 blue and 5 yellow cones for optimization.")
            return
        
        self.status_label.config(text="Optimizing...", foreground="orange")
        self.optimize_button.config(state='disabled')
        self.root.update()
        
        # Run optimization in thread to avoid freezing GUI
        thread = threading.Thread(target=self._run_optimization_thread)
        thread.daemon = True
        thread.start()
    
    def _run_optimization_thread(self):
        """Thread worker for optimization"""
        try:
            # Update vehicle width
            try:
                vehicle_width = float(self.vehicle_width_var.get())
                self.optimizer.vehicle_width = vehicle_width
            except ValueError:
                pass
            
            # Generate reference track ordered from the car's current position
            self.reftrack = self.optimizer.cones_to_reftrack(
                self.left_cones,
                self.right_cones,
                min_points=5,
                start_pos=self.car_position
            )

            if self.reftrack is None:
                self.root.after(0, lambda: self.optimization_failed("Failed to generate reference track"))
                return

            # Optimize trajectory, starting from the car position
            opt_type = self.opt_type_var.get()
            self.optimized_trajectory = self.optimizer.optimize_trajectory(
                self.reftrack,
                opt_type=opt_type,
                start_pos=self.car_position
            )
            
            if self.optimized_trajectory is None:
                self.root.after(0, lambda: self.optimization_failed("Optimization failed"))
                return
            
            # Success
            self.root.after(0, self.optimization_success)
            
        except Exception as e:
            self.root.after(0, lambda: self.optimization_failed(str(e)))
    
    def optimization_success(self):
        """Handle successful optimization"""
        self.status_label.config(text="✓ Optimization Complete", foreground="green")
        self.optimize_button.config(state='normal')
        self.update_plot()
        self.update_statistics()
    
    def optimization_failed(self, message):
        """Handle failed optimization"""
        self.status_label.config(text=f"✗ Failed: {message}", foreground="red")
        self.optimize_button.config(state='normal')
        messagebox.showerror("Optimization Failed", message)
    
    def update_statistics(self):
        """Update statistics display"""
        self.stats_text.delete('1.0', tk.END)

        stats  = f"Left Cones:    {len(self.left_cones)}\n"
        stats += f"Right Cones:   {len(self.right_cones)}\n"
        stats += f"Orange Cones:  {len(self.orange_cones)}\n"
        stats += f"Total Cones:   {len(self.left_cones) + len(self.right_cones) + len(self.orange_cones)}\n"
        stats += f"\nCar Position:  ({self.car_position[0]:.1f}, {self.car_position[1]:.1f}) m\n"
        stats += f"Car Heading:   {np.degrees(self.car_heading):.1f} deg\n"

        # Track geometry from reftrack (available after optimisation)
        if self.reftrack is not None:
            cx, cy = self.reftrack[:, 0], self.reftrack[:, 1]
            track_len   = float(np.sum(np.hypot(np.diff(cx), np.diff(cy))))
            avg_width   = float(np.mean(self.reftrack[:, 2] + self.reftrack[:, 3]))
            stats += f"\n--- Track ---\n"
            stats += f"Length:        {track_len:.1f} m\n"
            stats += f"Avg Width:     {avg_width:.2f} m\n"

        if self.optimized_trajectory is not None:
            traj = self.optimized_trajectory
            dists      = np.hypot(np.diff(traj[:, 0]), np.diff(traj[:, 1]))
            path_len   = float(np.sum(dists))
            velocities = traj[:, 4]
            kappas     = np.abs(traj[:, 3])
            max_curv   = float(np.max(kappas))
            min_radius = 1.0 / max_curv if max_curv > 1e-6 else float('inf')
            avg_vel    = float(np.mean(velocities))
            min_vel    = float(np.min(velocities))
            max_vel    = float(np.max(velocities))
            est_time   = path_len / avg_vel if avg_vel > 0 else 0.0

            stats += f"\n--- Optimised Path ---\n"
            stats += f"Path Length:   {path_len:.1f} m\n"
            stats += f"Waypoints:     {len(traj)}\n"
            stats += f"Min Radius:    {min_radius:.2f} m\n"
            stats += f"Max Curvature: {max_curv:.4f} rad/m\n"
            stats += f"Velocity:      {min_vel:.1f} – {max_vel:.1f} m/s\n"
            stats += f"Avg Velocity:  {avg_vel:.1f} m/s\n"
            stats += f"Est. Lap Time: {est_time:.1f} s\n"
        else:
            stats += f"\nNo optimised path yet\n"

        self.stats_text.insert('1.0', stats)
    
    # ------------------------------------------------------------------
    # Scenario helpers
    # ------------------------------------------------------------------

    def _cones_from_centerline(self, points, half_width=1.5, closed=False):
        """Generate left/right cone pairs offset from a centerline.

        Computes the unit left-normal at every centerline point from the
        local tangent, then places one cone on each side at half_width.
        """
        pts = np.array(points, dtype=float)
        n = len(pts)
        left_cones, right_cones = [], []

        for i in range(n):
            if closed:
                tan = pts[(i + 1) % n] - pts[(i - 1) % n]
            elif i == 0:
                tan = pts[1] - pts[0]
            elif i == n - 1:
                tan = pts[-1] - pts[-2]
            else:
                tan = pts[i + 1] - pts[i - 1]

            mag = np.linalg.norm(tan)
            if mag < 1e-8:
                continue
            tan /= mag
            left_n = np.array([-tan[1], tan[0]])

            cx, cy = pts[i]
            left_cones.append((cx + half_width * left_n[0],
                                cy + half_width * left_n[1]))
            right_cones.append((cx - half_width * left_n[0],
                                 cy - half_width * left_n[1]))

        return left_cones, right_cones

    @staticmethod
    def _arc(cx, cy, radius, start_angle, end_angle, n):
        """Return n points on a circular arc."""
        angles = np.linspace(start_angle, end_angle, n)
        return [(cx + radius * np.cos(a), cy + radius * np.sin(a))
                for a in angles]

    @staticmethod
    def _straight(x0, y0, x1, y1, spacing=5.0):
        """Return evenly spaced points along a straight segment."""
        length = np.hypot(x1 - x0, y1 - y0)
        n = max(2, int(round(length / spacing)) + 1)
        return [(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
                for t in np.linspace(0, 1, n)]

    # ------------------------------------------------------------------
    # Scenarios
    # ------------------------------------------------------------------

    def load_scenario(self):
        """Load a predefined scenario"""
        scenario = self.scenario_var.get()
        self.selected_scenario = scenario

        self.left_cones       = []
        self.right_cones      = []
        self.orange_cones     = []
        self.car_position     = (0.0, 0.0)
        self.car_heading      = 0.0
        self.optimized_trajectory = None
        self.reftrack         = None

        hw = 3.0   # track half-width (m) — wide enough for 1.5 m vehicle with clearance

        if scenario == "Straight Track":
            # 100 m straight, cones every 5 m
            pts = self._straight(0, 0, 100, 0, spacing=5)
            self.left_cones, self.right_cones = self._cones_from_centerline(pts, hw)
            # Start / finish orange cones flanking the track
            self.orange_cones = [(-2, hw), (-2, -hw), (102, hw), (102, -hw)]
            self.car_position = (0.0, 0.0)
            self.car_heading  = 0.0

        elif scenario == "Simple Curve":
            # Approach straight → 90° right arc → exit straight
            # Approach: East, 0→20 m
            approach = self._straight(0, 0, 20, 0, spacing=5)
            # Right arc: centre (20, -14), r=14, 90°→0°
            arc = self._arc(20, -14, 14, np.pi / 2, 0, 14)
            # Exit: South from (34, -14), 20 m
            exit_s = self._straight(34, -14, 34, -34, spacing=5)
            pts = approach + arc[1:] + exit_s[1:]
            self.left_cones, self.right_cones = self._cones_from_centerline(pts, hw)
            self.orange_cones = [(-2, hw), (-2, -hw)]
            self.car_position = (0.0, 0.0)
            self.car_heading  = 0.0

        elif scenario == "S-Curve (Chicane)":
            # Approach → right arc → left arc → exit  (all in the same plane)
            approach = self._straight(0, 0, 16, 0, spacing=4)
            # Right arc: centre (16, -12), r=12, 90°→0°  → exit (28, -12) going S
            arc1 = self._arc(16, -12, 12, np.pi / 2, 0, 10)
            # Left arc:  centre (40, -12), r=12, 180°→270° → exit (40, -24) going E
            arc2 = self._arc(40, -12, 12, np.pi, 3 * np.pi / 2, 10)
            exit_s = self._straight(40, -24, 60, -24, spacing=4)
            pts = approach + arc1[1:] + arc2[1:] + exit_s[1:]
            self.left_cones, self.right_cones = self._cones_from_centerline(pts, hw)
            self.orange_cones = [(-2, hw), (-2, -hw)]
            self.car_position = (0.0, 0.0)
            self.car_heading  = 0.0

        elif scenario == "Hairpin Turn":
            # Approach East → 180° right arc → exit West (parallel return)
            # r=12 gives a 24 m-wide apex; outer wall at r+hw=15 m radius
            approach = self._straight(0, 0, 30, 0, spacing=5)
            # Hairpin: centre (30, -12), r=12, 90°→-90° (clockwise)
            hairpin  = self._arc(30, -12, 12, np.pi / 2, -np.pi / 2, 24)
            # Exit: West from (30, -24) back to origin level
            exit_s   = self._straight(30, -24, 0, -24, spacing=5)
            pts = approach + hairpin[1:] + exit_s[1:]
            self.left_cones, self.right_cones = self._cones_from_centerline(pts, hw)
            # Orange cones at the apex of the hairpin
            self.orange_cones = [(42 + hw, -12 + hw), (42 + hw, -12 - hw)]
            self.car_position = (0.0, 0.0)
            self.car_heading  = 0.0

        elif scenario == "Oval Track":
            # Ellipse: semi-major 28 m (x), semi-minor 12 m (y), 48 cones
            a, b = 28.0, 12.0
            angles = np.linspace(0, 2 * np.pi, 49)[:-1]
            pts = [(a * np.cos(t), b * np.sin(t)) for t in angles]
            self.left_cones, self.right_cones = self._cones_from_centerline(
                pts, hw, closed=True)
            # Start / finish orange cones at the right end of the straight
            self.orange_cones = [(a + 1, hw), (a + 1, -hw)]
            self.car_position = (a, 0.0)
            self.car_heading  = np.pi / 2   # heading North at start/finish

        elif scenario == "Figure-8":
            # Two tangent circles of radius 15 m joined at the origin.
            # Car starts at the top of the right loop, away from the crossing,
            # so nearest-neighbour chaining is unambiguous.
            r = 15.0
            n = 28
            # Right loop: clockwise (angles π → -π)
            right_loop = self._arc(r, 0, r, np.pi, -np.pi, n + 1)[:-1]
            # Left loop: counter-clockwise (angles 0 → 2π)
            left_loop  = self._arc(-r, 0, r, 0, 2 * np.pi, n + 1)[:-1]
            pts = right_loop + left_loop
            self.left_cones, self.right_cones = self._cones_from_centerline(
                pts, hw, closed=True)
            # Orange cones at the crossing point
            self.orange_cones = [(0, hw), (0, -hw)]
            # Start at the top of the right loop heading East — well away from crossing
            self.car_position = (r, r)      # (15, 15) — top of right loop
            self.car_heading  = 0.0         # heading East (tangent at angle 90°)

        elif scenario == "Slalom Course":
            # Tight zigzag: 11 gates, alternating left / right offset, 8 m apart
            n_gates   = 11
            spacing   = 8.0
            amplitude = 5.0
            pts = [(0.0, 0.0)]
            for i in range(n_gates):
                x = (i + 1) * spacing
                y = amplitude * (1 if i % 2 == 0 else -1)
                pts.append((x, y))
            pts.append(((n_gates + 1) * spacing, 0.0))
            self.left_cones, self.right_cones = self._cones_from_centerline(
                pts, half_width=hw)
            # Orange gate markers just outside each alternating gate
            for i in range(0, n_gates, 2):
                gx = (i + 1) * spacing
                gy = amplitude
                self.orange_cones.append((gx,  gy + hw * 0.5))
                self.orange_cones.append((gx, -gy - hw * 0.5))
            self.car_position = (0.0, 0.0)
            self.car_heading  = 0.0

        self.update_plot()
        self.update_statistics()
    
    def save_scenario(self):
        """Save current scenario to JSON file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Scenario"
        )
        
        if not filename:
            return
        
        data = {
            "scenario_name": self.selected_scenario,
            "left_cones": self.left_cones,
            "right_cones": self.right_cones,
            "orange_cones": self.orange_cones,
            "car_position": self.car_position,
            "car_heading": self.car_heading,
            "vehicle_width": float(self.vehicle_width_var.get()),
            "optimization_type": self.opt_type_var.get()
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            messagebox.showinfo("Success", f"Scenario saved to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")
    
    def load_scenario_from_file(self):
        """Load scenario from JSON file"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Scenario"
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            self.left_cones = [tuple(c) for c in data.get("left_cones", [])]
            self.right_cones = [tuple(c) for c in data.get("right_cones", [])]
            self.orange_cones = [tuple(c) for c in data.get("orange_cones", [])]
            self.car_position = tuple(data.get("car_position", (0.0, 0.0)))
            self.car_heading = data.get("car_heading", 0.0)
            
            if "vehicle_width" in data:
                self.vehicle_width_var.set(str(data["vehicle_width"]))
            if "optimization_type" in data:
                self.opt_type_var.set(data["optimization_type"])
            
            self.selected_scenario = data.get("scenario_name", "Loaded")
            self.scenario_var.set("Custom")
            
            self.optimized_trajectory = None
            self.reftrack = None
            
            self.update_plot()
            self.update_statistics()
            messagebox.showinfo("Success", f"Scenario loaded from {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load: {e}")
    
    def export_plot(self):
        """Export current plot to image"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf"), ("All files", "*.*")],
            title="Export Plot"
        )
        
        if not filename:
            return
        
        try:
            self.fig.savefig(filename, dpi=300, bbox_inches='tight')
            messagebox.showinfo("Success", f"Plot exported to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {e}")
    
    def toggle_ros(self):
        """Toggle ROS 2 integration"""
        if not ROS_AVAILABLE:
            messagebox.showerror("Error", "ROS 2 not available")
            self.ros_enabled_var.set(False)
            return
        
        if self.ros_enabled_var.get():
            # Initialize ROS 2
            try:
                if self.ros_node is None:
                    rclpy.init()
                    self.ros_node = rclpy.create_node('path_planning_gui')
                    
                    # Create publishers
                    self.cone_pub = self.ros_node.create_publisher(String, '/detected_cones', 10)
                    self.path_pub = self.ros_node.create_publisher(NavPath, '/planned_path', 10)
                    self.pose_pub = self.ros_node.create_publisher(PoseStamped, '/car_pose', 10)
                    
                    # Start spinning in thread
                    self.ros_thread = threading.Thread(target=self._ros_spin, daemon=True)
                    self.ros_thread.start()
                    
                    messagebox.showinfo("ROS 2", "ROS 2 node initialized")
            except Exception as e:
                messagebox.showerror("ROS 2 Error", f"Failed to initialize ROS 2: {e}")
                self.ros_enabled_var.set(False)
        else:
            # Shutdown ROS 2
            if self.ros_node:
                self.ros_node.destroy_node()
                self.ros_node = None
            if rclpy.ok():
                rclpy.shutdown()
            messagebox.showinfo("ROS 2", "ROS 2 node stopped")
    
    def _ros_spin(self):
        """ROS 2 spin thread"""
        while rclpy.ok() and self.ros_node:
            rclpy.spin_once(self.ros_node, timeout_sec=0.1)
    
    def publish_cones(self):
        """Publish cone data to ROS 2"""
        if not self.ros_node:
            messagebox.showwarning("Warning", "ROS 2 not enabled")
            return
        
        # Format: x,y,z,label per line
        cone_data = []
        
        for x, y in self.left_cones:
            cone_data.append(f"{x},{y},0.0,0")
        
        for x, y in self.right_cones:
            cone_data.append(f"{x},{y},0.0,1")
        
        for x, y in self.orange_cones:
            cone_data.append(f"{x},{y},0.0,2")
        
        msg = String()
        msg.data = '\n'.join(cone_data)
        self.cone_pub.publish(msg)
        
        # Also publish car pose
        pose_msg = PoseStamped()
        pose_msg.header.stamp = self.ros_node.get_clock().now().to_msg()
        pose_msg.header.frame_id = 'map'
        pose_msg.pose.position.x = self.car_position[0]
        pose_msg.pose.position.y = self.car_position[1]
        pose_msg.pose.position.z = 0.0
        pose_msg.pose.orientation.w = 1.0
        self.pose_pub.publish(pose_msg)
        
        self.status_label.config(text="✓ Published to ROS", foreground="blue")
        self.root.after(2000, lambda: self.status_label.config(text="Ready", foreground="green"))
    
    def publish_path(self):
        """Publish planned path to ROS 2"""
        if not self.ros_node:
            messagebox.showwarning("Warning", "ROS 2 not enabled")
            return
        
        if self.optimized_trajectory is None:
            messagebox.showwarning("Warning", "No optimized path available")
            return
        
        path_msg = NavPath()
        path_msg.header.stamp = self.ros_node.get_clock().now().to_msg()
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
        
        self.status_label.config(text="✓ Path Published", foreground="blue")
        self.root.after(2000, lambda: self.status_label.config(text="Ready", foreground="green"))
    
    def on_closing(self):
        """Handle window closing"""
        if self.ros_node:
            try:
                self.ros_node.destroy_node()
                if rclpy.ok():
                    rclpy.shutdown()
            except Exception:
                pass
        self.root.destroy()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = PathPlanningGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
