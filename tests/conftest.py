import sys
from pathlib import Path

import pandas as pd
import pytest

KORIJEN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KORIJEN))


def _zapis(a, b, vrijeme=None, tip="poziv", tezina=1):
    return {
        "pozivatelj": a,
        "primatelj": b,
        "vrijeme": pd.Timestamp(vrijeme) if vrijeme else pd.NaT,
        "tip": tip,
        "tezina": tezina,
    }


@pytest.fixture
def napravi_kom():
    def _napravi(zapisi):
        df = pd.DataFrame(zapisi)
        df.insert(0, "id", range(1, len(df) + 1))
        return df
    return _napravi


@pytest.fixture
def zapis():
    return _zapis
