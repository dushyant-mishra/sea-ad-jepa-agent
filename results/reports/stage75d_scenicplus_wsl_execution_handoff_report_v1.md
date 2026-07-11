# Stage75D SCENIC+/CellOracle WSL execution handoff

## Readiness

| stage75d_handoff_written | large_download_run_in_codex | environment_install_run_in_codex | ready_for_stage75e_after_user_wsl_completion | stage75e_should_verify_files_before_running |
| --- | --- | --- | --- | --- |
| True | False | False | True | True |

## Commands

| step | command |
| --- | --- |
| remove_failed_env_if_needed | conda env remove -y -n sea-ad-scenicplus // true |
| create_env | conda create -y -n sea-ad-scenicplus python=3.10.13 |
| install_base | conda run -n sea-ad-scenicplus python -m pip install --upgrade pip wheel setuptools |
| install_compiled_genomics_deps | conda install -y -n sea-ad-scenicplus -c conda-forge -c bioconda pybedtools=0.9.1 bedtools macs2=2.2.9.1 cython=0.29.37 numpy pandas scipy |
| verify_pybedtools_preinstalled | conda run -n sea-ad-scenicplus python - <<'PY'
import setuptools, pybedtools
print('setuptools', setuptools.__version__)
print('pybedtools', pybedtools.__version__)
PY |
| install_scenicplus | cd /tmp && rm -rf scenicplus && git clone https://github.com/aertslab/scenicplus && cd scenicplus && git checkout development && (conda run -n sea-ad-scenicplus python -m pip install . // (conda run -n sea-ad-scenicplus python -m pip install 'poetry<1.2' poetry-core 'packaging>=24.2' && conda run -n sea-ad-scenicplus python -m pip install --no-build-isolation .)) |
| install_celloracle_helpers | conda run -n sea-ad-scenicplus python -m pip install celloracle pyranges pybiomart mudata scanpy anndata |
| download_rankings | cd '/mnt/c/Users/dushy/Desktop/Jepa project' && mkdir -p '/mnt/c/Users/dushy/Desktop/Jepa project/data/external_resources/stage75b' && wget -c -O '/mnt/c/Users/dushy/Desktop/Jepa project/data/external_resources/stage75b/hg38_screen_v10_clust.regions_vs_motifs.rankings.feather' 'https://resources.aertslab.org/cistarget/databases/homo_sapiens/hg38/screen/mc_v10_clust/region_based/hg38_screen_v10_clust.regions_vs_motifs.rankings.feather' |
| download_scores | cd '/mnt/c/Users/dushy/Desktop/Jepa project' && mkdir -p '/mnt/c/Users/dushy/Desktop/Jepa project/data/external_resources/stage75b' && wget -c -O '/mnt/c/Users/dushy/Desktop/Jepa project/data/external_resources/stage75b/hg38_screen_v10_clust.regions_vs_motifs.scores.feather' 'https://resources.aertslab.org/cistarget/databases/homo_sapiens/hg38/screen/mc_v10_clust/region_based/hg38_screen_v10_clust.regions_vs_motifs.scores.feather' |
| verify_sha1 | cd '/mnt/c/Users/dushy/Desktop/Jepa project/data/external_resources/stage75b' && sha1sum -c hg38_screen_v10_clust.regions_vs_motifs.rankings.feather.sha1sum.txt && sha1sum -c hg38_screen_v10_clust.regions_vs_motifs.scores.feather.sha1sum.txt |
| postcheck | cd '/mnt/c/Users/dushy/Desktop/Jepa project' && conda run -n sea-ad-scenicplus python - <<'PY'
import importlib.util
mods=['scenicplus','pycisTopic','pycistarget','ctxcore','arboreto','celloracle','pyranges','mudata','scanpy']
print({m: bool(importlib.util.find_spec(m)) for m in mods})
PY |

## Large resource checklist

| resource | path_wsl | expected_size | required_before_stage75e |
| --- | --- | --- | --- |
| rankings_feather | /mnt/c/Users/dushy/Desktop/Jepa project/data/external_resources/stage75b/hg38_screen_v10_clust.regions_vs_motifs.rankings.feather | 33G | True |
| scores_feather | /mnt/c/Users/dushy/Desktop/Jepa project/data/external_resources/stage75b/hg38_screen_v10_clust.regions_vs_motifs.scores.feather | 13G | True |
| rankings_sha1 | /mnt/c/Users/dushy/Desktop/Jepa project/data/external_resources/stage75b/hg38_screen_v10_clust.regions_vs_motifs.rankings.feather.sha1sum.txt | 99B | True |
| scores_sha1 | /mnt/c/Users/dushy/Desktop/Jepa project/data/external_resources/stage75b/hg38_screen_v10_clust.regions_vs_motifs.scores.feather.sha1sum.txt | 97B | True |

## Claim boundary

| stage75d_handoff_only | no_large_download_run_in_codex | no_scenicplus_run | no_celloracle_run | no_model_training | raw_downloads_not_committed | no_external_validation_claim | no_causal_knockout_claim | no_therapeutic_claim | safety_audit_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| True | True | True | True | True | True | True | True | True | True |
