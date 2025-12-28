#!/usr/bin/env bash
set -euo pipefail

# Port-forward the heart-api service in Minikube and run the API smoke test.
PROFILE="${MINIKUBE_PROFILE:-mlops-assign1}"
NAMESPACE="${NAMESPACE:-default}"
SERVICE_NAME="${SERVICE_NAME:-heart-api}"
LOCAL_PORT="${LOCAL_PORT:-8000}"
TARGET_PORT="${TARGET_PORT:-80}"
REQUEST_JSON="${REQUEST_JSON:-data/sample/request.json}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1"
    exit 1
  fi
}

require_cmd kubectl

if command -v minikube >/dev/null 2>&1; then
  minikube status -p "${PROFILE}" >/dev/null
  KUBECTL_CMD=(minikube -p "${PROFILE}" kubectl --)
else
  KUBECTL_CMD=(kubectl)
fi

echo "[+] Verifying service ${SERVICE_NAME} exists in namespace ${NAMESPACE}..."
"${KUBECTL_CMD[@]}" get svc "${SERVICE_NAME}" -n "${NAMESPACE}" >/dev/null

echo "[+] Port-forwarding svc/${SERVICE_NAME} ${LOCAL_PORT}:${TARGET_PORT}..."
"${KUBECTL_CMD[@]}" port-forward "svc/${SERVICE_NAME}" "${LOCAL_PORT}:${TARGET_PORT}" -n "${NAMESPACE}" >/tmp/heart_port_forward.log 2>&1 &
PF_PID=$!

cleanup() {
  if ps -p "${PF_PID}" >/dev/null 2>&1; then
    kill "${PF_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

# Give port-forward a moment to establish.
sleep 5

echo "[+] Running smoke test via port-forwarded service..."
HEALTH_URL="http://localhost:${LOCAL_PORT}/health" \
PREDICT_URL="http://localhost:${LOCAL_PORT}/predict" \
REQUEST_JSON="${REQUEST_JSON}" \
REQUIRE_MODEL=1 \
  "${SCRIPT_DIR}/smoke_test_api.sh"

echo "[+] k8s smoke test passed."
