from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # Start cone mapper
        # need the perception package
        Node(
            package='cone_mapper',
            executable='cone_mapper',
            name='cone_mapper_node',
            output='screen'
        ),
        
        # Start path planner
        Node(
            package='path_planning',  
            executable='path_planner',  # Changed from 'integration' to 'path_planner'
            name='path_planner_node',
            output='screen'
        ),
    ])