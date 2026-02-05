#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
K8S_DIR="$ROOT_DIR/k8s"

kubectl apply -k "$K8S_DIR"

kubectl -n neptune rollout status statefulset/neptune-postgres --timeout=180s
kubectl -n neptune rollout status statefulset/neptune-minio --timeout=180s
kubectl -n neptune rollout status deployment/neptune-ollama --timeout=180s
kubectl -n neptune rollout status deployment/neptune-backend --timeout=180s
kubectl -n neptune rollout status deployment/neptune-indexer --timeout=180s

echo "Deployment complete."
