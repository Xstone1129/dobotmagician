from launch import LaunchDescription
from launch.actions import UnsetEnvironmentVariable
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg = FindPackageShare('dobot_magician_ros')
    xacro_file = PathJoinSubstitution([pkg, 'urdf', 'dobot_magician.urdf.xacro'])
    rviz_config = PathJoinSubstitution([pkg, 'rviz', 'dobot_magician.rviz'])
    description = ParameterValue(
        Command([FindExecutable(name='xacro'), ' ', xacro_file]), value_type=str
    )
    return LaunchDescription([
        # Ignore a host Fast DDS profile that filters every local interface.
        # RViz, joint_state_publisher, and robot_state_publisher must share the
        # default local discovery settings to exchange robot_description/TF.
        UnsetEnvironmentVariable('FASTRTPS_DEFAULT_PROFILES_FILE'),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': description}],
            output='screen',
        ),
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
            parameters=[{'zeros': {'joint_1': 0.0, 'joint_2': 0.0, 'joint_3': 0.0, 'joint_4': 0.0}}],
            output='screen',
        ),
        Node(package='rviz2', executable='rviz2', arguments=['-d', rviz_config], output='screen'),
    ])
