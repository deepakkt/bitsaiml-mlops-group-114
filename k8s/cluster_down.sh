#!/usr/bin/env bash
set -euo pipefail

PROFILE="${1:-${MINIKUBE_PROFILE:-mlops-assign1}}"

if ! command -v minikube >/dev/null 2>&1; then
  echo "minikube is required but not found; nothing to delete."
  exit 0
fi

if minikube status -p "${PROFILE}" >/dev/null 2>&1; then
  echo "[+] Deleting Minikube profile '${PROFILE}'..."
  minikube delete -p "${PROFILE}"
else
  echo "[+] Minikube profile '${PROFILE}' not found; nothing to do."
fi
