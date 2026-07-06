from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser(description="Create synthetic CSV demos for pipeline testing.")
    parser.add_argument("--output-dir", default="data/demos")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = Path(__file__).resolve().parents[1] / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    phase = np.linspace(0.0, 1.0, 120)
    for idx, offset in enumerate([0.0, 0.018, -0.014, 0.01, -0.006], start=1):
        t = 2.5 * phase
        x = 0.18 + 0.10 * phase
        y = offset + 0.055 * np.sin(np.pi * phase)
        z = 0.09 + 0.025 * np.sin(2.0 * np.pi * phase)
        trajectory = np.column_stack([t, x, y, z])
        np.savetxt(
            output_dir / f"demo_{idx:02d}.csv",
            trajectory,
            delimiter=",",
            header="t,x,y,z",
            comments="",
            fmt="%.8f",
        )

    print(f"Wrote sample demonstrations to {output_dir.resolve()}")


if __name__ == "__main__":
    main()
