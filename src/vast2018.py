from pathlib import Path

import pandas as pd

from src.database import DATA_DIR

MAPA = DATA_DIR / "vast2018"

POCETAK = pd.Timestamp("2015-05-11 14:00:00")

TIPOVI = {0: "poziv", 1: "email", 2: "kupnja", 3: "sastanak"}

DATOTEKE = ["calls.csv", "emails.csv", "purchases.csv", "meetings.csv"]

INSAJDER_DATOTEKE = [
    "Suspicious_calls.csv",
    "Suspicious_emails.csv",
    "Suspicious_purchases.csv",
    "Suspicious_meetings.csv",
    "Other_suspicious_purchases.csv",
]

SUMNJIVA_SKUPINA = [
    "Alex Hall", "Lizbeth Jindra", "Patrick Lane", "Richard Fox", "Sara Ballard",
    "May Burton", "Glen Grant", "Dylan Ballard", "Meryl Pastuch", "Melita Scarpaci",
    "Augusta Sharp", "Kerstin Belveal", "Rosalia Larroque", "Lindsy Henion", "Julie Tierno",
    "Jose Ringwald", "Ramiro Gault", "Tobi Gatlin", "Refugio Orrantia", "Jenice Savaria",
]

IZVOR_SKUPINE = "VAST 2018 MC3, Insider_letter_to_M_Vogel.docx"

STUPCI = ["izvor_id", "tip_id", "odrediste_id", "sekunde"]


VELICINA_DIJELA = 500_000


def _citaj(putanja: Path) -> pd.DataFrame:
    zaglavlje = 0 if putanja.name.startswith("Other") else None
    df = pd.read_csv(putanja, header=zaglavlje, dtype="int64")
    df.columns = STUPCI
    return df


def _u_zapise(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "pozivatelj": df["izvor_id"].astype(str),
        "primatelj": df["odrediste_id"].astype(str),
        "vrijeme": POCETAK + pd.to_timedelta(df["sekunde"], unit="s"),
        "tip": df["tip_id"].map(TIPOVI),
    })


def _komunikacija_u_dijelovima(mapa: Path):
    for d in DATOTEKE:
        for dio in pd.read_csv(mapa / d, header=None, dtype="int64", chunksize=VELICINA_DIJELA):
            dio.columns = STUPCI
            yield _u_zapise(dio)


def ucitaj(mapa: Path = MAPA) -> dict:
    nedostaje = [d for d in DATOTEKE + INSAJDER_DATOTEKE + ["CompanyIndex.csv"] if not (mapa / d).exists()]
    if nedostaje:
        raise FileNotFoundError(f"U mapi {mapa} nedostaju datoteke: {', '.join(nedostaje)}")

    indeks = pd.read_csv(mapa / "CompanyIndex.csv", dtype={"ID": str})
    osobe = pd.DataFrame({
        "broj": indeks["ID"],
        "ime": indeks["first"].str.strip() + " " + indeks["last"].str.strip(),
    })

    po_imenu = osobe.set_index("ime")["broj"]
    nisu_pronadeni = [ime for ime in SUMNJIVA_SKUPINA if ime not in po_imenu.index]
    if nisu_pronadeni:
        raise ValueError(f"U imeniku nisu pronađeni: {', '.join(nisu_pronadeni)}")
    scenarij = pd.DataFrame({
        "broj": [po_imenu[ime] for ime in SUMNJIVA_SKUPINA],
        "uloga": "sumnjiva skupina prema insajderu",
        "odnos": None,
        "ishod": None,
        "izvor": IZVOR_SKUPINE,
    })

    insajder = pd.concat(
        [_u_zapise(_citaj(mapa / d)).assign(izvor=f"VAST 2018 MC3, {d}") for d in INSAJDER_DATOTEKE],
        ignore_index=True,
    )

    return {
        "osobe": osobe,
        "bazne_stanice": None,
        "komunikacija": _komunikacija_u_dijelovima(mapa),
        "scenarij": scenarij,
        "zamjene_brojeva": None,
        "insajder_zapisi": insajder,
    }
