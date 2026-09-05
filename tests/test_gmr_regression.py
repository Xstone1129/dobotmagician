import numpy as np

from dobot_algorithms.gmr.regression import gmr


def test_responsibilities_include_gaussian_normalization():
    means = np.array([[0.0, 1.0], [0.0, 0.0]])
    covariances = np.array([np.diag([0.01, 1.0]), np.diag([1.0, 1.0])])
    result = gmr(means, covariances, np.array([0.5, 0.5]), np.array([[0.0]]), 1, 1)
    densities = 1 / np.sqrt(np.array([0.01, 1.0]) + 1e-6)
    np.testing.assert_allclose(result[0, 0], densities[0] / densities.sum())


def test_far_query_does_not_underflow_to_zero():
    result = gmr(
        np.array([[0.0, 7.0]]), np.array([np.eye(2)]),
        np.array([1.0]), np.array([[1000.0]]), 1, 1,
    )
    np.testing.assert_allclose(result, [[7.0]])
