"""MLflow utility helpers."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Dict, Mapping

import mlflow
import mlflow.sklearn

from .config import settings


def configure_mlflow() -> None:
    """Configure MLflow tracking URI and experiment."""
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment(settings.experiment_name)


def start_run(run_name: str):
    """Start an MLflow run after ensuring configuration."""
    configure_mlflow()
    return mlflow.start_run(run_name=run_name)


def log_params_and_metrics(params: Mapping[str, object], metrics: Mapping[str, float]) -> None:
    """Log params and metrics if provided."""
    if params:
        mlflow.log_params(params)
    if metrics:
        mlflow.log_metrics(metrics)


def log_figures(figures: Dict[str, object], prefix: str = "") -> None:
    """Log matplotlib figures as MLflow artifacts."""
    for name, fig in figures.items():
        filename = f"{prefix}{name}.png" if prefix else f"{name}.png"
        mlflow.log_figure(fig, filename)


def export_model(model, run_id: str, model_name: str) -> Path:
    """
    Persist the trained model in MLflow format to the configured artifacts directory.

    Returns the path where the model was saved.
    """
    target_path = Path(settings.model_dir)
    if target_path.exists():
        shutil.rmtree(target_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    mlflow.sklearn.save_model(model, path=target_path)
    metadata = {
        "run_id": run_id,
        "model_name": model_name,
        "artifact_path": str(target_path),
    }
    meta_path = target_path / "metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2))
    return target_path
