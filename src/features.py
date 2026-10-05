from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

import numpy as np
import pandas as pd


class RollingStats:
    """Simple stateful rolling statistics for a single station.

    Online analysis only keeps a short history, which is sufficient for a
    first-pass anomaly detector and keeps the code easy to understand.
    """

    def __init__(self, window: int = 12):
        self.window = max(3, int(window))
        self.history: List[float] = []

    def update(self, value: float) -> dict:
        self.history.append(float(value))
        if len(self.history) > self.window:
            self.history = self.history[-self.window:]

        values = np.asarray(self.history, dtype=float)
        current = float(value)
        mean = float(np.mean(values))
        std = float(np.std(values, ddof=0))
        previous = self.history[-2] if len(self.history) >= 2 else current
        delta = current - previous if len(self.history) >= 2 else 0.0
        z_score = (current - mean) / std if len(values) > 1 and std > 0 else 0.0

        return {
            "value": current,
            "mean": mean,
            "std": std,
            "previous": previous,
            "delta": delta,
            "z_score": float(z_score),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
        }


def station_rolling_features(df: pd.DataFrame) -> list[dict]:
    """Add rolling temporal features to a stream-replayed DataFrame."""
    stats_by_station: Dict[str, RollingStats] = defaultdict(RollingStats)
    rows: list[dict] = []

    for row in df.sort_values(["timestamp", "station_id"]).to_dict(orient="records"):
        station = row["station_id"]
        features = stats_by_station[station].update(float(row["pm25"]))
        row.update(
            {
                "pm25_lag": features["previous"],
                "pm25_delta": features["delta"],
                "pm25_rolling_mean": features["mean"],
                "pm25_rolling_std": features["std"],
                "pm25_z_score": features["z_score"],
                "pm25_recent_min": features["min"],
                "pm25_recent_max": features["max"],
            }
        )
        rows.append(row)

    return rows
