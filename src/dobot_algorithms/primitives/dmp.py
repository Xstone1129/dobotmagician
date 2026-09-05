from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp
from scipy.interpolate import CubicSpline

from dobot_algorithms.primitives.base import PrimitiveBase
from dobot_algorithms.trajectory_selection import normalize_demo


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
        self.zero_displacement_: np.ndarray | None = None
        self.initial_velocity_: np.ndarray | None = None

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
        self.zero_displacement_ = np.abs(self.goal_ - self.y0_) < 1e-6
        self.weights_ = self._fit_forcing_terms(self.demo_mean_)
        return self

    def dynamic_rollout(self) -> np.ndarray:
        self._require_fit()
        goal_delta = self.goal_ - self.y0_
        safe_goal_delta = np.where(np.abs(goal_delta) < 1e-6, 1.0, goal_delta)
        dt = 1.0 / max(self.config.n_time_steps - 1, 1)
        initial_velocity = getattr(self, "initial_velocity_", None)
        if initial_velocity is None:
            initial_velocity = np.zeros_like(self.y0_)

        def dynamics(t, state):
            phase, basis = self._basis(np.array([t]))
            forcing = self._forcing(phase, basis)[0]
            y, velocity = np.split(state, 2)
            acceleration = (
                self.config.alpha_z * (self.config.beta_z * (self.goal_ - y) - velocity)
                + forcing * safe_goal_delta
            )
            return np.concatenate([velocity, acceleration])

        # Unit forcing scale is well-defined for closed paths; do not bypass the ODE.
        solution = solve_ivp(
            dynamics, (0.0, 1.0), np.concatenate([self.y0_, initial_velocity]),
            t_eval=np.linspace(0.0, 1.0, self.config.n_time_steps),
            max_step=dt, rtol=1e-7, atol=1e-9,
        )
        if not solution.success:
            raise RuntimeError(f"DMP integration failed: {solution.message}")
        trajectory = solution.y[:self.n_dims].T.copy()
        if self.n_dims is not None and self.n_dims >= 4:
            trajectory[:, 3] = np.clip(trajectory[:, 3], 0.0, 1.0)
        return trajectory

    def rollout(self) -> np.ndarray:
        """PrimitiveBase-compatible name for dynamic_rollout."""
        return self.dynamic_rollout()

    def _fit_forcing_terms(self, trajectory: np.ndarray) -> np.ndarray:
        phase, basis = self._basis()
        times = np.linspace(0.0, 1.0, len(trajectory))
        spline = CubicSpline(times, trajectory, axis=0)
        dy = spline(times, 1)
        ddy = spline(times, 2)
        self.initial_velocity_ = dy[0].copy()

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

    def _basis(self, t: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
        if t is None:
            t = np.linspace(0.0, 1.0, self.config.n_time_steps)
        phase = np.exp(-self.config.alpha_s * t)
        centers = np.exp(-self.config.alpha_s * np.linspace(0.0, 1.0, self.config.n_basis))
        widths = np.full(self.config.n_basis, self.config.n_basis**1.5 / max(self.config.alpha_s, 1e-6))
        basis = np.exp(-widths[None, :] * (phase[:, None] - centers[None, :]) ** 2)
        return phase, basis / np.maximum(basis.sum(axis=1, keepdims=True), 1e-12)

    def _require_fit(self) -> None:
        if self.weights_ is None or self.demo_mean_ is None:
            raise RuntimeError("Fit the DMP before rollout.")
