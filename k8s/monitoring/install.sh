#!/usr/bin/env bash
set -euo pipefail

# Install Prometheus + Grafana (kube-prometheus-stack) into Minikube.
PROFILE="${1:-${MINIKUBE_PROFILE:-mlops-assign1}}"
NAMESPACE="${NAMESPACE:-monitoring}"
RELEASE="${RELEASE:-kube-prometheus-stack}"
PROM_INSTANCE="${PROM_INSTANCE:-${RELEASE}-prometheus}"
GRAFANA_ADMIN_PASSWORD="${GRAFANA_ADMIN_PASSWORD:-prom-operator}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1"
    exit 1
  fi
}

require_cmd minikube
require_cmd kubectl
require_cmd helm

echo "[+] Ensuring Minikube profile '${PROFILE}' is running..."
if ! minikube status -p "${PROFILE}" >/dev/null 2>&1; then
  echo "Minikube profile '${PROFILE}' is not running. Start it with 'make k8s-up' first."
  exit 1
fi

minikube -p "${PROFILE}" update-context >/dev/null

echo "[+] Adding helm repo 'prometheus-community' (if needed)..."
if ! helm repo list | grep -q "prometheus-community"; then
  helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
fi
helm repo update

echo "[+] Creating namespace '${NAMESPACE}' (if missing)..."
kubectl get ns "${NAMESPACE}" >/dev/null 2>&1 || kubectl create namespace "${NAMESPACE}"

echo "[+] Installing/Upgrading '${RELEASE}' in namespace '${NAMESPACE}'..."
helm upgrade --install "${RELEASE}" prometheus-community/kube-prometheus-stack \
  --namespace "${NAMESPACE}" \
  --create-namespace \
  --wait \
  --set grafana.adminUser=admin \
  --set grafana.adminPassword="${GRAFANA_ADMIN_PASSWORD}" \
  --set prometheus.prometheusSpec.serviceMonitorSelector.matchLabels.release="${RELEASE}" \
  --set grafana.service.type=ClusterIP \
  --set prometheus.service.type=ClusterIP

echo "[+] Applying ServiceMonitor for heart-api..."
kubectl apply -n default -f "${SCRIPT_DIR}/../manifests/servicemonitor.yaml"

echo "[+] Waiting for Prometheus and Grafana pods to be Ready..."
kubectl wait --for=condition=Ready pods -l "app.kubernetes.io/name=grafana,app.kubernetes.io/instance=${RELEASE}" -n "${NAMESPACE}" --timeout=180s
kubectl wait --for=condition=Ready pods -l "prometheus=${PROM_INSTANCE}" -n "${NAMESPACE}" --timeout=180s

cat <<EOF

Monitoring stack is installed.

Port-forward Grafana (username: admin, password: ${GRAFANA_ADMIN_PASSWORD}):
  kubectl -n ${NAMESPACE} port-forward svc/${RELEASE}-grafana 3000:80

Port-forward Prometheus UI:
  kubectl -n ${NAMESPACE} port-forward svc/${RELEASE}-prometheus 9090:9090

Verify scraping:
  1) Open http://localhost:9090/targets and search for "heart-api".
  2) You should see the ServiceMonitor target UP and metrics like 'heart_api_requests_total'.

Grafana dashboard JSON is at k8s/monitoring/grafana-dashboard.json. Import it after logging in.
EOF
