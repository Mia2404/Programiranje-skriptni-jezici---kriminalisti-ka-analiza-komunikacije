import argparse

import pandas as pd

from src import analysis, database, evaluacija, montagna, skupina, vast2008, vast2018

UCITAVACI = {
    "vast2008": vast2008.ucitaj,
    "vast2018": vast2018.ucitaj,
    "montagna": montagna.ucitaj,
}


def naredba_ucitaj(args):
    nazivi = list(UCITAVACI) if args.skup == "sve" else [args.skup]
    for naziv in nazivi:
        print(f"\n[{naziv}] učitavanje...")
        podaci = UCITAVACI[naziv]()
        if "neispravni" in podaci and not podaci["neispravni"].empty:
            print(f"Izbačeno zapisa s negativnim trajanjem: {len(podaci['neispravni'])}")
        putanja = database.BAZE[naziv]
        database.spremi(putanja, podaci)

        sazetak = database.sazetak(putanja)
        print(f"Osoba/brojeva: {sazetak['osoba']}")
        print(f"Zapisa komunikacije: {sazetak['zapisa']}")
        print("Po vrsti:", sazetak["po_vrsti"])
        if sazetak["od"]:
            print(f"Razdoblje: {sazetak['od']} – {sazetak['do']}")
        else:
            print("Razdoblje: podaci nemaju vrijeme")
        print(f"Zapisa u rješenju (scenarij): {sazetak['scenarij']}")
        print(f"Baza spremljena u: {putanja}")


def naredba_analiziraj(args):
    putanja = database.BAZE[args.baza]
    if args.baza == "vast2018":
        analiziraj_vast2018(putanja)
        return

    df_kom = database.ucitaj_komunikaciju(putanja)
    osobe = database.ucitaj_osobe(putanja).set_index("broj")["ime"]

    G = analysis.izgradi_graf(df_kom)
    print(f"\nMreža: {G.number_of_nodes()} čvorova, {G.number_of_edges()} veza\n")

    cent = analysis.centralnost(G)
    if osobe.notna().any():
        cent.insert(0, "ime", cent.index.map(osobe))
    print("Top 10 po posredništvu (betweenness):")
    print(cent.head(10).round(3).to_string())

    if df_kom["vrijeme"].isna().all():
        print("\nPodaci nemaju vrijeme, pa vremenska analiza nije moguća.")
        return

    print("\nTop 5 po noćnoj aktivnosti:")
    print(analysis.nocna_aktivnost(df_kom).head(5).round(2).to_string())

    print("\nNeuobičajeni porasti aktivnosti:")
    promjene = analysis.promjene_ponasanja(df_kom)
    print(promjene.head(10).round({"z": 2}).to_string() if not promjene.empty else "Nema.")

    print("\nBrojevi koji su se pojavili naknadno:")
    novi = analysis.novi_brojevi(df_kom)
    print(novi.to_string() if not novi.empty else "Nema.")


def _skupina_vast2018(putanja):
    sc = database.ucitaj_scenarij(putanja)
    osobe = database.ucitaj_osobe(putanja).set_index("broj")["ime"]
    clanovi = set(sc["broj"])
    print("Dohvaćanje zapisa oko skupine...")
    return clanovi, osobe, skupina.zapisi_oko(putanja, clanovi)


def analiziraj_vast2018(putanja):
    clanovi, osobe, df = _skupina_vast2018(putanja)
    print(f"\nSumnjiva skupina prema insajderu: {len(clanovi)} osoba")
    print(f"Zapisa u kojima sudjeluje barem jedan član: {len(df)}")
    print("Po vrsti:", df["tip"].value_counts().to_dict())

    unutra = df[df["pozivatelj"].isin(clanovi) & df["primatelj"].isin(clanovi)]
    print(f"Od toga unutar skupine: {len(unutra)}")

    print("\nBliski suradnici (prvih 10 osoba izvan popisa po broju različitih članova s kojima su u kontaktu):")
    suradnici = skupina.bliski_suradnici(df, clanovi, k=10)
    suradnici.insert(0, "ime", suradnici.index.map(osobe))
    print(suradnici.to_string())

    print("\nKontakti unutar skupine po mjesecima:")
    print(skupina.unutarnji_tijek(df, clanovi).to_string())

    insajder = database.ucitaj_insajder(putanja)
    kupnje = insajder[insajder["tip"] == "kupnja"].copy()
    kupnje.insert(1, "kupac", kupnje["pozivatelj"].map(osobe))
    kupnje.insert(3, "prodavac", kupnje["primatelj"].map(osobe))
    print("\nSumnjive kupnje prema insajderu:")
    print(kupnje[["pozivatelj", "kupac", "primatelj", "prodavac", "vrijeme", "izvor"]].to_string(index=False))

    kupci = sorted(set(kupnje.loc[kupnje["izvor"].str.contains("Other_"), "pozivatelj"]))
    if kupci:
        print("\nKupci iz ostalih sumnjivih kupnji:")
        oko_kupaca = skupina.zapisi_oko(putanja, kupci)
        profili = pd.DataFrame([skupina.profil_osobe(oko_kupaca, k, clanovi) for k in kupci])
        profili.insert(1, "ime", profili["broj"].map(osobe))
        print(profili.to_string(index=False))


def evaluiraj_vast2018(putanja):
    clanovi, osobe, df = _skupina_vast2018(putanja)
    tablica = skupina.izostavi_jednog(df, clanovi)
    tablica.insert(1, "ime", tablica["clan"].map(osobe))
    print(f"\nSkup: vast2018")
    print("Provjera izostavljanjem: svaki član se redom izostavi iz skupine, a ostale osobe se rangiraju")
    print("po broju različitih preostalih članova s kojima su u kontaktu. Gleda se rang izostavljenog člana.")
    print(f"\nČlanova: {len(tablica)}")
    for k in (1, 10, 50):
        print(f"Izostavljeni član na rangu do {k}: {int((tablica['rang'] <= k).sum())}")
    print(f"Nije povezan ni s jednim preostalim članom: {int(tablica['rang'].isna().sum())}")
    print(f"Medijan ranga: {tablica['rang'].median()}, očekivano kod nasumičnog rangiranja: "
          f"{tablica['ocekivano_slucajno'].median()}")
    print("\nRezultat po članu:")
    print(tablica.to_string(index=False))


def naredba_evaluiraj(args):
    if args.baza == "vast2018":
        evaluiraj_vast2018(database.BAZE["vast2018"])
        return

    tablica, rang, oz = evaluacija.evaluiraj(args.baza, k=args.k)
    pozitivnih = int((oz == evaluacija.POZITIVNO).sum())
    print(f"\nSkup: {args.baza}")
    print(f"Osoba u mreži: {len(oz)}")
    print(f"U rješenju: {pozitivnih}, izvan rješenja: {int((oz == evaluacija.IZVAN).sum())}, "
          f"nepoznato: {int((oz == evaluacija.NEPOZNATO).sum())}")
    if args.baza == "montagna":
        print("U rješenju = osobe kojima je sud odredio uhićenje, zatvor ili kućni pritvor, ili su u bijegu.")
        print("Izvan rješenja = odbijen zahtjev za uhićenje, nedostatak dokaza ili nije umiješan.")
        print("Nepoznato = ishod nije naveden u izvoru.")

    prikaz = tablica.copy()
    for stupac in ("preciznost", "odziv"):
        prikaz[stupac] = prikaz[stupac].map(lambda v: "–" if pd.isna(v) else f"{v:.0%}")
    prikaz["ocekivano_slucajno"] = prikaz["ocekivano_slucajno"].round(2)
    print("\nRezultati po metodi:")
    print(prikaz.to_string(index=False))

    print(f"\nRang osoba iz rješenja po posredništvu (od {len(oz)}; izjednačene osobe dijele isti rang):")
    print(rang.to_string(index=False))


def main():
    parser = argparse.ArgumentParser(description="Kriminalistička analiza komunikacije")
    sub = parser.add_subparsers(dest="naredba", required=True)

    p_uc = sub.add_parser("ucitaj", help="učitava skup podataka u SQLite bazu")
    p_uc.add_argument("skup", choices=[*UCITAVACI, "sve"])
    p_uc.set_defaults(func=naredba_ucitaj)

    p_an = sub.add_parser("analiziraj", help="pokreće analizu nad bazom")
    p_an.add_argument("--baza", choices=list(database.BAZE), default="vast2008")
    p_an.set_defaults(func=naredba_analiziraj)

    p_ev = sub.add_parser("evaluiraj", help="uspoređuje rezultate analize s rješenjem")
    p_ev.add_argument("--baza", choices=list(database.BAZE), default="vast2008")
    p_ev.add_argument("--k", type=int, default=10, help="koliko prvih osoba uzeti kod rangiranja")
    p_ev.set_defaults(func=naredba_evaluiraj)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
