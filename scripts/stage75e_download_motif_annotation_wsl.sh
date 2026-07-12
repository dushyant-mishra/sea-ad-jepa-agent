#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "${SCRIPT_DIR}/.." && pwd)}"
RESOURCE_DIR="${PROJECT_DIR}/data/external_resources/stage75b"
OUT="${RESOURCE_DIR}/motifs-v10nr_clust-nr.hgnc-m0.001-o0.0.tbl"
URL="https://resources.aertslab.org/cistarget/motif2tf/motifs-v10nr_clust-nr.hgnc-m0.001-o0.0.tbl"

mkdir -p "${RESOURCE_DIR}"

echo "Downloading human motif-to-TF annotation..."
wget -c -O "${OUT}" "${URL}"

test -s "${OUT}"
file "${OUT}"
head -n 3 "${OUT}"
sha256sum "${OUT}" > "${OUT}.sha256.txt"

echo
echo "Motif annotation ready:"
ls -lh "${OUT}" "${OUT}.sha256.txt"
