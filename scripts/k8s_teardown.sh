#!/usr/bin/env bash
set -euo pipefail

kubectl delete namespace neptune --ignore-not-found
echo "Namespace neptune deleted."
