PYTHON ?= python3
VENV ?= .venv
PIP := $(VENV)/bin/pip
PYTHON_BIN := $(VENV)/bin/python
UVICORN := $(VENV)/bin/uvicorn
MLFLOW := $(VENV)/bin/mlflow

IMAGE_NAME ?= heart-api:local
CONTAINER_NAME ?= heart-api-local
MINIKUBE_PROFILE ?= mlops-assign1
VERIFY_SKIP_MONITORING ?= 0

.DEFAULT_GOAL := help

.PHONY: help setup lint test data eda train mlflow-ui api docker-build docker-run docker-stop smoke-test k8s-up k8s-down k8s-deploy k8s-undeploy k8s-smoke monitor-up monitor-down monitor-check verify clean

help:
	@echo "Available targets:"
	@echo "  setup          Create/reuse venv and install dependencies"
	@echo "  lint           Run ruff checks"
	@echo "  test           Run pytest suite"
	@echo "  data           Download/preprocess dataset"
	@echo "  eda            Generate basic EDA figures to report/figures"
	@echo "  train          Train models with MLflow logging (--quick for CI/fast runs)"
	@echo "  mlflow-ui      Launch MLflow UI"
	@echo "  api            Run FastAPI locally with uvicorn"
	@echo "  docker-build   Build heart-api:local image"
	@echo "  docker-run     Run API image locally (detached)"
	@echo "  docker-stop    Stop local API container"
	@echo "  smoke-test     Hit /health endpoint for quick validation"
	@echo "  k8s-up/down    Start or delete Minikube profile"
	@echo "  k8s-deploy     Deploy API manifests to Minikube"
	@echo "  k8s-undeploy   Remove API manifests from Minikube"
	@echo "  k8s-smoke      Port-forward svc/heart-api from Minikube and run smoke test"
	@echo "  monitor-up     Install kube-prometheus-stack (Prometheus + Grafana) and apply ServiceMonitor"
	@echo "  monitor-down   Uninstall monitoring stack"
	@echo "  monitor-check  Confirm Prometheus is scraping heart-api targets (port-forward + API check)"
	@echo "  verify         One-command end-to-end flow (includes docker + k8s)"
	@echo "  clean          Remove build artifacts and caches"

setup:
	./scripts/bootstrap_venv.sh

lint:
	$(VENV)/bin/ruff check src tests

test:
	$(VENV)/bin/pytest

data:
	$(PYTHON_BIN) scripts/download_data.py

eda:
	$(PYTHON_BIN) -m src.heart.eda

train:
	$(PYTHON_BIN) -m src.heart.train

mlflow-ui:
	MLFLOW_TRACKING_URI=file:./mlruns $(MLFLOW) ui --port 5000

api:
	$(UVICORN) src.heart.api.main:app --host 0.0.0.0 --port 8000 --reload

docker-build:
	@if [ ! -d "$(CURDIR)/artifacts/model" ]; then \
		echo "Missing artifacts/model. Run 'make train' to export the MLflow model before docker-build."; \
		exit 1; \
	fi
	docker build -t $(IMAGE_NAME) -f docker/Dockerfile .

docker-run:
	@if [ ! -d "$(CURDIR)/artifacts/model" ]; then \
		echo "Missing artifacts/model. Run 'make train' to export the MLflow model before docker-run."; \
		exit 1; \
	fi
	docker run --rm -d --name $(CONTAINER_NAME) -p 8000:8000 \
		-e MODEL_PATH=/app/artifacts/model \
		-v $(CURDIR)/artifacts/model:/app/artifacts/model:ro \
		$(IMAGE_NAME)

docker-stop:
	-@docker stop $(CONTAINER_NAME) >/dev/null 2>&1 || true

smoke-test:
	REQUIRE_MODEL=1 ./scripts/smoke_test_api.sh

k8s-up:
	bash k8s/cluster_up.sh $(MINIKUBE_PROFILE)

k8s-down:
	bash k8s/cluster_down.sh $(MINIKUBE_PROFILE)

k8s-deploy:
	bash k8s/deploy.sh $(MINIKUBE_PROFILE)

k8s-undeploy:
	bash k8s/undeploy.sh $(MINIKUBE_PROFILE)

monitor-up:
	bash k8s/monitoring/install.sh

monitor-down:
	bash k8s/monitoring/uninstall.sh

k8s-smoke:
	bash scripts/k8s_smoke_test.sh

monitor-check:
	bash scripts/check_prometheus_target.sh

verify:
	@echo "Running verify end-to-end (includes docker smoke test)..."
	$(MAKE) setup
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) data
	$(MAKE) train
	$(MAKE) docker-build
	$(MAKE) docker-run
	sleep 5
	$(MAKE) smoke-test
	$(MAKE) docker-stop
	$(MAKE) k8s-up
	$(MAKE) k8s-deploy
	$(MAKE) k8s-smoke
	@if [ "$(VERIFY_SKIP_MONITORING)" -ne "1" ]; then $(MAKE) monitor-up; $(MAKE) monitor-check; else echo "Skipping monitoring per VERIFY_SKIP_MONITORING"; fi
	$(MAKE) k8s-undeploy
	@if [ "$(VERIFY_SKIP_MONITORING)" -ne "1" ]; then $(MAKE) monitor-down; fi
	$(MAKE) k8s-down
	@echo "Verify completed."

clean:
	rm -rf __pycache__ */__pycache__ .pytest_cache .ruff_cache mlruns artifacts data/processed
	find data/raw -maxdepth 1 -type f ! -name "metadata.json" -delete 2>/dev/null || true
	find . -name "*.pyc" -delete
