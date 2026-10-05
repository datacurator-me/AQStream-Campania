from __future__ import annotations

import pandas as pd


def precision_recall_f1(tp: int, fp: int, fn: int) -> dict:
    """Compute a minimal event-detection summary."""
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "false_positives": int(fp),
        "false_negatives": int(fn),
        "true_positives": int(tp),
    }


def evaluate_anomalies(df: pd.DataFrame, label_col: str = "is_event") -> dict:
    """Evaluate predictions when a small amount of labelled ground truth exists."""
    if label_col not in df.columns:
        return {
            "status": "no_ground_truth",
            "message": "No reliable ground-truth labels are available for evaluation.",
        }

    predicted = df.get("regional_event", False).fillna(False).astype(bool)
    actual = df[label_col].fillna(False).astype(bool)
    tp = int((predicted & actual).sum())
    fp = int((predicted & (~actual)).sum())
    fn = int((~predicted & actual).sum())

    return precision_recall_f1(tp=tp, fp=fp, fn=fn)


def summarize_events(df: pd.DataFrame) -> dict:
    """Produce a simple event summary for reporting or dashboard display."""
    return {
        "temporal": int(df["temporal_anomaly"].sum()) if "temporal_anomaly" in df.columns else 0,
        "spatial": int(df["spatial_anomaly"].sum()) if "spatial_anomaly" in df.columns else 0,
        "regional": int(df["regional_event"].sum()) if "regional_event" in df.columns else 0,
        "station_count": df["station_id"].nunique() if "station_id" in df.columns else 0,
    }
