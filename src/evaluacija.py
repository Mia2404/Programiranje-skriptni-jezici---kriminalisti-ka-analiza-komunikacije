from pathlib import Path

import networkx as nx
import pandas as pd

from src import analysis, database

POZITIVNO = "u rješenju"
IZVAN = "izvan rješenja"
NEPOZNATO = "nepoznato"

MONTAGNA_ISHODI = {
    "arrested": POZITIVNO,
    "in jail": POZITIVNO,
    "house arrest": POZITIVNO,
    "fugitive": POZITIVNO,
    "arrest request denied": IZVAN,
    "lack of evidence": IZVAN,
    "uninvolved": IZVAN,
}


def oznake(putanja: Path, baza: str) -> pd.Series:
    osobe = database.ucitaj_osobe(putanja)["broj"]
    scenarij = database.ucitaj_scenarij(putanja)

    if baza == "montagna":
        ishod = scenarij.set_index("broj")["ishod"].str.strip().str.lower()
        rezultat = pd.Series(NEPOZNATO, index=osobe, dtype=object)
        poznati = ishod.map(MONTAGNA_ISHODI).dropna()
        rezultat.loc[poznati.index] = poznati
    else:
        rezultat = pd.Series(IZVAN, index=osobe, dtype=object)
        rezultat.loc[rezultat.index.isin(scenarij["broj"])] = POZITIVNO

    rezultat.index.name = "broj"
    return rezultat.rename("oznaka")


def procijeni(oznaceni, oznake_osoba: pd.Series) -> dict:
    oznaceni = list(dict.fromkeys(oznaceni))
    o = oznake_osoba.reindex(oznaceni).fillna(NEPOZNATO)
    pogodaka = int((o == POZITIVNO).sum())
    izvan = int((o == IZVAN).sum())
    nepoznato = int((o == NEPOZNATO).sum())
    ukupno_pozitivnih = int((oznake_osoba == POZITIVNO).sum())
    udio_pozitivnih = ukupno_pozitivnih / len(oznake_osoba) if len(oznake_osoba) else 0.0
    return {
        "oznaceno": len(oznaceni),
        "pogodaka": pogodaka,
        "izvan_rjesenja": izvan,
        "nepoznato": nepoznato,
        "preciznost": pogodaka / (pogodaka + izvan) if pogodaka + izvan else None,
        "odziv": pogodaka / ukupno_pozitivnih if ukupno_pozitivnih else None,
        "ocekivano_slucajno": len(oznaceni) * udio_pozitivnih,
    }


DECIMALE = 12


def prvih_k(vrijednosti: pd.Series, k: int) -> list:
    v = vrijednosti.round(DECIMALE)
    if len(v) <= k:
        granica = v.min()
    else:
        granica = v.sort_values(ascending=False).iloc[k - 1]
    odabrani = v[v >= granica]
    return sorted(odabrani.index, key=lambda broj: (-odabrani[broj], str(broj)))


def rangovi(vrijednosti: pd.Series, oznake_osoba: pd.Series) -> pd.DataFrame:
    rang = vrijednosti.round(DECIMALE).rank(method="min", ascending=False)
    pozitivni = oznake_osoba[oznake_osoba == POZITIVNO].index
    tablica = pd.DataFrame({
        "broj": pozitivni,
        "rang": [int(rang[b]) if b in rang.index else None for b in pozitivni],
        "izjednacenih": [int((rang == rang[b]).sum()) if b in rang.index else None for b in pozitivni],
        "od": len(rang),
    })
    tablica["rang"] = tablica["rang"].astype("Int64")
    tablica["izjednacenih"] = tablica["izjednacenih"].astype("Int64")
    return tablica.sort_values(["rang", "broj"], na_position="last").reset_index(drop=True)


def metode(df_kom: pd.DataFrame, G: nx.Graph, k: int) -> tuple[dict, pd.DataFrame]:
    cent = analysis.centralnost(G)
    rezultat = {}
    for mjera, naziv in [("posrednistvo", "posredništvo"), ("stupanj", "stupanj"),
                         ("blizina", "blizina"), ("pagerank", "PageRank")]:
        rezultat[f"Centralnost – {naziv}, prvih {k}"] = prvih_k(cent[mjera], k)

    if df_kom["vrijeme"].notna().any():
        rezultat[f"Noćna aktivnost, prvih {k}"] = prvih_k(analysis.nocna_aktivnost(df_kom), k)
        rezultat["Nagli porasti aktivnosti (z > 3)"] = list(analysis.promjene_ponasanja(df_kom)["broj"])
        rezultat["Brojevi koji su se pojavili naknadno"] = list(analysis.novi_brojevi(df_kom)["broj"])
    return rezultat, cent


def evaluiraj(baza: str, k: int = 10) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    putanja = database.BAZE[baza]
    df_kom = database.ucitaj_komunikaciju(putanja)
    G = analysis.izgradi_graf(df_kom)
    oz = oznake(putanja, baza).reindex(list(G.nodes)).fillna(NEPOZNATO)
    oz.index.name = "broj"

    rezultati, cent = metode(df_kom, G, k)
    tablica = pd.DataFrame(
        [{"metoda": naziv, **procijeni(oznaceni, oz)} for naziv, oznaceni in rezultati.items()]
    )
    return tablica, rangovi(cent["posrednistvo"], oz), oz
