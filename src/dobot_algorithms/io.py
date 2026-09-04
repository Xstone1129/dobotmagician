from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import yaml


def project_root() -> Path:
    """Return the repository root regardless of the current working directory."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").exists():
            return parent
    return Path.cwd()


def project_path(path: str | Path) -> Path:
    path = Path(path)
    if path.is_absolute():
        return path
    return project_root() / path


def load_config(path: str | Path) -> dict:
    with project_path(path).open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_demonstrations(
    demos_dir: str | Path,
    *,
    time_column: str,
    coordinate_columns: list[str],
    gripper_column: str | None = None,
) -> list[np.ndarray]:
    demos_path = project_path(demos_dir)
    csv_files = sorted(demos_path.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV demonstrations found in {demos_path.resolve()}")

    demos: list[np.ndarray] = []
    for csv_file in csv_files:
        header = np.genfromtxt(csv_file, delimiter=",", names=True, max_rows=1).dtype.names
        if header is None:
            raise ValueError(f"{csv_file} must contain a header row.")
        missing = [name for name in [time_column, *coordinate_columns] if name not in header]
        if missing:
            raise ValueError(f"{csv_file} is missing columns: {missing}")

        data = np.genfromtxt(csv_file, delimiter=",", names=True)
        if data.ndim == 0:
            raise ValueError(f"{csv_file} must contain at least two data rows.")

        order = np.argsort(data[time_column])
        cols = [data[col][order] for col in coordinate_columns]
        if gripper_column:
            if gripper_column not in header:
                raise ValueError(f"{csv_file} is missing required gripper column: {gripper_column}")
            cols.append(data[gripper_column][order])
        trajectory = np.column_stack(cols)
        demos.append(trajectory)
    return demos


def save_model(model: object, path: str | Path) -> None:
    output_path = project_path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output_path)


def load_model(path: str | Path) -> object:
    return joblib.load(project_path(path))
