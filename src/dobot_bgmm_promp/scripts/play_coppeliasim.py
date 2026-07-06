from __future__ import annotations

import argparse

from dobot_bgmm_promp.coppeliasim_client import CoppeliaConfig, CoppeliaDobotClient
from dobot_bgmm_promp.io import load_config, load_model


def _model_path(config: dict) -> str:
    active_algorithm = config["model"].get("active_algorithm", config["model"].get("algorithm", "gmm_gmr_dmp"))
    if active_algorithm == "compare":
        active_algorithm = "gmm_gmr_dmp"
    if active_algorithm in {
        "gmm_gmr_dmp",
        "inc_gmm_gmr_dmp",
        "gmm_gmr_segmented_dmp",
        "bgmm_gmr_promp",
    }:
        return config[active_algorithm]["output_path"]
    raise ValueError(
        "model.active_algorithm must be one of: "
        "gmm_gmr_dmp, inc_gmm_gmr_dmp, gmm_gmr_segmented_dmp, bgmm_gmr_promp"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay a learned trajectory in CoppeliaSim.")
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--no-start", action="store_true", help="Do not start/stop the simulation.")
    parser.add_argument("--place-index", type=int, help="Select target place point. Only 1 is configured by default.")
    args = parser.parse_args()

    config = load_config(args.config)
    model = load_model(_model_path(config))
    coppeliasim = config["coppeliasim"]
    place_positions = coppeliasim.get(
        "place_positions",
        [
            [0.34, -0.16, 0.006],
        ],
    )
    place_index = args.place_index or coppeliasim.get("place_index")
    sim_config = CoppeliaConfig(
        host=coppeliasim["host"],
        port=coppeliasim["port"],
        target_path=coppeliasim["target_path"],
        tip_path=coppeliasim.get("tip_path"),
        playback_dt=coppeliasim["playback_dt"],
        gripper_signal=coppeliasim.get("gripper_signal"),
        left_gripper_joint_path=coppeliasim.get("left_gripper_joint_path"),
        right_gripper_joint_path=coppeliasim.get("right_gripper_joint_path"),
        block_path=coppeliasim.get("block_path"),
        block_local_position=tuple(coppeliasim.get("block_local_position", [0.0, 0.0, -0.018])),
        pick_position=tuple(coppeliasim.get("pick_position", [0.20, -0.16, 0.006])),
        place_positions=tuple(tuple(position) for position in place_positions),
        place_index=place_index,
        gripper_open_position=float(coppeliasim.get("gripper_open_position", 0.010)),
        gripper_closed_position=float(coppeliasim.get("gripper_closed_position", 0.000)),
        pickup_threshold=float(coppeliasim.get("pickup_threshold", 0.65)),
        release_threshold=float(coppeliasim.get("release_threshold", 0.35)),
        release_mode=str(coppeliasim.get("release_mode", "current_pose")),
        coordinate_scale=tuple(coppeliasim.get("coordinate_scale", [1.0, 1.0, 1.0])),
        coordinate_offset=tuple(coppeliasim.get("coordinate_offset", [0.0, 0.0, 0.0])),
    )

    if place_index:
        trajectory = model.trajectory_for_place(place_index, place_positions)
    elif coppeliasim.get("use_mean_trajectory", True):
        trajectory = model.mean_trajectory()
    else:
        sample_index = int(coppeliasim.get("sample_index", 0))
        trajectory = model.sample_trajectories(sample_index + 1)[sample_index]

    client = CoppeliaDobotClient(sim_config)
    client.connect()
    if not args.no_start:
        client.start()
    try:
        client.play_cartesian_trajectory(trajectory)
    finally:
        if not args.no_start:
            client.stop()


if __name__ == "__main__":
    main()
