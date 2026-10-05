import pandas as pd

from src.anomaly import StreamProcessor
from src.stream import stream_rows

def test_stream_processor_updates_one_observation_at_a_time():
    stations = pd.DataFrame(
        {
            "station_id": ["S1", "S2"],
            "latitude": [40.85, 40.86],
            "longitude": [14.25, 14.26],
        }
    )

    processor = StreamProcessor(
        stations,
        max_distance_km=10,
    )

    first = processor.process(
        {
            "station_id": "S1",
            "timestamp": pd.Timestamp("2026-01-01 00:00:00"),
            "pm25": 20.0,
        }
    )

    assert first["station_id"] == "S1"
    assert first["num_neighbours"] == 0

    second = processor.process(
        {
            "station_id": "S2",
            "timestamp": pd.Timestamp("2026-01-01 01:00:00"),
            "pm25": 22.0,
        }
    )

    assert second["station_id"] == "S2"
    assert second["num_neighbours"] == 1
    assert processor.last_values["S1"] == 20.0
    assert processor.last_values["S2"] == 22.0
    
def test_stream_rows_yields_observations_in_order():
    df = pd.DataFrame(
        [
            {
                "station_id": "S2",
                "timestamp": pd.Timestamp("2026-01-01 01:00:00"),
                "pm25": 22.0,
            },
            {
                "station_id": "S1",
                "timestamp": pd.Timestamp("2026-01-01 00:00:00"),
                "pm25": 20.0,
            },
        ]
    )

    rows = list(stream_rows(df))

    assert rows[0]["station_id"] == "S1"
    assert rows[1]["station_id"] == "S2"
    assert rows[0]["pm25"] == 20.0
    assert rows[1]["pm25"] == 22.0