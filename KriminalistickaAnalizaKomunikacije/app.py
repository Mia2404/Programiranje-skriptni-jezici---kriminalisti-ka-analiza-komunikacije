from flask import Flask, render_template

from src import analysis, database

app = Flask(__name__)


@app.route("/")
def index():
    if not database.DB_PUTANJA.exists():
        return render_template("index.html", nema_podataka=True)

    df_kom = database.ucitaj_komunikaciju()
    osobe = database.ucitaj_osobe().set_index("broj")["ime"]

    G = analysis.izgradi_graf(df_kom)
    cent = analysis.centralnost(G).head(10).round(3)
    cent.insert(0, "ime", cent.index.map(osobe))

    statistika = {
        "zapisa": len(df_kom),
        "brojeva": G.number_of_nodes(),
        "veza": G.number_of_edges(),
        "od": df_kom["vrijeme"].min().date(),
        "do": df_kom["vrijeme"].max().date(),
    }
    promjene = analysis.promjene_ponasanja(df_kom).head(10).round({"z": 2})
    promjene.insert(1, "ime", promjene["broj"].map(osobe))

    return render_template(
        "index.html",
        nema_podataka=False,
        statistika=statistika,
        centralnost=cent.reset_index().to_dict("records"),
        promjene=promjene.to_dict("records"),
    )


if __name__ == "__main__":
    app.run(debug=True)
