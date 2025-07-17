from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # Start cone mapper
        Node(
            package='cone_mapper',
            executable='cone_mapper',
            name='cone_mapper_node',
            output='screen'
        ),
        
        # Start path planner
        Node(
            package='path_planning',  # You'll need to create this package
            executable='path_planner',
            name='path_planner_node',
            output='screen'
        ),
    ])