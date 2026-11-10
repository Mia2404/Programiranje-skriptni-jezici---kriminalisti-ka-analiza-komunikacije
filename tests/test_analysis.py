import pandas as pd

from src import analysis


def test_graf_zbraja_tezine_i_nije_usmjeren(napravi_kom, zapis):
    df = napravi_kom([zapis("A", "B", tezina=1), zapis("B", "A", tezina=2), zapis("A", "C")])
    G = analysis.izgradi_graf(df)
    assert G.number_of_nodes() == 3
    assert G.number_of_edges() == 2
    assert G["A"]["B"]["tezina"] == 3
    assert G["B"]["A"]["tezina"] == 3
    assert G["A"]["C"]["tezina"] == 1
    assert abs(G["A"]["B"]["udaljenost"] - 1 / 3) < 1e-12


def test_centralnost_sredisnja_osoba_zvijezde_je_prva(napravi_kom, zapis):
    df = napravi_kom([zapis("S", x) for x in "ABCDE"])
    cent = analysis.centralnost(analysis.izgradi_graf(df))
    assert cent.index[0] == "S"
    assert cent.loc["S", "posrednistvo"] == 1.0
    assert cent.loc["S", "stupanj"] == 1.0
    assert (cent.drop("S")["posrednistvo"] == 0).all()


def test_centralnost_most_izmedu_dvije_skupine(napravi_kom, zapis):
    lijevo = [zapis(a, b) for a, b in [("A", "B"), ("B", "C"), ("A", "C")]]
    desno = [zapis(a, b) for a, b in [("D", "E"), ("E", "F"), ("D", "F")]]
    most = [zapis("C", "M"), zapis("M", "D")]
    cent = analysis.centralnost(analysis.izgradi_graf(napravi_kom(lijevo + desno + most)))
    assert cent.index[0] == "M"


def test_nocna_aktivnost_granice(napravi_kom, zapis):
    df = napravi_kom([
        zapis("u2200", "X", "2020-01-01 22:00"),
        zapis("u2159", "X", "2020-01-01 21:59"),
        zapis("u0359", "X", "2020-01-02 03:59"),
        zapis("u0400", "X", "2020-01-02 04:00"),
        zapis("u0000", "X", "2020-01-02 00:00"),
        zapis("pola", "X", "2020-01-02 23:30"),
        zapis("pola", "X", "2020-01-02 12:00"),
    ])
    nocna = analysis.nocna_aktivnost(df)
    assert nocna["u2200"] == 1.0
    assert nocna["u2159"] == 0.0
    assert nocna["u0359"] == 1.0
    assert nocna["u0400"] == 0.0
    assert nocna["u0000"] == 1.0
    assert nocna["pola"] == 0.5


def test_promjene_ponasanja_otkrivaju_nagli_porast(napravi_kom, zapis):
    zapisi = [zapis("A", "X", f"2020-01-{d:02d} 10:00") for d in range(1, 8)]
    zapisi += [zapis("A", "X", "2020-01-08 10:00") for _ in range(10)]
    zapisi += [zapis("B", "X", f"2020-01-{d:02d} 10:00") for d in range(1, 9)]
    rezultat = analysis.promjene_ponasanja(napravi_kom(zapisi))
    assert list(rezultat["broj"]) == ["A"]
    assert rezultat.loc[0, "dan"] == pd.Timestamp("2020-01-08")
    assert rezultat.loc[0, "z"] == 9.0


def test_promjene_ponasanja_trebaju_sedam_dana_povijesti(napravi_kom, zapis):
    zapisi = [zapis("A", "X", f"2020-01-{d:02d} 10:00") for d in range(1, 7)]
    zapisi += [zapis("A", "X", "2020-01-07 10:00") for _ in range(20)]
    assert analysis.promjene_ponasanja(napravi_kom(zapisi)).empty


def test_novi_brojevi_nakon_prve_cetvrtine_razdoblja(napravi_kom, zapis):
    df = napravi_kom([
        zapis("A", "B", "2020-01-01 00:00"),
        zapis("A", "C", "2020-01-03 12:00"),
        zapis("D", "A", "2020-01-03 12:01"),
        zapis("A", "E", "2020-01-08 00:00"),
        zapis("A", "B", "2020-01-11 00:00"),
    ])
    novi = analysis.novi_brojevi(df)
    assert list(novi["broj"]) == ["D", "E"]
    assert novi.loc[0, "prvo_pojavljivanje"] == pd.Timestamp("2020-01-03 12:01")


def test_novi_brojevi_granica_ovisi_o_duljini_razdoblja(napravi_kom, zapis):
    kratko = napravi_kom([zapis("A", "B", "2020-01-01"), zapis("C", "A", "2020-01-04"),
                          zapis("A", "B", "2020-01-11")])
    dugo = napravi_kom([zapis("A", "B", "2020-01-01"), zapis("C", "A", "2020-01-04"),
                        zapis("A", "B", "2020-03-01")])
    assert list(analysis.novi_brojevi(kratko)["broj"]) == ["C"]
    assert analysis.novi_brojevi(dugo).empty


def test_novi_brojevi_udio_nula_i_jedan(napravi_kom, zapis):
    df = napravi_kom([zapis("A", "B", "2020-01-01"), zapis("C", "A", "2020-01-05"),
                      zapis("A", "D", "2020-01-10")])
    assert set(analysis.novi_brojevi(df, udio=0)["broj"]) == {"C", "D"}
    assert analysis.novi_brojevi(df, udio=1).empty
