# AQStream-Campania

**Online analysis of air-quality data streams in Campania, Italy**

This project explores online processing of air-quality measurements from monitoring stations in Campania.

The main idea is to replay real ARPAC air-quality observations as a data stream and process them one observation at a time. The stream processor keeps a small amount of state for each station and looks for unusual behaviour in both the temporal and spatial context.

The project was built as a practical study of **Data Stream Mining** and **Spatio-Temporal Analysis**, rather than as a production monitoring system.

---

## What does the project do?

The project focuses on PM2.5 measurements and performs three main types of analysis:

* **Temporal anomalies**
  Detect observations that are unusual compared with the recent history of the same station.

* **Spatial anomalies**
  Compare a station with nearby monitoring stations and detect values that are unusual in the local spatial context.

* **Spatio-temporal events**
  Look for short periods where several nearby stations show unusual behaviour.

Historical ARPAC observations are replayed in timestamp order to simulate a streaming environment.

---

## Data

The data comes from the **ARPAC (Agenzia Regionale per la Protezione Ambientale della Campania)** open-data platform.

The project currently uses:

* PM2.5 hourly observations
* Monitoring station metadata
* Station coordinates
* Province and station type information

The dataset used during development contains:

* **3,628 PM2.5 observations**
* **36 monitoring stations**
* observations from **January 10, 2026 to May 10, 2026**
* observations from the ARPAC near-real-time air-quality dataset

The raw data is not included in the repository. It should be downloaded separately and placed under:

```text
data/raw/
```

Source:

* ARPAC Open Data: https://dati.arpacampania.it/it/dataset/dati-grezzi-orari-qualita-aria

---

## How the stream works

The historical data is not processed as one large batch by the online detector.

Instead, observations are ordered by timestamp and passed to the processor one by one.

For each observation, the processor updates:

* recent statistics for the station
* the latest value observed at each station
* nearby station information
* temporal and spatial anomaly scores

The basic flow is:

```text
ARPAC hourly data
        |
        v
   Stream replay
        |
        v
 Temporal features
        |
        +------> Spatial neighbours
        |                |
        v                v
      Online anomaly checks
        |
        v
   Dashboard / analysis
```

The spatial neighbourhood is based on a distance threshold between monitoring stations. The current default is **10 km**.

---

## Anomaly detection

### Temporal anomaly

Each station keeps a short rolling history of PM2.5 values.

A z-score is calculated from the recent observations:

```text
z = (current_value - rolling_mean) / rolling_std
```

An observation is marked as a temporal anomaly when its absolute z-score exceeds the configured threshold.

The current default temporal threshold is:

```text
|z| > 2.5
```

### Spatial anomaly

For a station, the processor looks at the most recent values from neighbouring stations.

The current observation is then compared with the local neighbourhood:

```text
spatial_z =
    (station_value - neighbour_mean)
    / neighbour_std
```

The current spatial threshold is:

```text
|spatial_z| > 2.0
```

These thresholds are not presented as universal air-quality limits. They are parameters of the anomaly-detection method and should be evaluated and tuned against better ground truth in future work.

### Regional events

A secondary analysis looks for nearby stations that show unusual behaviour within a short time window.

This part is currently implemented as a **batch analysis over the observations already processed by the stream**, rather than as a fully online regional-event detector.

This distinction is intentional and documented in the project.

---

## Results on the current dataset

Running the current anomaly pipeline on the ARPAC dataset produced:

| Metric                 | Result |
| ---------------------- | -----: |
| PM2.5 observations     |  3,628 |
| Monitoring stations    |     36 |
| Temporal anomalies     |    108 |
| Spatial anomalies      |    493 |
| Spatio-temporal events |     29 |

These numbers are specific to the current dataset and threshold configuration. They should not be interpreted as official ARPAC air-quality classifications.

---

## Dashboard

The project includes a small Streamlit dashboard for replaying the stream and inspecting the results.

The dashboard provides:

* stream replay controls
* processed observation count
* latest PM2.5 observation
* temporal and spatial anomaly indicators
* online stream visualization
* anomaly markers
* temporal and spatial z-scores
* anomaly heatmap
* regional event visualization
* station-level analysis
* station metadata
* recent anomaly table

The stream can be advanced manually using:

```text
Start Stream
Next 10 Observations
Reset
```

This keeps the dashboard simple while still making the online processing behaviour visible.

---

## Project structure

```text
AQStream-Campania/
│
├── dashboard/
│   └── app.py
│
├── data/
│   ├── raw/
│   │   └── .gitkeep
│   └── processed/
│       └── .gitkeep
│
├── docs/
│   ├── dashboard-overview.png
│   ├── stream-anomalies.png
│   └── regional-events.png
│
├── notebooks/
│   ├── 01_arpac_exploration.ipynb
│   └── 02_anomaly_analysis.ipynb
│
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
│
├── tests/
│   ├── test_anomaly.py
│   ├── test_arpac.py
│   ├── test_features.py
│   └── test_stream.py
│
├── .gitignore
├── README.md
└── requirements.txt
```

---

## Installation

Python 3.10+ is recommended.

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

Install the dependencies:

```bash
pip install -r requirements.txt
```

---

## Getting the data

Download the ARPAC hourly air-quality dataset and station metadata from the ARPAC Open Data portal.

Place the files in:

```text
data/raw/
```

The current project expects the ARPAC observation CSV and station metadata CSV to be available locally.

The raw files are ignored by Git because they are external input data.

---

## Running the dashboard

From the project root:

```bash
streamlit run dashboard/app.py
```

Then open the local Streamlit address shown in the terminal.

The dashboard can be used without running a separate backend service.

---

## Running the tests

Run:

```bash
pytest
```

The tests cover parts of:

* stream ordering
* online processor state
* spatial neighbour handling
* feature calculations
* ARPAC data loading

The goal of the tests is mainly to protect the core processing logic while the project is being developed.

---

## Design choices

### Why simulate a stream?

The available ARPAC data is historical data, but the main purpose of this project is to study stream processing.

Replaying the observations one by one provides a simple way to reproduce streaming behaviour without pretending that this repository is connected to a live production sensor network.

### Why not Kafka or another message broker?

A message broker would be useful in a production system, but it is not necessary for demonstrating the main idea here.

The focus of this project is the **online processing logic** rather than distributed infrastructure.

A future version could replace the replay generator with an MQTT, Kafka, or other real-time source.

### Why use spatial information?

Air-quality measurements are not independent.

A station can look unusual compared with its own recent history while still being consistent with nearby stations. The opposite can also happen: a station may look normal historically but be unusual compared with its local neighbourhood.

This is why both temporal and spatial context are used.

---

## Limitations

There are several limitations in the current version.

* The stream is simulated from historical ARPAC data.
* The anomaly thresholds are heuristic and have not been calibrated using labelled anomaly data.
* The current spatial model uses a simple distance-based neighbourhood.
* Regional event detection is currently a secondary batch analysis, not a fully online algorithm.
* Weather and meteorological variables are not included.
* There is no labelled ground truth for evaluating whether detected anomalies correspond to real events.
* One PM2.5 station in the observation data (`IT2342A`) does not have matching coordinates in the current station metadata file, so it cannot be used reliably for spatial analysis.
* The dashboard is intended for exploration and demonstration, not operational air-quality monitoring.

---

## Future work

Some possible next steps are:

* improve the online regional-event detector
* evaluate threshold sensitivity
* add labelled anomaly evaluation
* experiment with adaptive thresholds
* include meteorological variables
* investigate River-based online models
* connect the stream processor to MQTT or Kafka
* add automatic stream refresh to the dashboard
* improve the spatial event visualization

---

## References

1. **ARPAC – Agenzia Regionale per la Protezione Ambientale della Campania**
   Open Data Portal
   https://dati.arpacampania.it/

2. **ARPAC – Dati grezzi orari qualità aria**
   https://dati.arpacampania.it/it/dataset/dati-grezzi-orari-qualita-aria

3. **River – Online Machine Learning in Python**
   https://riverml.xyz/

4. **Streamlit Documentation**
   https://docs.streamlit.io/

5. **Pandas Documentation**
   https://pandas.pydata.org/docs/

6. **GeoPandas Documentation**
   https://geopandas.org/

---

## License

This project is intended for research, learning, and portfolio purposes.

The ARPAC data used by the project remains subject to the terms and conditions of the original data provider.
