# Heart Disease MLOps (Parts 1-7: Data + EDA + Training/MLflow + FastAPI + Docker + Minikube + Monitoring)

This repository scaffolds an end-to-end MLOps project for the UCI Heart Disease dataset: data acquisition, preprocessing/EDA, model training with MLflow, serving via FastAPI, containerization, Kubernetes on local Minikube, monitoring with Prometheus/Grafana, and CI via GitHub Actions. Part-6 adds Minikube deployment scripts and manifests with a clean start profile workflow; Part-7 completes monitoring.

## Prerequisites
- Python 3.11+ (venv, pip)
- make
- Docker (for `docker-build`/`docker-run`)
- Minikube + kubectl + Helm (required for k8s/monitoring steps)
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

# 7) Run the API locally (loads MLflow model from artifacts/model)
make api
# in another terminal
curl http://localhost:8000/health
curl -X POST -H "Content-Type: application/json" -d @data/sample/request.json http://localhost:8000/predict
curl http://localhost:8000/metrics | head -n 5

# 8) Build and run the Docker image (requires artifacts/model from training)
make docker-build
make docker-run           # mounts ./artifacts/model into the container
./scripts/smoke_test_api.sh
make docker-stop

# 9) (Optional) Deploy to local Minikube (clean start)
make k8s-up               # deletes existing profile 'mlops-assign1' then starts fresh
make k8s-deploy           # loads heart-api:local image and applies manifests
kubectl -n default port-forward svc/heart-api 8000:80 &
curl http://localhost:8000/health
curl -X POST -H "Content-Type: application/json" -d @data/sample/request.json http://localhost:8000/predict
make k8s-undeploy
make k8s-down

# 10) (Optional) Install monitoring (Prometheus + Grafana) and verify scraping
make monitor-up           # installs kube-prometheus-stack in monitoring namespace + applies ServiceMonitor
kubectl -n default get servicemonitor heart-api
kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090 &
# Visit http://localhost:9090/targets and search for heart-api; should be UP
kubectl -n monitoring port-forward svc/kube-prometheus-stack-grafana 3000:80 &
# Login admin/prom-operator, import k8s/monitoring/grafana-dashboard.json
make monitor-down

# 11) View MLflow UI
MLFLOW_TRACKING_URI=file:./mlruns .venv/bin/mlflow ui --port 5000
```

`make verify` runs the full flow (including Minikube deploy/teardown and monitoring install). Skip monitoring with `VERIFY_SKIP_MONITORING=1` if resources are tight.

## Make Targets
- `setup`: create/reuse `.venv` and install deps
- `lint`: ruff checks
- `test`: pytest suite (uses sample dataset)
- `data`: download and clean the heart disease dataset (saves raw/processed/sample + metadata)
- `eda`: generate basic EDA figures to `report/figures/`
- `train`: train Dummy + LogisticRegression + RandomForest with sklearn pipelines, CV, MLflow logging (`--quick` for CI)
- `api`: run FastAPI locally on `0.0.0.0:8000`
- `docker-build` / `docker-run` / `docker-stop`: build and run the API image (requires `artifacts/model` from training)
- `smoke-test`: hits `/health` and optionally `/predict` (uses `data/sample/request.json`; set `REQUIRE_MODEL=1` to fail if model is missing)
- `k8s-*`: Minikube clean start, deploy, and teardown scripts
- `monitor-*`: install/uninstall kube-prometheus-stack (Prometheus + Grafana) and re-apply `ServiceMonitor`
- `verify`: chained end-to-end flow (includes docker smoke test + k8s deploy)
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

## API Serving (Part-4)
- Run locally: `make api` (override model location with `MODEL_PATH=/path/to/model`).
- Health: `curl http://localhost:8000/health` → `{"status":"ok","model_loaded":true/false,...}`.
- Predict (uses MLflow-exported model): `curl -X POST -H "Content-Type: application/json" -d @data/sample/request.json http://localhost:8000/predict` → `{"prediction":0/1,"probability":0.xx,"model_version":"...","run_id":"..."}`.
- Metrics: `curl http://localhost:8000/metrics | head -n 5` (Prometheus exposition with `heart_api_requests_total`, latency histogram, error counter).
- Logging: JSON logs with `request_id`, `path`, `status_code`, `model_version`, `run_id`; request ID also returned as `X-Request-ID` header.
- Smoke test: `./scripts/smoke_test_api.sh` (set `REQUIRE_MODEL=1` to fail if the model is absent; uses `data/sample/request.json`).

## Containerization (Part-5)
- Prereq: run `make train` so `artifacts/model` exists for mounting.
- Build: `make docker-build`.
- Run: `make docker-run` (bind-mounts `$(pwd)/artifacts/model` into `/app/artifacts/model` read-only and sets `MODEL_PATH` accordingly).
- Smoke test: `./scripts/smoke_test_api.sh` (fails if model missing because `REQUIRE_MODEL=1` in the Make target).
- Stop: `make docker-stop`.
- Direct curl against the container: `curl http://localhost:8000/health` and `curl -X POST -H "Content-Type: application/json" -d @data/sample/request.json http://localhost:8000/predict`.

## Kubernetes Deploy (Part-6)
- Prereqs: `make train` and `make docker-build` (image embeds `artifacts/model`).
- Clean start: `make k8s-up` (deletes existing `mlops-assign1` profile, starts fresh with metrics-server addon).
- Deploy: `make k8s-deploy` (loads `heart-api:local` into Minikube, applies manifests, waits for rollout).
- Port-forward: `kubectl -n default port-forward svc/heart-api 8000:80` then curl health/predict as above.
- Inspect: `minikube -p mlops-assign1 kubectl -- get pods,svc` to confirm 2 replicas and ClusterIP service.
- Teardown: `make k8s-undeploy` then `make k8s-down`.
- ServiceMonitor is included and re-applied automatically when monitoring is installed.

## Monitoring (Part-7)
- Install stack (requires running Minikube profile): `make monitor-up` (installs `kube-prometheus-stack` into `monitoring`, applies `k8s/manifests/servicemonitor.yaml`).
- Verify targets: `kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090 &` → open `http://localhost:9090/targets` and search for `heart-api` (should be UP).
- Grafana: `kubectl -n monitoring port-forward svc/kube-prometheus-stack-grafana 3000:80 &` → login `admin/prom-operator`, import `k8s/monitoring/grafana-dashboard.json` (panels for request rate, p95 latency, error rate, pod CPU/mem).
- Default credentials are local-only; override with `GRAFANA_ADMIN_PASSWORD` env when running `make monitor-up` if desired.
- Uninstall: `make monitor-down` (helm uninstall + deletes `monitoring` namespace).

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
- `k8s/` — cluster scripts and manifests (includes ServiceMonitor and monitoring install scripts)
- `.github/workflows/ci.yml` — CI pipeline (lint, test, placeholder train)
- `report/` — report/figures/screenshots placeholders

## Known Placeholders (to be filled in future parts)
- Report content and CI artifact uploads

## Troubleshooting (early bootstrap)
- Reinstall deps: `rm -rf .venv && ./scripts/bootstrap_venv.sh`
- Ruff not found: ensure `.venv/bin` is on PATH (`source .venv/bin/activate`)
- Docker build fails on network: retry after ensuring connectivity to PyPI
- Minikube issues: run `make k8s-down` then `make k8s-up` for a clean start; ensure the `minikube` binary is on PATH
