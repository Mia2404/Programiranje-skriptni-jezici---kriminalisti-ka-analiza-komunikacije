import argparse

import pandas as pd

from src import analysis, database, evaluacija, montagna, vast2008, vast2018

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
        print("Analiza za vast2018 još nije prilagođena veličini podataka (25 milijuna zapisa).")
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


def naredba_evaluiraj(args):
    if args.baza == "vast2018":
        print("Provjera za vast2018 još nije moguća jer analiza nije prilagođena veličini podataka.")
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
