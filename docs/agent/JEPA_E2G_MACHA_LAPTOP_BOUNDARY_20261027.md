# JEPA E2G × Stage75 follow-on: local custody audit and Macha laptop execution boundary — 2026-10-27

**Authority:** `READ_ONLY__SOURCE_IDENTITY_PROVISIONAL__NO_TARGET_SELECTION__NO_TRAINING__NO_STAGE4`.

## Work completed in the current chat runtime (not the GPU laptop)

The locally mounted assets were inspected, not guessed:
- `e2g_public_7tracks_symbol_only.json` (54,322 bytes), frozen public seven-reference survey.
- `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`, containing `contracts/address_namespace.csv` (41,238 rows), where the uncompressed table SHA-256 is `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd`, matching the archive's own `BUNDLE_SHA256_MANIFEST.csv`.
- Additional large expression/checkpoint archives exist but are *not* a replacement for ATAC motif/peak coordinate evidence; they were not used in this task.
- A local read-only identity audit found all **27 Stage75 target symbols** have a **single source-native `current_exact` Ensembl assignment** in this **historical August 24** namespace. **25** have no other same-symbol address; **two** also have a separate legacy exact address:
  - `HLA-DPA1` current `ENSG00000231389`, legacy-only NPH52 `ENSG00000168384`.
  - `HLA-DPB1` current `ENSG00000223865`, legacy-only NPH52 `ENSG00000215048`.
  These legacy addresses are **not** synonymous canonical aliases. Never collapse them, infer a new current mapping, or replace the later repaired molecular-address authority with this earlier bundle.
- All *external* E2G browser BEDPE target labels remain **symbols**, not source-authenticated Ensembl IDs. The historical registry identifies the *project* side; it does not automatically authenticate external E2G source gene identity.

The exact local audit report and the executable Macha transfer kit are preserved as conversation attachments, not added as human/molecular matrices to GitHub. Compact kit name:
`MACHA_STAGE75_E2G_EXECUTION_PACKAGE_20261027.zip`
(22,201 bytes; SHA-256 `624e740635288ca664a2b38659b1aec799f8147ea6695d978555ef9afe81c7e9`).
**The laptop needs the ZIP supplied from the originating chat**, not an invented GitHub download URL. It includes the scripts, adversarial test, local 27-gene identity CSV/JSON, hash manifest, seven-track survey and full handoff.

Six local synthetic/adversarial tests passed for the prospective TF/peak/E2G interval join:
- exact reciprocal interval overlap and TF/target scoping;
- wrong build attestation blocked;
- modified public track SHA blocked;
- proximity-only evidence silently promoted to regulation blocked;
- wrong chromosome / different-gene matches do not count.

## What is NOT physically available in chat runtime

The full Stage75F **TF-bound motif-to-peak-to-target** rows from
`results/tables/stage75f_primary_tf_region_gene_evidence_v1.csv` and
`results/tables/stage75f_secondary_tf_region_gene_evidence_v1.csv`
are **not mounted here**, and the GitHub repository carries summary/frozen provenance rather than these fine-grained rows.
The original GSE174367 ATAC peak matrix, matching metadata and complete cisTarget/source intervals are also not mounted.
The existing integrated 96 TF→target summary does not contain authentic complete TF/motif enhancer intervals.
Therefore **no Stage75-to-external E2G coordinate concordance is claimed** from this environment.

## Macha laptop mission — independent execution, no training

1. Read current PR #457 scientific prospective contract, current PRs #322/#323 authority, and latest gene-ID repair custody. Re-check the current Task4 gate rather than relying on Oct 17 as active indefinitely.
2. Verify the laptop project root and all six required Stage75 tables:
   - `results/tables/stage75_integrated_tf_target_summary_v1.csv` — **96** frozen TF→target rows, blob `fd0f8e12c1161629f53f568f30cbc0bf8e3ff1a1`;
   - `results/tables/stage75f_primary_tf_region_gene_evidence_v1.csv`;
   - `results/tables/stage75f_secondary_tf_region_gene_evidence_v1.csv`;
   - `results/tables/stage75f_candidate_peak_gene_links_v1.csv`;
   - `results/tables/stage75c_peak_to_gene_preflight_v1.csv`;
   - motif hits and original peak/matrix reference as necessary for coordinate-assembly provenance.
3. Verify **true GRCh38 and zero-based half-open** peak coordinates from independent source headers/alignment/annotation metadata; the name of the cisTarget hg38 DB is not enough. Preserve exact file SHA-256, gene-ID binding, TF/motif direct vs extended status, and separate-nucleus provenance. Stop on unresolved genome build, missing file or identity collisions.
4. From the chat-supplied transfer kit in a **separate read-only review directory**, use `download_e2g_seven_public_tracks_v1.py --outdir results/regulatory/e2g_public_tracks_readonly`. This resolves seven fixed source IDs from `https://e2g.stanford.edu/graphql`, downloads only the publicly served browser BEDPE files from `storage.googleapis.com`, enforces <=9 MB each / <=50 MB total, exact SHA-256 checks and URL allowlisting. **Do not access the requester-pays `gs://e2g` bulk bucket.**
5. Produce a source-evidenced JSON build attestation with `stage75_build`, `e2g_build`, `interval_convention`, `evidence_verification`, `reviewer`, `source_provenance` only after actually auditing the source records.
6. Execute `macha_stage75_e2g_interval_corroboration_v1.py --project-dir . --track-dir results/regulatory/e2g_public_tracks_readonly --build-attestation <source-reviewed-build-file.json> --output-dir results/regulatory/e2g_stage75_laptop_candidate_v1`.
7. Return **only** source-hash preflight, `stage75_e2g_provisional_interval_overlap_receipt_v1.json` and compact `stage75_e2g_provisional_interval_overlap_v1.csv` (up to 672 TF→gene×source rows), or an explicit blocked/RED receipt. Do not upload donor-level data, controlled-access matrices, big genomic files or source observations.

The join computes **exact target-symbol match plus reciprocal >=0.5 genomic peak-element overlap**. It is provisional motif-element concordance in non-microglial or mixed references — not a TF causal edge, enhancer perturbation, donor-generalization result, dynamic disease trajectory, or a selected JEPA target. Zero thresholded rows are non-evidence of biological absence. Strong nulls (distance-matched/shuffled elements), source/donor transport and direct perturbations require a **separate prospective plan** after this first coordinate feasibility readout.

**Current result:** local identity custody **PASS**, laptop Stage75 genomic evidence **MISSING HERE / BLOCKED**. Keep all earlier graph-specific negative priors closed.
