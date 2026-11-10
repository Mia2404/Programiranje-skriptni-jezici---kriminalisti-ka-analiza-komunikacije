import networkx as nx
import pandas as pd


def izgradi_graf(df_kom: pd.DataFrame) -> nx.Graph:
    parovi = (
        df_kom.assign(
            a=df_kom[["pozivatelj", "primatelj"]].min(axis=1),
            b=df_kom[["pozivatelj", "primatelj"]].max(axis=1),
        )
        .groupby(["a", "b"])["tezina"]
        .sum()
        .reset_index()
    )
    G = nx.Graph()
    for row in parovi.itertuples(index=False):
        G.add_edge(row.a, row.b, tezina=row.tezina, udaljenost=1 / row.tezina)
    return G


def centralnost(G: nx.Graph) -> pd.DataFrame:
    mjere = {
        "stupanj": nx.degree_centrality(G),
        "posrednistvo": nx.betweenness_centrality(G, weight="udaljenost"),
        "blizina": nx.closeness_centrality(G, distance="udaljenost"),
        "pagerank": nx.pagerank(G, weight="tezina"),
    }
    df = pd.DataFrame(mjere)
    df.index.name = "broj"
    return df.sort_values("posrednistvo", ascending=False)


def dnevna_aktivnost(df_kom: pd.DataFrame) -> pd.DataFrame:
    df = df_kom.assign(dan=df_kom["vrijeme"].dt.normalize())
    return df.pivot_table(index="dan", columns="pozivatelj", values="id",
                          aggfunc="count", fill_value=0)


def nocna_aktivnost(df_kom: pd.DataFrame) -> pd.Series:
    sat = df_kom["vrijeme"].dt.hour
    nocno = (sat >= 22) | (sat < 4)
    return df_kom.assign(nocno=nocno).groupby("pozivatelj")["nocno"].mean().sort_values(ascending=False)


def promjene_ponasanja(df_kom: pd.DataFrame, prozor: int = 7, prag: float = 3.0) -> pd.DataFrame:
    dnevno = dnevna_aktivnost(df_kom)
    prosjek = dnevno.rolling(prozor, min_periods=prozor).mean().shift(1)
    std = dnevno.rolling(prozor, min_periods=prozor).std().shift(1).clip(lower=1)
    z = (dnevno - prosjek) / std

    rezultat = (
        z.stack()
        .rename("z")
        .reset_index()
        .rename(columns={"pozivatelj": "broj"})
    )
    rezultat = rezultat[rezultat["z"] > prag].sort_values("z", ascending=False)
    return rezultat.reset_index(drop=True)


def novi_brojevi(df_kom: pd.DataFrame, udio: float = 0.25) -> pd.DataFrame:
    prvo = pd.concat([
        df_kom[["pozivatelj", "vrijeme"]].rename(columns={"pozivatelj": "broj"}),
        df_kom[["primatelj", "vrijeme"]].rename(columns={"primatelj": "broj"}),
    ]).groupby("broj")["vrijeme"].min()
    pocetak, kraj = df_kom["vrijeme"].min(), df_kom["vrijeme"].max()
    granica = pocetak + (kraj - pocetak) * udio
    return prvo[prvo > granica].sort_values().rename("prvo_pojavljivanje").reset_index()
