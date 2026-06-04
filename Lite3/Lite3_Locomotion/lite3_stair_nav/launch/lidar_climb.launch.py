from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # Déclaration des paramètres configurables (avec leurs valeurs par défaut de ton script)
    frame_id_arg = DeclareLaunchArgument(
        'frame_id', default_value='rslidar',
        description="Frame de référence du capteur LiDAR"
    )
    input_topic_arg = DeclareLaunchArgument(
        'input_topic', default_value='/rslidar_points',
        description="Topic du nuage de points PointCloud2 entrant"
    )
    measurement_topic_arg = DeclareLaunchArgument(
        'measurement_topic', default_value='/stair_detection_robot/measurements',
        description="Topic de sortie des dimensions estimées"
    )
    ground_clearance_arg = DeclareLaunchArgument(
        'ground_clearance_m', default_value='0.06',
        description="Hauteur de sécurité minimale au-dessus du sol pour isoler l'escalier"
    )
    averaging_window_arg = DeclareLaunchArgument(
        'averaging_window_size', default_value='10',
        description="Taille de la fenêtre glissante de lissage pour les mesures stables"
    )

    return LaunchDescription([
        frame_id_arg,
        input_topic_arg,
        measurement_topic_arg,
        ground_clearance_arg,
        averaging_window_arg,

        Node(
            package='stair_climber',
            executable='lidar_climb', # Sera mappé dans le setup.py
            name='stair_climber_complete',
            output='screen',
            emulate_tty=True,
            parameters=[{
                'frame_id': LaunchConfiguration('frame_id'),
                'input_topic': LaunchConfiguration('input_topic'),
                'measurement_topic': LaunchConfiguration('measurement_topic'),
                'ground_clearance_m': LaunchConfiguration('ground_clearance_m'),
                'averaging_window_size': LaunchConfiguration('averaging_window_size'),
            }]
        )
    ])