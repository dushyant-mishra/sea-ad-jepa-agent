#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "${SCRIPT_DIR}/.." && pwd)}"
RESOURCE_DIR="${PROJECT_DIR}/data/external_resources/stage75b"

cd "${PROJECT_DIR}"
mkdir -p "${RESOURCE_DIR}"
wget -c -O "${RESOURCE_DIR}/hg38_screen_v10_clust.regions_vs_motifs.rankings.feather" "https://resources.aertslab.org/cistarget/databases/homo_sapiens/hg38/screen/mc_v10_clust/region_based/hg38_screen_v10_clust.regions_vs_motifs.rankings.feather"
wget -c -O "${RESOURCE_DIR}/hg38_screen_v10_clust.regions_vs_motifs.scores.feather" "https://resources.aertslab.org/cistarget/databases/homo_sapiens/hg38/screen/mc_v10_clust/region_based/hg38_screen_v10_clust.regions_vs_motifs.scores.feather"
cd "${RESOURCE_DIR}"
sha1sum -c hg38_screen_v10_clust.regions_vs_motifs.rankings.feather.sha1sum.txt
sha1sum -c hg38_screen_v10_clust.regions_vs_motifs.scores.feather.sha1sum.txt
