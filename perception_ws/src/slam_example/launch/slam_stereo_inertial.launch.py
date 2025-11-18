from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    slam_share = get_package_share_directory('slam_example')

    viewer_arg = LaunchConfiguration('viewer')
    left_topic_arg = LaunchConfiguration('left_image_topic')
    right_topic_arg = LaunchConfiguration('right_image_topic')
    imu_topic_arg = LaunchConfiguration('imu_topic')
    sync_timer_arg = LaunchConfiguration('sync_timer_ms')
    odom_topic_arg = LaunchConfiguration('odom_topic')
    child_frame_arg = LaunchConfiguration('child_frame_id')
    max_sync_delta_arg = LaunchConfiguration('max_sync_delta')
    vocab_arg = LaunchConfiguration('vocab_path')
    config_arg = LaunchConfiguration('config_path')

    return LaunchDescription([
        DeclareLaunchArgument(
            'viewer', default_value='true',
            description='Enable Pangolin viewer (requires DISPLAY forwarding).'),
        DeclareLaunchArgument(
            'left_image_topic', default_value='/zed/left/image_rect_color',
            description='Left stereo image topic.'),
        DeclareLaunchArgument(
            'right_image_topic', default_value='/zed/right/image_rect_color',
            description='Right stereo image topic.'),
        DeclareLaunchArgument(
            'imu_topic', default_value='/imu/data',
            description='IMU topic providing inertial measurements.'),
        DeclareLaunchArgument(
            'sync_timer_ms', default_value='33',
            description='Manual sync timer period in milliseconds.'),
        DeclareLaunchArgument(
            'odom_topic', default_value='/odometry/slam',
            description='Topic where the SLAM odometry is published.'),
        DeclareLaunchArgument(
            'child_frame_id', default_value='base_link',
            description='Child frame ID used in published odometry.'),
        DeclareLaunchArgument(
            'max_sync_delta', default_value='0.02',
            description='Max allowed time delta (seconds) between stereo images when manually syncing.'),
        DeclareLaunchArgument(
            'vocab_path',
            default_value=f'{slam_share}/config/ORBvoc.txt',
            description='Path to ORB vocabulary file.'),
        DeclareLaunchArgument(
            'config_path',
            default_value=f'{slam_share}/config/camera_and_slam_settings.yaml',
            description='Stereo+IMU configuration file.'),
        Node(
            package='slam_example',
            executable='orb_slam3_stereo_inertial',
            name='orb_slam3_stereo_inertial',
            output='screen',
            parameters=[
                {
                    "vocab_path": vocab_arg,
                    "config_path": config_arg,
                    "camera_frame": "zed_left_camera_optical_frame",
                    "viewer": ParameterValue(viewer_arg, value_type=bool),
                    "left_image_topic": left_topic_arg,
                    "right_image_topic": right_topic_arg,
                    "imu_topic": imu_topic_arg,
                    "sync_timer_ms": ParameterValue(sync_timer_arg, value_type=int),
                    "odom_topic": odom_topic_arg,
                    "child_frame_id": child_frame_arg,
                    "max_sync_delta": ParameterValue(max_sync_delta_arg, value_type=float)
                }
            ]
        )
    ])