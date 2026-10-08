# V64 chat-runtime custody manifest — 2026-09-29

Status: AUDITED CUSTODY RECORD  
Branch lineage: successor of Claude PR #198 head `e96d22854250cfb8938a876606011614a65f1856`  
Scientific governance: `TRAINING=OFF`; `TD60=BLOCKED`

## Purpose

Preserve the identity and recovery path of files physically available in this ChatGPT runtime that are not themselves present as repository blobs on the live V64 successor branch. This file distinguishes exact GitHub custody from hash-only custody. A hash-only entry MUST NOT be described as though its exact bytes were committed.

## Newly acquired scientific inputs

| File | Bytes | MD5 | SHA-256 | GitHub custody | Recovery |
|---|---:|---|---|---|---|
| NIHMS1066836-supplement-Table_S5.xlsx | 36,876,140 | c07e07916c07bd181a09b730c6011017 | 81c99689533d9da372cecdd469e7ff02cc985720105b83b3bd66c3ac8c93972e | HASH_ONLY; exact binary not stored by connector | User-supplied Nott supplementary Table S5. Authentication/results are committed at `results/v63/V63_NOTT_S5_AUTHENTICATION_V1.json` on `e96d2285`. Re-acquired copy must match both size and SHA-256 before use. |
| formatted_output_PU1_optimal_peak_IDR_ENCODE.ATAC_lifted.bed.gz | 841,467 | 9fc7767d501a938f90c44caa25a2d68f | 7cadc9906dbf335e252c823a8f19da738b64c7c45692ab4abbb962e18971cf36 | HASH_ONLY; public-redownloadable | FILER Nott 2019 processed hg38 microglia ATAC. |
| formatted_output_NeuN_optimal_peak_IDR_ENCODE.ATAC_lifted.bed.gz | 943,524 | 021f5f79663b653312674edba82d0333 | e5a094c69ef4d06338583c7d3fec5aced1e6b4fdf4e49a5d726c3e20d96299a4 | HASH_ONLY; public-redownloadable | FILER Nott 2019 processed hg38 neuronal ATAC. |
| formatted_output_Olig2_optimal_peak_IDR_ENCODE.ATAC_lifted.bed.gz | 655,864 | 6b2c4ffe6b3231aad4c075865a59f6ed | 220db7ae656001e81dd9af84c0382c6d020c1b023ffdbd5abb231a61ba1b0922 | HASH_ONLY; public-redownloadable | FILER Nott 2019 processed hg38 oligodendrocyte ATAC. |
| hg19ToHg38.over.chain.gz | 227,698 | 35887f73fe5e2231656504d1f6430900 | 5c0598e500ceb5a78c73086929e8ef993aec309bcafb595139b53d440b125a1d | HASH_ONLY; public-redownloadable | UCSC hg19→hg38 liftOver chain. |
| hg38ToHg19.over.chain.gz | 1,246,411 | ff3031d93792f4cbb86af44055efd903 | 14a712e8e147d9fc8e9d87d51977b46f6f8ddb93efbe5d0843d86b6205f587b1 | HASH_ONLY; public-redownloadable | UCSC hg38→hg19 liftOver chain. |

## Public recovery URLs

- PU1/microglia ATAC hg38: https://filer2.niagads.org/Annotationtracks/hg38_lifted/Nott_2019/ATAC-seq/bed3-lifted/hg38/formatted_output_PU1_optimal_peak_IDR_ENCODE.ATAC_lifted.bed.gz
- NeuN ATAC hg38: https://filer2.niagads.org/Annotationtracks/hg38_lifted/Nott_2019/ATAC-seq/bed3-lifted/hg38/formatted_output_NeuN_optimal_peak_IDR_ENCODE.ATAC_lifted.bed.gz
- Olig2 ATAC hg38: https://filer2.niagads.org/Annotationtracks/hg38_lifted/Nott_2019/ATAC-seq/bed3-lifted/hg38/formatted_output_Olig2_optimal_peak_IDR_ENCODE.ATAC_lifted.bed.gz
- hg19→hg38 chain: https://hgdownload.gi.ucsc.edu/goldenpath/hg19/liftOver/hg19ToHg38.over.chain.gz
- hg38→hg19 chain: https://hgdownload.gi.ucsc.edu/goldenpath/hg38/liftOver/hg38ToHg19.over.chain.gz

All re-downloads must be rejected unless their byte size and SHA-256 match this manifest.

## Repository-side authentication records

- `results/v63/V63_NOTT_S5_AUTHENTICATION_V1.json` — Claude's Table S5 authentication at `e96d2285`.
- `results/v64/V64_NOTT_ATAC_AND_CHAIN_AUTHENTICATION_RECEIPT_V1.json` — ChatGPT authentication of the three ATAC tracks and both chain directions at `194f8a6a`.
- `results/v64/V64_E2_SINGLE_SOURCE_SUCCESSOR_CONTRACT_V1.json` — explicit Nott-centered successor semantics.
- `results/v64/V64_NOTT_SAME_STUDY_SUBSTRATE_FIT_CONTRACT_V1.json` exists on the parallel successor branch and should be reconciled/cherry-picked before execution if not already incorporated.

## Prior project-mounted assets intentionally NOT duplicated

The following files are physically mounted in this runtime but are not reclassified as chat-exclusive. Prior V46 custody already indexes their exact identities:

- FOUNDATION_CALIBRATION_BUNDLE_20260824.zip
- FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part001
- FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.part002
- FOUNDATION_DISCOVERY_EXPRESSION_41K_LOG1P10K.zip.parts.sha256.csv
- checkpoints.zip
- expression.zip
- t1_checkpoint_u0200.zip
- 66e64913-959f-4a7c-bbfe-6ff906fb281d.npz
- Status and Repair Plan.txt
- WSL execution issue.txt

Do not duplicate these large assets merely because they are visible in this runtime.

## Exact-binary limitation

The available GitHub connector can create text files and Git objects from supplied text/base64, but it cannot stream arbitrary local container binaries directly into a repository. Therefore the six newly acquired binary inputs above are recorded as HASH_ONLY rather than falsely claimed as repository-resident exact bytes. This distinction is deliberate and fail-closed.

## Next-chat takeover rule

A future chat or Claude session must:
1. read this manifest;
2. verify the relevant authentication receipt;
3. re-acquire any needed hash-only binary from the user or public recovery URL;
4. verify SHA-256 before execution;
5. never silently substitute a similarly named file.

