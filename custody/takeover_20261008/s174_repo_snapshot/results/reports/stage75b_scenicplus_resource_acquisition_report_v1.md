# Stage75B SCENIC+/CellOracle resource acquisition

## Readiness

| stage75b_resource_acquisition_run | small_download_requested | large_download_requested | small_resources_ready | large_resources_ready | ready_for_stage75b_scenicplus_run | ready_for_stage75c_state_response_model | ready_for_stage75d_perturbation_engine | large_cistarget_databases_deferred |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| True | True | False | True | False | False | False | False | True |

## Download status

| resource_name | resource_class | download_requested | download_succeeded_or_present | status | output | url |
| --- | --- | --- | --- | --- | --- | --- |
| hg38_chrom_sizes | small | True | True | already_present | data/external_resources/stage75b/hg38.chrom.sizes | https://hgdownload.soe.ucsc.edu/goldenPath/hg38/bigZips/hg38.chrom.sizes |
| gencode_v44_gtf | small | True | True | already_present | data/external_resources/stage75b/gencode.v44.annotation.gtf.gz | https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_44/gencode.v44.annotation.gtf.gz |
| cistarget_rankings_sha1 | small | True | True | downloaded | data/external_resources/stage75b/hg38_screen_v10_clust.regions_vs_motifs.rankings.feather.sha1sum.txt | https://resources.aertslab.org/cistarget/databases/homo_sapiens/hg38/screen/mc_v10_clust/region_based/hg38_screen_v10_clust.regions_vs_motifs.rankings.feather.sha1sum.txt |
| cistarget_scores_sha1 | small | True | True | downloaded | data/external_resources/stage75b/hg38_screen_v10_clust.regions_vs_motifs.scores.feather.sha1sum.txt | https://resources.aertslab.org/cistarget/databases/homo_sapiens/hg38/screen/mc_v10_clust/region_based/hg38_screen_v10_clust.regions_vs_motifs.scores.feather.sha1sum.txt |
| hg38_screen_region_motif_rankings | large | False | False | large_download_not_requested | data/external_resources/stage75b/hg38_screen_v10_clust.regions_vs_motifs.rankings.feather | https://resources.aertslab.org/cistarget/databases/homo_sapiens/hg38/screen/mc_v10_clust/region_based/hg38_screen_v10_clust.regions_vs_motifs.rankings.feather |
| hg38_screen_region_motif_scores | large | False | False | large_download_not_requested | data/external_resources/stage75b/hg38_screen_v10_clust.regions_vs_motifs.scores.feather | https://resources.aertslab.org/cistarget/databases/homo_sapiens/hg38/screen/mc_v10_clust/region_based/hg38_screen_v10_clust.regions_vs_motifs.scores.feather |

## Large resource handoff

| resource_name | resource_class | url | output | exists | size_bytes | expected_size | required_for_stage75b_scenicplus | required_for_stage75c | recommended_wsl_command |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hg38_screen_region_motif_rankings | large | https://resources.aertslab.org/cistarget/databases/homo_sapiens/hg38/screen/mc_v10_clust/region_based/hg38_screen_v10_clust.regions_vs_motifs.rankings.feather | data/external_resources/stage75b/hg38_screen_v10_clust.regions_vs_motifs.rankings.feather | False | 0 | 33G | True | False | wget -c -O 'data/external_resources/stage75b/hg38_screen_v10_clust.regions_vs_motifs.rankings.feather' 'https://resources.aertslab.org/cistarget/databases/homo_sapiens/hg38/screen/mc_v10_clust/region_based/hg38_screen_v10_clust.regions_vs_motifs.rankings.feather' |
| hg38_screen_region_motif_scores | large | https://resources.aertslab.org/cistarget/databases/homo_sapiens/hg38/screen/mc_v10_clust/region_based/hg38_screen_v10_clust.regions_vs_motifs.scores.feather | data/external_resources/stage75b/hg38_screen_v10_clust.regions_vs_motifs.scores.feather | False | 0 | 13G | True | False | wget -c -O 'data/external_resources/stage75b/hg38_screen_v10_clust.regions_vs_motifs.scores.feather' 'https://resources.aertslab.org/cistarget/databases/homo_sapiens/hg38/screen/mc_v10_clust/region_based/hg38_screen_v10_clust.regions_vs_motifs.scores.feather' |

## Claim boundary

| stage75b_acquisition_only | raw_downloads_not_committed | no_scenicplus_run | no_celloracle_run | no_model_training | no_external_validation_claim | no_causal_knockout_claim | no_therapeutic_claim | safety_audit_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| True | True | True | True | True | True | True | True | True |
