from pathlib import Path

import pandas as pd

from src.database import DATA_DIR

MAPA = DATA_DIR / "montagna"

IZVOR = "Montagna Operation, Zenodo 10.5281/zenodo.3938818"


def _bridovi(putanja: Path, sep: str, tip: str) -> pd.DataFrame:
    df = pd.read_csv(putanja, sep=sep)
    df.columns = [c.strip() for c in df.columns]
    return pd.DataFrame({
        "pozivatelj": df["Source"].str.strip(),
        "primatelj": df["Target"].str.strip(),
        "vrijeme": pd.NaT,
        "tip": tip,
        "tezina": df["Weight"].astype(int),
    })


def _tekst(s: pd.Series) -> pd.Series:
    s = s.astype("string").str.strip()
    return s.mask(s == "")


def ucitaj(mapa: Path = MAPA) -> dict:
    pozivi = _bridovi(mapa / "Montagna_Phone_Calls_Edgelist.csv", ",", "poziv")
    sastanci = _bridovi(mapa / "Montagna_Meetings_Edgelist.csv", " ", "sastanak")
    kom = pd.concat([pozivi, sastanci], ignore_index=True)

    uloge = pd.read_csv(mapa / "Montagna_Roles.csv", dtype=str, encoding="utf-8-sig")
    uloge.columns = [c.strip() for c in uloge.columns]
    scenarij = pd.DataFrame({
        "broj": uloge["Node"].str.strip(),
        "ime": None,
        "uloga": _tekst(uloge["Role"]),
        "odnos": _tekst(uloge["Relationship"]),
        "ishod": _tekst(uloge["Request"]),
        "izvor": IZVOR,
    })

    cvorovi = sorted(set(kom["pozivatelj"]) | set(kom["primatelj"]) | set(scenarij["broj"]),
                     key=lambda c: int(c.lstrip("N")))
    osobe = pd.DataFrame({"broj": cvorovi, "ime": None})

    return {
        "osobe": osobe,
        "bazne_stanice": None,
        "komunikacija": kom,
        "scenarij": scenarij,
        "zamjene_brojeva": None,
    }
