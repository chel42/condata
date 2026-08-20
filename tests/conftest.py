"""Fixtures Pytest partagées."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def valid_csv(fixtures_dir: Path) -> Path:
    return fixtures_dir / "valid.csv"


@pytest.fixture
def clean_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "age": [21, 34, 45, 29],
            "region": ["Brazzaville", "Pointe-Noire", "Dolisie", "Owando"],
            "score": [1.2, 3.4, 2.1, 4.0],
        }
    )


@pytest.fixture
def messy_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "age": [21, 34, None, 21],
            "region": ["Brazzaville", "brazzaville", "Pointe-Noire", "Brazzaville"],
            "score": [1.2, 3.4, 2.1, 1.2],
            "note": ["ok", "12", "ko", "ok"],
            "flag": ["yes", "yes", "yes", "yes"],
        }
    )
