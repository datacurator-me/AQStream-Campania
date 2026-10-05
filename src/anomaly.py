from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

import numpy as np
import pandas as pd

from .features import RollingStats
from .spatial import compute_neighbours


class StreamProcessor:
    """Minimal online processor used for temporal and spatial checks."""

    def __init__(
        self,
        stations: pd.DataFrame,
        max_distance_km: float = 10.0,
        temporal_z: float = 2.5,
        spatial_z: float = 2.0,
    ):
        self.stations = stations.copy().reset_index(drop=True)
        self.max_distance_km = float(max_distance_km)
        self.temporal_z = float(temporal_z)
        self.spatial_z = float(spatial_z)
        self.rolling: Dict[str, RollingStats] = defaultdict(
            lambda: RollingStats(window=12)
        )
        self.last_values: Dict[str, float] = {}
        self.recent_events: List[dict] = []
        self.neighbours = compute_neighbours(
            self.stations,
            max_distance_km=self.max_distance_km,
        )


    def process(self, row: dict) -> dict:
        station_id = row["station_id"]
        value = float(row["pm25"])

        temporal = self.rolling[station_id].update(value)

        temporal_flag = (
            abs(temporal["z_score"]) > self.temporal_z
            and temporal["std"] > 0
        )

        neighbour_values = [
            self.last_values[other]
            for other in self.neighbours.get(station_id, [])
            if other in self.last_values
        ]

        if neighbour_values:
            neighbour_mean = float(np.mean(neighbour_values))
            neighbour_std = float(np.std(neighbour_values, ddof=0))

            if neighbour_std > 0:
                spatial_z = (value - neighbour_mean) / neighbour_std
            else:
                spatial_z = 0.0
        else:
            neighbour_mean = value
            neighbour_std = 1.0
            spatial_z = 0.0

        spatial_flag = (
            len(neighbour_values) > 0
            and abs(spatial_z) > self.spatial_z
        )

        event_flag = temporal_flag and spatial_flag

        if event_flag:
            self.recent_events.append(
                {
                    "station_id": station_id,
                    "timestamp": row["timestamp"],
                    "pm25": value,
                    "spatial_z": spatial_z,
                }
            )

        self.last_values[station_id] = value

        return {
            "station_id": station_id,
            "timestamp": row["timestamp"],
            "pm25": value,
            "temporal_anomaly": bool(temporal_flag),
            "spatial_anomaly": bool(spatial_flag),
            "spatio_temporal_event": bool(event_flag),
            "temporal_z_score": float(temporal["z_score"]),
            "spatial_z_score": float(spatial_z),
            "neighbour_mean": float(neighbour_mean),
            "neighbour_std": float(neighbour_std),
            "num_neighbours": len(neighbour_values),
        }


def detect_stream(
    df: pd.DataFrame,
    stations: pd.DataFrame,
    max_distance_km: float = 10.0,
    temporal_z: float = 2.5,
    spatial_z: float = 2.0,
) -> pd.DataFrame:
    """Replay the historical stream and label each observation."""

    processor = StreamProcessor(
        stations,
        max_distance_km=max_distance_km,
        temporal_z=temporal_z,
        spatial_z=spatial_z,
    )

    records = []

    ordered = df.sort_values(["timestamp", "station_id"])

    for row in ordered.to_dict(orient="records"):
        records.append(processor.process(row))

    return pd.DataFrame(records)


def detect_regional_events(
    df: pd.DataFrame,
    stations: pd.DataFrame,
    max_distance_km: float = 10.0,
    time_window_hours: int = 1,
    min_stations: int = 2,
) -> pd.DataFrame:
    """Mark short-lived regional events shared by nearby stations."""

    results = df.copy()
    results["timestamp"] = pd.to_datetime(results["timestamp"])
    results["regional_event"] = False

    neighbours = compute_neighbours(
        stations,
        max_distance_km=max_distance_km,
    )

    flagged = results[
        results["temporal_anomaly"]
        | results["spatial_anomaly"]
    ].copy()

    for _, row in flagged.iterrows():
        station_id = row["station_id"]
        timestamp = row["timestamp"]

        nearby = neighbours.get(station_id, [])

        if not nearby:
            continue

        start = timestamp - pd.Timedelta(
            hours=time_window_hours
        )
        end = timestamp + pd.Timedelta(
            hours=time_window_hours
        )

        window = flagged[
            (flagged["timestamp"] >= start)
            & (flagged["timestamp"] <= end)
            & (
                flagged["station_id"].isin(
                    [station_id] + nearby
                )
            )
        ]

        station_count = window["station_id"].nunique()

        if station_count >= min_stations:
            results.loc[
                (results["timestamp"] >= start)
                & (results["timestamp"] <= end)
                & (
                    results["station_id"].isin(
                        [station_id] + nearby
                    )
                ),
                "regional_event",
            ] = True

    return results