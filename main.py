import argparse
from pathlib import Path

from src import analysis, database, generator, vast


def naredba_generiraj(args):
    df_osobe, df_stanice, df_kom = generator.generiraj(seed=args.seed)
    database.spremi(df_osobe, df_stanice, df_kom)
    print(f"Generirano {len(df_osobe)} brojeva i {len(df_kom)} zapisa komunikacije.")
    print(f"Baza spremljena u: {database.DB_PUTANJA}")


def naredba_ucitaj_vast(args):
    df_osobe, df_stanice, df_kom = vast.ucitaj(Path(args.csv))
    database.spremi(df_osobe, df_stanice, df_kom, putanja=vast.VAST_DB_PUTANJA)
    print(f"Učitano {len(df_osobe)} brojeva i {len(df_kom)} zapisa komunikacije.")
    print(f"Baza spremljena u: {vast.VAST_DB_PUTANJA}")


def naredba_analiziraj(args):
    putanja = vast.VAST_DB_PUTANJA if args.baza == "vast" else database.DB_PUTANJA
    df_kom = database.ucitaj_komunikaciju(putanja)
    osobe = database.ucitaj_osobe(putanja).set_index("broj")["ime"]

    G = analysis.izgradi_graf(df_kom)
    print(f"\nMreža: {G.number_of_nodes()} čvorova, {G.number_of_edges()} veza\n")

    cent = analysis.centralnost(G)
    cent.insert(0, "ime", cent.index.map(osobe))
    print("Top 10 po posredništvu (betweenness):")
    print(cent.head(10).round(3).to_string())

    print("\nTop 5 po noćnoj aktivnosti:")
    print(analysis.nocna_aktivnost(df_kom).head(5).round(2).to_string())

    print("\nNeuobičajeni porasti aktivnosti:")
    promjene = analysis.promjene_ponasanja(df_kom)
    print(promjene.head(10).round({"z": 2}).to_string() if not promjene.empty else "Nema.")

    print("\nBrojevi koji su se pojavili naknadno:")
    novi = analysis.novi_brojevi(df_kom)
    print(novi.to_string() if not novi.empty else "Nema.")


def main():
    parser = argparse.ArgumentParser(description="Kriminalistička analiza komunikacije")
    sub = parser.add_subparsers(dest="naredba", required=True)

    p_gen = sub.add_parser("generiraj", help="generira sintetičke podatke i sprema ih u bazu")
    p_gen.add_argument("--seed", type=int, default=generator.SEED)
    p_gen.set_defaults(func=naredba_generiraj)

    p_vast = sub.add_parser("ucitaj-vast", help="učitava VAST 2008 CSV s pozivima u zasebnu bazu")
    p_vast.add_argument("--csv", default="data/CellPhoneCallRecords.csv")
    p_vast.set_defaults(func=naredba_ucitaj_vast)

    p_an = sub.add_parser("analiziraj", help="pokreće analizu nad bazom")
    p_an.add_argument("--baza", choices=["sinteticka", "vast"], default="sinteticka")
    p_an.set_defaults(func=naredba_analiziraj)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
