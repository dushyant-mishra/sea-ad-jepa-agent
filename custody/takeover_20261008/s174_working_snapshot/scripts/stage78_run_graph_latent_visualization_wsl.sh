#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="${PROJECT_DIR:-/mnt/d/Jepa project}"
CONFIG="${CONFIG:-configs/stage75f_out_of_core_v1.yaml}"
cd "${PROJECT_DIR}"

export PATH="$HOME/.local/bin:$PATH"
export STAGE78_NODE_VERSION="$(node --version)"
export STAGE78_NPM_VERSION="$(npm --version)"

pushd web/stage78_graph_explorer >/dev/null
npm ci --no-bin-links
npm run build
popd >/dev/null

python3 scripts/stage78_build_graph_latent_visualization.py   --config "${CONFIG}"   --project-dir .
