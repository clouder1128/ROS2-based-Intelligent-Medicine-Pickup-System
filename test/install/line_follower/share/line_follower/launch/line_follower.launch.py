"""
启动 Gazebo↔ROS2 桥接 + 巡线节点

使用方法（先在另一个终端启动 Gazebo）:
  Terminal 1:  cd test && gz sim test_world.sdf
  Terminal 2:  ros2 launch line_follower line_follower.launch.py

如果 Gazebo 里的话题名不是默认的 /camera 和 /cmd_vel，
可以通过命令行覆盖:
  ros2 launch line_follower line_follower.launch.py \
      gz_camera_topic:=/world/empty/model/mycar/link/camera/sensor/camera/image \
      gz_cmd_vel_topic:=/model/mycar/cmd_vel
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # 声明可覆盖参数
    gz_camera_arg = DeclareLaunchArgument(
        'gz_camera_topic', default_value='/camera',
        description='Gazebo camera image topic name')
    gz_cmd_vel_arg = DeclareLaunchArgument(
        'gz_cmd_vel_topic', default_value='/cmd_vel',
        description='Gazebo cmd_vel topic name')

    # ros_gz_bridge: 把 Gazebo Transport 话题桥接到 ROS2
    bridge_node = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            # GZ → ROS: 相机图像
            '/camera@sensor_msgs/msg/Image[gz.msgs.Image',
            # ROS → GZ: 速度指令
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
        ],
        output='screen',
    )

    # 巡线节点
    follower_node = Node(
        package='line_follower',
        executable='line_follower',
        name='line_follower',
        output='screen',
        parameters=[{
            'image_topic': '/camera',
            'cmd_vel_topic': '/cmd_vel',
            'linear_speed': 0.5,
            'kp': 0.005,
            'kd': 0.001,
            'stop_duration': 3.0,
            'red_pixel_threshold': 300,
            'line_lost_rotate_speed': 0.3,
            'roi_ratio': 0.25,
            'red_cooldown': 2.0,
            'binary_thresh': 80,
        }],
    )

    return LaunchDescription([
        gz_camera_arg,
        gz_cmd_vel_arg,
        bridge_node,
        follower_node,
    ])
