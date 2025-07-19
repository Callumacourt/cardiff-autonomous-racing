from rrt_star import rrt_star, PathStatus
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, Point
from std_msgs.msg import Header, String
from nav_msgs.msg import Path

class PathPlannerNode(Node):
    def __init__(self):
        super().__init__('path_planner')
        self.current_pose = (0.0, 0.0)
        self.left_cones = []  # [x, y]
        self.right_cones = [] 
        self.centerline = []
        self.last_goal_idx = 0

        # Subscribe to cone mapper output
        self.create_subscription(PoseStamped, '/odometry/slam', self.pose_callback, 10)
        self.create_subscription(String, '/cone_map/global', self.world_cones_callback, 10)

        # Publisher for the planned path
        self.path_pub = self.create_publisher(Path, '/planned_path', 10)
        self.timer = self.create_timer(0.2, self.main_loop)

    def pose_callback(self, msg):
        self.current_pose = (msg.pose.position.x, msg.pose.position.y)

    def world_cones_callback(self, msg):
        """Parse cone data from cone mapper"""
        self.left_cones = []
        self.right_cones = []
        
        if not msg.data:
            return
            
        lines = msg.data.strip().split('\n')
        for line in lines:
            parts = line.strip().split(',')
            if len(parts) != 4:
                continue
            x, y, z, colour = map(float, parts)
            
            # 0 = blue (left), 1 = yellow (right), 2 = orange
            if int(colour) == 0:  # Blue cones (left side)
                self.left_cones.append((x, y))
            elif int(colour) == 1:  # Yellow cones (right side)
                self.right_cones.append((x, y))

    def generate_centerline(self):
        """Generate centerline from left and right cones"""
        if not self.left_cones or not self.right_cones:
            return
        
        # Simple centerline generation - average of nearest left/right pairs
        self.centerline = []
        for left_cone in self.left_cones:
            # Find nearest right cone
            min_dist = float('inf')
            nearest_right = None
            for right_cone in self.right_cones:
                dist = ((left_cone[0] - right_cone[0])**2 + (left_cone[1] - right_cone[1])**2)**0.5
                if dist < min_dist:
                    min_dist = dist
                    nearest_right = right_cone
            
            if nearest_right:
                center_x = (left_cone[0] + nearest_right[0]) / 2
                center_y = (left_cone[1] + nearest_right[1]) / 2
                self.centerline.append((center_x, center_y))

    def get_next_local_goal(self, lookahead=2.0):
        cx, cy = self.current_pose
        for i in range(self.last_goal_idx, len(self.centerline)):
            pt = self.centerline[i]
            dist = ((pt[0] - cx) ** 2 + (pt[1] - cy) ** 2) ** 0.5
            if dist >= lookahead:
                self.last_goal_idx = i
                return pt
        return self.centerline[-1] if self.centerline else (0, 0)

    def get_current_obstacles(self, cone_radius=1.0):
        return [(x, y, cone_radius) for (x, y) in self.left_cones + self.right_cones]

    def publish_path(self, path_points):
        path_msg = Path()
        path_msg.header = Header()
        path_msg.header.stamp = self.get_clock().now().to_msg()
        path_msg.header.frame_id = "map"
        for x, y in path_points:
            pose = PoseStamped()
            pose.header = path_msg.header
            pose.pose.position.x = float(x)
            pose.pose.position.y = float(y)
            pose.pose.position.z = 0.0
            path_msg.poses.append(pose)
        self.path_pub.publish(path_msg)

    def main_loop(self):
        try:
            if not self.left_cones or not self.right_cones:
                self.get_logger().warn("Waiting for cone data...")
                return

            # Generate centerline from cones
            self.generate_centerline()
            if not self.centerline:
                self.get_logger().warn("No centerline generated")
                return

            start = self.current_pose
            goal = self.get_next_local_goal(lookahead=2.0)
            obstacles = self.get_current_obstacles()
            x_max, y_max = 500, 500

            # Run path planning
            result = rrt_star(start, goal, obstacles, x_max, y_max, max_iter=200, max_step=2, goal_sample_rate=0.05)
            
            if result.status in [PathStatus.SUCCESS, PathStatus.PARTIAL]:
                self.get_logger().info(f"Path found with {len(result.path)} points")
                self.publish_path(result.path)
            else:
                self.get_logger().warn("No path found")

        except Exception as e:
            self.get_logger().error(f"Exception in main_loop: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = PathPlannerNode()
    rclpy.spin(node)

if __name__ == '__main__':
    main()