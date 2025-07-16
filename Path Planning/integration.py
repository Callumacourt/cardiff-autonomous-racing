# Continuously moves towards local goal given by perception info
from rrt_star import rrt_star, PathStatus
# TODO: resolve imports for where they are in perception stack
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, Point
from cones.msg import ConeArray
from track_msgs.msg import CenterlineMsg

class PathPlannerNode(Node):
    def __init__(self):
        super().__init__('path_planner')
        self.current_pose = (0.0, 0.0)
        self.left_cones = []
        self.right_cones = []
        self.centerline = []
        self.last_goal_idx = 0

        self.create_subscription(PoseStamped, '/car_pose', self.pose_callback, 10)
        self.create_subscription(ConeArray, '/cones', self.cones_callback, 10)
        self.create_subscription(CenterlineMsg, '/centerline', self.centerline_callback, 10)

        self.timer = self.create_timer(0.2, self.main_loop)  # 5 Hz

    def pose_callback(self, msg):
        self.current_pose = (msg.pose.position.x, msg.pose.position.y)

    def cones_callback(self, msg):
        self.left_cones = [(cone.x, cone.y) for cone in msg.left]
        self.right_cones = [(cone.x, cone.y) for cone in msg.right]

    def centerline_callback(self, msg):
        self.centerline = [(pt.x, pt.y) for pt in msg.points]

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

    def has_finished(self, threshold=0.5):
        last_pt = self.centerline[-1]
        dist = ((self.current_pose[0] - last_pt[0]) ** 2 + (self.current_pose[1] - last_pt[1]) ** 2) ** 0.5
        return dist < threshold

    def main_loop(self):
        if not self.left_cones or not self.right_cones or not self.centerline:
            return

        start = self.current_pose
        goal = self.get_next_local_goal(lookahead=2.0)
        obstacles = self.get_current_obstacles()
        x_max, y_max = 500, 500

        result = rrt_star(start, goal, obstacles, x_max, y_max, max_iter=200, max_step=2, goal_sample_rate=0.05)
        self.get_logger().info(f"Start: {start}, Goal: {goal}")
        if result.status in [PathStatus.SUCCESS, PathStatus.PARTIAL]:
            self.get_logger().info(f"Path: {result.path}")
        else:
            self.get_logger().warn("No path found")

        if goal == self.centerline[-1] and self.has_finished():
            self.get_logger().info("Finished, car has reached the end of the track.")
            rclpy.shutdown()

def main(args=None):
    rclpy.init(args=args)
    node = PathPlannerNode()
    rclpy.spin(node)

if __name__ == '__main__':
    main()