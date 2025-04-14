# metric_depth/utils.py

"""
Utility functions for depth estimation evaluation
"""
from typing import Optional
import numpy as np

def rgb_to_grayscale_depth(rgb: np.ndarray) -> np.ndarray:
    """
    Convert an RGB image (H x W x 3) to a single-channel grayscale image
    using standard luminance formula.

    Parameters:
        rgb (np.ndarray): RGB image with shape (H, W, 3), dtype=float or uint8.

    Returns:
        np.ndarray: Grayscale image with shape (H, W).
    """
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError("Input must be an RGB image with shape (H, W, 3).")

    # Normalize if dtype is uint8
    if rgb.dtype == np.uint8:
        rgb = rgb.astype(np.float32) / 255.0

    # Grayscale conversion: Y = 0.299 R + 0.587 G + 0.114 B
    grayscale = np.dot(rgb[..., :3], [0.299, 0.587, 0.114])
    return grayscale

def scale_and_shift_align(pred: np.ndarray, gt: np.ndarray, mask: Optional[np.ndarray] = None) -> np.ndarray:
    """
    Perform scale and shift alignment (least squares fit) of predicted depth
    to the ground truth depth.

    Finds α and β such that:
        aligned_pred = α * pred + β

    Parameters:
        pred (np.ndarray): Predicted depth map (H, W)
        gt (np.ndarray): Ground truth depth map (H, W)
        mask (np.ndarray, optional): Boolean mask where gt is valid (H, W)

    Returns:
        np.ndarray: Aligned prediction with the same shape as input.
    """
    if pred.shape != gt.shape:
        raise ValueError("Shape mismatch: pred and gt must have the same shape.")
    
    if mask is None:
        mask = gt > 0

    x = pred[mask].reshape(-1, 1)
    y = gt[mask].reshape(-1, 1)

    # Add bias column for β
    A = np.hstack([x, np.ones_like(x)])

    # Solve for [α, β] via least squares
    result = np.linalg.lstsq(A, y, rcond=None)
    alpha, beta = result[0].squeeze()

    return alpha * pred + beta