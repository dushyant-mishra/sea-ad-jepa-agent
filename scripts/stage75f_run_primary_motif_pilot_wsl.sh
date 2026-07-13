#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "${SCRIPT_DIR}/.." && pwd)}"
IMAGE="${IMAGE:-scenicplus:1.0a2-container.1}"
CONFIG="${CONFIG:-configs/stage75f_out_of_core_v1.yaml}"
DOCKER_MEMORY="${DOCKER_MEMORY:-24g}"
FORCE="${FORCE:-0}"

cd "${PROJECT_DIR}"
mkdir -p \
  results/tables \
  results/reports \
  results/stage75f_motif_pilot \
  results/stage75e_container

docker image inspect "${IMAGE}" >/dev/null

extra_args=()
if [[ "${FORCE}" == "1" ]]; then
  extra_args+=(--force)
fi

docker run --rm \
  --memory="${DOCKER_MEMORY}" \
  -e PYTHONUNBUFFERED=1 \
  -e OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}" \
  -e OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-4}" \
  -e MKL_NUM_THREADS="${MKL_NUM_THREADS:-4}" \
  -v "${PROJECT_DIR}:/workspace" \
  -w /workspace \
  "${IMAGE}" \
  /opt/conda/bin/python -u \
    scripts/stage75f_run_primary_motif_pilot.py \
    --config "${CONFIG}" \
    --project-dir /workspace \
    "${extra_args[@]}" \
  2>&1 | tee \
    results/stage75e_container/stage75f_primary_motif_pilot.log
