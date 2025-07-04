# Copyright 2016 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ackermann_msgs.msg
import rclpy
from rclpy.node import Node
import ackermann_msgs

import std_msgs
import std_msgs.msg


class MinimalPublisher(Node):

    def __init__(self):
        super().__init__('ros_control')
        self.publisher_ = self.create_publisher(ackermann_msgs.msg.AckermannDriveStamped, 'cmd', 10)
        self.timer_period = 0.01  # seconds
        self.timer = self.create_timer(self.timer_period, self.timer_callback)
        self.i = 0

    def timer_callback(self):
        msg = ackermann_msgs.msg.AckermannDriveStamped()
        msg.header = std_msgs.msg.Header()
        msg.drive = ackermann_msgs.msg.AckermannDrive()

        # THIS IS WHERE COMMANDS ARE SENT TO ROS_CAN
        #ros_can will then check to make sure the commands are valid, and that the car should be driving
        # before sending them to the car
        msg.drive.speed=10.0    
        msg.drive.acceleration=1.0
        # msg.drive.steering_angle
        # msg.drive.steering_angle_velocity
        # msg.drive.jerk
        self.publisher_.publish(msg)
        #self.get_logger().info(f'Publishing: "{msg.drive}" \n & {msg.header}')
        self.i += 1


def main(args=None):
    rclpy.init(args=args)

    minimal_publisher = MinimalPublisher()

    rclpy.spin(minimal_publisher)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    minimal_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
