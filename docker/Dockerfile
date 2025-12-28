# Base image
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MODEL_PATH=/app/artifacts/model

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source and assets; the trained MLflow model is baked into the image (artifacts/model).
COPY src ./src
COPY scripts ./scripts
COPY data/sample ./data/sample
COPY artifacts/model ./artifacts/model

# Prepare writable dirs for artifacts/data
RUN mkdir -p artifacts/model artifacts/plots data/raw data/processed

EXPOSE 8000

CMD ["uvicorn", "src.heart.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
