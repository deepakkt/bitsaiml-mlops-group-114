# Heart Disease MLOps (Parts 1-3: Data + EDA + Training/MLflow)

This repository scaffolds an end-to-end MLOps project for the UCI Heart Disease dataset: data acquisition, preprocessing/EDA, model training with MLflow, serving via FastAPI, containerization, Kubernetes on local Minikube, monitoring with Prometheus/Grafana, and CI via GitHub Actions. Part-3 now implements full feature pipelines, model training/comparison with MLflow logging, and MLflow-format model export.

## Prerequisites
- Python 3.11+ (venv, pip)
- make
- Docker (for `docker-build`/`docker-run`)
- Minikube + kubectl + Helm (for later parts; current scripts are placeholders)
- GitHub Actions enabled for CI

## Quickstart (local)
```bash
# 1) Create/reuse the venv (respects existing .venv)
./scripts/bootstrap_venv.sh

# 2) Activate
source .venv/bin/activate

# 3) Basic checks
make lint
make test

# 4) Download + preprocess the dataset
make data

# 5) (Optional) Generate EDA figures to report/figures
make eda

# 6) Train models with MLflow logging (full search; use --quick for faster CI/local)
make train               # full
python -m src.heart.train --quick --test-size 0.25  # quick mode

# 7) Run the API locally (serves health + metrics; will load model if artifacts/model exists)
make api
# in another terminal
curl http://localhost:8000/health

# 8) View MLflow UI
MLFLOW_TRACKING_URI=file:./mlruns .venv/bin/mlflow ui --port 5000
```

`make verify` is wired with all required stages but still uses placeholder k8s/monitoring steps until later parts.

## Make Targets
- `setup`: create/reuse `.venv` and install deps
- `lint`: ruff checks
- `test`: pytest suite (uses sample dataset)
- `data`: download and clean the heart disease dataset (saves raw/processed/sample + metadata)
- `eda`: generate basic EDA figures to `report/figures/`
- `train`: train Dummy + LogisticRegression + RandomForest with sklearn pipelines, CV, MLflow logging (`--quick` for CI)
- `api`: run FastAPI locally on `0.0.0.0:8000`
- `docker-build` / `docker-run` / `docker-stop`: build and run the API image
- `smoke-test`: curl `/health`
- `k8s-*`, `monitor-*`: stubs for Minikube deployment and monitoring
- `verify`: chained end-to-end flow (placeholder heavy steps)
- `clean`: remove caches and generated raw/processed data

## Data & EDA (Part-2)
- Command: `make data` (downloads via `ucimlrepo` with GitHub CSV fallback)
- Outputs:
  - `data/raw/heart.csv` (gitignored) + `data/raw/metadata.json` with checksum/source
  - `data/processed/heart_processed.csv` (gitignored)
  - `data/sample/sample.csv` (10–50-row committed sample for tests)
- Optional EDA: `make eda` writes plots to `report/figures/`:
  - `target_balance.png`, `numeric_distributions.png`, `correlation_heatmap.png`, `missingness.png`

## Model Training + MLflow (Part-3)
- Command: `make train` (full) or `python -m src.heart.train --quick --test-size 0.25`
- Models compared: DummyClassifier (baseline), LogisticRegression (tuned), RandomForestClassifier (tuned) using sklearn `Pipeline` + `ColumnTransformer`.
- Data split: stratified train/test with StratifiedKFold CV; metrics: accuracy, precision, recall, ROC-AUC.
- MLflow:
  - Tracking URI: `file:./mlruns` (gitignored), experiment: `heart-disease-uci`.
  - Artifacts: plots to `artifacts/plots/`, model export to `artifacts/model/` (MLflow format with `metadata.json`), summary to `artifacts/training_summary.json`.
  - View UI: `MLFLOW_TRACKING_URI=file:./mlruns .venv/bin/mlflow ui --port 5000`.

## Repository Layout
Key paths (see `AGENTS.md` for the authoritative spec):
- `scripts/bootstrap_venv.sh` — venv creation/install (skips creation if `.venv` exists)
- `scripts/download_data.py` — reproducible dataset download/cleaning + metadata logging
- `src/heart/` — package skeleton (config, data, features, train/evaluate, API)
- `src/heart/eda.py` — scriptable EDA that saves plots to `report/figures/`
- `src/heart/train.py` — training CLI with quick/full modes and MLflow export
- `src/heart/mlflow_utils.py` — MLflow helpers (configure, log, export model)
- `src/heart/evaluate.py` — metrics + ROC/confusion plotting
- `src/heart/features.py` — preprocessing pipelines (impute/scale/one-hot)
- `data/sample/sample.csv` — small committed sample for tests
- `docker/Dockerfile` — FastAPI container definition
- `k8s/` — manifests and scripts (placeholders until Part-6/7)
- `.github/workflows/ci.yml` — CI pipeline (lint, test, placeholder train)
- `report/` — report/figures/screenshots placeholders

## Known Placeholders (to be filled in future parts)
- Full FastAPI prediction flow bound to exported MLflow model
- Docker smoke tests, Minikube deploy scripts, monitoring install scripts
- Report content and CI artifact uploads

## Troubleshooting (early bootstrap)
- Reinstall deps: `rm -rf .venv && ./scripts/bootstrap_venv.sh`
- Ruff not found: ensure `.venv/bin` is on PATH (`source .venv/bin/activate`)
- Docker build fails on network: retry after ensuring connectivity to PyPI
- Minikube not installed: skip `k8s-*`/`monitor-*` until Part-6/7 implementation
