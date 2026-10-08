#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "${SCRIPT_DIR}/.." && pwd)}"
IMAGE="${IMAGE:-scenicplus:1.0a2}"
CONFIG="${CONFIG:-configs/stage75e_scenicplus_preflight_v1.yaml}"
MODE="${MODE:-inputs}"
VERIFY_SHA1="${VERIFY_SHA1:-0}"

cd "${PROJECT_DIR}"
mkdir -p results/tables results/reports

docker image inspect "${IMAGE}" >/dev/null

echo "Running Stage75E input/schema inventory..."
docker run --rm \
  -v "${PROJECT_DIR}:/workspace" \
  -w /workspace \
  "${IMAGE}" \
  micromamba run -n base python \
  scripts/stage75e_validate_inputs.py \
  --config "${CONFIG}" \
  --project-dir /workspace

echo
echo "Building mechanics-only TF/target/peak smoke subset..."
docker run --rm \
  -v "${PROJECT_DIR}:/workspace" \
  -w /workspace \
  "${IMAGE}" \
  micromamba run -n base python \
  scripts/stage75e_prepare_smoke_subset.py \
  --config "${CONFIG}" \
  --project-dir /workspace

if [[ "${MODE}" == "all" ]]; then
  echo
  echo "Validating cisTarget and motif resources..."
  EXTRA_ARGS=()
  if [[ "${VERIFY_SHA1}" == "1" ]]; then
    EXTRA_ARGS+=(--verify-sha1)
  fi
  docker run --rm \
    -v "${PROJECT_DIR}:/workspace" \
    -w /workspace \
    "${IMAGE}" \
    micromamba run -n base python \
    scripts/stage75e_validate_cistarget_resources.py \
    --config "${CONFIG}" \
    --project-dir /workspace \
    "${EXTRA_ARGS[@]}"
else
  echo
  echo "MODE=${MODE}: large cisTarget validation deferred until downloads finish."
fi

echo
echo "Stage75E preflight preparation completed."
echo "prediction_benchmark_updated=False"
echo "causal_validation_pass=False"
echo "therapeutic_target_claim=False"
echo "validated_grn_claim=False"
