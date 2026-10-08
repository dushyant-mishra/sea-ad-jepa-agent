# Stage75E Preparation Bundle Readme

This file was moved from the repository root during v4 launchpad cleanup. It is retained as provenance for the Stage75E SCENIC+/cisTarget setup work.

Original contents:

Stage75E preparation bundle
===========================

Copy/extract this bundle into the root of the JEPA repository.

Immediate commands while the large cisTarget download continues:

  bash scripts/stage75e_download_motif_annotation_wsl.sh
  MODE=inputs bash scripts/stage75e_run_preflight_wsl.sh

After both large feather files finish and their downloader checksums pass:

  MODE=all VERIFY_SHA1=0 bash scripts/stage75e_run_preflight_wsl.sh

An additional streamed SHA1 pass is optional:

  MODE=all VERIFY_SHA1=1 bash scripts/stage75e_run_preflight_wsl.sh

Generated data remain under results/. Raw resources remain under data/ and
must not be committed.
