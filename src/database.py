import sqlite3
from pathlib import Path

import pandas as pd

DB_PUTANJA = Path(__file__).resolve().parent.parent / "data" / "komunikacija.db"

SHEMA = """
CREATE TABLE IF NOT EXISTS osobe (
    broj        TEXT PRIMARY KEY,
    ime         TEXT
);

CREATE TABLE IF NOT EXISTS bazne_stanice (
    stanica_id  TEXT PRIMARY KEY,
    naziv       TEXT,
    lat         REAL,
    lon         REAL
);

CREATE TABLE IF NOT EXISTS komunikacija (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    pozivatelj  TEXT NOT NULL REFERENCES osobe(broj),
    primatelj   TEXT NOT NULL REFERENCES osobe(broj),
    vrijeme     TEXT NOT NULL,
    tip         TEXT CHECK (tip IN ('poziv', 'sms')),
    trajanje_s  INTEGER,
    stanica_id  TEXT REFERENCES bazne_stanice(stanica_id)
);

CREATE INDEX IF NOT EXISTS idx_kom_vrijeme ON komunikacija(vrijeme);

CREATE TABLE IF NOT EXISTS scenarij (
    broj        TEXT PRIMARY KEY,
    uloga       TEXT
);
"""


def povezi(putanja: Path = DB_PUTANJA) -> sqlite3.Connection:
    putanja.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(putanja)


def spremi(df_osobe: pd.DataFrame, df_stanice: pd.DataFrame, df_kom: pd.DataFrame,
           putanja: Path = DB_PUTANJA) -> None:
    if putanja.exists():
        putanja.unlink()
    with povezi(putanja) as con:
        con.executescript(SHEMA)
        df_osobe[["broj", "ime"]].to_sql("osobe", con, if_exists="append", index=False)
        df_osobe[["broj", "uloga"]].to_sql("scenarij", con, if_exists="append", index=False)
        df_stanice.to_sql("bazne_stanice", con, if_exists="append", index=False)
        kom = df_kom.copy()
        kom["vrijeme"] = kom["vrijeme"].astype(str)
        kom.to_sql("komunikacija", con, if_exists="append", index=False)


def ucitaj_komunikaciju(putanja: Path = DB_PUTANJA) -> pd.DataFrame:
    with povezi(putanja) as con:
        return pd.read_sql("SELECT * FROM komunikacija", con, parse_dates=["vrijeme"])


def ucitaj_osobe(putanja: Path = DB_PUTANJA) -> pd.DataFrame:
    with povezi(putanja) as con:
        return pd.read_sql("SELECT * FROM osobe", con)


def ucitaj_stanice(putanja: Path = DB_PUTANJA) -> pd.DataFrame:
    with povezi(putanja) as con:
        return pd.read_sql("SELECT * FROM bazne_stanice", con)


def ucitaj_scenarij(putanja: Path = DB_PUTANJA) -> pd.DataFrame:
    with povezi(putanja) as con:
        return pd.read_sql("SELECT * FROM scenarij", con)
