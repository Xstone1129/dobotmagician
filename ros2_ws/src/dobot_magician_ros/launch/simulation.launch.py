from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, SetEnvironmentVariable, UnsetEnvironmentVariable
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg = FindPackageShare('dobot_magician_ros')
    xacro_file = PathJoinSubstitution([pkg, 'urdf', 'dobot_magician.urdf.xacro'])
    world = PathJoinSubstitution([pkg, 'worlds', 'suction_turn.sdf'])
    description = ParameterValue(
        Command([FindExecutable(name='xacro'), ' ', xacro_file]), value_type=str
    )
    return LaunchDescription([
        DeclareLaunchArgument('gui', default_value='true'),
        # The user's hotspot Fast DDS profile filters every interface on this host.
        # Gazebo and ROS must use the default local discovery profile for simulation.
        UnsetEnvironmentVariable('FASTRTPS_DEFAULT_PROFILES_FILE'),
        SetEnvironmentVariable(
            'GZ_SIM_SYSTEM_PLUGIN_PATH',
            [PathJoinSubstitution([FindPackageShare('dobot_suction'), '../../lib']),
             ':/opt/ros/jazzy/lib'],
        ),
        # Gazebo Sim does not reliably resolve ROS package:// URIs unless the
        # installed package share directory is on its resource search path.
        SetEnvironmentVariable('GZ_SIM_RESOURCE_PATH', pkg),
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             parameters=[{'robot_description': description, 'use_sim_time': True}]),
        ExecuteProcess(cmd=['gz', 'sim', '-r', world], output='screen',
                       condition=IfCondition(LaunchConfiguration('gui'))),
        ExecuteProcess(cmd=['gz', 'sim', '-s', '-r', world], output='screen',
                       condition=UnlessCondition(LaunchConfiguration('gui'))),
        Node(package='ros_gz_bridge', executable='parameter_bridge',
             arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
                        '/dobot_magician/suction_state@std_msgs/msg/String[gz.msgs.StringMsg'],
             parameters=[{'use_sim_time': True}], output='screen'),
        Node(package='ros_gz_sim', executable='create',
             arguments=['-topic', 'robot_description', '-name', 'dobot_magician'], output='screen'),
        Node(package='controller_manager', executable='spawner',
             arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager',
                        '--controller-manager-timeout', '60'],
             parameters=[{'use_sim_time': True}], output='screen'),
        Node(package='controller_manager', executable='spawner',
             arguments=['arm_controller', '--controller-manager', '/controller_manager',
                        '--controller-manager-timeout', '60'],
             parameters=[{'use_sim_time': True}], output='screen'),
    ])
