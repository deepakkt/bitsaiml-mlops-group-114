"""FastAPI app for serving the heart disease model (MLflow format)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Optional, Tuple
from uuid import uuid4

import mlflow
import mlflow.sklearn
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse

from ..config import settings
from . import metrics
from .logging import setup_logging
from .schema import HealthResponse, PredictionRequest, PredictionResponse

logger = setup_logging()

MODEL_PATH = Path(os.getenv("MODEL_PATH", settings.model_dir))
app = FastAPI(
    title="Heart Disease API",
    version="0.1.0",
    description="Serves the MLflow-exported heart disease classifier.",
)


@dataclass
class ModelState:
    """In-memory state for the loaded model."""

    model: Optional[object] = None
    model_version: Optional[str] = None
    run_id: Optional[str] = None
    source: str = str(MODEL_PATH)


model_state = ModelState()


def _read_metadata(model_dir: Path) -> dict:
    """Read model metadata json if present."""
    meta_path = model_dir / "metadata.json"
    if not meta_path.exists():
        return {}
    try:
        return json.loads(meta_path.read_text())
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to parse %s: %s", meta_path, exc)
        return {}


def _set_model_state(model=None, model_version=None, run_id=None, source=str(MODEL_PATH)) -> None:
    model_state.model = model
    model_state.model_version = model_version
    model_state.run_id = run_id
    model_state.source = source


def _load_model() -> None:
    """Load MLflow model if present; tolerate absence during bootstrap."""
    if not MODEL_PATH.exists():
        logger.info("MODEL_PATH %s not found; start the API after running `make train`.", MODEL_PATH)
        return

    try:
        mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        pyfunc_model = mlflow.pyfunc.load_model(str(MODEL_PATH))
        try:
            inference_model = mlflow.sklearn.load_model(str(MODEL_PATH))
        except Exception:  # noqa: BLE001
            inference_model = pyfunc_model

        info = mlflow.models.get_model_info(str(MODEL_PATH))
        meta = _read_metadata(MODEL_PATH)

        _set_model_state(
            model=inference_model,
            model_version=info.model_uuid or meta.get("model_name"),
            run_id=meta.get("run_id") or info.run_id,
            source=str(MODEL_PATH),
        )
        logger.info(
            "loaded-mlflow-model",
            extra={
                "model_version": model_state.model_version,
                "run_id": model_state.run_id,
                "source": model_state.source,
            },
        )
    except Exception:  # noqa: BLE001
        logger.exception("Failed to load model from %s", MODEL_PATH)
        _set_model_state()


def _predict_with_probability(model, df: pd.DataFrame) -> Tuple[int, float]:
    """Return (prediction, probability) with safe fallbacks."""
    raw_pred = model.predict(df)
    try:
        pred_value = raw_pred[0]
    except Exception:  # noqa: BLE001
        pred_value = raw_pred
    pred_int = int(pred_value)

    probability: float
    try:
        proba = model.predict_proba(df)
        probability = float(proba[0][-1])
    except Exception:  # noqa: BLE001
        probability = float(pred_int)
    return pred_int, probability


@app.on_event("startup")
async def _ensure_model_loaded() -> None:
    if model_state.model is None:
        _load_model()


@app.middleware("http")
async def add_metrics_and_logging(request: Request, call_next):
    """Record Prometheus metrics and structured logs with request ids."""
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    start = perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as exc:  # noqa: BLE001
        status_code = getattr(exc, "status_code", 500) if hasattr(exc, "status_code") else 500
        elapsed = perf_counter() - start
        if metrics.should_track_path(request.url.path):
            metrics.record_error(endpoint=request.url.path, method=request.method)
            metrics.record_request(
                endpoint=request.url.path,
                method=request.method,
                status_code=status_code,
                elapsed_seconds=elapsed,
            )
        logger.exception(
            "request-error",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
                "status_code": status_code,
                "duration_ms": round(elapsed * 1000, 2),
                "model_version": model_state.model_version,
                "run_id": model_state.run_id,
            },
        )
        raise
    else:
        elapsed = perf_counter() - start
        if metrics.should_track_path(request.url.path):
            metrics.record_request(
                endpoint=request.url.path,
                method=request.method,
                status_code=status_code,
                elapsed_seconds=elapsed,
            )
        logger.info(
            "request-complete",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
                "status_code": status_code,
                "duration_ms": round(elapsed * 1000, 2),
                "model_version": model_state.model_version,
                "run_id": model_state.run_id,
            },
        )
        response.headers["X-Request-ID"] = request_id
        return response


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Health probe."""
    return HealthResponse(
        status="ok",
        model_loaded=model_state.model is not None,
        model_version=model_state.model_version,
        run_id=model_state.run_id,
    )


@app.post("/predict", response_model=PredictionResponse)
def predict(payload: PredictionRequest) -> PredictionResponse:
    """Generate a prediction with the loaded model."""
    if model_state.model is None:
        raise HTTPException(status_code=503, detail="Model not loaded. Run `make train` then restart the API.")

    try:
        df = pd.DataFrame([payload.model_dump()])
        pred, prob = _predict_with_probability(model_state.model, df)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Prediction failed", extra={"model_version": model_state.model_version, "run_id": model_state.run_id})
        raise HTTPException(status_code=500, detail="Prediction failed") from exc

    return PredictionResponse(prediction=pred, probability=prob, model_version=model_state.model_version, run_id=model_state.run_id)


@app.get("/metrics", response_class=PlainTextResponse)
def prometheus_metrics():
    """Expose Prometheus metrics."""
    body, content_type = metrics.prometheus_response()
    return PlainTextResponse(body, media_type=content_type)
