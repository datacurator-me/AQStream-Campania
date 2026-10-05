from __future__ import annotations

from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATA_PATH = BASE_DIR / "data" / "sample" / "observations.csv"
DEFAULT_STATION_PATH = BASE_DIR / "data" / "sample" / "stations.csv"


def load_air_quality_data(path: str | Path | None = None) -> pd.DataFrame:
    """Load a small sample of air-quality observations for Campania.

    This keeps the project reproducible and small enough to understand. In a
    fuller deployment, the same function can be replaced by an ARPAC-specific
    loader that reads the actual raw files.
    """
    data_path = Path(path) if path is not None else DEFAULT_DATA_PATH
    if not data_path.exists():
        raise FileNotFoundError(f"Air-quality data not found at {data_path}")

    df = pd.read_csv(data_path, parse_dates=["timestamp"])
    required = {"station_id", "timestamp", "pm25"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Dataset missing required columns: {sorted(missing)}")

    return df.sort_values(["timestamp", "station_id"]).reset_index(drop=True)


def load_station_metadata(path: str | Path | None = None) -> pd.DataFrame:
    """Load a small station table with coordinates used for spatial checks."""
    station_path = Path(path) if path is not None else DEFAULT_STATION_PATH
    if not station_path.exists():
        raise FileNotFoundError(f"Station metadata not found at {station_path}")

    df = pd.read_csv(station_path)
    required = {"station_id", "latitude", "longitude", "region"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Station metadata missing required columns: {sorted(missing)}")

    return df.reset_index(drop=True)
