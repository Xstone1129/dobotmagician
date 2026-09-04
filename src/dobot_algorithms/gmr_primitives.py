from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.mixture import BayesianGaussianMixture, GaussianMixture

from dobot_algorithms.dmp import DiscreteDMP
from dobot_algorithms.gmr.regression import gmr
from dobot_algorithms.incremental_gmm import IncrementalGMM
from dobot_algorithms.model_selection import normalize_demo, select_trajectory_for_place


@dataclass(frozen=True)
class GMRPrimitiveConfig:
    n_time_steps: int = 150
    n_components: int = 6
    covariance_type: str = "full"
    reg_covar: float = 1e-6
    random_state: int | None = None
    inc_lam: float = 0.25
    dmp_basis: int = 35
    dmp_alpha_z: float = 25.0
    dmp_beta_z: float = 6.25
    dmp_alpha_s: float = 4.0
    ridge_lambda: float = 1e-6
    n_segments: int = 4
    promp_basis: int = 25
    promp_basis_width: float = 0.08


class GMMGMRDMP:
    """Classic EM-GMM + GMR + DMP baseline."""

    def __init__(self, **kwargs) -> None:
        self.config = GMRPrimitiveConfig(**kwargs)
        self.n_dims: int | None = None
        self.gmm: GaussianMixture | None = None
        self.gmr_trajectory_: np.ndarray | None = None
        self.dmp_: DiscreteDMP | None = None
        self.trajectory_: np.ndarray | None = None

    def fit(self, demos: list[np.ndarray]) -> "GMMGMRDMP":
        trajectories = self._normalize_demos(demos)
        joint_points = _joint_time_output_points(trajectories)
        n_components = min(self.config.n_components, len(joint_points))
        self.gmm = GaussianMixture(
            n_components=n_components,
            covariance_type=self.config.covariance_type,
            reg_covar=self.config.reg_covar,
            random_state=self.config.random_state,
        ).fit(joint_points)
        self.gmr_trajectory_ = _regress_with_gmr(
            self.gmm.means_,
            self.gmm.covariances_,
            self.gmm.weights_,
            self.config.n_time_steps,
            self.n_dims,
        )
        self.trajectory_ = self._fit_dmp(self.gmr_trajectory_).dynamic_rollout()
        self._clip_gripper()
        return self

    def mean_trajectory(self) -> np.ndarray:
        self._require_fit()
        return self.trajectory_.copy()

    def sample_trajectories(self, n_samples: int = 1) -> np.ndarray:
        self._require_fit()
        return np.tile(self.mean_trajectory()[None, :, :], (n_samples, 1, 1))

    def component_trajectories(self) -> np.ndarray:
        self._require_fit()
        return self.mean_trajectory()[None, :, :]

    def mixture_parameters(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Return the exact fitted GMM used as the input to GMR visualization."""

        self._require_fit()
        if self.gmm is None:
            raise RuntimeError("This model has no fitted classic GMM.")
        return self.gmm.means_, self.gmm.covariances_, self.gmm.weights_

    def trajectory_for_place(
        self,
        place_index: int,
        place_positions: list[list[float]] | tuple[tuple[float, float, float], ...],
    ) -> np.ndarray:
        return select_trajectory_for_place(self.component_trajectories(), place_index, place_positions)

    def _normalize_demos(self, demos: list[np.ndarray]) -> list[np.ndarray]:
        if not demos:
            raise ValueError("At least one demonstration is required.")
        trajectories = [normalize_demo(demo, self.config.n_time_steps) for demo in demos]
        self.n_dims = trajectories[0].shape[1]
        if any(traj.shape[1] != self.n_dims for traj in trajectories):
            raise ValueError("All demonstrations must have the same number of dimensions.")
        return trajectories

    def _fit_dmp(self, reference: np.ndarray) -> DiscreteDMP:
        self.dmp_ = DiscreteDMP(
            n_time_steps=self.config.n_time_steps,
            n_basis=self.config.dmp_basis,
            alpha_z=self.config.dmp_alpha_z,
            beta_z=self.config.dmp_beta_z,
            alpha_s=self.config.dmp_alpha_s,
            ridge_lambda=self.config.ridge_lambda,
        ).fit([reference])
        return self.dmp_

    def _clip_gripper(self) -> None:
        if self.n_dims is not None and self.n_dims >= 4:
            self.trajectory_[:, 3] = np.clip(self.trajectory_[:, 3], 0.0, 1.0)

    def _require_fit(self) -> None:
        if self.trajectory_ is None:
            raise RuntimeError("Fit the model before using it.")


class IncGMMGMRDMP(GMMGMRDMP):
    """Incremental GMM + GMR + DMP."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.inc_gmm: IncrementalGMM | None = None

    def fit(self, demos: list[np.ndarray]) -> "IncGMMGMRDMP":
        trajectories = self._normalize_demos(demos)
        self.inc_gmm = IncrementalGMM(lam=self.config.inc_lam)
        for point in _joint_time_output_points(trajectories):
            self.inc_gmm.partial_fit(point)
        means = np.asarray(self.inc_gmm.means, dtype=float)
        covs = np.asarray(self.inc_gmm.covs, dtype=float)
        priors = np.asarray(self.inc_gmm.counts, dtype=float)
        priors /= np.sum(priors)
        self.gmr_trajectory_ = _regress_with_gmr(
            means,
            covs,
            priors,
            self.config.n_time_steps,
            self.n_dims,
        )
        self.trajectory_ = self._fit_dmp(self.gmr_trajectory_).dynamic_rollout()
        self._clip_gripper()
        return self

    def mixture_parameters(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        self._require_fit()
        if self.inc_gmm is None:
            raise RuntimeError("This model has no fitted incremental GMM.")
        counts = np.asarray(self.inc_gmm.counts, dtype=float)
        return (
            np.asarray(self.inc_gmm.means, dtype=float),
            np.asarray(self.inc_gmm.covs, dtype=float),
            counts / counts.sum(),
        )


class GMMGMRSegmentedDMP(GMMGMRDMP):
    """GMM + GMR with a segmented DMP movement primitive."""

    def fit(self, demos: list[np.ndarray]) -> "GMMGMRSegmentedDMP":
        super().fit(demos)
        self.trajectory_ = _segmented_dmp_rollout(
            self.gmr_trajectory_,
            self.config.n_segments,
            self.config,
        )
        self._clip_gripper()
        return self


class BGMMGMRProMP(GMMGMRDMP):
    """Bayesian GMM + GMR with a ProMP trajectory representation."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.bgmm: BayesianGaussianMixture | None = None
        self.promp_weights_: np.ndarray | None = None

    def fit(self, demos: list[np.ndarray]) -> "BGMMGMRProMP":
        trajectories = self._normalize_demos(demos)
        joint_points = _joint_time_output_points(trajectories)
        n_components = min(self.config.n_components, len(joint_points))
        self.bgmm = BayesianGaussianMixture(
            n_components=n_components,
            covariance_type=self.config.covariance_type,
            reg_covar=self.config.reg_covar,
            weight_concentration_prior_type="dirichlet_process",
            random_state=self.config.random_state,
        ).fit(joint_points)
        self.gmr_trajectory_ = _regress_with_gmr(
            self.bgmm.means_,
            self.bgmm.covariances_,
            self.bgmm.weights_,
            self.config.n_time_steps,
            self.n_dims,
        )
        self.trajectory_ = self._promp_reconstruct(self.gmr_trajectory_)
        self._clip_gripper()
        return self

    def _promp_reconstruct(self, reference: np.ndarray) -> np.ndarray:
        phase = np.linspace(0.0, 1.0, self.config.n_time_steps)
        centers = np.linspace(0.0, 1.0, self.config.promp_basis)
        basis = np.exp(
            -0.5 * ((phase[:, None] - centers[None, :]) / self.config.promp_basis_width) ** 2
        )
        basis /= np.maximum(basis.sum(axis=1, keepdims=True), 1e-12)
        lhs = basis.T @ basis + self.config.ridge_lambda * np.eye(basis.shape[1])
        rhs = basis.T @ reference
        self.promp_weights_ = np.linalg.solve(lhs, rhs)
        return basis @ self.promp_weights_

    def mixture_parameters(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        self._require_fit()
        if self.bgmm is None:
            raise RuntimeError("This model has no fitted Bayesian GMM.")
        return self.bgmm.means_, self.bgmm.covariances_, self.bgmm.weights_


def _joint_time_output_points(trajectories: list[np.ndarray]) -> np.ndarray:
    n_steps = trajectories[0].shape[0]
    phase = np.linspace(0.0, 1.0, n_steps)
    return np.vstack([np.column_stack([phase, trajectory]) for trajectory in trajectories])


def _regress_with_gmr(
    means: np.ndarray,
    covs: np.ndarray,
    priors: np.ndarray,
    n_time_steps: int,
    output_dim: int,
) -> np.ndarray:
    query = np.linspace(0.0, 1.0, n_time_steps).reshape(-1, 1)
    trajectory = gmr(means, covs, priors, query, input_dim=1, output_dim=output_dim)
    if output_dim >= 4:
        trajectory[:, 3] = np.clip(trajectory[:, 3], 0.0, 1.0)
    return trajectory


def _segmented_dmp_rollout(
    reference: np.ndarray,
    n_segments: int,
    config: GMRPrimitiveConfig,
) -> np.ndarray:
    segments = np.array_split(reference, max(1, n_segments))
    rollouts = []
    for segment in segments:
        dmp = DiscreteDMP(
            n_time_steps=len(segment),
            n_basis=min(config.dmp_basis, max(2, len(segment) - 1)),
            alpha_z=config.dmp_alpha_z,
            beta_z=config.dmp_beta_z,
            alpha_s=config.dmp_alpha_s,
            ridge_lambda=config.ridge_lambda,
        ).fit([segment])
        rollouts.append(dmp.dynamic_rollout())
    return np.vstack(rollouts)
