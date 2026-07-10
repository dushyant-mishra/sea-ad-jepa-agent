#!/usr/bin/env bash
set -euo pipefail
cd "/mnt/c/Users/dushy/Desktop/Jepa project"
mkdir -p "/mnt/c/Users/dushy/Desktop/Jepa project/data/external_resources/stage75b"
wget -c -O "/mnt/c/Users/dushy/Desktop/Jepa project/data/external_resources/stage75b/hg38_screen_v10_clust.regions_vs_motifs.rankings.feather" "https://resources.aertslab.org/cistarget/databases/homo_sapiens/hg38/screen/mc_v10_clust/region_based/hg38_screen_v10_clust.regions_vs_motifs.rankings.feather"
wget -c -O "/mnt/c/Users/dushy/Desktop/Jepa project/data/external_resources/stage75b/hg38_screen_v10_clust.regions_vs_motifs.scores.feather" "https://resources.aertslab.org/cistarget/databases/homo_sapiens/hg38/screen/mc_v10_clust/region_based/hg38_screen_v10_clust.regions_vs_motifs.scores.feather"
cd "/mnt/c/Users/dushy/Desktop/Jepa project/data/external_resources/stage75b"
sha1sum -c hg38_screen_v10_clust.regions_vs_motifs.rankings.feather.sha1sum.txt
sha1sum -c hg38_screen_v10_clust.regions_vs_motifs.scores.feather.sha1sum.txt
