#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/neptune-backend"
FRONTEND_DIR="$ROOT_DIR/neptune-frontend"

BACKEND_VENV="$BACKEND_DIR/venv"

cleanup() {
  if [[ -n "${BACKEND_PID:-}" ]]; then
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
  fi
  if [[ -n "${FRONTEND_PID:-}" ]]; then
    kill "$FRONTEND_PID" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT

echo "Starting Neptune backend..."
cd "$BACKEND_DIR"
if [[ ! -d "$BACKEND_VENV" ]]; then
  python3 -m venv "$BACKEND_VENV"
fi
source "$BACKEND_VENV/bin/activate"
pip install -r requirements.txt >/dev/null

export NEPTUNE_MODE=desktop
export DB_BACKEND=sqlite
export HOST=127.0.0.1
export PORT=8000
export CORS_ALLOW_ALL=true

python -m uvicorn app.main:app --reload >/tmp/neptune_backend.log 2>&1 &
BACKEND_PID=$!

echo "Starting Neptune frontend..."
cd "$FRONTEND_DIR"
if [[ ! -d "node_modules" ]]; then
  npm install >/dev/null
fi

PORT=3000 npm run dev >/tmp/neptune_frontend.log 2>&1 &
FRONTEND_PID=$!

echo ""
echo "Neptune is running:"
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo ""
echo "Logs:"
echo "  Backend:  /tmp/neptune_backend.log"
echo "  Frontend: /tmp/neptune_frontend.log"
echo ""
echo "Press Ctrl+C to stop."

wait
