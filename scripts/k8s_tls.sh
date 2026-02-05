#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="neptune"
CERT_DIR="/tmp/neptune-tls"
HOSTS=("neptune.local" "ollama.local")

mkdir -p "$CERT_DIR"

openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout "$CERT_DIR/tls.key" \
  -out "$CERT_DIR/tls.crt" \
  -subj "/CN=neptune.local"

kubectl -n "$NAMESPACE" create secret tls neptune-tls \
  --key "$CERT_DIR/tls.key" \
  --cert "$CERT_DIR/tls.crt" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "TLS secret created in namespace $NAMESPACE"
