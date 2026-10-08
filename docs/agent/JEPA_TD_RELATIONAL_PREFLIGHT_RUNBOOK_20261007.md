# JEPA Target Discovery — corrected relational replay preflight runbook

Date: 2026-10-07
Status: `RUNBOOK_FROZEN__VALUE_BLIND_G4_G5_ONLY__NO_REAL_VALUE_REPLAY_AUTHORITY`

## Purpose
Run the remaining Target-Discovery replay preflight in the canonical local JEPA environment without reopening expression values.

This runbook closes operational ambiguity only. It does **not** authorize count-array reads, corrected materialization, replay outcomes, TD60, model fitting, or training.

## Canonical one-command driver
From the repository/project root on the canonical Windows JEPA machine:

```powershell
python scripts/v5/run_td_relational_replay_preflight.py
```

Default paths are intentionally explicit:

- project/repository root: `D:/Jepa project`
- Stage81A3R historical root: `D:/Jepa project-stage81a3r-20260814`
- sample freeze: `D:/Jepa project/exports/foundation_corpus_discovery_v1/FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv`
- Stage81A2R provenance: `D:/Jepa project/results/v4/stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz`
- Stage81A3R collision ledger: `D:/Jepa project-stage81a3r-20260814/results/v4/stage81a3r_expression_materialization_collision_ledger.csv.gz`
- calibration bundle: `D:/Jepa project/FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`
- historical TD41–TD58 archive: `D:/Jepa project/JEPA_TARGET_DISCOVERY_WORKING_ARTIFACTS_TD41_TD58_20260908.zip`
- Macha authority: extracted by `git show` from `claude/s174-train-cache-rebuild-20261007:results/v77/S174_REBUILD_FREEZE_V1.json`

If the Macha branch is not locally fetched, STOP and fetch that branch. Do not substitute a hand-copied freeze with unknown bytes.

## What the driver does

1. Verifies the exact hashes of:
   - `FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv` = `79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6`
   - Stage81A2R provenance = `df0cb60f2308c08adaeacb1db5d1099c9cd12e90323af8e3958c428d6869cd51`
   - Stage81A3R collision ledger = `f6909f81a2e73383b4346f8cf6d8b3ecfc282f81bfb42d695c6d6896b6c74722`
   - Macha S174 freeze = `240b2b71a94802477ca726a2b4bb020d2ad5542ccf31c4e732906008f81e967c`
2. Regenerates the exact historical 9,216-address manifest from the calibration bundle + preserved TD artifacts.
3. Requires regenerated manifest SHA-256 = `4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660`.
4. Runs `scripts/v5/audit_td_relational_replay_mapping_preflight.py`.
5. Opens only H5AD `var` and `obs` plus file metadata; it does not open `raw/X` or `X` count arrays.
6. Requires every one of the 9,216 frozen addresses to resolve one-to-one for each required HVS/SEA-AD matrix.
7. Requires every historical Sample-A HVS/SEA-AD `local_row` to resolve to the exact frozen `cell_id`.
8. Writes `PREFLIGHT_RESULT.json` only on PASS.

Required terminal status:

`PASS_TD_RELATIONAL_PREFLIGHT_DRIVER_VALUE_BLIND`

Underlying mapping receipt must be:

`PASS_TD_RELATIONAL_MAPPING_PREFLIGHT_VALUE_BLIND`

## Immutable namespaces
Frozen before any value replay:

- preflight: `results/target_discovery/td_relational_corrected_replay_20261007/preflight_v1`
- future corrected value cache: `data/cache/td_relational_corrected_sampleA_9216_v1`
- future replay results: `results/target_discovery/td_relational_corrected_replay_20261007/value_replay_v1`

If a terminal artifact already exists in a frozen namespace, STOP. Never overwrite it.

Authority: `docs/agent/JEPA_TD_RELATIONAL_IMMUTABLE_NAMESPACE_FREEZE_20261007.json`.

## PASS consequences
A PASS closes only G4/G5:

- exact 9,216-address physical mapping is resolvable under the corrected gene-ID join;
- exact historical Sample-A cells resolve to their raw-matrix rows.

It does **not** authorize values.

The next separately authorized step would need to close:

- **G6**: for every Sample-A cell, recomputed whole-cell raw library size and detected-feature count exactly reproduce historical sentinels;
- **G7**: corrected reads overlapping existing S174 sentinels agree exactly under the inherited rule;
- corrected values are then written only into the already-frozen immutable cache namespace.

## FAIL consequences
Any missing address, join collision affecting a required address, missing matrix, wrong file size, row mismatch, authority-hash mismatch, missing Macha branch, or existing terminal output => STOP.

Do not:
- replace a gene;
- choose another cell;
- recompute a new common core;
- loosen a collision rule;
- change source support;
- read expression values to diagnose a failed G4/G5 result.

## Associated code/tests

- `scripts/v5/run_td_relational_replay_preflight.py`
- `scripts/v5/build_td_relational_replay_manifest.py`
- `scripts/v5/audit_td_relational_replay_mapping_preflight.py`
- `tests/v5/test_run_td_relational_replay_preflight.py`
- `tests/v5/test_build_td_relational_replay_manifest.py`
- `tests/v5/test_audit_td_relational_replay_mapping_preflight.py`

## Current scientific boundary
No target winner exists. TD56–TD59 remain historical relational candidates under corrected replay. `QUERY_EXCHANGEABILITY` remains a q-locality prerequisite, not evidence of incremental value beyond a global/relational backbone. Training remains OFF.
