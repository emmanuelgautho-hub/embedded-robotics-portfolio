import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='stair_climber',
            executable='blind_climb',
            name='stair_climber_blind',
            output='screen',
            emulate_tty=True
        )
    ])