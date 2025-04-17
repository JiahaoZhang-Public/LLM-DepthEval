import os
import re
from typing import List, Tuple

import cv2
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from metric_depth.evaluation import DepthEvaluator
from metric_depth.utils import (
    compute_valid_mask,
    resize_depth_map,
    rgb_to_grayscale_depth,
    scale_and_shift_align,
)


def prepare_nyu_v2_data(depth_dir: str, output_dir: str) -> Tuple[List[np.ndarray], List[np.ndarray]]:
    """
    Load NYU‑V2 depth maps and corresponding predictions.

    - GT files:  depth_XXXXXX.npy
    - Pred files: image_XXXXXX.png

    Returns two parallel lists (gt_list, pred_list), sorted by index.
    """

    # Regex to extract the 6‑digit index
    depth_re = re.compile(r"^depth_(\d{6})\.npy$")
    image_re = re.compile(r"^image_(\d{6})\.png$")

    # Map index → filename
    depth_map = {}
    for fn in os.listdir(depth_dir):
        m = depth_re.match(fn)
        if m:
            idx = m.group(1)
            depth_map[idx] = os.path.join(depth_dir, fn)

    pred_map = {}
    for fn in os.listdir(output_dir):
        m = image_re.match(fn)
        if m:
            idx = m.group(1)
            pred_map[idx] = os.path.join(output_dir, fn)

    # Find common indices, sorted
    common_idxs = sorted(set(depth_map) & set(pred_map))

    gt_list: List[np.ndarray] = []
    pred_list: List[np.ndarray] = []

    for idx in common_idxs:
        # Load GT
        gt = np.load(depth_map[idx])

        # Load prediction and convert
        bgr = cv2.imread(pred_map[idx])
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        pred = rgb_to_grayscale_depth(rgb)

        gt_list.append(gt)
        pred_list.append(pred)

    return gt_list, pred_list


def evaluate_and_plot(depth_dir: str, output_dir: str):
    """Run DepthEvaluator over NYU‑V2 and plot global metrics."""
    # 1) load
    gts, preds = prepare_nyu_v2_data(depth_dir, output_dir)

    # 2) evaluator
    evaluator = DepthEvaluator(
        resize_fn=resize_depth_map,
        align_fn=scale_and_shift_align,
        valid_mask_fn=compute_valid_mask,
    )

    # 3) run evaluation
    all_results = [evaluator.evaluate(gt, pred) for gt, pred in zip(gts, preds)]

    # 4) aggregate into DataFrame
    df = pd.DataFrame([res["global"] for res in all_results])
    df.index.name = "sample_idx"

    # 5) per‐sample line plot
    plt.figure()
    plt.plot(df.index, df["AbsRel"], label="AbsRel")
    plt.plot(df.index, df["δ1"], label="δ1")
    plt.plot(df.index, df["RMSE"], label="RMSE")
    plt.xlabel("Sample Index")
    plt.ylabel("Metric Value")
    plt.title("NYU-V2 Global Metrics per Sample")
    plt.legend()
    plt.tight_layout()
    plt.show()

    # 6) average‐bar plot
    means = df.mean()
    plt.figure()
    plt.bar(means.index, means.values)
    plt.xlabel("Metric")
    plt.ylabel("Mean Value")
    plt.title("NYU-V2 Average Global Metrics")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    depth_dir = "your path to depth_raw" # flatten folder: depth_000000.npy
    output_dir = "your path to image" # flatten folder: image_000000.png
    evaluate_and_plot(depth_dir, output_dir) 