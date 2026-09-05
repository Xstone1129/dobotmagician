from __future__ import annotations

import numpy as np
from scipy.special import logsumexp


def gmr(
    means: np.ndarray,
    covariances: np.ndarray,
    priors: np.ndarray,
    x_query: np.ndarray,
    input_dim: int,
    output_dim: int,
) -> np.ndarray:
    """Run Gaussian Mixture Regression on a fitted joint distribution p(x, y)."""
    means = np.asarray(means, dtype=float)
    covariances = np.asarray(covariances, dtype=float)
    priors = np.asarray(priors, dtype=float)
    x_query = np.asarray(x_query, dtype=float)

    if means.ndim != 2:
        raise ValueError("means must have shape (n_components, n_dimensions).")
    if covariances.ndim != 3:
        raise ValueError("covariances must have shape (n_components, n_dimensions, n_dimensions).")
    if input_dim + output_dim != means.shape[1]:
        raise ValueError("input_dim + output_dim must match the GMM dimensionality.")

    priors = priors / np.maximum(np.sum(priors), 1e-12)
    n_components = len(priors)
    mu_x = means[:, :input_dim]
    mu_y = means[:, input_dim:]
    sigma_xx = covariances[:, :input_dim, :input_dim]
    sigma_yx = covariances[:, input_dim:, :input_dim]

    log_weights = np.empty((len(x_query), n_components))
    conditional_means = np.empty((len(x_query), n_components, output_dim))
    for k in range(n_components):
        covariance = sigma_xx[k] + 1e-6 * np.eye(input_dim)
        diff = x_query - mu_x[k]
        solved = np.linalg.solve(covariance, diff.T).T
        sign, log_det = np.linalg.slogdet(covariance)
        if sign <= 0:
            raise ValueError("Input covariance must be positive definite.")
        # Responsibilities require the full Gaussian density, including its volume.
        log_weights[:, k] = (
            np.log(priors[k]) if priors[k] > 0 else -np.inf
        ) - 0.5 * (np.sum(diff * solved, axis=1) + log_det + input_dim * np.log(2 * np.pi))
        conditional_means[:, k] = mu_y[k] + solved @ sigma_yx[k].T
    weights = np.exp(log_weights - logsumexp(log_weights, axis=1, keepdims=True))
    return np.sum(weights[:, :, None] * conditional_means, axis=1)
