from __future__ import annotations

import numpy as np

from dobot_algorithms.gmm.base import GMMBase
from dobot_algorithms.gmr.base import GMRBase
from dobot_algorithms.gmr_primitives import _regress_with_gmr


class ConditionalGMR(GMRBase):
    """Concrete GMR stage shared by every pipeline composition."""

    def __init__(self, output_dim: int, n_time_steps: int):
        self.output_dim = output_dim
        self.n_time_steps = n_time_steps

    def regress(self, model: GMMBase, query: np.ndarray) -> np.ndarray:
        means, covariances, weights = model.parameters()
        return _regress_with_gmr(means, covariances, weights, len(query), self.output_dim)
