from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    """Launch the cone detector node with configurable parameters."""
    
    # Declare launch arguments
    model_path_arg = DeclareLaunchArgument(
        'model_path',
        default_value='yolov8n.pt',
        description='Path to YOLO model file'
    )
    
    confidence_threshold_arg = DeclareLaunchArgument(
        'confidence_threshold',
        default_value='0.5',
        description='Confidence threshold for detections'
    )
    
    camera_topic_arg = DeclareLaunchArgument(
        'camera_topic',
        default_value='/camera/image_raw',
        description='Input camera topic'
    )
    
    output_topic_arg = DeclareLaunchArgument(
        'output_topic',
        default_value='/cone_detections',
        description='Output topic for cone detections'
    )
    
    publish_debug_image_arg = DeclareLaunchArgument(
        'publish_debug_image',
        default_value='true',
        description='Whether to publish debug images with bounding boxes'
    )
    
    # Create the cone detector node
    cone_detector_node = Node(
        package='cone_detector',
        executable='cone_detector_node',
        name='cone_detector',
        parameters=[{
            'model_path': LaunchConfiguration('model_path'),
            'confidence_threshold': LaunchConfiguration('confidence_threshold'),
            'camera_topic': LaunchConfiguration('camera_topic'),
            'output_topic': LaunchConfiguration('output_topic'),
            'publish_debug_image': LaunchConfiguration('publish_debug_image'),
        }],
        output='screen'
    )
    
    return LaunchDescription([
        model_path_arg,
        confidence_threshold_arg,
        camera_topic_arg,
        output_topic_arg,
        publish_debug_image_arg,
        cone_detector_node,
    ])