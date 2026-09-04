from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from dobot_algorithms.trajectory_selection import normalize_demo
from dobot_algorithms.primitives.base import PrimitiveBase


@dataclass(frozen=True)
class DMPConfig:
    n_time_steps: int = 150
    n_basis: int = 35
    alpha_z: float = 25.0
    beta_z: float = 6.25
    alpha_s: float = 4.0
    ridge_lambda: float = 1e-6


class DiscreteDMP(PrimitiveBase):
    """Multi-dimensional discrete DMP fitted to one reference trajectory."""

    def __init__(
        self,
        *,
        n_time_steps: int = 150,
        n_basis: int = 35,
        alpha_z: float = 25.0,
        beta_z: float = 6.25,
        alpha_s: float = 4.0,
        ridge_lambda: float = 1e-6,
    ) -> None:
        self.config = DMPConfig(
            n_time_steps=n_time_steps,
            n_basis=n_basis,
            alpha_z=alpha_z,
            beta_z=beta_z,
            alpha_s=alpha_s,
            ridge_lambda=ridge_lambda,
        )
        self.weights_: np.ndarray | None = None
        self.y0_: np.ndarray | None = None
        self.goal_: np.ndarray | None = None
        self.demo_mean_: np.ndarray | None = None
        self.n_dims: int | None = None

    def fit(self, trajectories: list[np.ndarray]) -> DiscreteDMP:
        if not trajectories:
            raise ValueError("At least one trajectory is required to fit a DMP.")
        normalized = [normalize_demo(traj, self.config.n_time_steps) for traj in trajectories]
        self.n_dims = normalized[0].shape[1]
        if any(traj.shape[1] != self.n_dims for traj in normalized):
            raise ValueError("All DMP trajectories must have the same dimensionality.")

        self.demo_mean_ = np.mean(np.stack(normalized), axis=0)
        self.y0_ = self.demo_mean_[0].copy()
        self.goal_ = self.demo_mean_[-1].copy()
        self.weights_ = self._fit_forcing_terms(self.demo_mean_)
        return self

    def dynamic_rollout(self) -> np.ndarray:
        self._require_fit()
        phase, basis = self._basis()
        forcing = self._forcing(phase, basis)
        goal_delta = self.goal_ - self.y0_
        safe_goal_delta = np.where(np.abs(goal_delta) < 1e-6, 1.0, goal_delta)
        dt = 1.0 / max(self.config.n_time_steps - 1, 1)

        y = self.y0_.copy()
        dy = np.zeros_like(y)
        trajectory = np.empty((self.config.n_time_steps, self.n_dims), dtype=float)
        for i in range(self.config.n_time_steps):
            trajectory[i] = y
            ddy = (
                self.config.alpha_z * (self.config.beta_z * (self.goal_ - y) - dy)
                + forcing[i] * safe_goal_delta
            )
            dy = dy + ddy * dt
            y = y + dy * dt
        trajectory = self._smooth_goal_transition(trajectory)
        if self.n_dims is not None and self.n_dims >= 4:
            trajectory[:, 3] = np.clip(trajectory[:, 3], 0.0, 1.0)
        return trajectory

    def rollout(self) -> np.ndarray:
        """PrimitiveBase-compatible name for dynamic_rollout."""
        return self.dynamic_rollout()

    def _smooth_goal_transition(self, trajectory: np.ndarray, window: int = 8) -> np.ndarray:
        """Blend the tail to the goal instead of snapping only the final point."""
        if len(trajectory) <= 1:
            return trajectory
        window = min(window, len(trajectory))
        weights = np.linspace(0.0, 1.0, window)[:, None]
        trajectory[-window:] = (1.0 - weights) * trajectory[-window:] + weights * self.goal_
        trajectory[-1] = self.goal_
        return trajectory

    def _fit_forcing_terms(self, trajectory: np.ndarray) -> np.ndarray:
        phase, basis = self._basis()
        dt = 1.0 / max(self.config.n_time_steps - 1, 1)
        dy = np.gradient(trajectory, dt, axis=0)
        ddy = np.gradient(dy, dt, axis=0)

        goal_delta = self.goal_ - self.y0_
        safe_goal_delta = np.where(np.abs(goal_delta) < 1e-6, 1.0, goal_delta)
        target_forcing = (
            ddy - self.config.alpha_z * (self.config.beta_z * (self.goal_ - trajectory) - dy)
        ) / safe_goal_delta

        features = basis * phase[:, None]
        lhs = features.T @ features + self.config.ridge_lambda * np.eye(features.shape[1])
        rhs = features.T @ target_forcing
        return np.linalg.solve(lhs, rhs).T

    def _forcing(self, phase: np.ndarray, basis: np.ndarray) -> np.ndarray:
        weighted = basis @ self.weights_.T
        return weighted * phase[:, None]

    def _basis(self) -> tuple[np.ndarray, np.ndarray]:
        t = np.linspace(0.0, 1.0, self.config.n_time_steps)
        phase = np.exp(-self.config.alpha_s * t)
        centers = np.exp(-self.config.alpha_s * np.linspace(0.0, 1.0, self.config.n_basis))
        widths = np.full(self.config.n_basis, self.config.n_basis**1.5 / max(self.config.alpha_s, 1e-6))
        basis = np.exp(-widths[None, :] * (phase[:, None] - centers[None, :]) ** 2)
        return phase, basis / np.maximum(basis.sum(axis=1, keepdims=True), 1e-12)

    def _require_fit(self) -> None:
        if self.weights_ is None or self.demo_mean_ is None:
            raise RuntimeError("Fit the DMP before rollout.")
