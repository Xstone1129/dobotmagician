from __future__ import annotations

import numpy as np


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

    predictions = []
    for x in x_query:
        weights = np.empty(n_components, dtype=float)
        conditional_means = []
        for k in range(n_components):
            sigma_xx_reg = sigma_xx[k] + 1e-6 * np.eye(input_dim)
            inv_sigma_xx = np.linalg.inv(sigma_xx_reg)
            diff = x - mu_x[k]
            weights[k] = priors[k] * np.exp(-0.5 * diff @ inv_sigma_xx @ diff)
            conditional_means.append(mu_y[k] + sigma_yx[k] @ inv_sigma_xx @ diff)

        weights /= np.maximum(np.sum(weights), 1e-12)
        prediction = np.sum(
            [weights[k] * conditional_means[k] for k in range(n_components)],
            axis=0,
        )
        predictions.append(prediction)

    return np.asarray(predictions)
