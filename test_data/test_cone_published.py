#!/usr/bin/env python3
# File: test_data/test_cone_publisher.py
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import math
import time

class MockConePublisher(Node):
    def __init__(self):
        super().__init__('mock_cone_publisher')
        self.publisher = self.create_publisher(String, '/detected_cones', 10)
        self.timer = self.create_timer(0.1, self.publish_mock_cones)
        self.counter = 0
        
    def publish_mock_cones(self):
        mock_cones = [
            "5.0,-1.0,0.0,0",    # Left cones (blue)
            "8.0,-1.0,0.0,0",
            "11.0,-1.0,0.0,0",
            "14.0,-1.0,0.0,0",
            "5.0,1.0,0.0,1",     # Right cones (yellow)
            "8.0,1.0,0.0,1",
            "11.0,1.0,0.0,1",
            "14.0,1.0,0.0,1",
        ]
        
        msg = String()
        msg.data = '\n'.join(mock_cones)
        self.publisher.publish(msg)
        
        self.counter += 1
        if self.counter % 100 == 0:
            self.get_logger().info(f"Published {len(mock_cones)} mock cones")

def main(args=None):
    rclpy.init(args=args)
    node = MockConePublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()