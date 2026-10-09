#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${1:-$(git rev-parse --show-toplevel)}"
R_ENV="${STAGE81A2R_R_ENV:-${HOME}/miniconda3/envs/stage81a2r-r-feature-audit}"
CACHE_DIR="${PROJECT_DIR}/data/external/v4/gene_identity_authority/r_feature_cache"
ENV_MANIFEST="${PROJECT_DIR}/results/v4/stage81a2r_r_feature_audit_environment.txt"

test -x "${R_ENV}/bin/Rscript"
test -f "${PROJECT_DIR}/scripts/v4/stage81a2r_extract_r_feature_metadata.R"

"${R_ENV}/bin/Rscript" \
  "${PROJECT_DIR}/scripts/v4/stage81a2r_extract_r_feature_metadata.R" \
  "${PROJECT_DIR}" \
  "${CACHE_DIR}"

"${R_ENV}/bin/Rscript" -e \
  "library(Matrix); library(qs); writeLines(capture.output(sessionInfo()), '${ENV_MANIFEST}')"

"${R_ENV}/bin/Rscript" -e \
  "stopifnot(requireNamespace('Matrix', quietly=TRUE), requireNamespace('qs', quietly=TRUE)); cat('Stage81A2R R feature-cache smoke PASS\n')"
