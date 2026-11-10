# Kriminalistička analiza komunikacije

Aplikacija za analizu komunikacije osumnjičenika na temelju zapisa o komunikaciji (pozivi, e-mailovi,
sastanci, kupnje). Iz podataka gradi mrežu kontakata, identificira ključne osobe pomoću mjera
centralnosti, prati kretanje kroz bazne stanice i otkriva promjene u ponašanju kroz vrijeme.

Projekt radi isključivo nad **vanjskim, javno dostupnim skupovima podataka s poznatim rješenjem**.
Podatke nije izradio autor projekta, pa rezultat analize nije moguće prilagoditi podacima.
Rješenje se koristi samo za provjeru točnosti, nikad u samoj analizi.

## Skupovi podataka

| Skup | Vrsta | Sadržaj | Rješenje |
|---|---|---|---|
| VAST 2008 MC3 | sintetički, izradili organizatori VAST Challengea | 9 834 poziva, 400 brojeva, 30 baznih stanica, 1.–10. 6. 2006. | službeno rješenje (`CellCallsSolution.doc`) |
| VAST 2018 MC3 | sintetički, izradili organizatori VAST Challengea | 10,6 mil. poziva, 14,6 mil. e-mailova, 762 tis. kupnji, 127 tis. sastanaka, svibanj 2015. – prosinac 2017. | insajderov popis 20 osoba i zapisi koje je označio kao sumnjive |
| Montagna | stvarni podaci sudskog postupka | mreža prisluškivanih poziva (150 zapisa veza, ukupno 276 poziva) i praćenih sastanaka (289 zapisa veza, ukupno 456 sastanaka), bez vremena | uloge osoba i ishod postupka (uhićen, u bijegu…) |

### VAST 2008 – Mini Challenge 3: Cell Phone Calls

- Izvor: Visual Analytics Benchmark Repository,
  https://visualdata.wustl.edu/varepository/VAST_Challenge_2008/challenges/MC3_-_Cell_Phone_Calls/
- `data/CellPhoneCallRecords.csv` – originalni zapisi poziva.
- `data/vast2008_stanice.csv` – **približne** koordinate 30 baznih stanica. Očitane su s karte
  `Cell Locations on Isla.ppt` iz službenog paketa podataka: položaj oznake svake stanice preračunat je
  u geografske koordinate pomoću koordinatne mreže ucrtane na karti. U službenom opisu podataka navodi se
  da položaji stanica na karti nisu precizni.
- Rješenje: imena osoba i zamjene brojeva preuzete su iz službenog rješenja (`CellCallsSolution.doc`),
  koje navodi da je raspored osoba po brojevima "jedan mogući raspored". Imena se spremaju samo u
  tablicu `scenarij`; analiza radi isključivo s brojevima.
- 4 zapisa imaju negativno trajanje poziva; pri učitavanju se izbacuju.

### VAST 2018 – Mini Challenge 3

- Izvor: Visual Analytics Benchmark Repository, VAST Challenge 2018, Mini-Challenge 3.
- Datoteke su prevelike za GitHub (oko 650 MB) i nisu dio repozitorija. Za učitavanje treba ove datoteke
  iz službenog paketa kopirati u `data/vast2018/`:
  `calls.csv`, `emails.csv`, `purchases.csv`, `meetings.csv`, `CompanyIndex.csv`,
  `Suspicious_calls.csv`, `Suspicious_emails.csv`, `Suspicious_purchases.csv`,
  `Suspicious_meetings.csv`, `Other_suspicious_purchases.csv`.
- Vrijeme je u izvornim datotekama zadano u sekundama od 11. 5. 2015. u 14:00 (prema
  `Backgrounder_on_Kasios_International_data.docx`).
- Sumnjiva skupina: 20 imena iz insajderova pisma (`Insider_letter_to_M_Vogel.docx`).
- U službenom paketu podataka nema rješenja; rezultati se mogu usporediti s objavljenim odgovorima timova.
- Uočena nedosljednost: sumnjiva kupnja iz `Suspicious_purchases.csv` (1847246 → 2038003) ima vrijeme
  74 565 933 s, a u `purchases.csv` ista kupnja ima vrijeme 74 525 933 s (razlika 40 000 s).

### Montagna Operation

- Izvor: Cavallaro L. i sur., *Criminal Network: The Sicilian Mafia. "Montagna Operation"*, Zenodo,
  https://doi.org/10.5281/zenodo.3938818, licenca CC BY 4.0.
- Podaci potječu iz rješenja o istražnom zatvoru Suda u Messini (14. 3. 2007.).
- `data/montagna/` – izvorne datoteke bez izmjena.
- Svaki redak datoteka s pozivima i sastancima je jedna veza između dvije osobe, a stupac `Weight`
  je broj poziva odnosno sastanaka. Datoteke sadrže 95 osoba i 120 različitih parova u pozivima te
  95 osoba i 249 različitih parova u sastancima. Opis skupa na Zenodu navodi drukčije brojeve
  (100 čvorova i 124 brida za pozive, 101 čvor i 256 bridova za sastanke).
- Uočene nepravilnosti u izvornim datotekama, koje se pri učitavanju ne mijenjaju:
  - u pozivima se jednom pojavljuje oznaka `52` umjesto oblika `N52` (veza N18 – 52, težina 4),
  - u sastancima postoji veza osobe same sa sobom (N47 – N47),
  - neki parovi se pojavljuju u više redaka (pozivi: N43 – N47, N66 – N61; sastanci: N22 – N18,
    N43 – N47, N47 – N27); težine takvih redaka se zbrajaju,
  - osobe `52` i `N35` nemaju redak u datoteci s ulogama, a osoba N154 ima ulogu, ali se ne pojavljuje
    ni u pozivima ni u sastancima.

## Pokretanje

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux / macOS

pip install -r requirements.txt

python main.py ucitaj vast2008
python main.py ucitaj montagna
python main.py ucitaj vast2018     # traje nekoliko minuta
python main.py ucitaj sve

python main.py analiziraj --baza vast2008
python main.py analiziraj --baza montagna
python app.py                      # web sučelje na http://127.0.0.1:5000
```

## Model podataka

Svaki skup podataka sprema se u zasebnu SQLite bazu (`data/vast2008.db`, `data/vast2018.db`,
`data/montagna.db`) s istom shemom.

| Tablica | Opis |
|---|---|
| `osobe` | broj ili ID osobe i ime, ako je poznato |
| `bazne_stanice` | identifikator, naziv i koordinate stanice (samo VAST 2008) |
| `komunikacija` | pozivatelj, primatelj, vrijeme, tip (poziv/email/sastanak/kupnja), trajanje, bazna stanica, težina |
| `scenarij` | imena i uloge iz rješenja – koristi se samo za provjeru točnosti analize |
| `zamjene_brojeva` | zamjene brojeva iz službenog rješenja (samo VAST 2008) |
| `insajder_zapisi` | zapisi koje je insajder označio kao sumnjive (samo VAST 2018) |

Stupac `tezina` je broj kontakata između dvije osobe; u Montagni je to izvorna težina brida, a u VAST
skupovima je svaki zapis jedan kontakt.
