import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple

from metric_depth.metrics import abs_rel, threshold_accuracy, rmse
from metric_depth.utils import compute_valid_mask, resize_depth_map, scale_and_shift_align


def global_metrics(
    gt: np.ndarray,
    pred: np.ndarray,
    mask: Optional[np.ndarray] = None
) -> Dict[str, float]:
    """
    Compute the standard global depth-estimation metrics:
      - Absolute Relative Error (AbsRel)
      - Threshold Accuracy δ1
      - Root Mean Squared Error (RMSE)

    Parameters:
        gt: Ground truth depth map of shape (H, W).
        pred: Predicted depth map of shape (H, W).
        mask: Optional boolean mask of valid pixels.

    Returns:
        A dict with keys 'AbsRel', 'δ1', and 'RMSE'.
    """
    if mask is None:
        mask = compute_valid_mask(gt)
    return {
        "AbsRel": abs_rel(gt, pred, mask),
        "δ1": threshold_accuracy(gt, pred, threshold=1.25, mask=mask),
        "RMSE": rmse(gt, pred, mask),
    }


def patch_metrics(
    gt: np.ndarray,
    pred: np.ndarray,
    patch_size: Tuple[int, int],
    mask: Optional[np.ndarray] = None
) -> pd.DataFrame:
    """
    Slice image into non-overlapping patches and compute metrics per patch.

    Parameters:
        gt: Ground truth depth map (H, W).
        pred: Predicted depth map (H, W).
        patch_size: Tuple of (patch_height, patch_width).
        mask: Optional boolean mask of valid pixels.

    Returns:
        DataFrame with columns ['y0', 'y1', 'x0', 'x1', 'AbsRel', 'δ1', 'RMSE']."""
    if mask is None:
        mask = compute_valid_mask(gt)

    H, W = gt.shape
    ph, pw = patch_size
    records: List[Dict[str, Any]] = []

    for y0 in range(0, H, ph):
        for x0 in range(0, W, pw):
            y1 = min(y0 + ph, H)
            x1 = min(x0 + pw, W)
            sub_mask = mask[y0:y1, x0:x1]
            sub_gt = gt[y0:y1, x0:x1]
            sub_pred = pred[y0:y1, x0:x1]
            if np.any(sub_mask):
                records.append({
                    "y0": y0,
                    "y1": y1,
                    "x0": x0,
                    "x1": x1,
                    "AbsRel": abs_rel(sub_gt, sub_pred, sub_mask),
                    "δ1": threshold_accuracy(sub_gt, sub_pred, threshold=1.25, mask=sub_mask),
                    "RMSE": rmse(sub_gt, sub_pred, sub_mask),
                })
    return pd.DataFrame.from_records(records)


class DepthEvaluator:
    """
    Encapsulates the full pipeline: resize → align → compute metrics.
    """

    def __init__(
        self,
        resize_fn: Any = resize_depth_map,
        align_fn: Any = scale_and_shift_align,
        valid_mask_fn: Any = compute_valid_mask,
    ) -> None:
        """
        Initialize DepthEvaluator.

        Parameters:
            resize_fn: Callable(pred, target_shape) → resized_pred.
            align_fn: Callable(pred, gt, mask) → aligned_pred.
            valid_mask_fn: Callable(gt) → mask.
        """
        self.resize_fn = resize_fn
        self.align_fn = align_fn
        self.valid_mask_fn = valid_mask_fn

    def _prepare(
        self,
        pred: np.ndarray,
        gt: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        1) Resize pred to gt.shape;
        2) Compute valid mask;
        3) Align pred to gt.

        Returns:
            aligned_pred, mask
        """
        pred_resized = self.resize_fn(pred, gt.shape)
        mask = self.valid_mask_fn(gt)
        pred_aligned = self.align_fn(pred_resized, gt, mask)
        return pred_aligned, mask

    def evaluate(
        self,
        gt: np.ndarray,
        pred: np.ndarray,
        patch_size: Optional[Tuple[int, int]] = None
    ) -> Dict[str, Any]:
        """
        Run full evaluation:
          - global metrics
          - optional patch metrics

        Parameters:
            gt: Ground truth depth map.
            pred: Predicted depth map.
            patch_size: If provided, compute patch metrics.

        Returns:
            Dict with keys 'global' and (if patch_size) 'patches'.
        """
        pred_prep, mask = self._prepare(pred, gt)
        results: Dict[str, Any] = {"global": global_metrics(gt, pred_prep, mask)}
        if patch_size is not None:
            results["patches"] = patch_metrics(gt, pred_prep, patch_size, mask)
        return results
