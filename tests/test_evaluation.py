
# tests/test_evaluation.py

import numpy as np
import pandas as pd
import pytest

from metric_depth.evaluation import DepthEvaluator, global_metrics, patch_metrics
from metric_depth.utils import (
    rgb_to_grayscale_depth,
    resize_depth_map,
    pad_to_aspect_ratio,
    compute_valid_mask,
    scale_and_shift_align,
)


@pytest.fixture
def dummy_data():
    # Ground truth: simple ramp 4×4
    H, W = 4, 4
    gt = np.arange(H * W, dtype=float).reshape(H, W)
    # Simulated “RGB depth”: each channel equals gt exactly
    rgb = np.stack([gt, gt, gt], axis=-1)
    return rgb, gt


def test_rgb_to_grayscale_depth(dummy_data):
    rgb, gt = dummy_data
    gray = rgb_to_grayscale_depth(rgb)
    # weights sum to 1.0, channels identical → exact match
    assert np.allclose(gray, gt)


def test_resize_depth_map(dummy_data):
    _, gt = dummy_data
    # downsample 4×4 → 2×2
    small = resize_depth_map(gt, (2, 2), interpolation="linear")
    assert small.shape == (2, 2)


def test_pad_to_aspect_ratio():
    arr = np.ones((4, 2))
    # pad to square
    padded = pad_to_aspect_ratio(arr, target_ratio=1.0, pad_value=-1)
    assert padded.shape[0] == padded.shape[1]
    assert np.any(padded == -1)


def test_compute_valid_mask(dummy_data):
    _, gt = dummy_data
    mask = compute_valid_mask(gt, invalid_val=0.0)
    # value 0 → invalid, positives → valid
    assert not mask[0, 0]
    assert mask[1, 1]


def test_scale_and_shift_align(dummy_data):
    _, gt = dummy_data
    pred = gt * 3.14 + 42.0
    aligned = scale_and_shift_align(pred, gt)
    assert np.allclose(aligned, gt, atol=1e-6)


def test_global_metrics_identity(dummy_data):
    _, gt = dummy_data
    res = global_metrics(gt, gt)
    assert pytest.approx(res["AbsRel"], abs=1e-6) == 0.0
    assert pytest.approx(res["δ1"], abs=1e-6) == 1.0
    assert pytest.approx(res["RMSE"], abs=1e-6) == 0.0


def test_patch_metrics_identity(dummy_data):
    _, gt = dummy_data
    df = patch_metrics(gt, gt, patch_size=(2, 2))
    # 4×4 / (2×2) → 4 patches
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 4
    assert all(df["AbsRel"].abs() < 1e-6)
    assert all((df["δ1"] - 1.0).abs() < 1e-6)
    assert all(df["RMSE"].abs() < 1e-6)


def test_depth_evaluator_pipeline(dummy_data):
    rgb, gt = dummy_data
    # build evaluator
    evaluator = DepthEvaluator(
        resize_fn=resize_depth_map,
        align_fn=scale_and_shift_align,
        valid_mask_fn=compute_valid_mask,
    )
    # prepare single‑channel prediction
    pred_gray = rgb_to_grayscale_depth(rgb)
    # full eval without patches
    out = evaluator.evaluate(gt, pred_gray)
    assert "global" in out
    gm = out["global"]
    assert pytest.approx(gm["AbsRel"], abs=1e-6) == 0.0
    # with patch breakdown
    out2 = evaluator.evaluate(gt, pred_gray, patch_size=(2, 2))
    assert "patches" in out2
    assert out2["patches"].shape[0] == 4