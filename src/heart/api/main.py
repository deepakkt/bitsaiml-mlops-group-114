"""FastAPI app for serving the heart disease model (placeholder-friendly)."""

from __future__ import annotations

import os
from pathlib import Path
from time import perf_counter
from typing import Optional

import mlflow
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse

from . import metrics
from .logging import setup_logging
from .schema import HealthResponse, PredictionRequest, PredictionResponse

logger = setup_logging()

MODEL_PATH = Path(os.getenv("MODEL_PATH", "artifacts/model"))
app = FastAPI(title="Heart Disease API", version="0.1.0")

model = None
model_version: Optional[str] = None
model_run_id: Optional[str] = None


def _load_model() -> None:
    """Load MLflow model if present; tolerate absence during bootstrap."""
    global model, model_version, model_run_id
    if not MODEL_PATH.exists():
        logger.info("MODEL_PATH %s not found; API will run without a model.", MODEL_PATH)
        return

    try:
        model = mlflow.pyfunc.load_model(str(MODEL_PATH))
        info = mlflow.models.get_model_info(str(MODEL_PATH))
        model_version = info.model_uuid
        model_run_id = info.run_id
        logger.info("Loaded model from %s (run_id=%s)", MODEL_PATH, model_run_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to load model from %s: %s", MODEL_PATH, exc)
        model = None
        model_version = None
        model_run_id = None


_load_model()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Health probe."""
    return HealthResponse(
        status="ok",
        model_loaded=model is not None,
        model_version=model_version,
        run_id=model_run_id,
    )


@app.post("/predict", response_model=PredictionResponse)
def predict(payload: PredictionRequest) -> PredictionResponse:
    """Generate a prediction with the loaded model or a safe fallback."""
    start = perf_counter()
    prob = 0.5
    pred = int(prob >= 0.5)
    status_code = 200

    try:
        if model is not None:
            df = pd.DataFrame([payload.model_dump()])
            # Some models may not expose predict_proba; handle gracefully.
            pred = int(model.predict(df)[0])
            if hasattr(model, "predict_proba"):
                prob = float(model.predict_proba(df)[0][1])
            else:
                prob = float(pred)
    except Exception as exc:  # noqa: BLE001
        status_code = 500
        metrics.record_error(endpoint="/predict", method="POST")
        logger.exception("Prediction failed: %s", exc)
        raise HTTPException(status_code=status_code, detail="Prediction failed") from exc
    finally:
        elapsed = perf_counter() - start
        metrics.record_request(endpoint="/predict", method="POST", status_code=status_code, elapsed_seconds=elapsed)

    return PredictionResponse(prediction=pred, probability=prob, model_version=model_version, run_id=model_run_id)


@app.get("/metrics", response_class=PlainTextResponse)
def prometheus_metrics():
    """Expose Prometheus metrics."""
    body, content_type = metrics.prometheus_response()
    return PlainTextResponse(body, media_type=content_type)
