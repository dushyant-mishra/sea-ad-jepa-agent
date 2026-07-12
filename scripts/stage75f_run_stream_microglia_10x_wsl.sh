#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "${SCRIPT_DIR}/.." && pwd)}"
IMAGE="${IMAGE:-scenicplus:1.0a2-container.1}"
CONFIG="${CONFIG:-configs/stage75f_out_of_core_v1.yaml}"
MODE="${MODE:-audit}"

cd "${PROJECT_DIR}"
mkdir -p results/reports results/stage75e_container data/processed/stage75f

docker image inspect "${IMAGE}" >/dev/null

docker run --rm \
  --memory="${DOCKER_MEMORY:-16g}" \
  -e PYTHONUNBUFFERED=1 \
  -v "${PROJECT_DIR}:/workspace" \
  -w /workspace \
  "${IMAGE}" \
  /opt/conda/bin/python -u \
  scripts/stage75f_stream_microglia_10x_h5.py \
  --config "${CONFIG}" \
  --project-dir /workspace \
  --mode "${MODE}" \
  2>&1 | tee results/stage75e_container/stage75f_stream_microglia_10x_${MODE}.log
