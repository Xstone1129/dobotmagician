from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class PrimitiveBase(ABC):
    """Common rollout contract for DMP, segmented DMP, and ProMP."""

    @abstractmethod
    def fit(self, trajectory: np.ndarray) -> PrimitiveBase:
        raise NotImplementedError

    @abstractmethod
    def rollout(self) -> np.ndarray:
        raise NotImplementedError
