from __future__ import annotations

from typing import Iterator

import pandas as pd


def stream_rows(df: pd.DataFrame) -> Iterator[dict]:
    """Yield historical observations one row at a time, as if they arrived from sensors."""
    for row in df.sort_values(["timestamp", "station_id"]).to_dict(orient="records"):
        yield row
