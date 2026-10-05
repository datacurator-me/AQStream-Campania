from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.anomaly import StreamProcessor, detect_regional_events
from src.evaluation import summarize_events
from src.ingestion import load_air_quality_data, load_station_metadata
from src.spatial import compute_neighbours
from src.stream import stream_rows


st.set_page_config(
    page_title="AQStream-Campania",
    layout="wide",
)


def reset_stream() -> None:
    st.session_state.stream_started = False
    st.session_state.stream_position = 0
    st.session_state.processor = None
    st.session_state.stream_iterator = None
    st.session_state.stream_results = []


def init_stream(observations: pd.DataFrame, stations: pd.DataFrame) -> None:
    if st.session_state.processor is None:
        st.session_state.processor = StreamProcessor(
            stations
        )

    if st.session_state.stream_iterator is None:
        st.session_state.stream_iterator = iter(
            stream_rows(observations)
        )

    st.session_state.stream_started = True


def process_next_observations(
    number: int,
) -> None:
    iterator = st.session_state.stream_iterator
    processor = st.session_state.processor

    if iterator is None or processor is None:
        return

    for _ in range(number):
        try:
            row = next(iterator)
        except StopIteration:
            st.session_state.stream_started = False
            break

        result = processor.process(row)

        st.session_state.stream_results.append(
            result
        )

        st.session_state.stream_position += 1


def plot_stream(df: pd.DataFrame) -> go.Figure:
    fig = px.line(
        df,
        x="timestamp",
        y="pm25",
        color="station_id",
        labels={
            "timestamp": "Time",
            "pm25": "PM2.5 (µg/m³)",
            "station_id": "Station",
        },
    )

    anomalies = df[
        df["temporal_anomaly"]
        | df["spatial_anomaly"]
    ]

    if not anomalies.empty:
        fig.add_trace(
            go.Scatter(
                x=anomalies["timestamp"],
                y=anomalies["pm25"],
                mode="markers",
                name="Anomaly",
                marker=dict(
                    size=11,
                    symbol="x",
                ),
                text=anomalies["station_id"],
                customdata=anomalies[
                    [
                        "temporal_z_score",
                        "spatial_z_score",
                    ]
                ],
                hovertemplate=(
                    "Station: %{text}<br>"
                    "PM2.5: %{y:.2f} µg/m³<br>"
                    "Time: %{x}<br>"
                    "Temporal z: %{customdata[0]:.2f}<br>"
                    "Spatial z: %{customdata[1]:.2f}"
                    "<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title="Online PM2.5 Stream",
        height=430,
        hovermode="x unified",
    )

    return fig


def plot_temporal_trend(
    df: pd.DataFrame,
    station_id: str,
) -> go.Figure:
    station_data = df[
        df["station_id"] == station_id
    ].copy()

    station_data["timestamp"] = pd.to_datetime(
        station_data["timestamp"]
    )

    station_data = station_data.sort_values(
        "timestamp"
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=station_data["timestamp"],
            y=station_data["pm25"],
            mode="lines+markers",
            name="PM2.5",
        )
    )

    anomalies = station_data[
        station_data["temporal_anomaly"]
    ]

    if not anomalies.empty:
        fig.add_trace(
            go.Scatter(
                x=anomalies["timestamp"],
                y=anomalies["pm25"],
                mode="markers",
                name="Temporal anomaly",
                marker=dict(
                    size=10,
                    symbol="circle",
                ),
            )
        )

    fig.update_layout(
        title=f"PM2.5 Time Series: {station_id}",
        xaxis_title="Timestamp",
        yaxis_title="PM2.5 (µg/m³)",
        height=400,
        hovermode="x unified",
    )

    return fig


def plot_spatial_comparison(
    df: pd.DataFrame,
    stations: pd.DataFrame,
    station_id: str,
) -> go.Figure:
    neighbours = compute_neighbours(
        stations,
        max_distance_km=10.0,
    )

    nearby = neighbours.get(
        station_id,
        [],
    )

    selected = [
        station_id,
        *nearby,
    ]

    data = df[
        df["station_id"].isin(selected)
    ].copy()

    data["timestamp"] = pd.to_datetime(
        data["timestamp"]
    )

    fig = px.line(
        data,
        x="timestamp",
        y="pm25",
        color="station_id",
        title=(
            f"Spatial comparison: "
            f"{station_id} and nearby stations"
        ),
        labels={
            "pm25": "PM2.5 (µg/m³)",
            "station_id": "Station",
            "timestamp": "Time",
        },
    )

    fig.update_layout(
        height=400,
        hovermode="x unified",
    )

    return fig


def plot_anomaly_heatmap(
    df: pd.DataFrame,
) -> go.Figure:
    data = df.copy()

    data["timestamp"] = pd.to_datetime(
        data["timestamp"]
    )

    data["anomaly_score"] = (
        data["temporal_anomaly"].astype(int)
        + data["spatial_anomaly"].astype(int)
    )

    pivot = data.pivot_table(
        index="station_id",
        columns=data["timestamp"].dt.floor("h"),
        values="anomaly_score",
        aggfunc="max",
    )

    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
        )
    )

    fig.update_layout(
        title="Anomaly Heatmap",
        xaxis_title="Time",
        yaxis_title="Station",
        height=450,
    )

    return fig


def plot_regional_events(
    df: pd.DataFrame,
    stations: pd.DataFrame,
) -> go.Figure:
    events = df[
        df["regional_event"]
    ].copy()

    if events.empty:
        fig = go.Figure()

        fig.update_layout(
            title="Regional events: no activity found",
            height=450,
        )

        return fig

    summary = (
        events.groupby("station_id")
        .size()
        .reset_index(name="event_count")
        .merge(
            stations,
            on="station_id",
            how="inner",
        )
    )

    fig = px.scatter_geo(
        summary,
        lat="latitude",
        lon="longitude",
        size="event_count",
        hover_name="station_id",
        title="Regional Events by Station",
        projection="mercator",
    )

    fig.update_layout(
        height=500,
    )

    return fig


def plot_pm25_statistics(
    df: pd.DataFrame,
) -> go.Figure:
    stats = (
        df.groupby("station_id")["pm25"]
        .agg(["mean", "std"])
        .reset_index()
        .sort_values(
            "mean",
            ascending=False,
        )
    )

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=stats["station_id"],
            y=stats["mean"],
            error_y=dict(
                type="data",
                array=stats["std"].fillna(0),
            ),
            name="Mean ± Std",
        )
    )

    fig.update_layout(
        title="PM2.5 Mean and Std Dev by Station",
        xaxis_title="Station",
        yaxis_title="PM2.5 (µg/m³)",
        height=400,
    )

    return fig


def main() -> None:
    if "stream_started" not in st.session_state:
        reset_stream()

    st.title("AQStream-Campania")

    st.caption(
        "Online analysis of air-quality data streams "
        "in Campania, Italy"
    )

    observations = load_air_quality_data()
    stations = load_station_metadata()

    # --------------------------------------------------
    # Stream controls
    # --------------------------------------------------

    st.subheader("Stream replay")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(
            "Start Stream",
            width="stretch",
        ):
            reset_stream()
            init_stream(
                observations,
                stations,
            )

    with col2:
        if st.button(
            "Next 10 Observations",
            width="stretch",
        ):
            if st.session_state.processor is None:
                init_stream(
                    observations,
                    stations,
                )

            process_next_observations(10)

    with col3:
        if st.button(
            "Reset",
            width="stretch",
        ):
            reset_stream()

    processed = st.session_state.stream_position
    total = len(observations)

    st.progress(
        min(processed / total, 1.0)
        if total
        else 0.0
    )

    st.write(
        f"Processed observations: {processed} / {total}"
    )

    # --------------------------------------------------
    # Online stream results
    # --------------------------------------------------

    stream_results = st.session_state.stream_results

    if stream_results:
        stream_df = pd.DataFrame(
            stream_results
        )

        latest = stream_df.iloc[-1]

        st.subheader("Latest observation")

        st.write(
            f"Timestamp: {latest['timestamp']}"
        )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Station",
            latest["station_id"],
        )

        col2.metric(
            "PM2.5",
            f"{latest['pm25']:.2f} µg/m³",
        )

        col3.metric(
            "Temporal anomaly",
            "Yes"
            if latest["temporal_anomaly"]
            else "No",
        )

        col4.metric(
            "Spatial anomaly",
            "Yes"
            if latest["spatial_anomaly"]
            else "No",
        )

        st.plotly_chart(
            plot_stream(stream_df),
            width="stretch",
        )

        # --------------------------------------------------
        # Latest anomaly details
        # --------------------------------------------------

        anomalies = stream_df[
            stream_df["temporal_anomaly"]
            | stream_df["spatial_anomaly"]
        ]

        if not anomalies.empty:
            latest_anomaly = anomalies.iloc[-1]

            st.subheader("Latest anomaly")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "Station",
                latest_anomaly["station_id"],
            )

            col2.metric(
                "PM2.5",
                f"{latest_anomaly['pm25']:.2f} µg/m³",
            )

            col3.metric(
                "Temporal z-score",
                f"{latest_anomaly['temporal_z_score']:.2f}",
            )

            col4.metric(
                "Spatial z-score",
                f"{latest_anomaly['spatial_z_score']:.2f}",
            )

            temporal = latest_anomaly[
                "temporal_anomaly"
            ]

            spatial = latest_anomaly[
                "spatial_anomaly"
            ]

            if temporal and spatial:
                anomaly_type = (
                    "Temporal + Spatial"
                )
            elif temporal:
                anomaly_type = "Temporal"
            else:
                anomaly_type = "Spatial"

            st.info(
                f"Anomaly type: {anomaly_type}"
            )

    else:
        st.info(
            "Start the stream to begin processing observations."
        )

    # --------------------------------------------------
    # Summary based on processed stream
    # --------------------------------------------------

    if stream_results:
        stream_summary = stream_df.copy()

        temporal_count = int(
            stream_summary["temporal_anomaly"].sum()
        )

        spatial_count = int(
            stream_summary["spatial_anomaly"].sum()
        )

        event_count = int(
            stream_summary[
                "spatio_temporal_event"
            ].sum()
        )
    else:
        temporal_count = 0
        spatial_count = 0
        event_count = 0

    st.subheader("Stream summary")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Processed",
        processed,
    )

    col2.metric(
        "Temporal anomalies",
        temporal_count,
    )

    col3.metric(
        "Spatial anomalies",
        spatial_count,
    )

    col4.metric(
        "Spatio-temporal events",
        event_count,
    )

    # --------------------------------------------------
    # Offline regional event analysis
    # --------------------------------------------------

    if stream_results:
        regional_results = detect_regional_events(
            stream_df,
            stations,
        )

        regional_summary = summarize_events(
            regional_results
        )
    else:
        regional_results = pd.DataFrame()
        regional_summary = {
            "temporal": 0,
            "spatial": 0,
            "regional": 0,
        }

    # --------------------------------------------------
    # Overview
    # --------------------------------------------------

    st.subheader("Overview")

    tab1, tab2, tab3 = st.tabs(
        [
            "Statistics",
            "Heatmap",
            "Regional events",
        ]
    )

    with tab1:
        st.plotly_chart(
            plot_pm25_statistics(observations),
            width="stretch",
        )

    with tab2:
        if stream_results:
            st.plotly_chart(
                plot_anomaly_heatmap(
                    stream_df
                ),
                width="stretch",
            )
        else:
            st.info(
                "The heatmap will appear after "
                "stream processing starts."
            )

    with tab3:
        if stream_results:
            st.plotly_chart(
                plot_regional_events(
                    regional_results,
                    stations,
                ),
                width="stretch",
            )
        else:
            st.info(
                "Regional events will appear after "
                "stream processing starts."
            )

    # --------------------------------------------------
    # Station analysis
    # --------------------------------------------------

    st.subheader("Station analysis")

    station_choice = st.selectbox(
        "Select station",
        sorted(
            stations["station_id"].unique()
        ),
    )

    col1, col2 = st.columns(2)

    with col1:
        data_for_station = (
            stream_df
            if stream_results
            else observations
        )

        if stream_results:
            station_plot = plot_temporal_trend(
                data_for_station,
                station_choice,
            )
        else:
            station_plot = go.Figure()

            station_data = observations[
                observations["station_id"]
                == station_choice
            ].copy()

            station_data["timestamp"] = pd.to_datetime(
                station_data["timestamp"]
            )

            station_plot.add_trace(
                go.Scatter(
                    x=station_data["timestamp"],
                    y=station_data["pm25"],
                    mode="lines",
                    name="PM2.5",
                )
            )

            station_plot.update_layout(
                title=(
                    f"PM2.5 Time Series: "
                    f"{station_choice}"
                ),
                height=400,
            )

        st.plotly_chart(
            station_plot,
            width="stretch",
        )

    with col2:
        st.plotly_chart(
            plot_spatial_comparison(
                observations,
                stations,
                station_choice,
            ),
            width="stretch",
        )

    # --------------------------------------------------
    # Station metadata
    # --------------------------------------------------

    st.subheader("Station metadata")

    station_summary = (
        observations.groupby(
            "station_id"
        )["pm25"]
        .agg(
            [
                "mean",
                "std",
                "min",
                "max",
            ]
        )
        .reset_index()
    )

    station_meta = stations.merge(
        station_summary,
        on="station_id",
        how="left",
    )

    st.dataframe(
        station_meta,
        width="stretch",
    )

    # --------------------------------------------------
    # Recent anomalies
    # --------------------------------------------------

    st.subheader("Recent anomalies")

    if stream_results:
        flagged = regional_results[
            regional_results["temporal_anomaly"]
            | regional_results["spatial_anomaly"]
            | regional_results["regional_event"]
        ].tail(30)

        if flagged.empty:
            st.info(
                "No anomalies detected in the processed stream."
            )
        else:
            st.dataframe(
                flagged[
                    [
                        "timestamp",
                        "station_id",
                        "pm25",
                        "temporal_z_score",
                        "spatial_z_score",
                        "temporal_anomaly",
                        "spatial_anomaly",
                        "regional_event",
                    ]
                ],
                width="stretch",
            )
    else:
        st.info(
            "No stream observations have been processed yet."
        )


if __name__ == "__main__":
    main()

