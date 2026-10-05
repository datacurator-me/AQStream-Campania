from pathlib import Path

import pandas as pd


ARPAC_COLUMNS = {
    "Stazione": "station_id",
    "Descrizione": "station_name",
    "Data_ora": "timestamp",
    "Valore": "pm25",
}


def load_arpac_pm25(path: str | Path) -> pd.DataFrame:
    """Load PM2.5 observations from an ARPAC NRT CSV."""

    df = pd.read_csv(
        path,
        sep=",",
        encoding="utf-8",
    )

    df = df[df["Inquinante"].astype(str).str.strip() == "PM2,5"].copy()

    df = df.rename(columns=ARPAC_COLUMNS)

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce",
    )

    df["pm25"] = pd.to_numeric(
        df["pm25"],
        errors="coerce",
    )

    df = df.dropna(
        subset=["station_id", "timestamp", "pm25"]
    )

    df = df[
        ["station_id", "station_name", "timestamp", "pm25"]
    ]

    df = df.sort_values(
        ["timestamp", "station_id"]
    ).reset_index(drop=True)

    return df

def load_arpac_stations(path: str | Path) -> pd.DataFrame:
    """Load station metadata from the ARPAC network CSV."""

    import csv

    with open(path, encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file)

        header = next(reader)
        rows = []

        for row in reader:
            if len(row) == len(header) + 1:
                row = (
                    row[:7]
                    + [row[7] + "," + row[8]]
                    + row[9:]
                )

            rows.append(row)

    df = pd.DataFrame(
        rows,
        columns=header,
    )

    df.columns = df.columns.str.strip()

    df = df.rename(
        columns={
            "Codice Arpac": "station_id",
            "Nome Stazione": "station_name",
            "Provincia": "province",
            "Latitudine": "latitude",
            "Longitudine": "longitude",
            "Tipo": "station_type",
        }
    )

    df["latitude"] = pd.to_numeric(
        df["latitude"],
        errors="coerce",
    )

    df["longitude"] = pd.to_numeric(
        df["longitude"],
        errors="coerce",
    )

    df = df.dropna(
        subset=["station_id", "latitude", "longitude"]
    )

    df = df[
        [
            "station_id",
            "station_name",
            "province",
            "latitude",
            "longitude",
            "station_type",
        ]
    ].drop_duplicates(
        subset=["station_id"]
    )

    return df.reset_index(drop=True)