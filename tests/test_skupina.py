import pandas as pd
import pytest

from src import database, skupina


@pytest.fixture
def mreza(napravi_kom, zapis):
    return napravi_kom([
        zapis("A", "B", "2020-01-05 10:00"),
        zapis("B", "C", "2020-01-06 10:00"),
        zapis("A", "C", "2020-02-01 10:00", tip="email"),
        zapis("A", "X", "2020-01-01 10:00"),
        zapis("X", "B", "2020-01-02 10:00", tip="email"),
        zapis("X", "C", "2020-01-03 10:00", tip="sastanak"),
        zapis("Y", "A", "2020-01-04 10:00"),
        zapis("Y", "A", "2020-01-04 11:00"),
        zapis("Y", "A", "2020-01-04 12:00"),
        zapis("Z", "B", "2020-01-04 10:00", tip="kupnja"),
        zapis("Q", "R", "2020-01-04 10:00"),
    ])


def test_povezanost_broji_razlicite_clanove(mreza):
    t = skupina.povezanost(mreza, {"A", "B", "C"})
    assert list(t.index) == ["X", "Y", "Z"]
    assert t.loc["X", "broj_clanova"] == 3
    assert t.loc["Y", "broj_clanova"] == 1
    assert t.loc["Y", "kontakata"] == 3
    assert t.loc["X", "poziv"] == 1 and t.loc["X", "email"] == 1 and t.loc["X", "sastanak"] == 1
    assert t.loc["Z", "kupnja"] == 1
    assert "Q" not in t.index and "R" not in t.index


def test_povezanost_vise_kontakata_kod_izjednacenih(mreza):
    t = skupina.povezanost(mreza, {"A", "B", "C"})
    assert t.loc["X", "rang"] == 1
    assert t.loc["Y", "rang"] == 2
    assert t.loc["Z", "rang"] == 3


def test_povezanost_izjednaceni_dijele_rang(napravi_kom, zapis):
    df = napravi_kom([zapis("P", "A"), zapis("R", "A"), zapis("S", "A"), zapis("S", "A")])
    t = skupina.povezanost(df, {"A"})
    assert t.loc["S", "rang"] == 1
    assert t.loc["P", "rang"] == 2
    assert t.loc["R", "rang"] == 2


def test_povezanost_unutarnji_kontakti_se_ne_broje(mreza):
    t = skupina.povezanost(mreza, {"A", "B", "C"})
    assert not set(t.index) & {"A", "B", "C"}


def test_izostavi_jednog(mreza):
    r = skupina.izostavi_jednog(mreza, {"A", "B", "C"}).set_index("clan")
    assert r.loc["A", "rang"] == 1
    assert r.loc["A", "povezan_s_clanova"] == 2
    assert r.loc["B", "povezan_s_clanova"] == 2
    assert r.loc["C", "povezan_s_clanova"] == 2


def test_izostavi_jednog_nepovezani_clan(napravi_kom, zapis):
    df = napravi_kom([zapis("A", "B"), zapis("C", "X")])
    r = skupina.izostavi_jednog(df, {"A", "B", "C"}).set_index("clan")
    assert pd.isna(r.loc["C", "rang"])
    assert r.loc["C", "povezan_s_clanova"] == 0


def test_bliski_suradnici_ukljucuju_izjednacene(napravi_kom, zapis):
    df = napravi_kom([zapis("P", "A"), zapis("R", "A"), zapis("S", "A"), zapis("S", "A")])
    assert set(skupina.bliski_suradnici(df, {"A"}, k=2).index) == {"S", "P", "R"}
    assert set(skupina.bliski_suradnici(df, {"A"}, k=1).index) == {"S"}


def test_unutarnji_tijek(mreza):
    t = skupina.unutarnji_tijek(mreza, {"A", "B", "C"})
    assert t.loc[pd.Period("2020-01", "M"), "poziv"] == 2
    assert t.loc[pd.Period("2020-02", "M"), "email"] == 1
    assert int(t.values.sum()) == 3


def test_profil_osobe(mreza):
    p = skupina.profil_osobe(mreza, "X", {"A", "B", "C"})
    assert p == {"broj": "X", "kontakata": 3, "razlicitih_osoba": 3,
                 "kontakata_sa_skupinom": 3, "clanova_skupine": 3}


def test_zapisi_oko_iz_baze(tmp_path, mreza):
    putanja = tmp_path / "s.db"
    database.spremi(putanja, {"osobe": pd.DataFrame({"broj": list("ABCXYZQR"), "ime": None}),
                              "komunikacija": mreza.drop(columns="id")})
    df = skupina.zapisi_oko(putanja, {"A"})
    assert len(df) == 6
    assert ((df["pozivatelj"] == "A") | (df["primatelj"] == "A")).all()
    assert len(skupina.zapisi_oko(putanja, {"Q", "Z"})) == 2


@pytest.mark.skipif(not database.BAZE["vast2018"].exists(), reason="baza vast2018 nije učitana")
def test_vast2018_zapisi_oko_skupine_sadrze_sve_insajderove():
    putanja = database.BAZE["vast2018"]
    clanovi = set(database.ucitaj_scenarij(putanja)["broj"])
    df = skupina.zapisi_oko(putanja, clanovi)
    unutra = df[df["pozivatelj"].isin(clanovi) & df["primatelj"].isin(clanovi)]
    assert len(df) == 2035
    assert len(unutra) == 137
    assert unutra["tip"].value_counts().to_dict() == {"poziv": 70, "email": 61, "sastanak": 5, "kupnja": 1}
