#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  echo "Usage: $0 <base-url> [namespace]" >&2
  exit 2
fi

base_url="${1%/}"
namespace="${2:-helmet-staging}"

check_url() {
  local name="$1"
  local url="$2"
  local status

  status="$(curl --head --silent --show-error --location --max-time 15 --output /dev/null --write-out '%{http_code}' "$url")"
  echo "${name}: HTTP ${status}"

  if [ "$status" -lt 200 ] || [ "$status" -ge 500 ]; then
    echo "Smoke check failed for ${name} at ${url}" >&2
    exit 1
  fi
}

check_url "frontend" "${base_url}/"
check_url "ingestion" "${base_url}/api/v1/videos"
check_url "violations" "${base_url}/api/v1/violations"

kubectl -n "$namespace" get pods
kubectl -n "$namespace" get svc

echo "Smoke checks completed for ${base_url}"
