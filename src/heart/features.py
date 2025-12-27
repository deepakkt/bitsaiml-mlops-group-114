"""Feature engineering utilities (placeholder for Part-3)."""

from __future__ import annotations

from typing import List

from sklearn.pipeline import Pipeline


def build_feature_pipeline() -> Pipeline:
    """Construct the sklearn Pipeline; detailed steps will be added in Part-3."""
    raise NotImplementedError("Feature pipeline will be implemented in Part-3.")


def get_feature_names() -> List[str]:
    """Return expected feature names for API/schema alignment."""
    return [
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
