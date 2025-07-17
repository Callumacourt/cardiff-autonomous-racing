from launch_ros.actions import Node
from launch import LaunchDescription
from launch.actions import RegisterEventHandler, LogInfo
from launch.event_handlers import OnProcessStart
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
            cmd_node,
            RegisterEventHandler(
                OnProcessStart(
                    target_action=cmd_node,
                    on_start=[LogInfo(msg="Started command node"),
                              df_pub_node]
                )),
            RegisterEventHandler(
                OnProcessStart(
                    target_action=df_pub_node,
                    on_start=[LogInfo(msg="Started driving flag node"),
                              mf_pub_node]
                )
            )
        ]
    )
    """
    return LaunchDescription(
        [
            mf_pub_node,
            df_pub_node,
            cmd_node
        ]
    )"""