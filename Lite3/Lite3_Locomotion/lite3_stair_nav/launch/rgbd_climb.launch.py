from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # Déclaration des arguments configurables
    sync_slop_arg = DeclareLaunchArgument(
        'sync_slop', default_value='0.1',
        description="Tolérance temporelle en secondes pour la synchronisation ApproximateTimeSynchronizer"
    )

    return LaunchDescription([
        sync_slop_arg,

        Node(
            package='stair_climber',
            executable='rgbd_climb', # Doit correspondre à l'entrée dans ton setup.py
            name='stair_climber_nav',
            output='screen',
            emulate_tty=True,
            parameters=[{
                'sync_slop': LaunchConfiguration('sync_slop'),
            }]
        )
    ])