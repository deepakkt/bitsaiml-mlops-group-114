"""Central configuration for the Heart Disease MLOps project."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="HEART_",
        protected_namespaces=("settings_",),
    )

    random_seed: int = 42
    experiment_name: str = "heart-disease-uci"

    data_dir: Path = Path("data")
    raw_data_dir: Path = Path("data/raw")
    processed_data_dir: Path = Path("data/processed")
    sample_data_path: Path = Path("data/sample/sample.csv")

    artifacts_dir: Path = Path("artifacts")
    model_dir: Path = Path("artifacts/model")
    plots_dir: Path = Path("artifacts/plots")
    mlflow_tracking_uri: str = "file:./mlruns"


settings = Settings()
