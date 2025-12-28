"""Pydantic models for the FastAPI service."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class APIModel(BaseModel):
    """Shared model settings for API schemas."""

    model_config = ConfigDict(protected_namespaces=())


class HealthResponse(APIModel):
    status: str = "ok"
    model_loaded: bool
    model_version: Optional[str] = None
    run_id: Optional[str] = None


class PredictionRequest(APIModel):
    age: float = Field(..., example=54)
    sex: int = Field(..., example=1, description="1=male, 0=female")
    cp: int = Field(..., example=0, description="Chest pain type")
    trestbps: float = Field(..., example=130)
    chol: float = Field(..., example=246)
    fbs: int = Field(..., example=0)
    restecg: int = Field(..., example=1)
    thalach: float = Field(..., example=150)
    exang: int = Field(..., example=0)
    oldpeak: float = Field(..., example=1.2)
    slope: int = Field(..., example=2)
    ca: int = Field(..., example=0)
    thal: int = Field(..., example=2)


class PredictionResponse(APIModel):
    prediction: int
    probability: float
    model_version: Optional[str] = None
    run_id: Optional[str] = None
