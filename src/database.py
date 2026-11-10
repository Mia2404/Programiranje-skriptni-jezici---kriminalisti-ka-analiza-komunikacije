import sqlite3
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

BAZE = {
    "vast2008": DATA_DIR / "vast2008.db",
    "vast2018": DATA_DIR / "vast2018.db",
    "montagna": DATA_DIR / "montagna.db",
}

SHEMA = """
CREATE TABLE osobe (
    broj        TEXT PRIMARY KEY,
    ime         TEXT
);

CREATE TABLE bazne_stanice (
    stanica_id  TEXT PRIMARY KEY,
    naziv       TEXT,
    lat         REAL,
    lon         REAL
);

CREATE TABLE komunikacija (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    pozivatelj  TEXT NOT NULL,
    primatelj   TEXT NOT NULL,
    vrijeme     TEXT,
    tip         TEXT NOT NULL CHECK (tip IN ('poziv', 'email', 'sastanak', 'kupnja')),
    trajanje_s  INTEGER,
    stanica_id  TEXT,
    tezina      INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE scenarij (
    broj        TEXT NOT NULL,
    uloga       TEXT,
    odnos       TEXT,
    ishod       TEXT,
    izvor       TEXT NOT NULL
);

CREATE TABLE zamjene_brojeva (
    stari       TEXT NOT NULL,
    novi        TEXT NOT NULL,
    osoba       TEXT,
    izvor       TEXT NOT NULL
);

CREATE TABLE insajder_zapisi (
    pozivatelj  TEXT NOT NULL,
    primatelj   TEXT NOT NULL,
    vrijeme     TEXT,
    tip         TEXT NOT NULL,
    izvor       TEXT NOT NULL
);
"""

INDEKSI = """
CREATE INDEX idx_kom_vrijeme ON komunikacija(vrijeme);
CREATE INDEX idx_kom_pozivatelj ON komunikacija(pozivatelj);
CREATE INDEX idx_kom_primatelj ON komunikacija(primatelj);
"""

STUPCI_KOMUNIKACIJE = ["pozivatelj", "primatelj", "vrijeme", "tip", "trajanje_s", "stanica_id", "tezina"]


def povezi(putanja: Path) -> sqlite3.Connection:
    putanja.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(putanja)


def _vrijeme_u_tekst(df: pd.DataFrame) -> pd.DataFrame:
    if "vrijeme" in df and pd.api.types.is_datetime64_any_dtype(df["vrijeme"]):
        df = df.assign(vrijeme=df["vrijeme"].dt.strftime("%Y-%m-%d %H:%M:%S"))
    return df


def spremi(putanja: Path, podaci: dict) -> None:
    if putanja.exists():
        putanja.unlink()
    with povezi(putanja) as con:
        con.executescript(SHEMA)
        for tablica in ("osobe", "bazne_stanice", "scenarij", "zamjene_brojeva", "insajder_zapisi"):
            df = podaci.get(tablica)
            if df is not None and not df.empty:
                _vrijeme_u_tekst(df).to_sql(tablica, con, if_exists="append", index=False)

        dijelovi = podaci["komunikacija"]
        if isinstance(dijelovi, pd.DataFrame):
            dijelovi = [dijelovi]
        for kom in dijelovi:
            for stupac in STUPCI_KOMUNIKACIJE:
                if stupac not in kom:
                    kom = kom.assign(**{stupac: 1 if stupac == "tezina" else None})
            kom = _vrijeme_u_tekst(kom[STUPCI_KOMUNIKACIJE])
            con.executemany(
                f"INSERT INTO komunikacija ({', '.join(STUPCI_KOMUNIKACIJE)}) "
                f"VALUES ({', '.join('?' * len(STUPCI_KOMUNIKACIJE))})",
                kom.astype(object).where(kom.notna(), None).itertuples(index=False, name=None),
            )
        con.executescript(INDEKSI)


def _citaj(putanja: Path, upit: str, **kwargs) -> pd.DataFrame:
    if not putanja.exists():
        raise FileNotFoundError(f"Baza {putanja.name} ne postoji. Pokreni: python main.py ucitaj {putanja.stem}")
    with povezi(putanja) as con:
        return pd.read_sql(upit, con, **kwargs)


def ucitaj_komunikaciju(putanja: Path, tip: str | None = None) -> pd.DataFrame:
    upit = "SELECT * FROM komunikacija" + (f" WHERE tip = '{tip}'" if tip else "")
    df = _citaj(putanja, upit)
    df["vrijeme"] = pd.to_datetime(df["vrijeme"])
    return df


def ucitaj_osobe(putanja: Path) -> pd.DataFrame:
    return _citaj(putanja, "SELECT * FROM osobe")


def ucitaj_stanice(putanja: Path) -> pd.DataFrame:
    return _citaj(putanja, "SELECT * FROM bazne_stanice")


def ucitaj_scenarij(putanja: Path) -> pd.DataFrame:
    return _citaj(putanja, "SELECT * FROM scenarij")


def ucitaj_zamjene(putanja: Path) -> pd.DataFrame:
    return _citaj(putanja, "SELECT * FROM zamjene_brojeva")


def ucitaj_insajder(putanja: Path) -> pd.DataFrame:
    return _citaj(putanja, "SELECT * FROM insajder_zapisi")


def sazetak(putanja: Path) -> dict:
    with povezi(putanja) as con:
        po_vrsti = dict(con.execute("SELECT tip, COUNT(*) FROM komunikacija GROUP BY tip").fetchall())
        od, do = con.execute("SELECT MIN(vrijeme), MAX(vrijeme) FROM komunikacija").fetchone()
        return {
            "osoba": con.execute("SELECT COUNT(*) FROM osobe").fetchone()[0],
            "zapisa": sum(po_vrsti.values()),
            "po_vrsti": po_vrsti,
            "od": od,
            "do": do,
            "scenarij": con.execute("SELECT COUNT(*) FROM scenarij").fetchone()[0],
        }
