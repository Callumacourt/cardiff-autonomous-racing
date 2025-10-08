#!/usr/bin/env python3

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    """Launch the SLAM system with configurable parameters."""
    
    # Declare launch arguments
    camera_topic_arg = DeclareLaunchArgument(
        'camera_topic',
        default_value='/camera/image_raw',
        description='Input camera topic'
    )
    
    camera_info_topic_arg = DeclareLaunchArgument(
        'camera_info_topic',
        default_value='/camera/camera_info',
        description='Camera info topic'
    )
    
    slam_mode_arg = DeclareLaunchArgument(
        'slam_mode',
        default_value='monocular',
        description='SLAM mode: monocular, stereo, or rgbd'
    )
    
    vocabulary_path_arg = DeclareLaunchArgument(
        'vocabulary_path',
        default_value='/workspace/ORB_SLAM3/Vocabulary/ORBvoc.txt',
        description='Path to ORB vocabulary file'
    )
    
    settings_path_arg = DeclareLaunchArgument(
        'settings_path',
        default_value='/workspace/ORB_SLAM3/Examples/Monocular/TUM1.yaml',
        description='Path to SLAM settings file'
    )
    
    # Create the SLAM system node
    slam_node = Node(
        package='slam_system',
        executable='slam_node',
        name='slam_system',
        parameters=[{
            'camera_topic': LaunchConfiguration('camera_topic'),
            'camera_info_topic': LaunchConfiguration('camera_info_topic'),
            'slam_mode': LaunchConfiguration('slam_mode'),
            'vocabulary_path': LaunchConfiguration('vocabulary_path'),
            'settings_path': LaunchConfiguration('settings_path'),
        }],
        output='screen'
    )
    
    return LaunchDescription([
        camera_topic_arg,
        camera_info_topic_arg,
        slam_mode_arg,
        vocabulary_path_arg,
        settings_path_arg,
        slam_node,
    ])