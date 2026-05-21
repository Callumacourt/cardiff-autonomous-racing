"""Unified launch for full perception stack: SLAM + YOLO + cone_mapper"""
import os
import platform
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.descriptions import ParameterValue


def _auto_viewer_default():
    has_display = bool(os.environ.get('DISPLAY'))
    try:
        is_wsl = 'microsoft' in platform.uname().release.lower()
    except Exception:
        is_wsl = False
    return 'true' if has_display and not is_wsl else 'false'


def generate_launch_description():
    slam_share = get_package_share_directory('slam_example')

    args = [
        DeclareLaunchArgument('use_slam',            default_value='true',
                              description='Launch ORB-SLAM3 stereo-inertial node.'),
        DeclareLaunchArgument('viewer',              default_value=_auto_viewer_default(),
                              description='Enable Pangolin viewer (requires DISPLAY).'),
        DeclareLaunchArgument('odom_frame_id',       default_value='odom'),
        DeclareLaunchArgument('left_image_topic',    default_value='/zed/left/image_rect_color'),
        DeclareLaunchArgument('right_image_topic',   default_value='/zed/right/image_rect_color'),
        DeclareLaunchArgument('depth_topic',         default_value='/zed/depth/image_raw'),
        DeclareLaunchArgument('camera_info_topic',   default_value='/zed/left/camera_info'),
        DeclareLaunchArgument('imu_topic',           default_value='/imu/data'),
        DeclareLaunchArgument('model_path',          default_value='/workspace/perception_ws/models/best.pt'),
        DeclareLaunchArgument('show_display',        default_value='false',
                              description='Show annotated YOLO output window (disable in headless Docker).'),
        DeclareLaunchArgument('conf_threshold',      default_value='0.5'),
        DeclareLaunchArgument('max_distance',        default_value='20.0'),
        DeclareLaunchArgument('cam_height',          default_value='0.5',
                              description='Camera height above base_link (metres).'),
        DeclareLaunchArgument('cam_forward',         default_value='0.3',
                              description='Camera forward offset from base_link (metres).'),
        DeclareLaunchArgument('cam_lateral',         default_value='0.0',
                              description='Camera lateral offset from base_link (metres).'),
        DeclareLaunchArgument('odom_topic',          default_value='/odometry/slam',
                              description='Odometry topic consumed by cone_mapper.'),
    ]

    slam_node = Node(
        condition=IfCondition(LaunchConfiguration('use_slam')),
        package='slam_example',
        executable='orb_slam3_stereo_inertial',
        name='orb_slam3_stereo_inertial',
        output='screen',
        parameters=[{
            'vocab_path':        f'{slam_share}/config/ORBvoc.txt',
            'config_path':       f'{slam_share}/config/camera_and_slam_settings.yaml',
            'viewer':            ParameterValue(LaunchConfiguration('viewer'),           value_type=bool),
            'left_image_topic':  LaunchConfiguration('left_image_topic'),
            'right_image_topic': LaunchConfiguration('right_image_topic'),
            'imu_topic':         LaunchConfiguration('imu_topic'),
            'odom_topic':        LaunchConfiguration('odom_topic'),
            'child_frame_id':    'base_link',
            'odom_frame_id':     LaunchConfiguration('odom_frame_id'),
            'sync_timer_ms':     33,
            'max_sync_delta':    0.02,
        }],
    )

    yolo_node = Node(
        package='cone_detector',
        executable='YOLO_cone_detector',
        name='yolo_cone_detector_3d_node',
        output='screen',
        parameters=[{
            'model_path':         LaunchConfiguration('model_path'),
            'show_display':       ParameterValue(LaunchConfiguration('show_display'),    value_type=bool),
            'conf_threshold':     ParameterValue(LaunchConfiguration('conf_threshold'),  value_type=float),
            'max_distance':       ParameterValue(LaunchConfiguration('max_distance'),    value_type=float),
            'rgb_topic':          LaunchConfiguration('left_image_topic'),
            'depth_topic':        LaunchConfiguration('depth_topic'),
            'camera_info_topic':  LaunchConfiguration('camera_info_topic'),
        }],
    )

    mapper_node = Node(
        package='cone_mapper',
        executable='cone_mapper',
        name='cone_mapper',
        output='screen',
        parameters=[{
            'odom_topic':   LaunchConfiguration('odom_topic'),
            'cam_height':   ParameterValue(LaunchConfiguration('cam_height'),   value_type=float),
            'cam_forward':  ParameterValue(LaunchConfiguration('cam_forward'),  value_type=float),
            'cam_lateral':  ParameterValue(LaunchConfiguration('cam_lateral'),  value_type=float),
        }],
    )

    return LaunchDescription(args + [slam_node, yolo_node, mapper_node])
