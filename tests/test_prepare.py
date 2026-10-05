import pandas as pd

from src.prepare import prepare_arpac_data


def test_prepare_arpac_data(tmp_path):
    observations_path = tmp_path / "observations.csv"
    stations_path = tmp_path / "stations.csv"

    observations = pd.DataFrame(
        [
            [
                "IT0936A",
                "Avellino AV41 Scuola V Circolo",
                "PM2,5",
                "01-10-2026 00:00:00 +01:00",
                "18.81",
                "µg/m3",
            ]
        ],
        columns=[
            "Stazione",
            "Descrizione",
            "Inquinante",
            "Data_ora",
            "Valore",
            "Um",
        ],
    )

    stations = pd.DataFrame(
        [
            [
                "IT0936A",
                "Avellino AV41 Scuola V Circolo",
                "Avellino",
                40.9230537,
                14.7866669,
                "FONDO",
            ]
        ],
        columns=[
            "Codice Arpac",
            "Nome Stazione",
            "Provincia",
            "Latitudine",
            "Longitudine",
            "Tipo",
        ],
    )

    observations.to_csv(observations_path, index=False)
    stations.to_csv(stations_path, index=False)

    result = prepare_arpac_data(
        observations_path,
        stations_path,
    )

    assert len(result) == 1
    assert result.iloc[0]["station_id"] == "IT0936A"
    assert result.iloc[0]["pm25"] == 18.81
    assert result.iloc[0]["latitude"] == 40.9230537