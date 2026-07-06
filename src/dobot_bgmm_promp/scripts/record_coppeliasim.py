from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path

from dobot_bgmm_promp.io import load_config, project_path


def _next_demo_path(demos_dir: str | Path) -> Path:
    demos_path = project_path(demos_dir)
    demos_path.mkdir(parents=True, exist_ok=True)
    existing = sorted(demos_path.glob("demo_*.csv"))
    max_index = 0
    for path in existing:
        try:
            max_index = max(max_index, int(path.stem.split("_")[-1]))
        except ValueError:
            continue
    return demos_path / f"demo_{max_index + 1:02d}.csv"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Record Dobot tip Cartesian positions from CoppeliaSim as t,x,y,z CSV."
    )
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--output", help="CSV output path. Defaults to next data/demos/demo_XX.csv.")
    parser.add_argument("--tip-path", help="CoppeliaSim object path to record. Defaults to config value.")
    parser.add_argument("--duration", type=float, default=10.0, help="Recording duration in seconds.")
    parser.add_argument("--sample-dt", type=float, default=0.03, help="Sampling interval in seconds.")
    parser.add_argument("--start", action="store_true", help="Start/stop the simulation around recording.")
    args = parser.parse_args()

    if args.duration <= 0:
        raise ValueError("--duration must be positive.")
    if args.sample_dt <= 0:
        raise ValueError("--sample-dt must be positive.")

    config = load_config(args.config)
    coppelia_config = config["coppeliasim"]
    tip_path = args.tip_path or coppelia_config.get("tip_path", "/tip")
    output_path = project_path(args.output) if args.output else _next_demo_path(config["data"]["demos_dir"])

    from coppeliasim_zmqremoteapi_client import RemoteAPIClient

    client = RemoteAPIClient(
        host=coppelia_config.get("host", "127.0.0.1"),
        port=coppelia_config.get("port", 23000),
    )
    sim = client.require("sim")
    try:
        tip = sim.getObject(tip_path)
    except Exception as exc:
        raise RuntimeError(
            f"CoppeliaSim object was not found: {tip_path!r}. "
            "Set coppeliasim.tip_path in the config or pass --tip-path."
        ) from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if args.start:
        sim.startSimulation()

    try:
        start = time.perf_counter()
        next_sample = start
        with output_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["t", "x", "y", "z"])
            while True:
                now = time.perf_counter()
                elapsed = now - start
                if elapsed > args.duration:
                    break
                if now >= next_sample:
                    x, y, z = sim.getObjectPosition(tip, -1)
                    writer.writerow([f"{elapsed:.6f}", f"{x:.9f}", f"{y:.9f}", f"{z:.9f}"])
                    next_sample += args.sample_dt
                time.sleep(min(0.002, args.sample_dt / 10.0))
    finally:
        if args.start:
            sim.stopSimulation()

    print(f"Recorded CoppeliaSim trajectory to {output_path.resolve()}")


if __name__ == "__main__":
    main()
