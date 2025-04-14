# tests/test_metric_utils.py

import numpy as np
import pytest
from metric_depth.utils import rgb_to_grayscale_depth, scale_and_shift_align


@pytest.fixture
def sample_rgb():
    """Return a simple 2x2 RGB image."""
    return np.array([
        [[255, 0, 0], [0, 255, 0]],
        [[0, 0, 255], [255, 255, 255]]
    ], dtype=np.uint8)


def test_rgb_to_grayscale_float(sample_rgb):
    gray = rgb_to_grayscale_depth(sample_rgb)
    assert gray.shape == (2, 2)
    assert np.all(gray >= 0) and np.all(gray <= 1)
    # Manually check expected luminance values
    expected = np.array([
        [0.299, 0.587],
        [0.114, 1.0]
    ])
    np.testing.assert_allclose(gray, expected, rtol=1e-2)


def test_rgb_to_grayscale_error():
    with pytest.raises(ValueError):
        rgb_to_grayscale_depth(np.random.rand(10, 10))  # Not RGB (no channel axis)


def test_scale_and_shift_align_basic():
    pred = np.array([[1, 2], [3, 4]], dtype=np.float32)
    gt = 2 * pred + 5  # True scale = 2, shift = 5
    aligned = scale_and_shift_align(pred, gt)
    np.testing.assert_allclose(aligned, gt, rtol=1e-5)


def test_scale_and_shift_align_masked():
    pred = np.array([[1, 2], [3, 4]], dtype=np.float32)
    gt = np.array([[7, 9], [11, 0]], dtype=np.float32)  # Ignore bottom-right (zero)
    mask = gt > 0

    aligned = scale_and_shift_align(pred, gt, mask)
    np.testing.assert_allclose(aligned[mask], gt[mask], rtol=1e-5)


def test_scale_and_shift_align_shape_mismatch():
    pred = np.ones((2, 2))
    gt = np.ones((3, 3))
    with pytest.raises(ValueError):
        scale_and_shift_align(pred, gt)