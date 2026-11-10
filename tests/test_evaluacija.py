import pandas as pd
import pytest

from src import database, evaluacija
from src.evaluacija import IZVAN, NEPOZNATO, POZITIVNO


@pytest.fixture
def oznake():
    return pd.Series(
        {"A": POZITIVNO, "B": POZITIVNO, "C": IZVAN, "D": IZVAN, "E": NEPOZNATO, "F": IZVAN},
        name="oznaka",
    )


def test_procijeni_broji_pogotke_i_promasaje(oznake):
    r = evaluacija.procijeni(["A", "C", "E"], oznake)
    assert r["oznaceno"] == 3
    assert r["pogodaka"] == 1
    assert r["izvan_rjesenja"] == 1
    assert r["nepoznato"] == 1
    assert r["preciznost"] == 0.5
    assert r["odziv"] == 0.5
    assert r["ocekivano_slucajno"] == pytest.approx(3 * 2 / 6)


def test_procijeni_ne_broji_dvaput_istu_osobu(oznake):
    r = evaluacija.procijeni(["A", "A", "B", "B"], oznake)
    assert r["oznaceno"] == 2
    assert r["pogodaka"] == 2
    assert r["odziv"] == 1.0
    assert r["preciznost"] == 1.0


def test_procijeni_osoba_izvan_mreze_je_nepoznata(oznake):
    r = evaluacija.procijeni(["Z"], oznake)
    assert r["nepoznato"] == 1
    assert r["preciznost"] is None


def test_procijeni_prazan_odabir(oznake):
    r = evaluacija.procijeni([], oznake)
    assert r["oznaceno"] == 0
    assert r["pogodaka"] == 0
    assert r["preciznost"] is None
    assert r["odziv"] == 0.0


def test_rangovi_izjednacene_osobe_dijele_rang(oznake):
    vrijednosti = pd.Series({"A": 0.0, "B": 0.5, "C": 0.9, "D": 0.0, "F": 0.0})
    r = evaluacija.rangovi(vrijednosti, oznake)
    assert list(r["broj"]) == ["B", "A"]
    assert list(r["rang"]) == [2, 3]
    assert list(r["izjednacenih"]) == [1, 3]
    assert (r["od"] == 5).all()


def test_rangovi_osoba_izvan_mreze(oznake):
    r = evaluacija.rangovi(pd.Series({"B": 1.0, "C": 0.5}), oznake)
    assert r.loc[0, "broj"] == "B"
    assert r.loc[0, "rang"] == 1
    assert pd.isna(r.loc[1, "rang"])


def test_prvih_k_ukljucuje_izjednacene_na_granici():
    v = pd.Series({"a": 5.0, "b": 4.0, "c": 3.0, "d": 3.0, "e": 1.0})
    assert evaluacija.prvih_k(v, 3) == ["a", "b", "c", "d"]
    assert evaluacija.prvih_k(v, 2) == ["a", "b"]
    assert evaluacija.prvih_k(v, 10) == ["a", "b", "c", "d", "e"]


def test_prvih_k_ne_ovisi_o_redoslijedu_ulaza():
    v = pd.Series({"a": 2.0, "b": 2.0, "c": 1.0, "d": 2.0})
    obrnuto = v[::-1]
    assert evaluacija.prvih_k(v, 2) == evaluacija.prvih_k(obrnuto, 2) == ["a", "b", "d"]


def test_prvih_k_zanemaruje_sum_zaokruzivanja():
    v = pd.Series({"a": 0.1 + 0.2, "b": 0.3, "c": 0.1})
    assert evaluacija.prvih_k(v, 1) == ["a", "b"]


def _baza(tmp_path, scenarij, osobe):
    putanja = tmp_path / "test.db"
    database.spremi(putanja, {
        "osobe": pd.DataFrame({"broj": osobe, "ime": None}),
        "komunikacija": pd.DataFrame({"pozivatelj": [osobe[0]], "primatelj": [osobe[1]],
                                      "vrijeme": [pd.NaT], "tip": ["poziv"]}),
        "scenarij": scenarij,
    })
    return putanja


def test_oznake_vast(tmp_path):
    scenarij = pd.DataFrame({"broj": ["1"], "ime": ["X"], "uloga": ["u"], "odnos": [None],
                             "ishod": [None], "izvor": ["test"]})
    oz = evaluacija.oznake(_baza(tmp_path, scenarij, ["1", "2", "3"]), "vast2008")
    assert oz.to_dict() == {"1": POZITIVNO, "2": IZVAN, "3": IZVAN}


def test_oznake_montagna(tmp_path):
    scenarij = pd.DataFrame({
        "broj": ["N1", "N2", "N3", "N4", "N5", "N6", "N7", "N8"],
        "ime": None, "uloga": None, "odnos": None,
        "ishod": [" arrested", "in jail", "house arrest", "fugitive",
                  "arrest request denied", "lack of evidence", "uninvolved", None],
        "izvor": "test",
    })
    oz = evaluacija.oznake(_baza(tmp_path, scenarij, ["N1", "N2", "N3", "N4", "N5", "N6", "N7", "N8", "N9"]),
                           "montagna")
    assert list(oz[["N1", "N2", "N3", "N4"]]) == [POZITIVNO] * 4
    assert list(oz[["N5", "N6", "N7"]]) == [IZVAN] * 3
    assert oz["N8"] == NEPOZNATO
    assert oz["N9"] == NEPOZNATO


def test_svi_ishodi_montagne_su_razvrstani():
    putanja = database.BAZE["montagna"]
    if not putanja.exists():
        pytest.skip("baza montagna nije učitana")
    ishodi = set(database.ucitaj_scenarij(putanja)["ishod"].dropna().str.strip().str.lower())
    assert ishodi <= set(evaluacija.MONTAGNA_ISHODI)


@pytest.mark.parametrize("baza", ["vast2008", "montagna"])
def test_rezultat_ne_ovisi_o_redoslijedu_zapisa(baza):
    from src import analysis
    putanja = database.BAZE[baza]
    if not putanja.exists():
        pytest.skip(f"baza {baza} nije učitana")
    df = database.ucitaj_komunikaciju(putanja)
    izmijesano = df.sample(frac=1, random_state=1).reset_index(drop=True)

    def sazetak(d):
        G = analysis.izgradi_graf(d)
        oz = evaluacija.oznake(putanja, baza).reindex(list(G.nodes)).fillna(NEPOZNATO)
        rezultati, cent = evaluacija.metode(d, G, 10)
        return ({k: sorted(v) for k, v in rezultati.items()},
                evaluacija.rangovi(cent["posrednistvo"], oz).to_dict("records"))

    assert sazetak(df) == sazetak(izmijesano)
