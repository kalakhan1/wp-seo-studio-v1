#!/usr/bin/env bash
# scripts/run_dev.sh
# Activate venv, ensure data dir, apply migrations, run uvicorn with reload.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
cd "$BACKEND_DIR"

if [ -f ".venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    # shellcheck disable=SC1091
    source .venv/bin/activate
else
    echo "Warning: .venv not found. Using system Python."
fi

mkdir -p data

echo "Applying database migrations..."
alembic upgrade head

echo "Starting uvicorn on http://127.0.0.1:8000 ..."
exec uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload