import pandas as pd

from src.arpac import (
    load_arpac_pm25,
    load_arpac_stations,
)


def test_load_arpac_pm25(tmp_path):
    path = tmp_path / "arpac.csv"

    data = pd.DataFrame(
        [
            [
                1,
                "IT0936A",
                "Avellino AV41 Sc. V Circolo °",
                "PM2,5",
                "01-10-2026 00:00:00 +01:00",
                "18.81",
                "µg/m3",
            ],
            [
                2,
                "IT0936A",
                "Avellino AV41 Sc. V Circolo °",
                "NO2",
                "01-10-2026 00:00:00 +01:00",
                "28.43",
                "µg/m3",
            ],
        ],
        columns=[
            "_id",
            "Stazione",
            "Descrizione",
            "Inquinante",
            "Data_ora",
            "Valore",
            "Um",
        ],
    )

    data.to_csv(path, index=False)

    result = load_arpac_pm25(path)

    assert len(result) == 1
    assert result.iloc[0]["station_id"] == "IT0936A"
    assert result.iloc[0]["pm25"] == 18.81
    
def test_load_arpac_stations(tmp_path):
    path = tmp_path / "stations.csv"

    data = pd.DataFrame(
        [
            [
                "RRMQA",
                "IT1508",
                "Avellino AV41 Scuola V Circolo",
                "IT0936A",
                "1506402",
                "IT0936A",
                "Avellino",
                "Via O. D'Agostino",
                "FONDO",
                "40.9230537",
                "14.7866669",
                "366",
            ]
        ],
        columns=[
            "Rete",
            "Zona",
            "Nome Stazione",
            "Codice Europeo",
            "Codice Nazionale",
            "Codice Arpac",
            "Provincia",
            "indirizzo",
            "Tipo",
            "Latitudine",
            "Longitudine",
            "Slm",
        ],
    )

    data.to_csv(path, index=False)

    result = load_arpac_stations(path)

    assert len(result) == 1
    assert result.iloc[0]["station_id"] == "IT0936A"
    assert result.iloc[0]["station_name"] == (
        "Avellino AV41 Scuola V Circolo"
    )
    assert result.iloc[0]["latitude"] == 40.9230537
    assert result.iloc[0]["longitude"] == 14.7866669