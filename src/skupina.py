from pathlib import Path

import pandas as pd

from src import database

TIPOVI = ["poziv", "email", "sastanak", "kupnja"]


def zapisi_oko(putanja: Path, brojevi) -> pd.DataFrame:
    brojevi = sorted(set(map(str, brojevi)))
    with database.povezi(putanja) as con:
        con.execute("CREATE TEMP TABLE trazeni (broj TEXT PRIMARY KEY)")
        con.executemany("INSERT INTO trazeni VALUES (?)", [(b,) for b in brojevi])
        df = pd.read_sql(
            "SELECT * FROM komunikacija WHERE pozivatelj IN (SELECT broj FROM trazeni) "
            "UNION SELECT * FROM komunikacija WHERE primatelj IN (SELECT broj FROM trazeni)",
            con,
        )
    df["vrijeme"] = pd.to_datetime(df["vrijeme"])
    return df.sort_values(["vrijeme", "id"]).reset_index(drop=True)


def _veze_prema_van(df: pd.DataFrame, skupina: set) -> pd.DataFrame:
    a_u = df["pozivatelj"].isin(skupina)
    b_u = df["primatelj"].isin(skupina)
    van_a = df[a_u & ~b_u].rename(columns={"pozivatelj": "clan", "primatelj": "osoba"})
    van_b = df[b_u & ~a_u].rename(columns={"primatelj": "clan", "pozivatelj": "osoba"})
    return pd.concat([van_a, van_b], ignore_index=True)[["clan", "osoba", "tip", "tezina"]]


def povezanost(df: pd.DataFrame, skupina) -> pd.DataFrame:
    skupina = set(map(str, skupina))
    veze = _veze_prema_van(df, skupina)
    if veze.empty:
        return pd.DataFrame(columns=["broj_clanova", "kontakata", *TIPOVI, "rang"]).rename_axis("osoba")
    tablica = veze.groupby("osoba").agg(broj_clanova=("clan", "nunique"), kontakata=("tezina", "sum"))
    po_tipu = veze.pivot_table(index="osoba", columns="tip", values="tezina", aggfunc="sum", fill_value=0)
    tablica = tablica.join(po_tipu.reindex(columns=TIPOVI, fill_value=0))
    tablica = tablica.reset_index().sort_values(
        ["broj_clanova", "kontakata", "osoba"], ascending=[False, False, True]
    )
    kljuc = list(zip(tablica["broj_clanova"], tablica["kontakata"]))
    prvi = {}
    for i, k in enumerate(kljuc, start=1):
        prvi.setdefault(k, i)
    tablica["rang"] = [prvi[k] for k in kljuc]
    return tablica.set_index("osoba")


def bliski_suradnici(df: pd.DataFrame, skupina, k: int = 10) -> pd.DataFrame:
    tablica = povezanost(df, skupina)
    if tablica.empty:
        return tablica
    granica = tablica["rang"].iloc[min(k, len(tablica)) - 1]
    return tablica[tablica["rang"] <= granica]


def izostavi_jednog(df: pd.DataFrame, skupina) -> pd.DataFrame:
    skupina = sorted(set(map(str, skupina)))
    redci = []
    for clan in skupina:
        ostali = set(skupina) - {clan}
        tablica = povezanost(df, ostali)
        if clan in tablica.index:
            r = tablica.loc[clan]
            redci.append({"clan": clan, "rang": int(r["rang"]), "kandidata": len(tablica),
                          "povezan_s_clanova": int(r["broj_clanova"]), "kontakata": int(r["kontakata"])})
        else:
            redci.append({"clan": clan, "rang": None, "kandidata": len(tablica),
                          "povezan_s_clanova": 0, "kontakata": 0})
    rezultat = pd.DataFrame(redci)
    rezultat["rang"] = rezultat["rang"].astype("Int64")
    rezultat["ocekivano_slucajno"] = (rezultat["kandidata"] + 1) / 2
    return rezultat.sort_values(["rang", "clan"], na_position="last").reset_index(drop=True)


def unutarnji_tijek(df: pd.DataFrame, skupina) -> pd.DataFrame:
    skupina = set(map(str, skupina))
    unutra = df[df["pozivatelj"].isin(skupina) & df["primatelj"].isin(skupina)]
    if unutra.empty:
        return pd.DataFrame(columns=TIPOVI)
    tablica = unutra.assign(mjesec=unutra["vrijeme"].dt.to_period("M")).pivot_table(
        index="mjesec", columns="tip", values="tezina", aggfunc="sum", fill_value=0
    )
    return tablica.reindex(columns=TIPOVI, fill_value=0)


def profil_osobe(df: pd.DataFrame, broj: str, skupina) -> dict:
    skupina = set(map(str, skupina))
    njegovi = df[(df["pozivatelj"] == broj) | (df["primatelj"] == broj)]
    partneri = set(njegovi["pozivatelj"]) | set(njegovi["primatelj"])
    partneri.discard(broj)
    sa_skupinom = njegovi[njegovi["pozivatelj"].isin(skupina - {broj}) | njegovi["primatelj"].isin(skupina - {broj})]
    return {
        "broj": broj,
        "kontakata": int(njegovi["tezina"].sum()),
        "razlicitih_osoba": len(partneri),
        "kontakata_sa_skupinom": int(sa_skupinom["tezina"].sum()),
        "clanova_skupine": len(partneri & (skupina - {broj})),
    }
