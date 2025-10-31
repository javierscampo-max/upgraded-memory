#!/usr/bin/env bash
set -euo pipefail

# Resolves repository root even when the script is run from another directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${SCRIPT_DIR}"

LOG_DIR="${ROOT_DIR}/logs"
LOG_FILE="${LOG_DIR}/uvicorn.log"

# Allow overriding default host/port via environment.
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

# Prevent multiple uvicorn instances on the same port.
while IFS= read -r pid; do
    [[ -n "${pid}" ]] || continue
    cmdline="$(ps -p "${pid}" -o command= 2>/dev/null || true)"
    [[ -n "${cmdline}" ]] || continue

    if [[ "${cmdline}" == *uvicorn* ]]; then
        echo "FastAPI server already running on port ${PORT} (PID=${pid}). Stop it first with ./stop_api.sh or choose a different PORT."
        exit 0
    fi
done < <(lsof -ti tcp:"${PORT}" -sTCP:LISTEN 2>/dev/null || true)

mkdir -p "${LOG_DIR}"

cd "${ROOT_DIR}"

echo "Starting FastAPI server on ${HOST}:${PORT}..."
python3 -m uvicorn fastapi_app:app --host "${HOST}" --port "${PORT}" >> "${LOG_FILE}" 2>&1 &
SERVER_PID=$!
echo "Server started (PID=${SERVER_PID}). Logs: ${LOG_FILE}"
