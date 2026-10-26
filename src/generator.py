import random
from dataclasses import dataclass
from datetime import datetime, timedelta

import pandas as pd

SEED = 42
BROJ_OSOBA = 40
POCETAK = datetime(2026, 9, 1)
BROJ_DANA = 60
DAN_DOGADAJA = 45

BAZNE_STANICE = [
    ("BS01", "Centar - Korzo", 45.3271, 14.4422),
    ("BS02", "Trsat", 45.3328, 14.4583),
    ("BS03", "Sušak", 45.3262, 14.4531),
    ("BS04", "Zamet", 45.3416, 14.4064),
    ("BS05", "Kantrida", 45.3378, 14.3881),
    ("BS06", "Kozala", 45.3355, 14.4377),
    ("BS07", "Turnić", 45.3367, 14.4224),
    ("BS08", "Luka Rijeka", 45.3225, 14.4310),
    ("BS09", "Martinkovac", 45.3487, 14.3740),
    ("BS10", "Draga", 45.3264, 14.4869),
]

IMENA = [
    "Ivan", "Marko", "Ana", "Petra", "Luka", "Maja", "Josip", "Ivana", "Tomislav",
    "Lucija", "Filip", "Sara", "Matej", "Nina", "Karlo", "Lana", "Dario", "Ema",
    "Nikola", "Tea", "Hrvoje", "Iva", "Domagoj", "Marta", "Ante", "Klara", "Bruno",
    "Paula", "Igor", "Dora", "Zoran", "Mia", "Goran", "Lea", "Saša", "Rea",
    "Dino", "Vita", "Toni", "Nora", "Robert", "Ena",
]
PREZIMENA = [
    "Horvat", "Kovačević", "Babić", "Marić", "Jurić", "Novak", "Kovačić", "Knežević",
    "Vuković", "Marković", "Petrović", "Matić", "Tomić", "Pavlović", "Božić", "Blažević",
    "Grgić", "Perić", "Radić", "Šarić",
]


@dataclass
class Osoba:
    broj: str
    ime: str
    uloga: str
    dom_stanica: str


def _novi_broj(rng: random.Random, zauzeti: set) -> str:
    while True:
        broj = f"+38591{rng.randint(1000000, 9999999)}"
        if broj not in zauzeti:
            zauzeti.add(broj)
            return broj


def generiraj_osobe(rng: random.Random) -> list[Osoba]:
    zauzeti: set = set()
    stanice = [s[0] for s in BAZNE_STANICE]
    osobe = []

    uloge = ["vođa"] + ["posrednik"] * 2 + ["izvršitelj"] * 4
    uloge += ["civil"] * (BROJ_OSOBA - len(uloge))

    for uloga in uloge:
        ime = f"{rng.choice(IMENA)} {rng.choice(PREZIMENA)}"
        osobe.append(Osoba(_novi_broj(rng, zauzeti), ime, uloga, rng.choice(stanice)))

    osobe.append(Osoba(_novi_broj(rng, zauzeti), "NEPOZNATO", "zamjenski", "BS08"))
    return osobe


def _zapis(rng, pozivatelj, primatelj, vrijeme, stanica, tip=None):
    tip = tip or rng.choice(["poziv", "poziv", "sms"])
    trajanje = rng.randint(10, 600) if tip == "poziv" else 0
    return {
        "pozivatelj": pozivatelj.broj,
        "primatelj": primatelj.broj,
        "vrijeme": vrijeme,
        "tip": tip,
        "trajanje_s": trajanje,
        "stanica_id": stanica,
    }


def _nasumicno_vrijeme(rng, dan: int, noc: bool = False) -> datetime:
    sat = rng.choice([22, 23, 0, 1, 2]) if noc else rng.randint(7, 22)
    return POCETAK + timedelta(days=dan, hours=sat, minutes=rng.randint(0, 59))


def generiraj_komunikaciju(rng: random.Random, osobe: list[Osoba]) -> list[dict]:
    civili = [o for o in osobe if o.uloga == "civil"]
    vodja = next(o for o in osobe if o.uloga == "vođa")
    posrednici = [o for o in osobe if o.uloga == "posrednik"]
    izvrsitelji = [o for o in osobe if o.uloga == "izvršitelj"]
    zamjenski = next(o for o in osobe if o.uloga == "zamjenski")
    clanovi = [vodja, *posrednici, *izvrsitelji]

    krugovi = {o.broj: rng.sample(civili, k=rng.randint(3, 7)) for o in civili + izvrsitelji}
    for o in [vodja, *posrednici]:
        krugovi[o.broj] = rng.sample(civili, k=2)

    zapisi = []
    for dan in range(BROJ_DANA):
        for o in civili + clanovi:
            for _ in range(rng.randint(0, 4)):
                prijatelj = rng.choice(krugovi[o.broj])
                zapisi.append(_zapis(rng, o, prijatelj, _nasumicno_vrijeme(rng, dan), o.dom_stanica))

        dani_do = DAN_DOGADAJA - dan
        if 0 <= dani_do <= 5:
            intenzitet = 4
        elif dan > DAN_DOGADAJA:
            intenzitet = 0
        else:
            intenzitet = 1

        for _ in range(intenzitet):
            p = rng.choice(posrednici)
            zapisi.append(_zapis(rng, vodja, p, _nasumicno_vrijeme(rng, dan, noc=True), vodja.dom_stanica, "poziv"))
            p = rng.choice(posrednici)
            iz = rng.choice(izvrsitelji)
            zapisi.append(_zapis(rng, p, iz, _nasumicno_vrijeme(rng, dan), p.dom_stanica))

        if dan == DAN_DOGADAJA:
            for iz in izvrsitelji:
                for drugi in izvrsitelji:
                    if iz is not drugi and rng.random() < 0.6:
                        vrijeme = POCETAK + timedelta(days=dan, hours=2, minutes=rng.randint(0, 50))
                        zapisi.append(_zapis(rng, iz, drugi, vrijeme, "BS08", "sms"))

        if dan > DAN_DOGADAJA:
            for _ in range(rng.randint(1, 3)):
                primatelj = rng.choice([vodja, *izvrsitelji])
                zapisi.append(_zapis(rng, zamjenski, primatelj, _nasumicno_vrijeme(rng, dan, noc=True), "BS08"))

    return zapisi


def generiraj(seed: int = SEED) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rng = random.Random(seed)
    osobe = generiraj_osobe(rng)
    zapisi = generiraj_komunikaciju(rng, osobe)

    df_osobe = pd.DataFrame([o.__dict__ for o in osobe])
    df_stanice = pd.DataFrame(BAZNE_STANICE, columns=["stanica_id", "naziv", "lat", "lon"])
    df_kom = pd.DataFrame(zapisi).sort_values("vrijeme").reset_index(drop=True)
    return df_osobe, df_stanice, df_kom
