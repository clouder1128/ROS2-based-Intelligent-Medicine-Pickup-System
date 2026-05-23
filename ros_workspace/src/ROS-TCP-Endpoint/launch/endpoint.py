from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    ros_ip = LaunchConfiguration("ROS_IP", default="0.0.0.0")
    ros_tcp_port = LaunchConfiguration("ROS_TCP_PORT", default="10000")

    return LaunchDescription(
        [
            DeclareLaunchArgument("ROS_IP", default_value="0.0.0.0"),
            DeclareLaunchArgument("ROS_TCP_PORT", default_value="10000"),
            Node(
                package="ros_tcp_endpoint",
                executable="default_server_endpoint",
                emulate_tty=True,
                parameters=[{"ROS_IP": ros_ip}, {"ROS_TCP_PORT": ros_tcp_port}],
            ),
        ]
    )
