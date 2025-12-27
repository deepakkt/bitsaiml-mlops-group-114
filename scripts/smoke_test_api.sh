#!/usr/bin/env bash
set -euo pipefail

URL="${URL:-http://localhost:8000/health}"

echo "Running API smoke test against ${URL} ..."
status_code=$(curl -s -o /tmp/health_response.json -w "%{http_code}" "${URL}")

if [ "${status_code}" != "200" ]; then
  echo "Smoke test failed: HTTP ${status_code}"
  exit 1
fi

echo "Response:"
cat /tmp/health_response.json
echo
echo "Smoke test passed."
