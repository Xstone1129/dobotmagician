"""Continuously log CoppeliaSim target/tip/suction tracking state."""

from __future__ import annotations

import argparse
import csv
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from dobot_bgmm_promp.io import load_config, project_path


def _position(sim, handle: int) -> np.ndarray:
    return np.asarray(sim.getObjectPosition(handle, -1), dtype=float)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Continuously log CoppeliaSim target, tip, and suction-cup tracking."
    )
    parser.add_argument("--config", default="configs/suction_arm.yaml")
    parser.add_argument("--output", default="logs/coppeliasim_follow.csv")
    parser.add_argument("--sample-dt", type=float, default=0.10)
    parser.add_argument(
        "--duration",
        type=float,
        default=0.0,
        help="Run for this many seconds; 0 means run until Ctrl+C.",
    )
    parser.add_argument("--no-console", action="store_true", help="Write the CSV without per-sample output.")
    args = parser.parse_args()
    if args.sample_dt <= 0:
        raise ValueError("--sample-dt must be positive.")
    if args.duration < 0:
        raise ValueError("--duration cannot be negative.")

    config = load_config(args.config)
    coppelia = config["coppeliasim"]
    target_path = coppelia.get("target_path", "/target")
    tip_path = coppelia.get("tip_path", "/tip") or "/tip"
    suction_path = coppelia.get("suction_path", "/SuctionCup")

    from coppeliasim_zmqremoteapi_client import RemoteAPIClient

    client = RemoteAPIClient(
        host=coppelia.get("host", "127.0.0.1"),
        port=int(coppelia.get("port", 23000)),
    )
    sim = client.require("sim")
    handles = {}
    for name, path in (("target", target_path), ("tip", tip_path), ("suction", suction_path)):
        if not path:
            handles[name] = None
            continue
        try:
            handles[name] = sim.getObject(path)
        except Exception as exc:
            if name == "suction":
                handles[name] = None
                print(f"WARNING: optional suction object {path!r} unavailable: {exc}")
            else:
                raise RuntimeError(f"Required CoppeliaSim object was not found: {path!r}") from exc

    output = project_path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "wall_time_utc", "elapsed_s", "simulation_time_s", "simulation_state",
        "target_x", "target_y", "target_z", "tip_x", "tip_y", "tip_z",
        "target_tip_error_m", "suction_x", "suction_y", "suction_z",
        "suction_tip_offset_m", "suction_parent_handle",
    ]
    print(f"Logging CoppeliaSim follow state to {output.resolve()}")
    print(f"target={target_path} tip={tip_path} suction={suction_path or '<disabled>'}")
    started = time.perf_counter()
    next_sample = started
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        try:
            while args.duration == 0 or time.perf_counter() - started < args.duration:
                now = time.perf_counter()
                if now < next_sample:
                    time.sleep(min(args.sample_dt / 5.0, next_sample - now))
                    continue
                target = _position(sim, handles["target"])
                tip = _position(sim, handles["tip"])
                target_tip_error = float(np.linalg.norm(target - tip))
                suction = _position(sim, handles["suction"]) if handles["suction"] is not None else np.full(3, np.nan)
                suction_tip_offset = float(np.linalg.norm(suction - tip)) if handles["suction"] is not None else float("nan")
                parent = sim.getObjectParent(handles["suction"]) if handles["suction"] is not None else -1
                elapsed = now - started
                row = {
                    "wall_time_utc": datetime.now(timezone.utc).isoformat(),
                    "elapsed_s": f"{elapsed:.6f}",
                    "simulation_time_s": f"{float(sim.getSimulationTime()):.6f}",
                    "simulation_state": int(sim.getSimulationState()),
                    "target_x": f"{target[0]:.9f}", "target_y": f"{target[1]:.9f}", "target_z": f"{target[2]:.9f}",
                    "tip_x": f"{tip[0]:.9f}", "tip_y": f"{tip[1]:.9f}", "tip_z": f"{tip[2]:.9f}",
                    "target_tip_error_m": f"{target_tip_error:.9f}",
                    "suction_x": f"{suction[0]:.9f}", "suction_y": f"{suction[1]:.9f}", "suction_z": f"{suction[2]:.9f}",
                    "suction_tip_offset_m": f"{suction_tip_offset:.9f}",
                    "suction_parent_handle": parent,
                }
                writer.writerow(row)
                stream.flush()
                if not args.no_console:
                    print(
                        f"t={elapsed:8.3f}s sim={row['simulation_state']} "
                        f"target=({target[0]: .4f},{target[1]: .4f},{target[2]: .4f}) "
                        f"tip=({tip[0]: .4f},{tip[1]: .4f},{tip[2]: .4f}) "
                        f"err={target_tip_error:.4f}m suction_tip={suction_tip_offset:.4f}m parent={parent}",
                        flush=True,
                    )
                next_sample += args.sample_dt
        except KeyboardInterrupt:
            print("Stopped by user.")
    print(f"Saved {output.resolve()}")


if __name__ == "__main__":
    main()
