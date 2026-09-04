from setuptools import setup
from glob import glob
import os

package_name = 'dobot_magician_ros'
setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/urdf', glob(os.path.join('urdf', '*.xacro')) + glob(os.path.join('urdf', '*.urdf'))),
        ('share/' + package_name + '/meshes', glob(os.path.join('meshes', '*'))),
        ('share/' + package_name + '/config', glob(os.path.join('config', '*.yaml'))),
        ('share/' + package_name + '/rviz', glob(os.path.join('rviz', '*.rviz'))),
        ('share/' + package_name + '/launch', glob(os.path.join('launch', '*.launch.py'))),
        ('share/' + package_name + '/worlds', glob(os.path.join('worlds', '*.sdf'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    entry_points={'console_scripts': ['trajectory_player = dobot_magician_ros.trajectory_player:main']},
)
