# tests/test_metrics.py

"""
Unit tests for Depth Estimation Metrics

Tested Functions:
- abs_rel
- threshold_accuracy
- rmse

Developer: Advanced AI Algorithm Engineer
"""

import numpy as np
import pytest

from metric_depth.metrics import abs_rel, threshold_accuracy, rmse



@pytest.fixture
def example_data():
    """Returns a basic ground truth and prediction pair for testing."""
    gt = np.array([1.0, 2.0, 3.0, 4.0])
    pred = np.array([1.1, 2.0, 2.7, 3.8])
    return gt, pred


def test_abs_rel_basic(example_data):
    gt, pred = example_data
    expected = np.mean(np.abs(gt - pred) / gt)
    assert np.isclose(abs_rel(gt, pred), expected), "AbsRel computation failed."


def test_threshold_accuracy_delta1(example_data):
    gt, pred = example_data
    delta = threshold_accuracy(gt, pred, threshold=1.25)
    assert 0.0 <= delta <= 1.0, "δ1 must be in [0, 1] range."


def test_rmse_basic(example_data):
    gt, pred = example_data
    expected = np.sqrt(np.mean((gt - pred) ** 2))
    assert np.isclose(rmse(gt, pred), expected), "RMSE computation failed."


def test_with_mask():
    gt = np.array([1.0, 2.0, 3.0, 4.0])
    pred = np.array([1.1, 2.1, 3.1, 3.5])
    mask = np.array([True, False, True, False])
    expected_abs_rel = np.mean(np.abs(gt[mask] - pred[mask]) / gt[mask])

    assert np.isclose(abs_rel(gt, pred, mask), expected_abs_rel), "Masked AbsRel failed."
    assert np.isclose(rmse(gt, pred, mask), np.sqrt(np.mean((gt[mask] - pred[mask]) ** 2))), "Masked RMSE failed."


def test_invalid_shape():
    gt = np.array([1.0, 2.0])
    pred = np.array([[1.0, 2.0]])
    with pytest.raises(ValueError):
        abs_rel(gt, pred)


def test_invalid_type():
    gt = [1.0, 2.0]
    pred = [1.0, 2.0]
    with pytest.raises(TypeError):
        rmse(gt, pred)