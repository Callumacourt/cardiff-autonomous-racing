import ackermann_msgs.msg
import rclpy
from rclpy.node import Node
import ackermann_msgs

import std_msgs
import std_msgs.msg

from eufs_msgs.msg import CanState, WheelSpeedsStamped
from geometry_msgs.msg import TwistWithCovarianceStamped, Quaternion
from sensor_msgs.msg import Imu,NavSatFix
from nav_msgs.msg import Path, Odometry

from std_srvs.srv import Trigger

import math
import numpy as np

#
from MPC.main import Model_Predictive_Control
from model.vehical_model import Vehicle_Input, Vehicle_State

from mission_control import Mission_Control
class CmdNode(Node):

    def __init__(self):
        super().__init__('ros_control')

        self.declare_parameter("eufs_simulate",value=False)
        self.eufs_sim = self.get_parameter("eufs_simulate").get_parameter_value().bool_value
        self.get_logger().info(f"using eufs sim: {self.eufs_sim}")

        self.publisher_ = self.create_publisher(ackermann_msgs.msg.AckermannDriveStamped, 'cmd', 10)
        self.get_logger().info("cmd publisher started")
        self.publisher_df = self.create_publisher(std_msgs.msg.Bool, "state_machine/driving_flag", 10)
        self.get_logger().info("state_machine/driving_flag publisher started")
        self.publisher_mf = self.create_publisher(std_msgs.msg.Bool, "ros_can/mission_completed", 10)
        self.get_logger().info("ros_can/mission_complete publisher started")
        self.timer_period = 0.01  # seconds
        self.timer = self.create_timer(self.timer_period, self.timer_callback)
        self.i = 0

        
        #self.steering_angle_rad = 0#current steering angle of wheels in radians (+ is left)
        #self.wheels_rpm = 0#current average rpm of all 4 wheels
        self.WHEEL_RADIUS = 0.253

        self.time_at_event_start = 0

        #set up subscribers to get data from car
        self.can_state_sub = self.create_subscription(CanState,"ros_can/state",self.can_state_callback,10)
        self.get_logger().info("ros_can/state subscriber started")
        self.wheel_speeds_sub = self.create_subscription(WheelSpeedsStamped,"ros_can/wheel_speeds",self.wheel_speeds_callback,10)
        self.get_logger().info("ros_can/wheel_speeds subscriber started")
        self.twist_sub = self.create_subscription(TwistWithCovarianceStamped,"ros_can/twist",self.twist_callback,10)
        self.get_logger().info("ros_can/twist subscriber started")
        self.imu_sub = self.create_subscription(Imu,"ros_can/imu",self.imu_callback,10)
        self.get_logger().info("ros_can/imu subscriber started")
        self.nav_sub = self.create_subscription(NavSatFix,"ros_can/fix",self.nav_callback,10)
        self.get_logger().info("ros_can/fix (sat nav) subscriber started")

        #set up subscriber(s) to get data via path planning
        self.path = None
        self.path_sub = self.create_subscription(Path,"planned_path",self.path_callback,10)
        self.get_logger().info("planned_path subscription started")

        #set up subscriber to get position from perception
        self.odometry_sub = self.create_subscription(Odometry, "odometry/slam", self.odometry_callback, 10)
        self.get_logger().info("Odometry/slam subscription started")

        self.current_state = Vehicle_State(x_pos=0.0, y_pos=0.0, yaw_angle=0.0, x_speed=0.0, y_speed=0.0, yaw_rate=0.0)
        
        #self.mission_complete_pub = self.create_publisher(std_msgs.msg.Bool, 'ros_control/mission_complete', 10)

        self.mission_controler = Mission_Control(mpc_unit=Model_Predictive_Control(self.timer_period,5.0),timer_period=self.timer_period,logger=self.get_logger,trigger_ebs=self.trigger_ebs)

        self.get_logger().info("Initialization complete")

    def set_time_at_event_start(self,time):
        if self.time_at_event_start == 0:
            self.time_at_event_start = time
    
    def trigger_ebs(self):
        client = self.create_client(Trigger,"/ros_can/ebs")
        while not client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for /ros_can/ebs service...')
        req = Trigger.Request()
        future = client.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        if future.result() is not None and future.result().success:
            self.get_logger().info('EBS triggered successfully!')
        else:
            self.get_logger().error('Failed to trigger EBS!')

    def odometry_callback(self,msg:Odometry):
        self.set_current_state(odometry=msg)

    def path_callback(self,msg:Path):
        header = msg.header
        self.path = msg.poses

    #called whenever a msg is recieved
    def can_state_callback(self, msg:CanState):
        self.mission_controler.set_can_states(msg.ami_state,msg.as_state)
        self.get_logger().info(f'Recieved: AMI:{msg.ami_state}, AS:{msg.as_state}')

    def wheel_speeds_callback(self,msg:WheelSpeedsStamped):
        header = msg.header
        wheels = msg.speeds
        # in RPM
        lb = wheels.lb_speed 
        lf = wheels.lf_speed
        rb = wheels.rb_speed
        rf = wheels.rf_speed
        # in RADIANS
        steering = wheels.steering
        self.current_state.wheels_rpm = (lb+lf+rb+rf)/4
        if self.eufs_sim:
            self.current_state.wheels_rpm -= 500
        self.current_state.steering_angle_rad = steering
        #import pdb; pdb.set_trace()
        self.get_logger().info(f"Recieved: Wheels_rpm: {self.current_state.wheels_rpm}, Steering_angle_rad: {self.current_state.steering_angle_rad}")
        """self.current_state  = Vehicle_State(
            x_pos=0.0, # MPC will always assume
            y_pos=0.0, # ????
            yaw_angle=0.0, 
            x_speed=(lb+lf+rb+rf)/4.0, # average speed
            y_speed=0.0, # how much the car is sliding
            yaw_rate= steering # DEFINITLY NOT CORRECT
            )"""

    def twist_callback(self,msg:TwistWithCovarianceStamped):
        header = msg.header
        twist_with_covariance = msg.twist
        twist = twist_with_covariance.twist
        covariance = twist_with_covariance.covariance
        self.get_logger().info(f"Recieved: twist: {twist}")
    def imu_callback(self,msg:Imu):
        try:

            header = msg.header
            angular_velocity = msg.angular_velocity
            av_with_covariance = msg.angular_velocity_covariance
            linear_acceleration = msg.linear_acceleration
            la_with_covariance = msg.linear_acceleration_covariance
            orientation = msg.orientation
            orientation_covariance = msg.orientation_covariance
            self.get_logger().info(f"Recieved IMU msg: a_vel: {angular_velocity}, l_accel: {linear_acceleration}, orientation: {orientation} ")
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
    
    def get_yaw_from_quaternion(self,orientation:Quaternion):
        """
        Returns the yaw (rotation around z) in radians from a geometry_msgs.msg.Quaternion
        """
        x = orientation.x
        y = orientation.y
        z = orientation.z
        w = orientation.w

        # Yaw calculation
        siny_cosp = 2.0 * (w * z + x * y)
        cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
        yaw = math.atan2(siny_cosp, cosy_cosp)
        return yaw
    def set_current_state(self, odometry:Odometry):
        pose = odometry.pose
        position = pose.pose.position
        
        orientation = pose.pose.orientation
        yaw = self.get_yaw_from_quaternion(orientation)

        twist = odometry.twist
        l_velocity = twist.twist.linear
        a_velocity = twist.twist.angular

        #use sin and cos to split into seperate velocities
        # Rotate local velocities into world frame
        v_x = l_velocity.x * math.cos(yaw) - l_velocity.y * math.sin(yaw)  # forward (directional)
        v_y = l_velocity.x * math.sin(yaw) + l_velocity.y * math.cos(yaw)  # sideways (perpendicular)


        state = Vehicle_State(
            x_pos=position.x,
            y_pos=position.y,
            x_speed=v_x,
            y_speed=v_y,
            yaw_angle=yaw,
            yaw_rate=a_velocity.z
            )
        self.mission_controler.mpc_unit.dynamics_model.set_state(state)


    #called periodically based on self.timer_period
    def timer_callback(self):
        #simulate = self.get_parameter("eufs_simulate").get_parameter_value().bool_value
        #self.get_logger().info(f"Simulate with eufs: {simulate}")
        
        msg = ackermann_msgs.msg.AckermannDriveStamped()
        msg.header = std_msgs.msg.Header()
        msg.drive = ackermann_msgs.msg.AckermannDrive()

        
        # THIS IS WHERE COMMANDS ARE SENT TO ROS_CAN
        #ros_can will then check to make sure the commands are valid, and that the car should be driving
        # before sending them to the car
        # the ackermanndrive msg has more parameters than the car uses, we currently only need to worry about 
        # acceleration and steering angle

        msg.drive.acceleration, msg.drive.steering_angle = self.mission_controler.get_message(self.current_state,self.path)
        
        self.publisher_.publish(msg)

        mission_msg = std_msgs.msg.Bool()
        mission_msg.data = self.mission_controler.get_mission_complete()

        driving_flag_msg = std_msgs.msg.Bool()
        driving_flag_msg.data = True

        self.publisher_df.publish(driving_flag_msg)
        self.publisher_mf.publish(mission_msg)
        self.i += 1


def main(args=None):
    rclpy.init(args=args)

    minimal_publisher = CmdNode()

    rclpy.spin(minimal_publisher)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    minimal_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
