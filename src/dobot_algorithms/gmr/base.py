from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from dobot_algorithms.gmm.base import GMMBase


class GMRBase(ABC):
    """Regression stage consuming any compatible GMM implementation."""

    @abstractmethod
    def regress(self, model: GMMBase, query: np.ndarray) -> np.ndarray:
        raise NotImplementedError
