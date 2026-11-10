from flask import Flask, render_template, request

from src import analysis, database

app = Flask(__name__)


@app.route("/")
def index():
    baza = request.args.get("baza", "vast2008")
    if baza not in database.BAZE or baza == "vast2018":
        baza = "vast2008"
    putanja = database.BAZE[baza]
    if not putanja.exists():
        return render_template("index.html", nema_podataka=True, baza=baza)

    df_kom = database.ucitaj_komunikaciju(putanja)
    osobe = database.ucitaj_osobe(putanja).set_index("broj")["ime"]

    G = analysis.izgradi_graf(df_kom)
    cent = analysis.centralnost(G).head(10).round(3)
    cent.insert(0, "ime", cent.index.map(osobe))

    ima_vrijeme = df_kom["vrijeme"].notna().any()
    statistika = {
        "zapisa": len(df_kom),
        "brojeva": G.number_of_nodes(),
        "veza": G.number_of_edges(),
        "od": df_kom["vrijeme"].min().date() if ima_vrijeme else "–",
        "do": df_kom["vrijeme"].max().date() if ima_vrijeme else "–",
    }
    promjene = []
    if ima_vrijeme:
        df_p = analysis.promjene_ponasanja(df_kom).head(10).round({"z": 2})
        df_p.insert(1, "ime", df_p["broj"].map(osobe))
        promjene = df_p.to_dict("records")

    return render_template(
        "index.html",
        nema_podataka=False,
        baza=baza,
        statistika=statistika,
        centralnost=cent.reset_index().to_dict("records"),
        promjene=promjene,
    )


if __name__ == "__main__":
    app.run(debug=True)
