from pathlib import Path

import pandas as pd

from src.heart import data
from src.heart.config import settings


def test_sample_dataset_exists():
    sample_path = settings.sample_data_path
    assert sample_path.exists(), "sample.csv should be present for quick tests"
    df = pd.read_csv(sample_path)
    assert not df.empty
    assert "target" in df.columns


def test_load_raw_missing_file_raises():
    missing = Path("data/raw/nonexistent.csv")
    try:
        data.load_raw(missing)
    except FileNotFoundError:
        return
    raise AssertionError("Expected FileNotFoundError for missing raw data")
