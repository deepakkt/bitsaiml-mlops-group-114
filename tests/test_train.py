import json
import sys

from src.heart import train
from src.heart.config import settings


def test_quick_training_exports_model(tmp_path, monkeypatch):
    """Quick training should export an MLflow model artifact and summary."""
    monkeypatch.setattr(settings, "model_dir", tmp_path / "model")
    monkeypatch.setattr(settings, "artifacts_dir", tmp_path / "artifacts")
    monkeypatch.setattr(settings, "plots_dir", tmp_path / "plots")
    monkeypatch.setattr(settings, "mlflow_tracking_uri", f"file:{tmp_path/'mlruns'}")
    monkeypatch.setenv("MLFLOW_TRACKING_URI", f"file:{tmp_path/'mlruns'}")

    monkeypatch.setattr(sys, "argv", ["train.py", "--quick", "--test-size", "0.25"])
    train.main()

    model_path = settings.model_dir / "MLmodel"
    metadata_path = settings.model_dir / "metadata.json"
    summary_path = settings.artifacts_dir / "training_summary.json"

    assert model_path.exists()
    assert metadata_path.exists()
    assert summary_path.exists()

    metadata = json.loads(metadata_path.read_text())
    assert "run_id" in metadata and metadata["run_id"]
    summary = json.loads(summary_path.read_text())
    assert isinstance(summary, list) and summary
