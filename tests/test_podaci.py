import csv
import sqlite3
from datetime import datetime

import pandas as pd
import pytest

from src import database, montagna, vast2008, vast2018
from src.database import DATA_DIR


@pytest.fixture(scope="module")
def v2008():
    return vast2008.ucitaj()


@pytest.fixture(scope="module")
def mont():
    return montagna.ucitaj()


def test_vast2008_svi_ispravni_zapisi_su_ucitani(v2008):
    with open(vast2008.CSV, newline="") as f:
        redci = list(csv.reader(f))[1:]
    assert len(redci) == 9834
    ocekivano = sorted(
        (a.strip(), b.strip(), datetime.strptime(t.strip(), "%Y%m%d %H%M"), int(d), s.strip())
        for a, b, t, d, s in redci if int(d) >= 0
    )
    kom = v2008["komunikacija"]
    ucitano = sorted(zip(kom["pozivatelj"], kom["primatelj"], [t.to_pydatetime() for t in kom["vrijeme"]],
                         kom["trajanje_s"].astype(int), kom["stanica_id"]))
    assert ucitano == ocekivano
    assert len(v2008["neispravni"]) == 4
    assert (v2008["neispravni"]["trajanje_s"] < 0).all()


def test_vast2008_analiza_ne_vidi_imena_iz_rjesenja(v2008):
    assert v2008["osobe"]["ime"].isna().all()
    assert len(v2008["osobe"]) == 400


def test_vast2008_rjesenje_prema_sluzbenom_dokumentu(v2008):
    zamjene = v2008["zamjene_brojeva"]
    assert list(zip(zamjene["osoba"], zamjene["stari"], zamjene["novi"])) == [
        ("Ferdinando Catalano", "200", "300"),
        ("David Vidro", "1", "309"),
        ("Estaban Catalano", "5", "306"),
        ("Jorge Vidro", "2", "397"),
        ("Juan Vidro", "3", "360"),
    ]
    assert sorted(v2008["scenarij"]["broj"], key=int) == ["1", "2", "3", "5", "200", "300", "306", "309", "360", "397"]


def test_vast2008_stanice(v2008):
    st = v2008["bazne_stanice"]
    assert sorted(st["stanica_id"], key=int) == [str(i) for i in range(1, 31)]
    assert st["lat"].between(23.4, 24.2).all()
    assert st["lon"].between(-80.4, -79.6).all()
    assert set(v2008["komunikacija"]["stanica_id"]) <= set(st["stanica_id"])


def test_montagna_tezine_jednake_izvoru(mont):
    kom = mont["komunikacija"]
    pozivi = pd.read_csv(montagna.MAPA / "Montagna_Phone_Calls_Edgelist.csv")
    sastanci = pd.read_csv(montagna.MAPA / "Montagna_Meetings_Edgelist.csv", sep=" ")
    assert (kom["tip"] == "poziv").sum() == len(pozivi) == 150
    assert (kom["tip"] == "sastanak").sum() == len(sastanci) == 289
    assert kom.loc[kom["tip"] == "poziv", "tezina"].sum() == pozivi["Weight"].sum() == 276
    assert kom.loc[kom["tip"] == "sastanak", "tezina"].sum() == sastanci["Weight"].sum() == 456
    assert kom["vrijeme"].isna().all()


def test_montagna_uloge(mont):
    sc = mont["scenarij"]
    assert len(sc) == 143
    assert sc["broj"].is_unique
    assert sc.set_index("broj").loc["N11", "uloga"] == "boss Cosa Nostra in Messina"
    assert sc.set_index("broj").loc["N99", "ishod"] == "arrested"
    assert len(mont["osobe"]) == 145


def test_spremi_i_ucitaj_bez_gubitka(tmp_path, v2008):
    putanja = tmp_path / "v.db"
    database.spremi(putanja, v2008)
    kom = database.ucitaj_komunikaciju(putanja)
    assert len(kom) == 9830
    izvor = v2008["komunikacija"].sort_values(["vrijeme", "pozivatelj", "primatelj"]).reset_index(drop=True)
    baza = kom.sort_values(["vrijeme", "pozivatelj", "primatelj"]).reset_index(drop=True)
    for stupac in ("pozivatelj", "primatelj", "vrijeme", "tip", "stanica_id"):
        assert list(izvor[stupac]) == list(baza[stupac])
    assert list(izvor["trajanje_s"].astype(int)) == list(baza["trajanje_s"].astype(int))
    assert len(database.ucitaj_scenarij(putanja)) == 10
    assert len(database.ucitaj_zamjene(putanja)) == 5
    assert len(database.ucitaj_stanice(putanja)) == 30
    assert database.ucitaj_osobe(putanja)["ime"].isna().all()


def test_vast2018_pretvorba_vremena():
    df = pd.DataFrame({"izvor_id": [1, 2], "tip_id": [0, 3], "odrediste_id": [5, 6], "sekunde": [0, 86400 + 61]})
    z = vast2018._u_zapise(df)
    assert list(z["vrijeme"]) == [pd.Timestamp("2015-05-11 14:00:00"), pd.Timestamp("2015-05-12 14:01:01")]
    assert list(z["tip"]) == ["poziv", "sastanak"]
    assert list(z["pozivatelj"]) == ["1", "2"]


@pytest.mark.skipif(not (DATA_DIR / "vast2018.db").exists(), reason="baza vast2018 nije učitana")
def test_vast2018_baza_odgovara_izvoru():
    with sqlite3.connect(DATA_DIR / "vast2018.db") as con:
        po_vrsti = dict(con.execute("SELECT tip, COUNT(*) FROM komunikacija GROUP BY tip").fetchall())
        scenarij = con.execute("SELECT COUNT(*) FROM scenarij").fetchone()[0]
        insajder = dict(con.execute("SELECT izvor, COUNT(*) FROM insajder_zapisi GROUP BY izvor").fetchall())
        osoba = con.execute("SELECT COUNT(*) FROM osobe").fetchone()[0]
    assert po_vrsti == {"poziv": 10606835, "email": 14550085, "kupnja": 762200, "sastanak": 127351}
    assert scenarij == 20
    assert osoba == 642631
    assert insajder == {
        "VAST 2018 MC3, Suspicious_calls.csv": 70,
        "VAST 2018 MC3, Suspicious_emails.csv": 61,
        "VAST 2018 MC3, Suspicious_purchases.csv": 1,
        "VAST 2018 MC3, Suspicious_meetings.csv": 5,
        "VAST 2018 MC3, Other_suspicious_purchases.csv": 7,
    }


@pytest.mark.skipif(not (vast2018.MAPA / "CompanyIndex.csv").exists(), reason="podaci vast2018 nisu u data/vast2018")
def test_vast2018_skupina_iz_pisma_postoji_u_imeniku():
    indeks = pd.read_csv(vast2018.MAPA / "CompanyIndex.csv", dtype={"ID": str})
    imena = set(indeks["first"].str.strip() + " " + indeks["last"].str.strip())
    assert set(vast2018.SUMNJIVA_SKUPINA) <= imena
    assert len(vast2018.SUMNJIVA_SKUPINA) == 20
