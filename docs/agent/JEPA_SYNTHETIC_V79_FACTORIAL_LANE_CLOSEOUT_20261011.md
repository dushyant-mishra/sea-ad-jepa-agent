# JEPA Synthetic V79 Factorial Lane Closeout — 2026-10-11

## Purpose

This is the terminal controller record for the current factorial synthetic-world engineering lane.

Canonical entry point remains PR #265.

## Current implementation authority

- PR #262
- branch `fix/v79-factorial-memory-hardening-20261010`
- head `9110c3fae6d34e43463d56631f43004bda33beb8`

## Current audit authority

- PR #264
- branch `audit/v79-factorial-preexecution-hardened-20261010`
- receipt closeout audit: `docs/agent/V79_FACTORIAL_RECEIPT_CLOSEOUT_AUDIT_20261011.md`

## What this lane has completed

The internal factorial implementation is now prospectively hardened before any H0-H3 scientific outcome:

- hierarchical biology generation is blockwise at registry scale;
- observation generation avoids full dense rate/count intermediates;
- scoring remains sparse until frozen selected genes are materialized;
- old-vs-new scoring/localization equivalence is regression tested;
- class- and observation-regime-conditioned abundance/depth distributions are included;
- scientific receipt payloads are bounded, atomic and fail closed against internal matrices and gene/address identity;
- scientific execution remains mechanically disabled pending an independently reviewed final preexecution package.

Fresh verification is GitHub Actions run `38147114407`, job `114492689105`: **94 tests passed in 1.04 s**. The run also repeated the untouched-#253 versus hardened same-runtime fixture and reproduced the same integer count and capture hashes.

## Scientific design remains unchanged

The prospective experiment is still:
- H0 = baseline biology + baseline observer;
- H1 = hierarchical anonymous biology + baseline observer;
- H2 = baseline biology + explicit observation process;
- H3 = hierarchical biology + explicit observation process;
- C_OBS = same latent biology, changed observation regime;
- C_BIO = changed latent biology, same observation regime.

The intended biological test is unchanged: measurement changes should not masquerade as biological state changes, while true biological changes should remain detectable.

## Macha interface after code/data audit

Macha remains an external upstream authority producer, not part of this lane's implementation.

No Macha result is consumable until PR #261 independently certifies it. In particular:
- V1 detection failure at S4 is preserved as a real failure;
- V2 is the final prospectively bounded detection attempt;
- V2 must be frozen centrally and auditable rather than depending on accidental launcher overrides;
- any accepted family needs complete simulation recovery and explicit code/config snapshot identity;
- snapshot equivalence must cover the actual recovery transformations used;
- local execution/scheduler failures must not be confused with statistical failure;
- corrected TRAIN inference remains forbidden until simulation qualification passes;
- later real-data inference should use a compact authenticated selected-gene cache to avoid repeatedly reconstructing the full 41,238-column matrix on the laptop.

If Macha never qualifies, this lane does not invent replacement posterior authorities. A separate prospective decision would be required about whether to retain the older frozen calibration or stop the tournament.

## What is genuinely left

No known internal engineering task remains in this factorial lane.

The remaining steps require external evidence or custody bytes:

1. Macha reaches a terminal independent ruling: qualified authorities or explicit failure.
2. If qualified and accepted, map the biology authority to H1 and observation authority to H2 without transferring real causal identity.
3. Freeze a successor biology/observation authority + arm manifest if that mapping materially changes the current calibration.
4. Recompute byte hashes from the exact authority files actually used.
5. Supply the external registry and repaired-marginal custody bytes.
6. Run a fresh preexecution-only replay on the final implementation/authority package.
7. Independently audit that fresh gate receipt.
8. Only then enable the one-shot H0/H1/H2/H3/C_OBS/C_BIO tournament.

The historical READY receipt in PR #256 is evidence for the earlier package only and cannot satisfy step 6 for a changed final authority.

## Terminal state

`FACTORIAL_INTERNAL_ENGINEERING_CLOSED__WAITING_ON_UPSTREAM_QUALIFIED_AUTHORITY_AND_FINAL_BYTE_CUSTODY__SCIENTIFIC_TOURNAMENT_NOT_RUN__TRAINING_OFF`

`training_authorized=false`

No TEST/Morabito, pathology, target-discovery rank/panel, SCENIC+/ATAC target evidence, V78 outcome retuning, Stage4/500K, JEPA training/checkpoints or post-outcome rescue is authorized.
