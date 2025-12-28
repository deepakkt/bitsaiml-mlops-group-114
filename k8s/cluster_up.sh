#!/usr/bin/env bash
set -euo pipefail

# Clean start for Minikube profile (deletes existing profile before starting).
PROFILE="${1:-${MINIKUBE_PROFILE:-mlops-assign1}}"
DRIVER="${DRIVER:-docker}"
CPUS="${CPUS:-4}"
MEMORY="${MEMORY:-8192}" # MiB

if ! command -v minikube >/dev/null 2>&1; then
  echo "minikube is required but not found. Install it from https://minikube.sigs.k8s.io/docs/start/ and retry."
  exit 1
fi

echo "[+] Ensuring clean Minikube profile '${PROFILE}'"
if minikube status -p "${PROFILE}" >/dev/null 2>&1; then
  echo "    Deleting existing profile ${PROFILE}..."
  minikube delete -p "${PROFILE}"
fi

echo "[+] Starting Minikube (driver=${DRIVER}, cpus=${CPUS}, memory=${MEMORY}MB)"
minikube start -p "${PROFILE}" --driver="${DRIVER}" --cpus="${CPUS}" --memory="${MEMORY}" --addons=metrics-server

echo "[+] Minikube status:"
minikube status -p "${PROFILE}"

cat <<EOF
Minikube is running with profile '${PROFILE}'.

To build/load the API image for this cluster:
  1) Build inside Minikube's Docker daemon:
       eval \$(minikube -p ${PROFILE} docker-env)
       make docker-build
  or
  2) Build locally then load into the cluster:
       make docker-build
       minikube -p ${PROFILE} image load heart-api:local

Port-forward after deploy:
  kubectl -n default port-forward svc/heart-api 8000:80
EOF
