# JEPA Target Discovery — current takeover handoff

Date: 2026-10-07
Branch: `governance/stage-a-prefreeze-decisions-20261007`
Status: `TARGET_DISCOVERY_REPLAY_PREFLIGHT_IN_PROGRESS__NO_REAL_VALUE_REPLAY_AUTHORITY__NO_TARGET_WINNER__NO_TRAINING_AUTHORITY`

## Start here
This file is the current entry point for the Target Discovery lane. Do not reconstruct the lane from older chats or from the initial Stage-A prefreeze files alone.

Read in this order:
1. `docs/agent/JEPA_STAGE_A_PREFREEZE_SELF_AUDIT_CORRECTION_20261007.md`
2. `docs/agent/JEPA_TARGET_DISCOVERY_RELATIONAL_REPLAY_SCOPE_CORRECTION_20261007.md`
3. `docs/agent/JEPA_TD_RELATIONAL_REPLAY_9216_RECEIPT_20261007.json`
4. `docs/agent/JEPA_TD_SAMPLE_A_ROW_IDENTITY_RECEIPT_20261007.json`
5. `docs/agent/JEPA_TD_RELATIONAL_CORRECTED_25K_REPLAY_CONTRACT_20261007.md`
6. `docs/agent/JEPA_TD_RELATIONAL_REPLAY_PREFLIGHT_STATUS_20261007.json`
7. `docs/agent/JEPA_TD_RELATIONAL_PREFLIGHT_RUNBOOK_20261007.md`
8. `docs/agent/JEPA_TD_RELATIONAL_G6_G7_PREFREEZE_20261007.md`
9. `docs/agent/JEPA_TD_RELATIONAL_IMMUTABLE_NAMESPACE_FREEZE_20261007.json`
10. `docs/agent/JEPA_MACHA_V77_CROSS_LANE_AUDIT_20261007.md`

## Superseded/corrected statements
The original `JEPA_STAGE_A_PREFREEZE_DECISIONS_20261007.*` files are historical records, not current authority where they conflict with the self-audit correction.

Current state:
- Foundation-model estimand: `UNSET`.
- Stage-A population: `UNSET`.
- Stage-A deciding donor split: `UNSET`.
- Historical 104 reader-fit / 68-36 split is not Stage-A authority.
- `QUERY_EXCHANGEABILITY` is a q-locality/shortcut prerequisite, not the deciding global-vs-global+local incremental test.
- TD56-TD59 are historical candidate evidence requiring corrected replay where HVS/SEA-AD values used the defective physical-axis materialization.
- NPH52 did not share the same positional-axis defect, but that does not make every NPH result globally qualified for every purpose.
- No target winner, representation winner, TD60 authority, or training authority exists.

## Physical-axis defect and Macha cross-lane authority
Historical HVS/SEA-AD materialization used a provenance/sorted ordinal as if it were the physical sparse-H5 column.

Macha lane: `claude/s174-train-cache-rebuild-20261007`.

Binding cross-lane facts:
- S174 freeze commit: `cf4d4708af68d32c8c1ec73b1a4b09294b2df6ef`.
- Correct join: physical var identifier -> frozen provenance exact Ensembl ID -> molecular address.
- Frozen G1 remains failed as history.
- Replacement G1b passed exactly at commit `4ab8e2101f2e595d9a97df05517d6e672768ecec`.
- Final G1b result: `results/v77/S174_REBUILD_G1B_RESULT_V1.json`.
- Do not use the earlier `S174_REBUILD_VERIFY_AND_COMPARISON_V1.json` failed-G1 result as final repair authority.
- Macha's corrected V77 cache is not a substitute for historical TD Sample-A cells.

Macha also flags 353 frozen historical-Ensembl-ID mappings whose current symbol differs. Do not tune or replace them. Before biological interpretation of TD replay, intersect the 9,216 replay addresses with that identity-flag set when the identity-lane artifact is available.

## Exact historical relational replay universe — CLOSED
Historical all-42 common measured-scalar core:
- rows: 17,186
- historical CSV SHA-256: `8aa8dfebb481aa2e60b12ab0f581ba1a36063b6c12dc2d8514d5fe7a20ad07ac`

TD56→TD59 uses only SHA-ranked positions 0..9215 under:
`SHA256("TD56S|gene|<molecular_address_index>")`.

Exact 9,216-address manifest SHA-256:
`4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660`.

Validated against preserved TD57B/TD57C arrays and all prospectively frozen TD59 gene/pair hashes.

Allocation:
- 0..1023: TD56 / TD57A / TD58
- 1024..3071: TD57B
- 3072..6143: TD57C
- 6144..9215: TD59

Never recompute a new corrected panel. Missing/noninjective frozen address => STOP / `NOT_ESTIMABLE`.

## Exact historical Sample-A identity — CLOSED
`FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv` SHA-256:
`79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6`.

Authenticated `A_NATURAL_MIXTURE`:
- 25,000 total
- HVS 1,129
- NPH52 1,310
- SEA-AD 22,561

Receipt: `docs/agent/JEPA_TD_SAMPLE_A_ROW_IDENTITY_RECEIPT_20261007.json`.

Do not resample or infer cells from the corrupted historical value matrix.

## Minimal corrected replay
Do not rebuild the full historical 50K x 41,238 matrix.

Future corrected cache, only after separate value authority:
- exact historical 25,000 Sample-A rows;
- logical canonical shape `(25000, 41238)`;
- stored values only for the exact 9,216 replay addresses;
- normalization `log1p(raw_count * 10000 / source_library)`;
- no gene/cell/panel/threshold/donor/locality substitution.

Replay order remains:
1. TD56
2. TD57A
3. TD58
4. TD57B
5. TD57C under original sequential stop rule
6. TD59

TD57C historical HVS failure stays recorded as history but current scientific status is `REPLAY_REQUIRED`.

## Current executable support

### Exact manifest generator
`scripts/v5/build_td_relational_replay_manifest.py`

### Value-blind mapping preflight
`scripts/v5/audit_td_relational_replay_mapping_preflight.py`

### One-command driver
`scripts/v5/run_td_relational_replay_preflight.py`

Canonical local run from `D:/Jepa project`:

```powershell
python scripts/v5/run_td_relational_replay_preflight.py
```

It:
- hash-checks sample freeze/provenance/collision ledger;
- regenerates and validates exact 9,216 manifest;
- extracts Macha's exact S174 freeze by `git show` from his branch and hash-checks it;
- opens only H5AD `var`/`obs`, never count arrays;
- verifies every required HVS/SEA address maps one-to-one;
- verifies every historical Sample-A HVS/SEA local row resolves to the exact frozen cell ID;
- writes only into the frozen preflight namespace.

Required terminal:
`PASS_TD_RELATIONAL_PREFLIGHT_DRIVER_VALUE_BLIND`.

Runbook:
`docs/agent/JEPA_TD_RELATIONAL_PREFLIGHT_RUNBOOK_20261007.md`.

## Immutable namespaces — CLOSED BEFORE VALUES
- preflight: `results/target_discovery/td_relational_corrected_replay_20261007/preflight_v1`
- corrected cache: `data/cache/td_relational_corrected_sampleA_9216_v1`
- replay results: `results/target_discovery/td_relational_corrected_replay_20261007/value_replay_v1`

Never overwrite an existing terminal artifact.

## G6/G7 — prefrozen but NOT authorized to execute
Binding authority:
`docs/agent/JEPA_TD_RELATIONAL_G6_G7_PREFREEZE_20261007.md`.

### G6
Exact gate is **whole-cell raw library total**:
- sum every raw count in the authenticated physical row before address filtering;
- require exact integer equality to historical TD50 `source_library` for all 25,000 cells.

Important correction:
- historical TD50 `detected` is old 41K CSR nnz after defective materialization;
- corrected collision exclusions can legitimately change it;
- therefore `detected` is diagnostic only, **not** a PASS gate.

### G7
Use final Macha **G1b PASS**, not old failed G1.

For every natural Sample-A/S174 overlapping cell and replay address present in the checked S174 set:
- exact integer raw-count equality;
- zero tolerance;
- use every natural overlap;
- never add/substitute cells to create overlap.

If there is no natural overlap, record `NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP` rather than manufacturing one.

## What remains now
Only the canonical local **value-blind G4/G5 run** remains before any count-array read may even be considered.

Current terminal:
`STOP_TD_RELATIONAL_CORRECTED_REPLAY_PREFLIGHT_INCOMPLETE_UNTIL_CANONICAL_LOCAL_G4_G5_PASS`.

After G4/G5 PASS, a separate explicit value-read/materialization authority would still be required for G6/G7 and corrected cache creation.

## Future agent must NOT
- treat old HVS/SEA 50K values as current numeric authority;
- substitute Macha V77 rebuilt cache for TD Sample-A;
- use the earlier failed S174 G1 receipt as final authority instead of G1b;
- make historical `detected` exact equality a replay gate;
- recompute a new common core or panel;
- reinterpret TD57C old failure as currently binding without replay;
- use query exchangeability as proof of incremental local value beyond global state;
- select donor weighting, 104 donors, 68/36, or 2,464 query membership as Stage-A authority from old proposal files;
- run TD60, training, TEST, DEV/SEALED, pathology, Morabito, or external qualification from this lane.

## Scientific question after corrected replay
Only:
**Which historical relational claims survive correction of the HVS/SEA physical-feature-axis defect under their exact original frozen rules?**

Only after that should Stage-A representation qualification resume and separately test whether q-safe local/program information adds held-donor information beyond the surviving global/relational state.
