from std_msgs.msg import Bool
import rclpy
from rclpy.node import Node

class MissionFlagNode(Node):
    def __init__(self):
        super().__init__("ros_control")
        self.publisher = self.create_publisher(Bool, "ros_can/mission_flag",10)
        
        self.mission_complete = False

        self.timer_period = 0.01
        self.timer = self.create_timer(self.timer_period, self.timer_callback)
        self.i=0


    def set_mission_complete(self,complete):
        self.mission_complete = complete

    def timer_callback(self):
        msg = Bool()
        msg.data = self.mission_complete
        self.publisher.publish(msg)
        self.i+=1

def main(args=None):
    rclpy.init(args=args)

    ms_pub = MissionFlagNode()

    rclpy.spin(ms_pub)

    ms_pub.destroy_node()
    rclpy.shutdown()
