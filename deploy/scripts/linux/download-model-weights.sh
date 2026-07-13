#!/usr/bin/env bash
set -euo pipefail

model_repo="${HF_MODEL_REPO:-dtdat1234/helmet-violation-detection-models}"
model_revision="${HF_MODEL_REVISION:-main}"
target_dir="${1:-backend/inference/weights}"
base_url="https://huggingface.co/${model_repo}/resolve/${model_revision}/weights"
models=(
  yolo_best.onnx
  rtdetr_best.onnx
  fasterrcnn_best.onnx
)

mkdir -p "$target_dir"

auth_header=()
if [ -n "${HF_TOKEN:-}" ]; then
  auth_header=(-H "Authorization: Bearer ${HF_TOKEN}")
fi

for model in "${models[@]}"; do
  destination="${target_dir}/${model}"
  if [ -s "$destination" ]; then
    echo "Model weight already exists: ${model}"
    continue
  fi

  tmp_file="${destination}.download"
  rm -f "$tmp_file"
  echo "Downloading model weight: ${model}"
  curl --fail --location --retry 5 --retry-delay 5 --connect-timeout 20 \
    "${auth_header[@]}" \
    --output "$tmp_file" \
    "${base_url}/${model}"

  if [ ! -s "$tmp_file" ]; then
    echo "::error::Downloaded model weight is empty: ${model}"
    exit 1
  fi

  mv "$tmp_file" "$destination"
done

find "$target_dir" -maxdepth 1 -type f -name '*.onnx' -printf '%f %s bytes\n' | sort
