"""Data loading and preparation utilities (placeholder for Part-2)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from .config import settings


def load_sample(path: Optional[Path] = None) -> pd.DataFrame:
    """Load the committed sample dataset for quick tests."""
    sample_path = Path(path) if path else settings.sample_data_path
    return pd.read_csv(sample_path)


def load_raw(path: Optional[Path] = None) -> pd.DataFrame:
    """Load raw dataset; in Part-2 this will read downloaded data."""
    data_path = Path(path) if path else settings.raw_data_dir / "heart.csv"
    if not data_path.exists():
        raise FileNotFoundError(
            f"Raw data not found at {data_path}. Run `make data` after Part-2 is implemented."
        )
    return pd.read_csv(data_path)


def train_test_split_data(_df: pd.DataFrame):
    """Placeholder train/test split to be replaced in Part-2."""
    raise NotImplementedError("Train/test split will be implemented in Part-2.")
