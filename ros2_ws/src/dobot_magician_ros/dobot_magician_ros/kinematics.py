"""Dobot Magician kinematics using the supplied standard-DH table.

The table is kept in ``config/dh_parameters.yaml`` for inspection and tooling.
These constants mirror that file so this module remains usable in a source
checkout and in unit tests without a ROS package index.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation


@dataclass(frozen=True)
class DHParameters:
    d1: float = 0.0080
    a2: float = 0.1350
    a3: float = 0.1470
    a4: float = 0.0597


DH = DHParameters()


def inverse_kinematics(
    x: float,
    y: float,
    tip_z: float,
    dh: DHParameters = DH,
    *,
    vertical_tool: bool = False,
) -> tuple[float, float, float, float]:
    """Solve the migrated URDF chain, optionally keeping the cup face horizontal."""
    target = np.array([x, y, tip_z], dtype=float)

    def residual(q: np.ndarray) -> np.ndarray:
        position_error = _urdf_tip_position(q) - target
        if vertical_tool:
            # The two flipped URDF joint frames give this upright-tool constraint.
            return np.append(position_error, 0.1 * (q[1] - q[2] + q[3]))
        return position_error

    result = least_squares(
        residual,
        x0=np.array([math.atan2(y, x), 0.8, 0.8, 0.0]),
        bounds=(np.array([-math.pi, 0.0, 0.0, -0.5]), np.array([math.pi, math.pi / 2, math.pi / 2, 0.5])),
        max_nfev=2000,
    )
    position_error = np.linalg.norm(_urdf_tip_position(result.x) - target)
    angle_error = abs(result.x[1] - result.x[2] + result.x[3])
    if not result.success or position_error > 2e-4 or (vertical_tool and angle_error > 1e-3):
        raise ValueError(f"Unreachable suction tip: ({x:.3f}, {y:.3f}, {tip_z:.3f})")
    return tuple(float(value) for value in result.x)


def _transform(xyz: tuple[float, float, float], rpy: tuple[float, float, float]) -> np.ndarray:
    transform = np.eye(4)
    transform[:3, :3] = Rotation.from_euler("xyz", rpy).as_matrix()
    transform[:3, 3] = xyz
    return transform


def _urdf_tip_position(q: np.ndarray) -> np.ndarray:
    origins = [
        ((0.0, 0.0, 0.024), (0.0, 0.0, 0.0)),
        ((-0.01175, 0.0, 0.114), (1.570796325, 0.0, -1.570796325)),
        ((0.02699, 0.13228, -0.01175), (0.0, math.pi, 0.0)),
        ((0.07431, -0.12684, 0.0), (0.0, math.pi, 0.0)),
    ]
    transform = np.eye(4)
    for index, (xyz, rpy) in enumerate(origins):
        transform = transform @ _transform(xyz, rpy) @ _transform((0.0, 0.0, 0.0), (0.0, 0.0, q[index]))
    transform = transform @ _transform((-0.0328, -0.02, 0.0), (-1.57, 0.0, 0.0))
    return transform[:3, 3]


def forward_position(q1: float, q2: float, q3: float, q4: float, dh: DHParameters = DH) -> tuple[float, float, float]:
    """Return the vertical-tool position for the supplied DH joint angles."""
    radial = (
        dh.a2 * math.cos(q2)
        + dh.a3 * math.cos(q2 + q3)
        + dh.a4 * math.cos(q2 + q3 + q4)
    )
    height = dh.d1 - dh.a2 * math.sin(q2) - dh.a3 * math.sin(q2 + q3)
    return radial * math.cos(q1), radial * math.sin(q1), height
