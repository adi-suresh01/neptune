#!/usr/bin/env bash
set -euo pipefail

kubectl -n neptune port-forward svc/neptune-backend 8000:8000 &
BACKEND_PID=$!

kubectl -n neptune port-forward svc/neptune-ollama 11434:11434 &
OLLAMA_PID=$!

trap "kill $BACKEND_PID $OLLAMA_PID" EXIT
echo "Port-forwarding:"
echo "  Backend: http://localhost:8000"
echo "  Ollama:  http://localhost:11434"

wait
