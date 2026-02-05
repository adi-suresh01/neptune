#!/usr/bin/env bash
set -euo pipefail

echo "Installing k3s..."
curl -sfL https://get.k3s.io | sh -

echo "Waiting for node to be ready..."
sudo k3s kubectl wait --for=condition=Ready node --all --timeout=120s

echo "Enabling kubeconfig for current user..."
mkdir -p "$HOME/.kube"
sudo k3s kubectl config view --raw > "$HOME/.kube/config"
chmod 600 "$HOME/.kube/config"

echo "k3s install complete."
