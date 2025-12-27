#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/bootstrap_venv.sh
# Respects existing .venv; creates one with python -m venv if missing.

PYTHON_BIN="${PYTHON:-python3}"
VENV_DIR="${VENV_DIR:-.venv}"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "Python interpreter '${PYTHON_BIN}' not found. Set PYTHON to override." >&2
  exit 1
fi

if [ ! -d "${VENV_DIR}" ]; then
  echo "Creating virtual environment at ${VENV_DIR} with ${PYTHON_BIN}"
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
else
  echo "Reusing existing virtual environment at ${VENV_DIR}"
fi

# shellcheck disable=SC1090
source "${VENV_DIR}/bin/activate"

echo "Upgrading pip and installing requirements..."
python -m pip install --upgrade pip

if [ ! -f requirements.txt ]; then
  echo "requirements.txt not found in $(pwd). Aborting." >&2
  exit 1
fi

pip install -r requirements.txt

echo "Environment ready. Activate with: source ${VENV_DIR}/bin/activate"
