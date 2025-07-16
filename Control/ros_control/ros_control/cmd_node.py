import ackermann_msgs.msg
import rclpy
from rclpy.node import Node
import ackermann_msgs

import std_msgs
import std_msgs.msg

from eufs_msgs.msg import CanState, WheelSpeedsStamped
from geometry_msgs.msg import TwistWithCovarianceStamped
from sensor_msgs.msg import Imu,NavSatFix

from numpy import ndarray

from ...MPC.main import Model_Predictive_Contol
from ...model.vehical_model import Vehicle_Input, Vehicle_State

class MinimalPublisher(Node):

    def __init__(self):
        super().__init__('ros_control')
        self.publisher_ = self.create_publisher(ackermann_msgs.msg.AckermannDriveStamped, 'cmd', 10)
        self.timer_period = 0.01  # seconds
        self.timer = self.create_timer(self.timer_period, self.timer_callback)
        self.i = 0

        #set up subscribers to get data from car
        self.can_state_sub = self.create_subscription(CanState,"ros_can/state",self.can_state_callback,10)
        self.wheel_speeds_sub = self.create_subscription(WheelSpeedsStamped,"ros_can/wheel_speeds",self.wheel_speeds_callback,10)
        self.twist_sub = self.create_subscription(TwistWithCovarianceStamped,"ros_can/twist",self.twist_callback,10)
        self.imu_sub = self.create_subscription(Imu,"ros_can/imu",self.imu_callback,10)
        self.nav_sub = self.create_subscription(NavSatFix,"ros_can/fix",self.nav_callback,10)

        #set up subscriber(s) to get data via path planning

        self.current_state = Vehicle_State(x_pos=0.0, y_pos=0.0, yaw_angle=0.0, directional_velocity=0.0, perpendicualar_velocity=0.0, yaw_rate=0.0)
        self.mpc_unit = Model_Predictive_Contol(self.timer_period)

    #called whenever a msg is recieved
    def can_state_callback(self, msg:CanState):
        self.ami_state = msg.ami_state
        self.as_state = msg.as_state
        pass
    def wheel_speeds_callback(self,msg:WheelSpeedsStamped):
        header = msg.header
        wheels = msg.speeds
        lb = wheels.lb_speed
        lf = wheels.lf_speed
        rb = wheels.rb_speed
        rf = wheels.rf_speed
        steering = wheels.steering
        self.current_state  = Vehicle_State(
            xpos=0.0, # MPC will always assume
            ypos=0.0, # ????
            yaw_angle=0.0, 
            directional_velocity=(lb+lf+rb+rf)/4.0, # average speed
            perpendicualar_velocity=0.0, # how much the car is sliding
            yaw_rate= steering # DEFINITLY NOT CORRECT
            )

    def twist_callback(self,msg:TwistWithCovarianceStamped):
        header = msg.header
        twist_with_covariance = msg.twist
        twist = twist_with_covariance.twist
        covariance = twist_with_covariance.covariance
        pass
    def imu_callback(self,msg:Imu):
        try:
            header = msg.header
            angular_velocity = msg.angular_velocity
            av_with_covariance = msg.angular_velocity_covariance
            linear_acceleration = msg.linear_acceleration
            la_with_covariance = msg.linear_acceleration_covariance
            orientation = msg.orientation
            orientation_covariance = msg.orientation_covariance
        except:
            print("error in Imu msg")
    def nav_callback(self,msg:NavSatFix):
        header = msg.header
        altitude = msg.altitude
        lat = msg.latitude
        long = msg.longitude
        covariance = msg.position_covariance
        cov_type = msg.position_covariance_type

        status = msg.status
        pass

    #called periodically based on self.timer_period
    def timer_callback(self):
        msg = ackermann_msgs.msg.AckermannDriveStamped()
        msg.header = std_msgs.msg.Header()
        msg.drive = ackermann_msgs.msg.AckermannDrive()

        # THIS IS WHERE COMMANDS ARE SENT TO ROS_CAN
        #ros_can will then check to make sure the commands are valid, and that the car should be driving
        # before sending them to the car
        # the ackermanndrive msg has more parameters than the car uses, we currently only need to worry about 
        # acceleration and steering angle
        if self.as_state == 3:# car is in AS_DRIVING
            # msg.drive.speed=10.0    

            try:
                commands = self.mpc_unit.main(initial_state=self.current_state, required_path=,)#get required path from path planning, not sure where to get initial state from
                msg.drive.acceleration = commands.acceleration 
                msg.drive.steering_angle = commands.steering_angle
            except Exception as e:
                msg.drive.acceleration = 1.0 # make sure these are floats
                msg.drive.steering_angle = 0.0
            # msg.drive.steering_angle_velocity
            # msg.drive.jerk
            self.publisher_.publish(msg)
            #self.get_logger().info(f'Publishing: "{msg.drive}" \n & {msg.header}')
        elif self.as_state == 2: # car is in AS_READY
            msg.drive.acceleration = 0.0
            msg.drive.steering_angle = 0.0
            #msg.drive.steering_angle_velocity = 0
        
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
