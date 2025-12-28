#!/usr/bin/env python
"""Download and preprocess the UCI Heart Disease dataset."""

from __future__ import annotations

import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Tuple

import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.heart import data as data_utils
from src.heart.config import settings

UCI_DATASET_ID = 45
FALLBACK_URL = "https://raw.githubusercontent.com/plotly/datasets/master/heart.csv"
UCI_SOURCE_URL = "https://archive.ics.uci.edu/ml/datasets/Heart+Disease"


def _sha256sum(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _fetch_via_ucimlrepo() -> Tuple[pd.DataFrame, str, str]:
    from ucimlrepo import fetch_ucirepo

    repo = fetch_ucirepo(id=UCI_DATASET_ID)
    features = repo.data.features
    targets = repo.data.targets
    df = pd.concat([features, targets], axis=1)
    if "target" not in df.columns and "num" in df.columns:
        df = df.rename(columns={"num": data_utils.TARGET_COLUMN})
    return df, f"ucimlrepo id={UCI_DATASET_ID} (Heart Disease)", UCI_SOURCE_URL


def _fetch_fallback() -> Tuple[pd.DataFrame, str, str]:
    response = requests.get(FALLBACK_URL, timeout=30)
    response.raise_for_status()
    df = pd.read_csv(io.StringIO(response.text))
    return df, "github:plotly-datasets heart.csv", FALLBACK_URL


def _download_dataset() -> Tuple[pd.DataFrame, str, str]:
    try:
        df, source, source_url = _fetch_via_ucimlrepo()
        print(f"Downloaded dataset via ucimlrepo (id={UCI_DATASET_ID}).")
        return df, source, source_url
    except Exception as exc:  # noqa: BLE001
        print(f"ucimlrepo download failed ({exc}); falling back to {FALLBACK_URL}")
        df, source, source_url = _fetch_fallback()
        return df, source, source_url


def main() -> None:
    settings.raw_data_dir.mkdir(parents=True, exist_ok=True)
    settings.processed_data_dir.mkdir(parents=True, exist_ok=True)
    settings.sample_data_path.parent.mkdir(parents=True, exist_ok=True)

    raw_df, source, source_url = _download_dataset()

    raw_path = settings.raw_data_dir / "heart.csv"
    raw_df.to_csv(raw_path, index=False)
    checksum = _sha256sum(raw_path)
    print(f"Saved raw dataset to {raw_path} ({len(raw_df)} rows).")

    processed_df = data_utils.prepare_heart_dataframe(raw_df)
    processed_path = settings.processed_data_dir / "heart_processed.csv"
    processed_df.to_csv(processed_path, index=False)
    print(f"Saved cleaned dataset to {processed_path} ({len(processed_df)} rows).")

    sample_rows = min(30, len(processed_df))
    sample_df = processed_df.sample(n=sample_rows, random_state=settings.random_seed)
    sample_df.to_csv(settings.sample_data_path, index=False)
    print(f"Wrote sample dataset to {settings.sample_data_path} ({sample_rows} rows).")

    metadata = {
        "source": source,
        "raw_path": str(raw_path),
        "processed_path": str(processed_path),
        "sample_path": str(settings.sample_data_path),
        "records_raw": len(raw_df),
        "records_clean": len(processed_df),
        "target_column": data_utils.TARGET_COLUMN,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checksum_sha256": checksum,
        "source_url": source_url,
        "notes": "Regenerate by running scripts/download_data.py; raw data is gitignored.",
    }
    meta_path = settings.raw_data_dir / "metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2))
    print(f"Metadata written to {meta_path}")


if __name__ == "__main__":
    main()
