from std_msgs.msg import Bool
import rclpy
from rclpy.node import Node

class DrivingFlagPub(Node):
    def __init__(self):
        super().__init__("ros_control")
        self.publisher = self.create_publisher(Bool, "state_machine/driving_flag", 10)
        self.timer_period = 0.01
        self.timer = self.create_timer(self.timer_period, self.timer_callback)
        self.i=0
    
    def timer_callback(self):
        msg = Bool()
        msg.data = True
        self.publisher.publish(msg)
        self.i+=1

def main(args=None):
    rclpy.init(args=args)

    ds_pub = DrivingFlagPub()

    rclpy.spin(ds_pub)

    ds_pub.destroy_node()
    rclpy.shutdown()
