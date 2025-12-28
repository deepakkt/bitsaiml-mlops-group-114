#!/usr/bin/env bash
set -euo pipefail

PROFILE="${1:-${MINIKUBE_PROFILE:-mlops-assign1}}"
NAMESPACE="${NAMESPACE:-monitoring}"
RELEASE="${RELEASE:-kube-prometheus-stack}"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1"
    exit 1
  fi
}

require_cmd minikube
require_cmd kubectl
require_cmd helm

if ! minikube status -p "${PROFILE}" >/dev/null 2>&1; then
  echo "Minikube profile '${PROFILE}' is not running; nothing to uninstall."
  exit 0
fi

minikube -p "${PROFILE}" update-context >/dev/null

echo "[+] Uninstalling '${RELEASE}' from namespace '${NAMESPACE}'..."
helm uninstall "${RELEASE}" -n "${NAMESPACE}" || true

echo "[+] Deleting namespace '${NAMESPACE}' (if empty)..."
kubectl delete namespace "${NAMESPACE}" --ignore-not-found --wait=true || true

echo "[+] Monitoring stack removal requested. Remaining Helm releases:"
helm list --all-namespaces || true
