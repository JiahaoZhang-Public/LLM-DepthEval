# metric_depth/utils.py

"""
Utility functions for depth estimation evaluation

Included :
- rgb_to_grayscale_depth: Convert an RGB image (H x W x 3) to a single-channel grayscale image
- scale_and_shift_align: Perform scale and shift alignment (least squares fit) of predicted depth
to the ground truth depth.

Author: Jiahao Zhang
Date: 2025-04-14
"""
from typing import Optional, Tuple
import numpy as np
import cv2


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

def resize_depth_map(
    depth: np.ndarray,
    target_shape: Tuple[int, int],
    interpolation: str = "linear",
) -> np.ndarray:
    """
    Resize a single-channel depth map to `target_shape` via OpenCV.

    Parameters:
        depth: (H, W) depth map.
        target_shape: (new_H, new_W).
        interpolation: "nearest" or "linear".

    Returns:
        Resized depth map of shape (new_H, new_W).
    """
    inter = cv2.INTER_NEAREST if interpolation == "nearest" else cv2.INTER_LINEAR
    return cv2.resize(depth, (target_shape[1], target_shape[0]), interpolation=inter)


def pad_to_aspect_ratio(
    image: np.ndarray,
    target_ratio: float,
    pad_value: float = 0.0,
) -> np.ndarray:
    """
    Pad a 2D array symmetrically so that width/height == target_ratio.

    Parameters:
        image: (H, W) array to pad.
        target_ratio: desired W/H.
        pad_value: fill value.

    Returns:
        Padded array.
    """
    h, w = image.shape
    current = w / h
    if abs(current - target_ratio) < 1e-6:
        return image
    # decide padding on width or height
    if current < target_ratio:
        # need to pad width
        new_w = int(target_ratio * h)
        pad = (new_w - w) // 2
        return np.pad(image, ((0, 0), (pad, new_w - w - pad)), constant_values=pad_value)
    else:
        # need to pad height
        new_h = int(w / target_ratio)
        pad = (new_h - h) // 2
        return np.pad(image, ((pad, new_h - h - pad), (0, 0)), constant_values=pad_value)


def compute_valid_mask(
    gt: np.ndarray,
    invalid_val: float = 0.0,
) -> np.ndarray:
    """
    Build a boolean mask of valid pixels in the ground truth map.

    Parameters:
        gt: ground‑truth depth (H, W).
        invalid_val: value to treat as invalid (e.g., 0 or negative).

    Returns:
        mask: Boolean array where gt > invalid_val.
    """
    return gt > invalid_val