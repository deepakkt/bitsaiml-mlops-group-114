"""Data loading and preparation utilities for the Heart Disease dataset."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
from sklearn.model_selection import train_test_split

from .config import settings

TARGET_COLUMN = "target"
NUMERIC_FEATURES = ["age", "trestbps", "chol", "thalach", "oldpeak", "ca"]
CATEGORICAL_FEATURES = ["sex", "cp", "fbs", "restecg", "exang", "slope", "thal"]
FEATURE_COLUMNS = [
    "age",
    "sex",
    "cp",
    "trestbps",
    "chol",
    "fbs",
    "restecg",
    "thalach",
    "exang",
    "oldpeak",
    "slope",
    "ca",
    "thal",
]


def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names and align target naming."""
    normalized = df.copy()
    normalized.columns = [col.strip().lower() for col in normalized.columns]
    if TARGET_COLUMN not in normalized.columns and "num" in normalized.columns:
        normalized = normalized.rename(columns={"num": TARGET_COLUMN})
    return normalized


def validate_schema(df: pd.DataFrame) -> None:
    """Ensure all expected columns are present."""
    required = set(FEATURE_COLUMNS + [TARGET_COLUMN])
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Dataset missing required columns: {sorted(missing)}")


def prepare_heart_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and align the heart disease dataframe."""
    prepared = _standardize_columns(df)
    prepared = prepared.replace("?", pd.NA)
    validate_schema(prepared)
    prepared = prepared[FEATURE_COLUMNS + [TARGET_COLUMN]].copy()

    for col in FEATURE_COLUMNS + [TARGET_COLUMN]:
        prepared[col] = pd.to_numeric(prepared[col], errors="coerce")

    prepared = prepared.dropna().reset_index(drop=True)
    prepared[TARGET_COLUMN] = (prepared[TARGET_COLUMN] > 0).astype(int)
    return prepared


def load_sample(path: Optional[Path] = None) -> pd.DataFrame:
    """Load the committed sample dataset for quick tests."""
    sample_path = Path(path) if path else settings.sample_data_path
    if not sample_path.exists():
        raise FileNotFoundError(f"Sample dataset not found at {sample_path}")
    df = pd.read_csv(sample_path)
    return prepare_heart_dataframe(df)


def load_raw(path: Optional[Path] = None) -> pd.DataFrame:
    """Load the raw downloaded dataset."""
    data_path = Path(path) if path else settings.raw_data_dir / "heart.csv"
    if not data_path.exists():
        raise FileNotFoundError(
            f"Raw data not found at {data_path}. Run `make data` to download it."
        )
    df = pd.read_csv(data_path)
    return _standardize_columns(df)


def load_processed(path: Optional[Path] = None) -> pd.DataFrame:
    """Load the cleaned/processed dataset."""
    data_path = Path(path) if path else settings.processed_data_dir / "heart_processed.csv"
    if not data_path.exists():
        raise FileNotFoundError(
            f"Processed data not found at {data_path}. Run `make data` to prepare it."
        )
    df = pd.read_csv(data_path)
    return prepare_heart_dataframe(df)


def split_features_target(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Split dataframe into features and target series."""
    validate_schema(df)
    X = df[FEATURE_COLUMNS].copy()
    y = df[TARGET_COLUMN].astype(int)
    return X, y


def train_test_split_data(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: Optional[int] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Split the dataset into stratified train and test sets.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe containing all feature columns and target.
    test_size : float
        Fraction allocated to the test set.
    random_state : Optional[int]
        Random seed for deterministic splits.
    """
    processed = prepare_heart_dataframe(df)
    X, y = split_features_target(processed)
    seed = settings.random_seed if random_state is None else random_state
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=seed
    )
    return X_train, X_test, y_train, y_test
