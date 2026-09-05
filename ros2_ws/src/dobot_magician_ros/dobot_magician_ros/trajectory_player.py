"""Publish a fast, joint-limit-safe pick-and-place path to Gazebo."""
import os
import subprocess

import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

from .kinematics import inverse_kinematics

class TrajectoryPlayer(Node):
    def __init__(self):
        super().__init__('trajectory_player')
        self.pub = self.create_publisher(JointTrajectory, '/arm_controller/joint_trajectory', 10)
        self.timer = self.create_timer(0.5, self.send_once)
        self.sent = False
        self.attach_timer = None
        self.detach_timer = None
        self.stop_timer = None

    def stop(self):
        if self.stop_timer is not None:
            self.stop_timer.cancel()
        rclpy.shutdown()

    @staticmethod
    def _send_gazebo_command(topic: str) -> None:
        subprocess.run(
            ['gz', 'topic', '-t', topic, '-m', 'gz.msgs.Empty', '-p', 'unused: true'],
            check=False, timeout=2.0, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )

    def attach_box(self):
        if self.attach_timer is not None:
            self.attach_timer.cancel()
        self._send_gazebo_command('/dobot_magician/attach')
        self.get_logger().info('Requested suction attachment for pick_box.')

    def detach_box(self):
        if self.detach_timer is not None:
            self.detach_timer.cancel()
        self._send_gazebo_command('/dobot_magician/detach')
        self.get_logger().info('Requested suction release at place_table.')

    def send_once(self):
        if self.sent:
            return
        if self.pub.get_subscription_count() == 0:
            self.get_logger().info('Waiting for arm_controller trajectory subscriber...')
            return
        # The targets are the actual SDF object coordinates. Values are link_7
        # frame positions, solved through the migrated URDF chain.
        cartesian_waypoints = [
            None,                         # home
            (0.18, -0.15, 0.065),         # above pick_box
            (0.18, -0.15, 0.045),         # descend onto its top
            (0.18, -0.15, 0.065),         # lift
            (0.08, 0.16, 0.065),          # above red place_table
            (0.08, 0.16, 0.012),          # descend near placement surface
            (0.08, 0.16, 0.065),          # lift away
            None,                         # home
        ]
        waypoints = [(0.0, 0.0, 0.0, 0.0)]
        waypoints.extend(inverse_kinematics(*point) for point in cartesian_waypoints[1:-1])
        waypoints.append((0.0, 0.0, 0.0, 0.0))
        msg = JointTrajectory(joint_names=['joint_1', 'joint_2', 'joint_3', 'joint_4'])
        for i, positions in enumerate(waypoints):
            p = JointTrajectoryPoint(positions=list(positions))
            p.time_from_start.sec = i + 1
            msg.points.append(p)
        self.pub.publish(msg)
        self.get_logger().info(
            f'Sent {len(msg.points)} pick-and-place waypoints for pick_box; duration={len(msg.points)} s.'
        )
        self.sent = True
        # Start attachment/release timing only after the trajectory was accepted
        # by an active controller, avoiding commands racing Gazebo startup.
        self.attach_timer = self.create_timer(3.5, self.attach_box)
        self.detach_timer = self.create_timer(6.5, self.detach_box)
        self.stop_timer = self.create_timer(9.0, self.stop)


def main():
    # The hotspot Fast DDS profile filters local interfaces and breaks discovery.
    # This node targets the local Gazebo simulation, so use the default profile.
    os.environ.pop('FASTRTPS_DEFAULT_PROFILES_FILE', None)
    rclpy.init()
    node = TrajectoryPlayer()
    rclpy.spin(node)
    node.destroy_node()
