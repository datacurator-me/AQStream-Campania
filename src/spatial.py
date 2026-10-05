from __future__ import annotations

from math import atan2, cos, radians, sin, sqrt

import pandas as pd


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Approximate great-circle distance in kilometres."""
    r = 6371.0
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
    return 2 * r * atan2(sqrt(a), sqrt(1 - a))


def compute_neighbours(stations: pd.DataFrame, max_distance_km: float = 10.0) -> dict:
    """Create a simple station adjacency map using a distance threshold.

    The threshold is intentionally easy to change, because the first version is an
    exploratory neighbourhood definition rather than a fixed scientific rule.
    """
    neighbours: dict[str, list[str]] = {}
    station_ids = stations["station_id"].tolist()

    for station_id in station_ids:
        current = stations[stations["station_id"] == station_id].iloc[0]
        nearby = []
        for other_id in station_ids:
            if other_id == station_id:
                continue
            other = stations[stations["station_id"] == other_id].iloc[0]
            distance = haversine_km(
                float(current["latitude"]),
                float(current["longitude"]),
                float(other["latitude"]),
                float(other["longitude"]),
            )
            if distance <= max_distance_km:
                nearby.append(other_id)
        neighbours[station_id] = nearby

    return neighbours


def station_neighbour_summary(df: pd.DataFrame, stations: pd.DataFrame, max_distance_km: float = 10.0) -> dict:
    """Return a simple summary of each station's recently observed neighbours."""
    neighbours = compute_neighbours(stations, max_distance_km=max_distance_km)
    summary: dict[str, dict] = {}
    for station_id, nearby in neighbours.items():
        station_data = df[df["station_id"] == station_id].copy()
        if station_data.empty:
            summary[station_id] = {"neighbours": nearby, "mean": 0.0, "std": 0.0, "n": 0}
            continue
        values = station_data["pm25"].astype(float)
        summary[station_id] = {
            "neighbours": nearby,
            "mean": float(values.mean()),
            "std": float(values.std(ddof=0)),
            "n": int(len(values)),
        }
    return summary
