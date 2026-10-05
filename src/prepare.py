from pathlib import Path

import pandas as pd

from .arpac import load_arpac_pm25, load_arpac_stations


def prepare_arpac_data(
    observations_path: str | Path,
    stations_path: str | Path,
) -> pd.DataFrame:
    """Combine ARPAC PM2.5 observations with station metadata."""

    observations = load_arpac_pm25(observations_path)
    stations = load_arpac_stations(stations_path)

    result = observations.merge(
        stations,
        on="station_id",
        how="left",
    )

    result = result.rename(
        columns={
            "station_name_x": "station_name",
        }
    )

    result = result.drop(
        columns=["station_name_y"]
    )

    result = result.sort_values(
        ["timestamp", "station_id"]
    ).reset_index(drop=True)

    return result