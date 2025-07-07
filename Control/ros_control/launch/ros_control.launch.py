from launch_ros.actions import Node
from launch import LaunchDescription
def generate_launch_description():

    df_pub_node = Node(
        package="ros_control",
        executable="driving_flag_pub",
    )

    mf_pub_node = Node(
        package="ros_control",
        executable="mission_flag_pub"
    )

    cmd_node = Node(
        package="ros_control",
        executable="command_node"
    )

    return LaunchDescription(
        [
            mf_pub_node,
            df_pub_node,
            cmd_node
        ]
    )