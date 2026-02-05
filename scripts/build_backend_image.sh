#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/neptune-backend"

IMAGE_NAME="neptune-backend:latest"

docker build -t "$IMAGE_NAME" "$BACKEND_DIR"
echo "Built $IMAGE_NAME"
