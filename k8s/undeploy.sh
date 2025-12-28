#!/usr/bin/env bash
set -euo pipefail

PROFILE="${1:-${MINIKUBE_PROFILE:-mlops-assign1}}"
NAMESPACE="${NAMESPACE:-default}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v minikube >/dev/null 2>&1; then
  echo "minikube is required but not found."
  exit 1
fi

if ! minikube status -p "${PROFILE}" >/dev/null 2>&1; then
  echo "Minikube profile '${PROFILE}' is not running; nothing to undeploy."
  exit 0
fi

echo "[+] Deleting heart-api resources from namespace '${NAMESPACE}'..."
minikube -p "${PROFILE}" kubectl -- delete -n "${NAMESPACE}" -f "${SCRIPT_DIR}/manifests/service.yaml" --ignore-not-found
minikube -p "${PROFILE}" kubectl -- delete -n "${NAMESPACE}" -f "${SCRIPT_DIR}/manifests/deployment.yaml" --ignore-not-found

if minikube -p "${PROFILE}" kubectl -- get crd servicemonitors.monitoring.coreos.com >/dev/null 2>&1; then
  minikube -p "${PROFILE}" kubectl -- delete -n "${NAMESPACE}" -f "${SCRIPT_DIR}/manifests/servicemonitor.yaml" --ignore-not-found
fi

echo "[+] Remaining resources in '${NAMESPACE}':"
minikube -p "${PROFILE}" kubectl -- get deploy,svc,pods -n "${NAMESPACE}" || true
