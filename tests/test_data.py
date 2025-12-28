from pathlib import Path

from src.heart import data
from src.heart.config import settings


def test_sample_dataset_exists():
    sample_path = settings.sample_data_path
    assert sample_path.exists(), "sample.csv should be present for quick tests"
    df = data.load_sample()
    assert not df.empty
    assert set(data.FEATURE_COLUMNS).issubset(df.columns)
    assert set(df[data.TARGET_COLUMN].unique()).issubset({0, 1})


def test_train_test_split_data_is_stratified():
    df = data.load_sample()
    X_train, X_test, y_train, y_test = data.train_test_split_data(
        df, test_size=0.25, random_state=123
    )
    assert len(X_train) + len(X_test) == len(df)
    assert set(X_train.columns) == set(data.FEATURE_COLUMNS)
    assert set(y_train.unique()) == set(y_test.unique())


def test_load_raw_missing_file_raises():
    missing = Path("data/raw/nonexistent.csv")
    try:
        data.load_raw(missing)
    except FileNotFoundError:
        return
    raise AssertionError("Expected FileNotFoundError for missing raw data")
