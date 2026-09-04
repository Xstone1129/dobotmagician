from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np


class GMMBase(ABC):
    """Common contract for batch, incremental, and Bayesian GMMs."""

    @abstractmethod
    def fit(self, data: np.ndarray) -> GMMBase:
        raise NotImplementedError

    @abstractmethod
    def parameters(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Return means, covariances, and normalized component weights."""
        raise NotImplementedError

    def raw_model(self) -> Any:
        """Return the underlying estimator when a caller needs it."""
        return self
