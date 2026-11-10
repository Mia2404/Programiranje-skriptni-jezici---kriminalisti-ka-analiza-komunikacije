from pathlib import Path

import pandas as pd

from src.database import DATA_DIR

CSV = DATA_DIR / "CellPhoneCallRecords.csv"
STANICE_CSV = DATA_DIR / "vast2008_stanice.csv"

IZVOR_RJESENJA = "VAST 2008 MC3, CellCallsSolution.doc"

RJESENJE = [
    ("Ferdinando Catalano", "200", "300"),
    ("David Vidro", "1", "309"),
    ("Estaban Catalano", "5", "306"),
    ("Jorge Vidro", "2", "397"),
    ("Juan Vidro", "3", "360"),
]


def ucitaj(putanja_csv: Path = CSV, putanja_stanice: Path = STANICE_CSV) -> dict:
    sirovo = pd.read_csv(putanja_csv, dtype=str)
    sirovo.columns = ["pozivatelj", "primatelj", "vrijeme", "trajanje_s", "stanica_id"]
    sirovo = sirovo.apply(lambda s: s.str.strip())

    kom = sirovo.assign(
        vrijeme=pd.to_datetime(sirovo["vrijeme"], format="%Y%m%d %H%M"),
        trajanje_s=pd.to_numeric(sirovo["trajanje_s"]),
        tip="poziv",
    )
    neispravni = kom[kom["trajanje_s"] < 0]
    kom = kom[kom["trajanje_s"] >= 0].sort_values("vrijeme").reset_index(drop=True)

    brojevi = sorted(set(sirovo["pozivatelj"]) | set(sirovo["primatelj"]), key=int)
    osobe = pd.DataFrame({"broj": brojevi, "ime": None})

    stanice = pd.read_csv(putanja_stanice, dtype={"stanica_id": str})
    stanice = stanice.assign(naziv="Toranj " + stanice["stanica_id"])[["stanica_id", "naziv", "lat", "lon"]]

    scenarij = pd.DataFrame(
        [(b, ime, "član obitelji Catalano/Vidro", None, None, IZVOR_RJESENJA)
         for ime, stari, novi in RJESENJE for b in (stari, novi)],
        columns=["broj", "ime", "uloga", "odnos", "ishod", "izvor"],
    )
    zamjene = pd.DataFrame(
        [(stari, novi, ime, IZVOR_RJESENJA) for ime, stari, novi in RJESENJE],
        columns=["stari", "novi", "osoba", "izvor"],
    )

    return {
        "osobe": osobe,
        "bazne_stanice": stanice,
        "komunikacija": kom,
        "scenarij": scenarij,
        "zamjene_brojeva": zamjene,
        "neispravni": neispravni,
    }
