# Heart Disease MLOps (Parts 1-2: Data + EDA)

This repository scaffolds an end-to-end MLOps project for the UCI Heart Disease dataset: data acquisition, preprocessing/EDA, model training with MLflow, serving via FastAPI, containerization, Kubernetes on local Minikube, monitoring with Prometheus/Grafana, and CI via GitHub Actions. Part-2 implements reproducible dataset download/cleaning plus EDA artifact generation; later parts will extend training, serving, and deployment.

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

# 6) Placeholder train/API steps (full pipeline arrives in later parts)
make train

# 7) Run the API locally (serves health + metrics; model loading is optional for now)
make api
# in another terminal
curl http://localhost:8000/health
```

`make verify` is wired with all required stages but currently runs placeholder implementations for data/train/k8s/monitoring; subsequent parts will replace these with full logic.

## Make Targets
- `setup`: create/reuse `.venv` and install deps
- `lint`: ruff checks
- `test`: pytest suite (uses sample dataset)
- `data`: download and clean the heart disease dataset (saves raw/processed/sample + metadata)
- `eda`: generate basic EDA figures to `report/figures/`
- `train`: placeholder training entrypoint
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

## Repository Layout
Key paths (see `AGENTS.md` for the authoritative spec):
- `scripts/bootstrap_venv.sh` — venv creation/install (skips creation if `.venv` exists)
- `scripts/download_data.py` — reproducible dataset download/cleaning + metadata logging
- `src/heart/` — package skeleton (config, data, features, train/evaluate, API)
- `src/heart/eda.py` — scriptable EDA that saves plots to `report/figures/`
- `data/sample/sample.csv` — small committed sample for tests
- `docker/Dockerfile` — FastAPI container definition
- `k8s/` — manifests and scripts (placeholders until Part-6/7)
- `.github/workflows/ci.yml` — CI pipeline (lint, test, placeholder train)
- `report/` — report/figures/screenshots placeholders

## Known Placeholders (to be filled in future parts)
- Feature pipeline + model training with MLflow logging and model export
- Full FastAPI prediction flow with MLflow-loaded model
- Docker smoke tests, Minikube deploy scripts, monitoring install scripts
- Report content and CI artifact uploads

## Troubleshooting (early bootstrap)
- Reinstall deps: `rm -rf .venv && ./scripts/bootstrap_venv.sh`
- Ruff not found: ensure `.venv/bin` is on PATH (`source .venv/bin/activate`)
- Docker build fails on network: retry after ensuring connectivity to PyPI
- Minikube not installed: skip `k8s-*`/`monitor-*` until Part-6/7 implementation
