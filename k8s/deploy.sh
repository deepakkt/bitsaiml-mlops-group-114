#!/usr/bin/env bash
set -euo pipefail

# Deploy the heart-api to Minikube.
PROFILE="${1:-${MINIKUBE_PROFILE:-mlops-assign1}}"
NAMESPACE="${NAMESPACE:-default}"
IMAGE_NAME="${IMAGE_NAME:-heart-api:local}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1"
    exit 1
  fi
}

require_cmd minikube
require_cmd kubectl
require_cmd docker

if ! minikube status -p "${PROFILE}" >/dev/null 2>&1; then
  echo "Minikube profile '${PROFILE}' is not running. Start it with 'make k8s-up' (or ${SCRIPT_DIR}/cluster_up.sh ${PROFILE})."
  exit 1
fi

if ! docker image inspect "${IMAGE_NAME}" >/dev/null 2>&1; then
  echo "Docker image '${IMAGE_NAME}' not found. Run 'make train' then 'make docker-build' first."
  exit 1
fi

echo "[+] Loading image '${IMAGE_NAME}' into Minikube (${PROFILE})..."
minikube -p "${PROFILE}" image load "${IMAGE_NAME}"

echo "[+] Applying deployment and service manifests to namespace '${NAMESPACE}'..."
minikube -p "${PROFILE}" kubectl -- apply -n "${NAMESPACE}" -f "${SCRIPT_DIR}/manifests/deployment.yaml"
minikube -p "${PROFILE}" kubectl -- apply -n "${NAMESPACE}" -f "${SCRIPT_DIR}/manifests/service.yaml"

if minikube -p "${PROFILE}" kubectl -- get crd servicemonitors.monitoring.coreos.com >/dev/null 2>&1; then
  echo "[+] ServiceMonitor CRD detected; applying servicemonitor.yaml..."
  minikube -p "${PROFILE}" kubectl -- apply -n "${NAMESPACE}" -f "${SCRIPT_DIR}/manifests/servicemonitor.yaml"
else
  echo "[ ] ServiceMonitor CRD not installed yet; skipping servicemonitor.yaml (install monitoring stack to enable)."
fi

echo "[+] Waiting for deployment rollout..."
minikube -p "${PROFILE}" kubectl -- rollout status deployment/heart-api -n "${NAMESPACE}" --timeout=120s

echo "[+] Current resources in namespace '${NAMESPACE}':"
minikube -p "${PROFILE}" kubectl -- get deploy,svc,pods -n "${NAMESPACE}"

cat <<EOF
Port-forward to reach the API:
  kubectl -n ${NAMESPACE} port-forward svc/heart-api 8000:80
Then call:
  curl http://localhost:8000/health
  curl -X POST -H "Content-Type: application/json" -d @data/sample/request.json http://localhost:8000/predict
EOF
