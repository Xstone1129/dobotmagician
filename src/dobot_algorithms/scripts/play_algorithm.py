"""Play one learned Cartesian trajectory on the ROS 2 Dobot controller.

The model is selected explicitly so that comparisons use the same runtime path.
"""
from __future__ import annotations

import argparse
import subprocess
import time

import numpy as np
import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

from dobot_algorithms.data_io import load_config, load_model
from dobot_magician_ros.kinematics import inverse_kinematics


ALGORITHMS = ("gmm_gmr_dmp", "inc_gmm_gmr_dmp", "gmm_gmr_segmented_dmp", "bgmm_gmr_promp")


class AlgorithmPlayer(Node):
    def __init__(self, algorithm: str, config: dict, speed: float) -> None:
        super().__init__("algorithm_player")
        self.pub = self.create_publisher(JointTrajectory, "/arm_controller/joint_trajectory", 10)
        self.algorithm = algorithm
        self.speed = max(float(speed), 0.1)
        path = config[algorithm]["output_path"]
        model = load_model(path)
        trajectory = np.asarray(model.mean_trajectory(), dtype=float)
        if trajectory.shape[1] < 3:
            raise ValueError("The learned trajectory must contain X, Y and Z columns")
        # Downsample while preserving the learned endpoints and gripper signal.
        indices = np.linspace(0, len(trajectory) - 1, 16).round().astype(int)
        points = [inverse_kinematics(*row[:3]) for row in trajectory[indices]]
        msg = JointTrajectory(joint_names=["joint_1", "joint_2", "joint_3", "joint_4"])
        for index, joints in enumerate(points, 1):
            point = JointTrajectoryPoint(positions=list(joints))
            point.time_from_start.sec = int(round(index / self.speed))
            msg.points.append(point)
        self.msg = msg
        self.sent = False
        self.timer = self.create_timer(0.5, self.send)

    def send(self) -> None:
        if self.sent or self.pub.get_subscription_count() == 0:
            return
        self.pub.publish(self.msg)
        self.sent = True
        self.get_logger().info("Playing %s with %d waypoints", self.algorithm, len(self.msg.points))
        self.timer.cancel()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--algorithm", choices=ALGORITHMS, required=True)
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--speed", type=float, default=1.0, help="trajectory playback speed multiplier")
    args = parser.parse_args()
    config = load_config(args.config)
    rclpy.init()
    node = AlgorithmPlayer(args.algorithm, config, args.speed)
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
