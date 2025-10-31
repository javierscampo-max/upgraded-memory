#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${SCRIPT_DIR}"

PORT="${PORT:-8000}"

graceful_kill() {
    local pid="$1"
    echo "Stopping FastAPI server (PID=${pid})..."
    kill "${pid}" 2>/dev/null || return

    for _ in {1..10}; do
        if ps -p "${pid}" > /dev/null 2>&1; then
            sleep 0.5
        else
            break
        fi
    done

    if ps -p "${pid}" > /dev/null 2>&1; then
        echo "Process did not exit gracefully; sending SIGKILL."
        kill -9 "${pid}" 2>/dev/null || true
    fi
}

stopped_any=false

# Find uvicorn processes listening on the target port even if they weren’t started via start_api.sh.
while IFS= read -r pid; do
    [[ -n "${pid}" ]] || continue

    cmdline="$(ps -p "${pid}" -o command= 2>/dev/null || true)"
    [[ -n "${cmdline}" ]] || continue

    if [[ "${cmdline}" == *uvicorn* ]]; then
        echo "Found uvicorn process on port ${PORT} (PID=${pid})."
        graceful_kill "${pid}"
        stopped_any=true
    fi
done < <(lsof -ti tcp:"${PORT}" -sTCP:LISTEN 2>/dev/null || true)

# As a safety net, terminate any remaining listeners on the port regardless of command.
while IFS= read -r pid; do
    [[ -n "${pid}" ]] || continue

    if ps -p "${pid}" > /dev/null 2>&1; then
        echo "Killing leftover process on port ${PORT} (PID=${pid})."
        graceful_kill "${pid}"
        stopped_any=true
    fi
done < <(lsof -ti tcp:"${PORT}" -sTCP:LISTEN 2>/dev/null || true)

if [[ "${stopped_any}" == true ]]; then
    echo "Server stopped."
else
    echo "No uvicorn process found listening on port ${PORT}."
fi
