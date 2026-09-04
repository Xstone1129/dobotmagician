"""Dobot Magician kinematics using the supplied standard-DH table.

The table is kept in ``config/dh_parameters.yaml`` for inspection and tooling.
These constants mirror that file so this module remains usable in a source
checkout and in unit tests without a ROS package index.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class DHParameters:
    d1: float = 0.0080
    a2: float = 0.1350
    a3: float = 0.1470
    a4: float = 0.0597


DH = DHParameters()


def inverse_kinematics(x: float, y: float, tip_z: float, dh: DHParameters = DH) -> tuple[float, float, float, float]:
    """Return a vertical-tool IK solution ``(q1, q2, q3, q4)`` in radians.

    The standard-DH frames use ``alpha1=-pi/2``.  With a vertical tool,
    ``q4=-(q2+q3)`` and the last DH link contributes only to the radial reach.
    This selects the elbow-up branch used by the physical joint limits.
    """
    q1 = math.atan2(y, x)
    radial = math.hypot(x, y) - dh.a4
    height = tip_z - dh.d1
    cosine = (radial * radial + height * height - dh.a2 * dh.a2 - dh.a3 * dh.a3) / (2.0 * dh.a2 * dh.a3)
    if not -1.0 <= cosine <= 1.0:
        raise ValueError(f"Unreachable suction tip: ({x:.3f}, {y:.3f}, {tip_z:.3f})")
    elbow = -math.acos(max(-1.0, min(1.0, cosine)))
    shoulder = math.atan2(-height, radial) - math.atan2(
        dh.a3 * math.sin(elbow), dh.a2 + dh.a3 * math.cos(elbow)
    )
    q2 = shoulder
    q3 = elbow
    q4 = -(q2 + q3)
    return q1, q2, q3, q4


def forward_position(q1: float, q2: float, q3: float, q4: float, dh: DHParameters = DH) -> tuple[float, float, float]:
    """Return the vertical-tool position for the supplied DH joint angles."""
    radial = (
        dh.a2 * math.cos(q2)
        + dh.a3 * math.cos(q2 + q3)
        + dh.a4 * math.cos(q2 + q3 + q4)
    )
    height = dh.d1 - dh.a2 * math.sin(q2) - dh.a3 * math.sin(q2 + q3)
    return radial * math.cos(q1), radial * math.sin(q1), height
