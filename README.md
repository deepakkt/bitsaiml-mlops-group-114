# Heart Disease MLOps (Bootstrap - Part 1)

This repository scaffolds an end-to-end MLOps project for the UCI Heart Disease dataset: data acquisition, preprocessing/EDA, model training with MLflow, serving via FastAPI, containerization, Kubernetes on local Minikube, monitoring with Prometheus/Grafana, and CI via GitHub Actions. This Part-1 bootstrap sets up the structure, dependencies, Make targets, and stubbed scripts so later parts can fill in the full pipeline.

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

# 4) Placeholder data/train steps
make data
make train

# 5) Run the API locally (serves health + metrics; model loading is optional for now)
make api
# in another terminal
curl http://localhost:8000/health
```

`make verify` is wired with all required stages but currently runs placeholder implementations for data/train/k8s/monitoring; subsequent parts will replace these with full logic.

## Make Targets
- `setup`: create/reuse `.venv` and install deps
- `lint`: ruff checks
- `test`: pytest suite (uses sample dataset)
- `data`: placeholder dataset acquisition (writes metadata stub)
- `train`: placeholder training entrypoint
- `api`: run FastAPI locally on `0.0.0.0:8000`
- `docker-build` / `docker-run` / `docker-stop`: build and run the API image
- `smoke-test`: curl `/health`
- `k8s-*`, `monitor-*`: stubs for Minikube deployment and monitoring
- `verify`: chained end-to-end flow (placeholder heavy steps)
- `clean`: remove caches and generated raw/processed data

## Repository Layout
Key paths (see `AGENTS.md` for the authoritative spec):
- `scripts/bootstrap_venv.sh` — venv creation/install (skips creation if `.venv` exists)
- `scripts/download_data.py` — placeholder for dataset download (Part-2 will add real logic)
- `src/heart/` — package skeleton (config, data, features, train/evaluate, API)
- `data/sample/sample.csv` — small committed sample for tests
- `docker/Dockerfile` — FastAPI container definition
- `k8s/` — manifests and scripts (placeholders until Part-6/7)
- `.github/workflows/ci.yml` — CI pipeline (lint, test, placeholder train)
- `report/` — report/figures/screenshots placeholders

## Known Placeholders (to be filled in future parts)
- Real dataset download/processing and EDA artifacts
- Feature pipeline + model training with MLflow logging and model export
- Full FastAPI prediction flow with MLflow-loaded model
- Docker smoke tests, Minikube deploy scripts, monitoring install scripts
- Report content and CI artifact uploads

## Troubleshooting (early bootstrap)
- Reinstall deps: `rm -rf .venv && ./scripts/bootstrap_venv.sh`
- Ruff not found: ensure `.venv/bin` is on PATH (`source .venv/bin/activate`)
- Docker build fails on network: retry after ensuring connectivity to PyPI
- Minikube not installed: skip `k8s-*`/`monitor-*` until Part-6/7 implementation
