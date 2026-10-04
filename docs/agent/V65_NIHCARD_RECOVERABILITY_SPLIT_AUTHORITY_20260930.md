# V65 NIH-CARD paired donor split authority resolution

**Date:** 2026-09-30  
**Status:** PROSPECTIVE AUTHORITY RESOLUTION — no biological correspondence opened

## Decision

The canonical donor-membership authority for future privileged-factor recoverability work is:

`results/v64/V64_NIHCARD_PAIRED_DONOR_SPLIT_V1.json`

produced by:

`scripts/v64/freeze_nihcard_paired_donor_split_v1.py`

with seed `20260930` and rule:

`sort unique donor IDs by sha256('<seed>|<donor_id>'); first 16 TRAIN, next 4 VALIDATION, final 4 TEST`.

The different membership embedded in:

`results/v64/V64_NIHCARD_PAIRED_RECOVERABILITY_PREFLIGHT_V1.json`

used a different seed string (`20260930-v64-recoverability-v1`). That preflight remains valid for schema/pairing observations, but its donor membership is superseded for future execution.

## Why this authority wins

The dedicated split has:
- a single-purpose deterministic producer;
- a dedicated machine-readable receipt;
- CI that tests determinism, donor disjointness, and outcome blindness;
- explicit governance that cross-modal correspondence remains unopened.

No donor membership is selected from RNA values, ATAC values, recoverability, or biological outcomes.

## Canonical membership

Use the donor lists exactly as recorded in `V64_NIHCARD_PAIRED_DONOR_SPLIT_V1.json`.

Do not use TEST to choose:
- privileged-factor rank;
- basis rotation;
- RNA predictor architecture;
- regularization;
- recoverability threshold;
- target definition.

## Governance

TRAINING OFF.  
Phase B STOPPED.  
Stage 4 NOT AUTHORIZED.  
Morabito PROTECTED.  
No RNA↔ATAC biological correspondence opened by this resolution.
