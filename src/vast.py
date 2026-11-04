from pathlib import Path

import pandas as pd

VAST_DB_PUTANJA = Path(__file__).resolve().parent.parent / "data" / "vast.db"

ZAMJENE_RJESENJE = {
    "200": "300",
    "1": "309",
    "5": "306",
    "2": "397",
    "3": "360",
}

VODA = {"200", "300"}


def _uloga(broj: str) -> str:
    if broj in VODA:
        return "vođa"
    if broj in ZAMJENE_RJESENJE or broj in ZAMJENE_RJESENJE.values():
        return "član"
    return "civil"


def ucitaj(putanja_csv: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    sirovo = pd.read_csv(putanja_csv, dtype=str)
    sirovo.columns = ["pozivatelj", "primatelj", "vrijeme", "trajanje_s", "stanica_id"]

    kom = sirovo.assign(
        pozivatelj=sirovo["pozivatelj"].str.strip(),
        primatelj=sirovo["primatelj"].str.strip(),
        vrijeme=pd.to_datetime(sirovo["vrijeme"].str.strip(), format="%Y%m%d %H%M"),
        trajanje_s=pd.to_numeric(sirovo["trajanje_s"]),
        stanica_id=sirovo["stanica_id"].str.strip(),
        tip="poziv",
    )
    odbaceno = int((kom["trajanje_s"] < 0).sum())
    kom = kom[kom["trajanje_s"] >= 0]
    kom = kom[["pozivatelj", "primatelj", "vrijeme", "tip", "trajanje_s", "stanica_id"]]
    kom = kom.sort_values("vrijeme").reset_index(drop=True)

    brojevi = sorted(set(kom["pozivatelj"]) | set(kom["primatelj"]), key=int)
    osobe = pd.DataFrame({
        "broj": brojevi,
        "ime": None,
        "uloga": [_uloga(b) for b in brojevi],
    })

    stanice_id = sorted(kom["stanica_id"].unique(), key=int)
    stanice = pd.DataFrame({
        "stanica_id": stanice_id,
        "naziv": [f"Toranj {s}" for s in stanice_id],
        "lat": None,
        "lon": None,
    })

    print(f"Odbačeno zapisa s negativnim trajanjem: {odbaceno}")
    return osobe, stanice, kom
