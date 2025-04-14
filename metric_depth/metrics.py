# metrics.py

"""
Depth Estimation Evaluation Metrics

This module provides implementations of standard evaluation metrics
for monocular depth estimation tasks.

Included Metrics:
- Absolute Relative Error (AbsRel)
- Threshold Accuracy (δ1)
- Root Mean Squared Error (RMSE)

Author: Jiahao Zhang
Date: 2025-04-14
"""

import numpy as np
from typing import Union


def _validate_inputs(gt: np.ndarray, pred: np.ndarray) -> None:
    """Raise error if inputs are not valid."""

    if not isinstance(gt, np.ndarray) or not isinstance(pred, np.ndarray):
        raise TypeError("Inputs must be NumPy arrays.")

    if gt.shape != pred.shape:
        raise ValueError("Ground truth and prediction arrays must have the same shape.")


def abs_rel(
    gt: np.ndarray, pred: np.ndarray, mask: Union[np.ndarray, None] = None
) -> float:
    """
    Compute Absolute Relative Error (AbsRel).

    Parameters:
        gt (np.ndarray): Ground truth depth map.
        pred (np.ndarray): Predicted depth map.
        mask (np.ndarray, optional): Boolean array to mask invalid pixels.

    Returns:
        float: Absolute Relative Error.
    """
    _validate_inputs(gt, pred)

    if mask is not None:
        gt, pred = gt[mask], pred[mask]

    return np.mean(np.abs(gt - pred) / gt)


def threshold_accuracy(
    gt: np.ndarray,
    pred: np.ndarray,
    threshold: float = 1.25,
    mask: Union[np.ndarray, None] = None
) -> float:
    """
    Compute Threshold Accuracy δ, e.g., δ1 when threshold=1.25.

    Parameters:
        gt (np.ndarray): Ground truth depth map.
        pred (np.ndarray): Predicted depth map.
        threshold (float): Threshold value (e.g., 1.25, 1.25^2).
        mask (np.ndarray, optional): Boolean array to mask invalid pixels.

    Returns:
        float: Threshold accuracy (proportion of predictions within threshold).
    """
    _validate_inputs(gt, pred)

    if mask is not None:
        gt, pred = gt[mask], pred[mask]

    max_ratio = np.maximum(gt / pred, pred / gt)
    return np.mean(max_ratio < threshold)


def rmse(
    gt: np.ndarray, pred: np.ndarray, mask: Union[np.ndarray, None] = None
) -> float:
    """
    Compute Root Mean Squared Error (RMSE).

    Parameters:
        gt (np.ndarray): Ground truth depth map.
        pred (np.ndarray): Predicted depth map.
        mask (np.ndarray, optional): Boolean array to mask invalid pixels.

    Returns:
        float: Root Mean Squared Error.
    """
    _validate_inputs(gt, pred)

    if mask is not None:
        gt, pred = gt[mask], pred[mask]

    return np.sqrt(np.mean((gt - pred) ** 2))