#!/usr/bin/env bash
set -euo pipefail

# Basic scrape verification for the heart-api ServiceMonitor using Prometheus API.
PROFILE="${MINIKUBE_PROFILE:-mlops-assign1}"
NAMESPACE="${NAMESPACE:-monitoring}"
RELEASE="${RELEASE:-kube-prometheus-stack}"
PROM_SERVICE="${PROM_SERVICE:-${RELEASE}-prometheus}"
TARGET_LABEL="${TARGET_LABEL:-heart-api}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1"
    exit 1
  fi
}

require_cmd kubectl
require_cmd curl
require_cmd python3

if command -v minikube >/dev/null 2>&1; then
  minikube status -p "${PROFILE}" >/dev/null
  KUBECTL_CMD=(minikube -p "${PROFILE}" kubectl --)
else
  KUBECTL_CMD=(kubectl)
fi

echo "[+] Ensuring Prometheus service ${PROM_SERVICE} exists in namespace ${NAMESPACE}..."
"${KUBECTL_CMD[@]}" get svc "${PROM_SERVICE}" -n "${NAMESPACE}" >/dev/null

echo "[+] Port-forwarding Prometheus service to localhost:9090 for scrape check..."
"${KUBECTL_CMD[@]}" port-forward "svc/${PROM_SERVICE}" 9090:9090 -n "${NAMESPACE}" >/tmp/prom_port_forward.log 2>&1 &
PF_PID=$!

cleanup() {
  if ps -p "${PF_PID}" >/dev/null 2>&1; then
    kill "${PF_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

# Give port-forward a moment to establish.
sleep 5

echo "[+] Querying Prometheus targets API for '${TARGET_LABEL}'..."

success=0
for attempt in $(seq 1 12); do
  TARGET_JSON=$(curl -s http://localhost:9090/api/v1/targets || true)
  if echo "${TARGET_JSON}" | python3 - "$TARGET_LABEL" <<'PY'; then
import json
import sys

target_name = sys.argv[1]

try:
    payload = json.loads(sys.stdin.read())
except json.JSONDecodeError as exc:
    print(f"Failed to parse Prometheus response: {exc}")
    sys.exit(1)

active = payload.get("data", {}).get("activeTargets", [])
matches = [
    t for t in active
    if target_name in t.get("labels", {}).values()
]

if not matches:
    sys.exit(2)

up = [t for t in matches if t.get("health") == "up"]
if not up:
    sys.exit(3)

print(f"Prometheus scrape is UP for '{target_name}' ({len(up)} target(s)).")
PY
  then
    success=1
    break
  else
    echo "[ ] Target not UP yet (attempt ${attempt}/12); waiting 5s..."
    sleep 5
  fi
done

if [ "${success}" -ne 1 ]; then
  echo "Prometheus scrape check failed after retries."
  exit 1
fi

echo "[+] Prometheus scrape check passed."
