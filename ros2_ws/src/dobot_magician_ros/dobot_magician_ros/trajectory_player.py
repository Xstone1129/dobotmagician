"""Publish a fast, joint-limit-safe pick-and-place path to Gazebo."""
import os

import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

class TrajectoryPlayer(Node):
    def __init__(self):
        super().__init__('trajectory_player')
        self.pub = self.create_publisher(JointTrajectory, '/arm_controller/joint_trajectory', 10)
        self.timer = self.create_timer(0.5, self.send_once)
        self.sent = False

    def send_once(self):
        if self.sent:
            return
        # All values are radians and remain inside the migrated URDF limits.
        # The sequence approximates: home -> pick_box -> lift -> place_table -> home.
        waypoints = [
            (0.0, 0.0, 0.0, 0.0),
            (-0.70, 0.45, 0.70, -0.50),
            (-0.70, 0.75, 0.70, -0.50),
            (-0.70, 0.45, 0.70, -0.50),
            (1.10, 0.45, 0.70, -0.50),
            (1.10, 0.75, 0.70, -0.50),
            (1.10, 0.45, 0.70, -0.50),
            (0.0, 0.0, 0.0, 0.0),
        ]
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


def main():
    # The hotspot Fast DDS profile filters local interfaces and breaks discovery.
    # This node targets the local Gazebo simulation, so use the default profile.
    os.environ.pop('FASTRTPS_DEFAULT_PROFILES_FILE', None)
    rclpy.init()
    node = TrajectoryPlayer()
    rclpy.spin_once(node, timeout_sec=5.0)
    node.destroy_node()
    rclpy.shutdown()
