from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg = FindPackageShare('dobot_magician_ros')
    simulation = PathJoinSubstitution([pkg, 'launch', 'simulation.launch.py'])
    return LaunchDescription([
        DeclareLaunchArgument('gui', default_value='true'),
        DeclareLaunchArgument('algorithm', default_value='gmm_gmr_dmp'),
        DeclareLaunchArgument('config', default_value='configs/suction_arm.yaml'),
        DeclareLaunchArgument('speed', default_value='1.0'),
        DeclareLaunchArgument('sample_period', default_value='0.08'),
        DeclareLaunchArgument('lead_in', default_value='2.0'),
        DeclareLaunchArgument('max_joint_speed', default_value='0.8'),
        DeclareLaunchArgument('max_waypoints', default_value='0'),
        DeclareLaunchArgument('startup_delay', default_value='8.0'),
        DeclareLaunchArgument('vertical_tail_fraction', default_value='1.0'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(simulation),
            launch_arguments={'gui': LaunchConfiguration('gui')}.items(),
        ),
        ExecuteProcess(
            cmd=[
                'python3',
                '-m',
                'dobot_algorithms.scripts.play_algorithm',
                '--algorithm', LaunchConfiguration('algorithm'),
                '--config', LaunchConfiguration('config'),
                '--speed', LaunchConfiguration('speed'),
                '--sample-period', LaunchConfiguration('sample_period'),
                '--lead-in', LaunchConfiguration('lead_in'),
                '--max-joint-speed', LaunchConfiguration('max_joint_speed'),
                '--max-waypoints', LaunchConfiguration('max_waypoints'),
                '--startup-delay', LaunchConfiguration('startup_delay'),
                '--vertical-tail-fraction', LaunchConfiguration('vertical_tail_fraction'),
            ],
            output='screen',
        ),
    ])
