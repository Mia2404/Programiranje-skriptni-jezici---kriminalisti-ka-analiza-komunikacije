# Kriminalistička analiza komunikacije

Aplikacija za analizu komunikacije osumnjičenika na temelju zapisa poziva i SMS poruka.
Iz podataka gradi mrežu kontakata, identificira ključne osobe pomoću mjera centralnosti,
prati kretanje kroz bazne stanice i otkriva promjene u ponašanju kroz vrijeme.

Projekt radi nad sintetičkim podacima generiranim sa skrivenim scenarijem, a cilj je da ga
analiza otkrije.

## Tehnologije

- **Python 3.10+**
- **pandas** – obrada i agregacija podataka
- **networkx** – mreža kontakata i mjere centralnosti
- **SQLite** – pohrana podataka
- **Flask** – web sučelje
- **folium**, **pyvis** – karte i interaktivni grafovi (planirano)

## Pokretanje

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux / macOS

pip install -r requirements.txt

python main.py generiraj      # stvara data/komunikacija.db
python main.py analiziraj     # ispis rezultata analize u terminalu
python app.py                 # web sučelje na http://127.0.0.1:5000
```

## Model podataka

| Tablica | Opis |
|---|---|
| `osobe` | telefonski broj i ime vlasnika |
| `bazne_stanice` | identifikator, naziv i koordinate stanice |
| `komunikacija` | pozivatelj, primatelj, vrijeme, tip (poziv/SMS), trajanje, bazna stanica |
| `scenarij` | stvarne uloge osoba – koristi se samo za provjeru točnosti analize |
