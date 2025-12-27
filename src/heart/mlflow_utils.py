"""MLflow utility helpers (placeholder for Part-3)."""

from __future__ import annotations

import mlflow

from .config import settings


def get_experiment() -> str:
    """Return the default experiment name."""
    return settings.experiment_name


def configure_mlflow() -> None:
    """Configure MLflow tracking URI and experiment."""
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment(settings.experiment_name)
