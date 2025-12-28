#!/usr/bin/env bash
set -euo pipefail

HEALTH_URL="${HEALTH_URL:-http://localhost:8000/health}"
PREDICT_URL="${PREDICT_URL:-http://localhost:8000/predict}"
REQUEST_JSON="${REQUEST_JSON:-data/sample/request.json}"
REQUIRE_MODEL="${REQUIRE_MODEL:-0}"

echo "Running API smoke test against ${HEALTH_URL} ..."
status_code=$(curl -s -o /tmp/health_response.json -w "%{http_code}" "${HEALTH_URL}")

if [ "${status_code}" != "200" ]; then
  echo "Smoke test failed: HTTP ${status_code}"
  exit 1
fi

echo "Response:"
cat /tmp/health_response.json
echo

if [ -f "${REQUEST_JSON}" ]; then
  echo "Sending sample prediction request with ${REQUEST_JSON} ..."
  predict_status=$(curl -s -o /tmp/predict_response.json -w "%{http_code}" -X POST -H "Content-Type: application/json" -d @"${REQUEST_JSON}" "${PREDICT_URL}")
  if [ "${predict_status}" != "200" ]; then
    if [ "${predict_status}" = "503" ] && [ "${REQUIRE_MODEL}" -ne "1" ]; then
      echo "Predict endpoint returned 503 (model not loaded). Skipping failure because REQUIRE_MODEL!=1."
    else
      echo "Prediction failed: HTTP ${predict_status}"
      cat /tmp/predict_response.json || true
      exit 1
    fi
  else
    echo "Prediction response:"
    cat /tmp/predict_response.json
    echo
  fi
else
  echo "Skipping /predict smoke test because ${REQUEST_JSON} was not found."
fi

echo "Smoke test passed."
