# Kriminalistička analiza komunikacije

Aplikacija za analizu komunikacije osumnjičenika na temelju zapisa poziva i SMS poruka.
Iz podataka gradi mrežu kontakata, identificira ključne osobe pomoću mjera centralnosti,
prati kretanje kroz bazne stanice i otkriva promjene u ponašanju kroz vrijeme.

Projekt radi nad sintetičkim podacima generiranim sa skrivenim scenarijem, a cilj je da ga
analiza otkrije. Ne koristi strojno učenje – oslanja se na analizu grafova, vremenske
obrasce i osnovnu statistiku.

*Projekt iz kolegija Skriptni jezici, Tehnički fakultet u Rijeci.*

## Funkcionalnosti

| Status | Funkcionalnost |
|:---:|---|
| ✅ | Generator sintetičkih podataka sa skrivenim scenarijem |
| ✅ | Spremanje podataka u SQLite bazu |
| ✅ | Mreža kontakata i mjere centralnosti (stupanj, posredništvo, blizina, PageRank) |
| ✅ | Vremenska analiza: noćna aktivnost, nagli porasti aktivnosti, novi brojevi |
| ✅ | Osnovno web sučelje (Flask) |
| ⬜ | Interaktivni prikaz mreže (pyvis) |
| ⬜ | Karta kretanja po baznim stanicama (folium) |
| ⬜ | Otkrivanje sastanaka (više osoba na istoj lokaciji u isto vrijeme) |
| ⬜ | Automatski izvještaj o analizi |

## Tehnologije

- **Python 3.10+**
- **pandas** – obrada i agregacija podataka
- **networkx** – mreža kontakata i mjere centralnosti
- **SQLite** – pohrana podataka
- **Flask** – web sučelje
- **folium**, **pyvis** – karte i interaktivni grafovi (planirano)

## Struktura projekta

```
├── main.py              # pokretanje iz naredbenog retka
├── app.py               # Flask web aplikacija
├── requirements.txt
├── src/
│   ├── generator.py     # generiranje sintetičkih podataka
│   ├── database.py      # SQLite shema, spremanje i učitavanje
│   └── analysis.py      # analiza mreže i vremenska analiza
├── templates/
│   └── index.html
└── data/                # ovdje se stvara baza (nije u gitu)
```

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

## Plan rada

| Kontrolna točka | Rok | Sadržaj |
|---|---|---|
| I | 01.11.2026. | Priprema repozitorija, definicija problema, osnovni kostur |
| II | 27.11.2026. | Generator, baza, analiza mreže i vremenska analiza |
| III | 18.12.2026. | Vizualizacija mreže, karta kretanja, otkrivanje sastanaka |
| IV | 22.01.2027. | Izvještaj, evaluacija prema skrivenom scenariju, dorada |

## Autorica

Mia Žuvić
