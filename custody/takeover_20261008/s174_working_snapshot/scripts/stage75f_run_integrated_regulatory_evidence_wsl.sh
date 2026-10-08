#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "${SCRIPT_DIR}/.." && pwd)}"
IMAGE="${IMAGE:-scenicplus:1.0a2-container.1}"
CONFIG="${CONFIG:-configs/stage75f_out_of_core_v1.yaml}"
DOCKER_MEMORY="${DOCKER_MEMORY:-4g}"

cd "${PROJECT_DIR}"
mkdir -p results/tables results/reports results/stage75e_container

docker image inspect "${IMAGE}" >/dev/null
GIT_COMMIT="$(git rev-parse HEAD)"

docker run --rm \
  --memory="${DOCKER_MEMORY}" \
  -e PYTHONUNBUFFERED=1 \
  -e STAGE75_GIT_COMMIT="${GIT_COMMIT}" \
  -v "${PROJECT_DIR}:/workspace" \
  -w /workspace \
  "${IMAGE}" \
  /opt/conda/bin/python -u \
    scripts/stage75f_integrate_regulatory_evidence.py \
    --config "${CONFIG}" \
    --project-dir /workspace \
  2>&1 | tee \
    results/stage75e_container/stage75f_integrated_regulatory_evidence.log