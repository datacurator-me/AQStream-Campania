# AQStream-Campania

**Online analysis of air-quality data streams in Campania, Italy, using temporal and spatial anomaly detection.**

AQStream-Campania is a small research/portfolio project for experimenting with **data stream mining** and **spatio-temporal analysis** on real air-quality measurements from Campania.

The project replays air-quality observations one by one, maintains a small amount of state for each monitoring station, and checks whether a new PM2.5 measurement is unusual compared with the station's recent history or nearby stations.

The goal is not to build a production streaming platform. The goal is to keep the streaming logic visible, reproducible, and easy to inspect.

---

## What this project does

The current pipeline focuses on PM2.5 observations from the ARPAC monitoring network.

For each observation, the system can perform:

* **Temporal anomaly detection** — compare a station's current PM2.5 value with its recent observations.
* **Spatial anomaly detection** — compare a station with nearby monitoring stations.
* **Spatio-temporal checks** — identify observations that are unusual in both temporal and spatial terms.
* **Regional event analysis** — group nearby anomalous observations occurring within a short time window.
* **Stream replay** — process historical observations one row at a time as a simple simulation of sensor data arriving over time.
* **Interactive monitoring** — inspect the replayed stream and anomaly results through a Streamlit dashboard.

---

## Why streaming?

Air-quality sensors continuously generate observations.

Instead of loading a complete dataset and calculating everything retrospectively, this project uses a small stateful processor:

```text
observation
     |
     v
stream replay
     |
     v
temporal state -----> temporal anomaly
     |
     +----> nearby stations -----> spatial anomaly
     |
     v
spatio-temporal check
     |
     v
dashboard / analysis
```

The important part is that `StreamProcessor.process()` receives **one observation at a time**.

The processor does not need the complete historical dataset to calculate its basic temporal and spatial checks.

---

## Data source

The project uses air-quality data published by **ARPAC — Agenzia Regionale per la Protezione Ambientale della Campania**.

The main source is the ARPAC open-data portal:

* ARPAC Open Data: https://dati.arpacampania.it/

The project currently uses the hourly near-real-time air-quality dataset and extracts measurements where:

```text
Inquinante = PM2,5
```

The original ARPAC files are not committed to the repository.

They should be placed under:

```text
data/raw/
```

and are ignored by Git.

This keeps the repository small while still allowing the real-data pipeline to be reproduced locally.

---

## Current real-data snapshot

A local run of the ARPAC preparation and anomaly pipeline produced:

| Metric                              | Value |
| ----------------------------------- | ----: |
| PM2.5 observations                  | 3,628 |
| Monitoring stations in observations |    36 |
| Stations with matching coordinates  |    35 |
| Temporal anomalies                  |   108 |
| Spatial anomalies                   |   493 |
| Spatio-temporal events              |    29 |

The observations in this snapshot cover approximately:

```text
2026-01-10 → 2026-05-10
```

The exact results depend on the downloaded ARPAC files and the current detection thresholds.

One station, `IT2342A` (`S. Gregorio Matese Lago`), appears in the PM2.5 observations but does not have matching coordinates in the metadata file used for this analysis.

The project does **not** invent coordinates for this station. Its temporal observations can still be processed, while spatial analysis requires valid station coordinates.

---

## Repository structure

```text
AQStream-Campania/
├── dashboard/
│   └── app.py
├── data/
│   ├── processed/
│   │   └── .gitkeep
│   ├── raw/
│   │   └── .gitkeep
│   └── sample/
│       ├── observations.csv
│       └── stations.csv
├── notebooks/
│   └── __init__.py
├── scripts/
│   └── bootstrap_dirs.py
├── src/
│   ├── __init__.py
│   ├── anomaly.py
│   ├── arpac.py
│   ├── evaluation.py
│   ├── features.py
│   ├── ingestion.py
│   ├── prepare.py
│   ├── spatial.py
│   └── stream.py
├── tests/
│   ├── test_anomaly.py
│   ├── test_arpac.py
│   ├── test_features.py
│   └── test_prepare.py
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

---

## Project components

### `src/arpac.py`

Contains the ARPAC-specific data loaders.

It handles:

* reading the raw ARPAC hourly CSV
* selecting PM2.5 measurements
* converting timestamps
* converting PM2.5 values to numeric values
* loading station metadata
* handling malformed metadata rows found in the downloaded CSV
* converting station coordinates to numeric values

This keeps ARPAC-specific details separate from the streaming logic.

---

### `src/prepare.py`

Combines:

```text
PM2.5 observations
        +
station metadata
        |
        v
prepared analysis table
```

The resulting table contains fields such as:

```text
station_id
station_name
timestamp
pm25
province
latitude
longitude
station_type
```

---

### `src/stream.py`

Provides the basic stream replay mechanism.

Historical observations are sorted by timestamp and yielded one at a time.

Conceptually:

```python
for observation in stream_rows(df):
    process(observation)
```

This is intentionally simple. A real message broker is not required for the current research prototype.

---

### `src/features.py`

Contains stateful temporal features.

The main component is:

```python
RollingStats
```

It maintains a short history for each station and calculates features such as:

* recent mean
* recent standard deviation
* previous value
* change from previous observation
* recent minimum
* recent maximum
* z-score

The current default history window is 12 observations.

For hourly data, this roughly represents the most recent 12 hours for a station.

---

### `src/spatial.py`

Contains the basic spatial logic.

The project currently uses a simple distance-based neighbourhood:

```text
station A ----\
               \
                station B
               /
station C ----/
```

Two stations are considered neighbours when their great-circle distance is within:

```text
10 km
```

Distance is calculated using the Haversine formula.

The 10 km value is intentionally treated as an exploratory parameter rather than a universal scientific rule.

---

### `src/anomaly.py`

Contains the main streaming anomaly processor.

The central class is:

```python
StreamProcessor
```

For every incoming observation it maintains:

* temporal state for the station
* latest known station value
* nearby stations
* anomaly flags
* anomaly scores

The processor returns information such as:

```text
temporal_anomaly
spatial_anomaly
spatio_temporal_event
temporal_z_score
spatial_z_score
neighbour_mean
neighbour_std
num_neighbours
```

---

## Temporal anomaly detection

The first anomaly signal is based on the station's recent history.

A simplified form is:

```text
z = (current_value - recent_mean) / recent_std
```

The current exploratory threshold is:

```text
|z| > 2.5
```

This is a deliberately simple baseline.

It provides an interpretable starting point before experimenting with more advanced online methods.

---

## Spatial anomaly detection

The spatial detector compares the current station value with the latest available values from neighbouring stations.

The simplified spatial score is:

```text
spatial_z =
    (station_value - neighbour_mean)
    / neighbour_std
```

The current threshold is:

```text
|spatial_z| > 2.0
```

A station therefore becomes spatially anomalous when its current value is substantially different from the latest values observed at nearby stations.

There are important limitations to this approach:

* neighbouring observations may not have exactly the same timestamp
* a neighbour's latest observation may be older
* station density is not uniform
* the 10 km neighbourhood is a heuristic
* the normal distribution assumption behind a z-score is only approximate

These are intentional areas for future improvement rather than hidden assumptions.

---

## Spatio-temporal events

The project also checks whether an observation is unusual from both perspectives:

```text
temporal anomaly
        +
spatial anomaly
        |
        v
spatio-temporal event
```

This produces a simple combined signal.

There is also a secondary function:

```python
detect_regional_events()
```

which looks for anomalous observations from multiple nearby stations within a short time window.

This part is currently **batch post-processing**, not a fully online regional-event detector.

That distinction is important: the per-observation anomaly processor is online/stateful, while regional grouping is currently performed after stream replay.

---

## Dashboard

The Streamlit dashboard provides a small interactive view of the stream.

It includes:

* stream start/reset controls
* incremental observation processing
* latest PM2.5 measurement
* anomaly indicators
* temporal and spatial z-scores
* recent anomaly information
* time-series plots
* station-level analysis
* spatial comparison
* regional event summaries

The dashboard currently uses the small datasets under:

```text
data/sample/
```

This is intentional.

The sample data makes the dashboard reproducible without requiring users to download the full ARPAC dataset first.

The real ARPAC pipeline is implemented separately in:

```text
src/arpac.py
src/prepare.py
```

---

## Sample data vs. real ARPAC data

There are two data paths in the project.

### Small sample data

Used by the dashboard and basic reproducible examples:

```text
data/sample/observations.csv
data/sample/stations.csv
```

These files are committed to Git.

### Real ARPAC data

Used for the actual ARPAC analysis:

```text
data/raw/
```

These files are ignored by Git because they are larger and come directly from the external data source.

A typical real-data workflow is:

```text
ARPAC CSV
   |
   v
src/arpac.py
   |
   v
src/prepare.py
   |
   v
prepared observations
   |
   v
StreamProcessor
   |
   v
anomaly results
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/datacurator-me/AQStream-Campania.git
cd AQStream-Campania
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Run the dashboard

From the project root:

```bash
streamlit run dashboard/app.py
```

The dashboard should open in the browser.

The default dashboard uses the small sample dataset, so no ARPAC download is required for the first run.

---

## Run the tests

The project uses pytest.

Run:

```bash
pytest
```

The tests currently cover:

* stream ordering
* stateful stream processing
* rolling statistics
* ARPAC data preparation
* basic data-loading behaviour

The test suite is intentionally small at this stage.

---

## Example: replay the stream

The core idea can be used without Streamlit:

```python
from src.anomaly import StreamProcessor
from src.stream import stream_rows

processor = StreamProcessor(stations)

for row in stream_rows(observations):
    result = processor.process(row)

    if result["temporal_anomaly"]:
        print(
            row["station_id"],
            row["timestamp"],
            row["pm25"],
        )
```

Each observation is processed independently while the processor keeps the required state.

---

## Current parameters

The main exploratory parameters are:

| Parameter                 |   Current value | Purpose                             |
| ------------------------- | --------------: | ----------------------------------- |
| Rolling window            | 12 observations | Recent station history              |
| Temporal z-score          |             2.5 | Temporal anomaly threshold          |
| Spatial z-score           |             2.0 | Spatial anomaly threshold           |
| Neighbour distance        |           10 km | Spatial neighbourhood               |
| Regional time window      |          1 hour | Regional event grouping             |
| Minimum regional stations |               2 | Minimum stations for regional event |

These values should not be interpreted as scientifically optimal parameters.

One of the next steps is to evaluate how anomaly counts change under different thresholds and neighbourhood sizes.

---

## Results and interpretation

For the current ARPAC snapshot, the initial detector produced:

```text
3,628 observations
108 temporal anomalies
493 spatial anomalies
29 combined spatio-temporal events
```

The relatively high number of spatial anomalies is useful as a diagnostic signal, but it also suggests that the current spatial baseline is sensitive.

Possible reasons include:

* different station environments
* uneven station density
* asynchronous measurements
* short neighbourhood windows
* threshold selection
* local pollution sources

Therefore, these results should be interpreted as **exploratory anomaly signals**, not confirmed pollution events.

---

## Limitations

This project is intentionally a first-pass research prototype.

### 1. The regional detector is not fully online

`StreamProcessor` works observation by observation, but `detect_regional_events()` currently performs regional grouping after the replay.

A future version could maintain active regional events incrementally.

### 2. Neighbour observations can be stale

The spatial detector currently uses the latest value available from a neighbour.

It does not yet enforce a maximum allowed time difference.

A better implementation would explicitly control observation freshness.

### 3. Thresholds are heuristic

The current z-score thresholds were chosen as simple starting points.

They should be tested through sensitivity analysis rather than treated as fixed scientific values.

### 4. No labelled ground truth

The project does not currently have a reliable set of manually labelled pollution anomalies.

Therefore, conventional supervised precision/recall evaluation is limited.

The evaluation module is prepared for labelled data but currently reports when reliable ground truth is unavailable.

### 5. Missing station metadata

`IT2342A` appears in the PM2.5 observations but has no matching coordinates in the metadata file used in this analysis.

The project keeps those observations for temporal processing but excludes the station from coordinate-dependent spatial analysis.

### 6. No production streaming infrastructure

There is currently no:

* Kafka
* Redis
* message queue
* database
* distributed processing cluster
* REST backend
* container orchestration

This is deliberate.

The project is intended to demonstrate the **data-stream processing logic**, not infrastructure engineering.

---

## Future work

Possible next steps include:

### Temporal detection

* calculate anomaly scores against the previous history before updating the rolling state
* compare z-score detection with robust statistics
* experiment with River's online anomaly models
* handle missing observations explicitly

### Spatial detection

* enforce neighbour timestamp freshness
* test several neighbourhood distances
* compare distance-based neighbours with k-nearest neighbours
* normalize for station-specific behaviour

### Regional events

* make regional event detection fully online
* maintain active event state
* estimate event duration
* calculate event intensity
* identify the stations participating in each event

### Evaluation

* create a small manually reviewed validation set
* perform threshold sensitivity analysis
* compare temporal and spatial detectors
* report false-positive behaviour

### Dashboard

* connect the dashboard to the real ARPAC pipeline
* add map-based station visualization
* expose anomaly thresholds as controls
* show active regional events over time

---

## Technologies

The project is intentionally built with a relatively small Python stack.

* **Python**
* **pandas** — data manipulation
* **NumPy** — numerical calculations
* **GeoPandas / Shapely** — spatial data support
* **Streamlit** — dashboard
* **Plotly** — interactive charts
* **pytest** — testing
* **River** — optional online machine-learning experimentation

---

## Project philosophy

The project follows a few simple principles:

1. Keep the streaming logic understandable.
2. Prefer small stateful components over unnecessary infrastructure.
3. Separate ARPAC-specific data handling from anomaly detection.
4. Make assumptions visible.
5. Do not fabricate missing geographic information.
6. Treat anomaly detection as exploratory unless there is ground truth.
7. Start with interpretable statistical baselines before adding more complex models.

---

## License

This project is released under the MIT License.

See [`LICENSE`](LICENSE) for details.

---

## Data attribution

Air-quality observations and station metadata are provided by **ARPAC — Agenzia Regionale per la Protezione Ambientale della Campania** through its open-data portal.

The project is an independent analysis and is not an official ARPAC application.

---

## References

* ARPAC Open Data: https://dati.arpacampania.it/
* ARPAC Campania: https://www.arpacampania.it/
* pandas: https://pandas.pydata.org/
* NumPy: https://numpy.org/
* Streamlit: https://streamlit.io/
* Plotly: https://plotly.com/python/
* River: https://riverml.xyz/
* pytest: https://docs.pytest.org/
