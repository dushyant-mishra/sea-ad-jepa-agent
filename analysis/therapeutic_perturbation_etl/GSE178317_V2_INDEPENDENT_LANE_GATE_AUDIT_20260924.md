# GSE178317 V2 independent lane-support review — 2026-09-24

Status: `OPEN_REVIEW / SYNTHETIC_GATE_ONLY / NO_FULL_V2_RESULT_INSPECTED`. This review begins from Claude PR #77 @ `90d5c82e13e377dc61116a62b8c20f8801688927`. It does **not** alter the in-progress physical read-count extraction on Claude's GPU-enabled laptop. The historical audit index classifies the NEW V2 caller as `CHANGED_INPUT_REQUIRES_REQUALIFICATION`; the v1 raw guide recovery remains supporting evidence, its 10 assignments remain FAIL and cannot serve as training or an intervention dataset.

## HIGH — pooled-cell V2 qualification could pass an unusable target/control design

The original `stage_call` used only global per-target counts >=40 (for >=30 genes) and total NTC >=40, without requiring target and NTC in the **same** sequencing lanes. Counterexample: 30 targets each with 40 fake assigned cells confined to L1, NTC with 40 confined to L2. That receives original PASS, but **zero within-lane target-versus-NTC pseudobulks exist**. This directly contradicts the downstream `build_gse178317_intervention_effects_v1.py` requirements: at least 10 target cells and 10 controls in a lane, with at least three contributing lanes before even a lane-spread estimate is allowed. A single deeply sampled lane must not substitute for multiple independent lanes.

Repair on this independent branch: a target is development-support-usable only when it has >=40 assigned cells in total AND >=3 named lanes with >=10 assigned target cells AND >=10 same-lane NTC cells. At least 30 targets must meet the rule. NTC must have >=40 cells total and >=10 in >=3 lanes. All per-lane counts and rejection reasons are recorded. A successful engineering gate says `PASS_LANE_SUPPORT_ONLY`, never unqualified `PASS`. Receipt explicitly states `DEVELOPMENT_POST_SMOKE_NOT_GUIDE_IDENTITY_VALIDATION`, independent guide-identity validation FALSE, biological replication validation FALSE.

## OPEN — more science and provenance gates remain

1. Thresholds `z=5`, `min_usable_targets=30`, `min_cells=40` were declared after an inspected 0.27% smoke run. This does not create prospective held-out confirmation. An independent held-out validation design needs to be frozen before new outcomes are viewed; previous smoke and v1 failures belong in DEVELOPMENT exposure.
2. Median/MAD z-scores and global-guide-share Poisson tests are a new approximation, **not an exact reimplementation of demuxEM or Tian et al.** Their assumptions and correlation require simulation under realistic heterogeneous ambient backgrounds and sensitivity analysis, not a claim of guaranteed false-discovery control. A source-linked independent guide-identity reference or orthogonal read-level validation is needed.
3. Four sequencing lanes are not automatically four independent biological replicates. The lane standard deviation is technical/process spread unless source-specific independent biological units are proved. Do not publish it as donor/line-level biological uncertainty.
4. `--stage call` accepts an arbitrary NPZ using `allow_pickle=True` and does not authenticate a separately reviewed count-stage receipt, original feature/barcode census, source RDS/H5 roots or the 81-guide library. A separately reviewed input-bound V3 execution gate is needed before scientific qualification. Do not run the pickle loader on unknown files. This review does not change `--stage count` while the physical count is active.
5. `stage_call` and the count producer can overwrite pre-existing output paths. Reissued immutable versioned output directories and independent SHA receipts are required before physical rerun.
6. The existing downstream intervention script must ensure guide-by-lane and source sample identities and must not present a lane-based standard error as biological replication. The processed CRISPRbrain table for the same experiment is reference data, NOT an independent replication dataset.
7. The full V2 physical count/call receipt was not present at the audited PR #77 head. No physical guide-assignment result, benchmark performance or training authority is claimed here.

## Synthetic red-team scope

`tests/test_gse178317_v2_lane_support_redteam_20260924.py` exercises the pure gate and **the actual V2 stage-call receipt path** with synthetic forced guide scores. It checks a positive four-lane synthetic control, every-target-only-in-one-lane false PASS, unmatched NTC, insufficient per-lane target cells, fewer than 30 supported targets, insufficient NTC lane coverage, invalid lane census, unknown lane and actual fail-closed receipt fields. Workflow runs warnings-as-errors and fails on any skipped mandatory check. None of these fixtures represents physical GSE178317 read data.

**Unchanged stops:** GSE311359 BIN1 feature-name collision remains STOP; GSE175721 guide-to-cell join remains STOP; real N1, protected outcomes, D_shared, training and therapeutic ranking remain OFF.
