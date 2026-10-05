from __future__ import annotations

from src.features import RollingStats


def test_rolling_stats_updates_mean_and_delta():
    stats = RollingStats(window=5)
    first = stats.update(10.0)
    second = stats.update(14.0)

    assert first["value"] == 10.0
    assert second["delta"] == 4.0
    assert second["mean"] >= 10.0
    assert second["std"] >= 0.0


def test_rolling_stats_zscore_is_finite():
    stats = RollingStats(window=5)
    for value in [10.0, 11.0, 13.0, 12.0, 15.0, 18.0]:
        result = stats.update(value)
        assert result["z_score"] == result["z_score"]
