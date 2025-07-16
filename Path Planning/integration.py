from rrt_star import rrt_star, PathStatus
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, Point
from cones.msg import ConeArray
from track_msgs.msg import CenterlineMsg
from std_msgs.msg import Header
from nav_msgs.msg import Path  # Standard message for publishing paths

class PathError(Exception):
    """Base exception for path errors"""

class PathPlannerNode(Node):
    def __init__(self):
        super().__init__('path_planner')
        self.current_pose = (0.0, 0.0)
        self.left_cones = []
        self.right_cones = []
        self.centerline = []
        self.last_goal_idx = 0

        # Subscribe to ROS 2 topics for perception and localization
        self.create_subscription(PoseStamped, '/car_pose', self.pose_callback, 10)
        self.create_subscription(ConeArray, '/cones', self.cones_callback, 10)
        self.create_subscription(CenterlineMsg, '/centerline', self.centerline_callback, 10)

        # Publisher for the planned path
        self.path_pub = self.create_publisher(Path, '/planned_path', 10)

        # Timer to run main_loop every 0.2 seconds (5 Hz)
        self.timer = self.create_timer(0.2, self.main_loop)

    def pose_callback(self, msg):
        self.current_pose = (msg.pose.position.x, msg.pose.position.y)

    def cones_callback(self, msg):
        self.left_cones = [(cone.x, cone.y) for cone in msg.left]
        self.right_cones = [(cone.x, cone.y) for cone in msg.right]

    def centerline_callback(self, msg):
        self.centerline = [(pt.x, pt.y) for pt in msg.points]
    
    # Finds the next local goal on the centerline at least 'lookahead' meters ahead
    def get_next_local_goal(self, lookahead=2.0):
        cx, cy = self.current_pose
        for i in range(self.last_goal_idx, len(self.centerline)):
            pt = self.centerline[i]
            dist = ((pt[0] - cx) ** 2 + (pt[1] - cy) ** 2) ** 0.5
            if dist >= lookahead:
                self.last_goal_idx = i
                return pt
        return self.centerline[-1]

    def get_current_obstacles(self, cone_radius=1.0):
        return [(x, y, cone_radius) for (x, y) in self.left_cones + self.right_cones]
    
    # Checks if the car is close enough to the last centerline point (finish condition)
    def has_finished(self, threshold=0.5):
        last_pt = self.centerline[-1]
        dist = ((self.current_pose[0] - last_pt[0]) ** 2 + (self.current_pose[1] - last_pt[1]) ** 2) ** 0.5
        return dist < threshold

    def publish_path(self, path_points):
        # Publish the planned path as a nav_msgs/Path so can be used by control
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
            if not self.left_cones or not self.right_cones or not self.centerline:
                self.get_logger().warn("Waiting for ROS data...")
                return

            start = self.current_pose
            goal = self.get_next_local_goal(lookahead=2.0)
            obstacles = self.get_current_obstacles()
            x_max, y_max = 500, 500

            # Run RRT* path planning
            result = rrt_star(start, goal, obstacles, x_max, y_max, max_iter=200, max_step=2, goal_sample_rate=0.05)
            self.get_logger().info(f"Start: {start}, Goal: {goal}")
            if result.status in [PathStatus.SUCCESS, PathStatus.PARTIAL]:
                self.get_logger().info(f"Path: {result.path}")
                self.publish_path(result.path)  # Publish the path for other nodes
            else:
                self.get_logger().warn("No path found")

            if goal == self.centerline[-1] and self.has_finished():
                self.get_logger().info("Finished, car has reached the end of the track.")
                rclpy.shutdown()
        except Exception as e:
            self.get_logger().error(f"Exception in main_loop: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = PathPlannerNode()
    rclpy.spin(node)

if __name__ == '__main__':
    main()