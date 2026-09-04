from __future__ import annotations

import numpy as np

from dobot_algorithms.gmm.base import GMMBase


class IncrementalGMM(GMMBase):
    """Simple online GMM approximation with adaptive component creation."""

    def __init__(self, lam: float = 0.1) -> None:
        self.lam = lam
        self.K = 0
        self.means: list[np.ndarray] = []
        self.covs: list[np.ndarray] = []
        self.counts: list[int] = []
        self.dist_accum: list[float] = []

    def partial_fit(self, x: np.ndarray) -> None:
        x = np.asarray(x, dtype=float)
        if self.K == 0:
            self._add_component(x, initial_cov=np.eye(x.size) * 1e-6)
            return

        distances = [np.linalg.norm(x - mean) for mean in self.means]
        k_star = int(np.argmin(distances))
        self.dist_accum[k_star] += distances[k_star]

        if self.dist_accum[k_star] > self.lam:
            self._add_component(x, initial_cov=np.eye(x.size) * 1e-6)
            return

        count = self.counts[k_star]
        delta = x - self.means[k_star]
        self.means[k_star] = self.means[k_star] + delta / (count + 1)
        eps = 1e-6 * np.eye(x.size)
        self.covs[k_star] = (
            ((count - 1) * self.covs[k_star] + np.outer(delta, delta) * count / (count + 1))
            / max(count, 1)
            + eps
        )
        self.counts[k_star] += 1

    def fit(self, data: np.ndarray) -> IncrementalGMM:
        for point in np.asarray(data, dtype=float):
            self.partial_fit(point)
        return self

    def parameters(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        counts = np.asarray(self.counts, dtype=float)
        return np.asarray(self.means), np.asarray(self.covs), counts / counts.sum()

    def _add_component(self, x: np.ndarray, *, initial_cov: np.ndarray) -> None:
        self.K += 1
        self.means.append(x.copy())
        self.covs.append(initial_cov.copy())
        self.counts.append(1)
        self.dist_accum.append(0.0)
