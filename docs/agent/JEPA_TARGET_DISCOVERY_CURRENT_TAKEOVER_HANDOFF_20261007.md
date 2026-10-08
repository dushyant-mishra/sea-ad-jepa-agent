# JEPA Target Discovery — current takeover handoff

Date: 2026-10-07
Branch: `governance/stage-a-prefreeze-decisions-20261007`
Status: `G4_G5_VALUE_BLIND_PREFLIGHT_NEXT__VALUES_NOT_AUTHORIZED__NO_TARGET_WINNER__TRAINING_OFF`

## Start here
This is the current Target-Discovery entry point. Do not rebuild state from old chats.

Read in order:
1. `JEPA_STAGE_A_PREFREEZE_SELF_AUDIT_CORRECTION_20261007.md`
2. `JEPA_TARGET_DISCOVERY_RELATIONAL_REPLAY_SCOPE_CORRECTION_20261007.md`
3. `JEPA_TD_RELATIONAL_REPLAY_9216_RECEIPT_20261007.json`
4. `JEPA_TD_SAMPLE_A_ROW_IDENTITY_RECEIPT_20261007.json`
5. `JEPA_TD_RELATIONAL_CORRECTED_25K_REPLAY_CONTRACT_20261007.md`
6. `JEPA_TD_RELATIONAL_REPLAY_PREFLIGHT_STATUS_20261007.json`
7. `JEPA_TD_RELATIONAL_PREFLIGHT_RUNBOOK_20261007.md`
8. `JEPA_TD_RELATIONAL_G6_G7_PREFREEZE_20261007.md`
9. `JEPA_TD_RELATIONAL_IMMUTABLE_NAMESPACE_FREEZE_20261007.json`
10. `JEPA_TD_RELATIONAL_VALUE_READ_AUTHORIZATION_TEMPLATE_20261007.json`
11. `JEPA_MACHA_V77_CROSS_LANE_AUDIT_20261007.md`

All are under `docs/agent/`.

## Current scientific state
- Foundation estimand: **UNSET**.
- Stage-A population: **UNSET**.
- Stage-A deciding split: **UNSET**.
- Target winner: **NONE**.
- Representation winner: **NONE**.
- TD60: **NOT AUTHORIZED**.
- Training / EMA: **OFF**.
- TEST, DEV/SEALED, pathology, Morabito, external qualification: **CLOSED**.
- `QUERY_EXCHANGEABILITY` is a q-locality prerequisite, not proof that local state adds beyond a global/relational state.

The original `JEPA_STAGE_A_PREFREEZE_DECISIONS_20261007.*` are historical where they conflict with the self-audit correction.

## Why corrected replay is required
Historical HVS/SEA-AD 50K values used a provenance/sorted ordinal as if it were the physical H5AD feature column.

Correct chain:
`matrix-native stable ID -> physical column -> canonical molecular address -> raw count`.

Macha cross-lane authority:
- branch `claude/s174-train-cache-rebuild-20261007`
- S174 freeze `cf4d4708af68d32c8c1ec73b1a4b09294b2df6ef`
- frozen G1 remains FAILED as history
- prospective G1b freeze `8cdf568af4f21305b967e6d44dd3b41674de0a45`
- G1b PASS `4ab8e2101f2e595d9a97df05517d6e672768ecec`
- final result `results/v77/S174_REBUILD_G1B_RESULT_V1.json`

Do not use the earlier failed-G1 verification receipt as final repair authority.

## Exact historical replay objects — CLOSED
### Genes
Historical all-42 common core: 17,186 addresses.
Historical common-core CSV SHA:
`8aa8dfebb481aa2e60b12ab0f581ba1a36063b6c12dc2d8514d5fe7a20ad07ac`

Exact relational lineage = first 9,216 addresses under:
`SHA256("TD56S|gene|<molecular_address_index>")`.

Replay-manifest SHA:
`4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660`.

Allocation:
- 0..1023 TD56 / TD57A / TD58
- 1024..3071 TD57B
- 3072..6143 TD57C
- 6144..9215 TD59

Validated against preserved TD57B/TD57C arrays and all frozen TD59 gene/pair hashes.

No replacement gene or recomputed common core is allowed.

### Cells
Exact historical Sample-A:
- 25,000 rows
- HVS 1,129
- NPH52 1,310
- SEA-AD 22,561

Sample-freeze SHA:
`79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6`.

Exact row identity receipt is PASS. No resampling.

## Immediate next action — G4/G5 only
On canonical local machine `D:/Jepa project`:

```powershell
python scripts/v5/run_td_relational_replay_preflight.py
```

This is value-blind. It opens H5AD `var`/`obs` only, not count arrays.

It requires:
- all exact 9,216 addresses one-to-one resolvable in every required HVS/SEA matrix;
- every historical Sample-A HVS/SEA local row resolves to the frozen cell ID.

Required terminal:
`PASS_TD_RELATIONAL_PREFLIGHT_DRIVER_VALUE_BLIND`.

Current terminal until that happens:
`STOP_TD_RELATIONAL_CORRECTED_REPLAY_PREFLIGHT_INCOMPLETE_UNTIL_CANONICAL_LOCAL_G4_G5_PASS`.

## Immutable namespaces — already frozen
- preflight: `results/target_discovery/td_relational_corrected_replay_20261007/preflight_v1`
- corrected value cache: `data/cache/td_relational_corrected_sampleA_9216_v1`
- replay results: `results/target_discovery/td_relational_corrected_replay_20261007/value_replay_v1`

Never overwrite a terminal artifact.

## G6/G7 — designed and coded, but NOT authorized
Prepared scripts:
- `scripts/v5/materialize_td_relational_corrected_sampleA.py`
- `scripts/v5/audit_td_relational_g7_s174_overlap.py`

Tests:
- `tests/v5/test_materialize_td_relational_corrected_sampleA.py`
- `tests/v5/test_audit_td_relational_g7_s174_overlap.py`

**Their existence is not permission to run them.** Both require:
1. exact G4/G5 PASS receipt; and
2. a separate exact-scope runtime value authorization.

`JEPA_TD_RELATIONAL_VALUE_READ_AUTHORIZATION_TEMPLATE_20261007.json` is deliberately a non-authorizing template and is rejected by the scripts.

### G6 rule
For every exact Sample-A cell, recompute the whole physical-row raw molecule total **before mapping/filtering** and require exact equality to historical TD50 `source_library`.

Historical TD50 `detected` is **diagnostic only**, because it is old post-materialization CSR nnz and corrected SEA collision exclusions can legitimately alter it.

### G7 rule
Use Macha's final G1b-authorized cache.

For every **natural** Sample-A/S174 HVS/SEA cell overlap and every frozen replay address:
- compare raw integer counts;
- zero tolerance;
- use every natural overlap;
- never select extra cells to manufacture overlap.

If no natural overlap exists:
`NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP`.

## Future corrected cache semantics
Only after explicit value authorization:
- exact historical 25K Sample-A rows;
- logical shape `(25000, 41238)`;
- stored values only on exact 9,216 replay addresses;
- HVS/SEA values from corrected physical-ID reads;
- NPH52 historical clean-path pass-through for this defect-specific replay;
- normalization exactly `log1p(raw_count * 10000 / source_library)`;
- no target/replay verdict computed during materialization.

## Replay order after corrected cache is qualified
1. TD56
2. TD57A
3. TD58
4. TD57B
5. TD57C with original sequential stop rule
6. TD59

TD57C historical HVS FAIL remains history, but current scientific status is `REPLAY_REQUIRED`.

## Open identity warning
Macha records 353 frozen historical-Ensembl-ID mappings whose current symbol differs. The actual 353-row listing is not present in the committed artifacts currently accessible from this lane.

Do not guess or reconstruct it from outcomes. If the identity-lane artifact is recovered, intersect it prospectively with the 9,216 replay addresses and carry warnings; do not substitute genes.

Separate Macha G1b remap set: 897 SEA-AD IDs (`source Ensembl ID != address ID`), with 829 collision-ledger excluded and 68 value-checked per matrix. This is **not** the same object as the 353 symbol-warning set.

## Future agent must not
- treat old HVS/SEA 50K values as current numeric authority;
- substitute Macha's V77 cache for TD Sample-A;
- use old failed G1 instead of final G1b;
- use historical `detected` equality as a gate;
- recompute the common core or gene panels;
- change cells, donor split, pair count, locality fraction, nulls, thresholds, or sequential rules;
- promote TD57C's old fail without replay;
- treat q-exchangeability as an incremental global+local test;
- run values merely because G6/G7 scripts exist;
- run TD60, training, TEST, DEV/SEALED, pathology, Morabito, or external biology.

## Scientific question after replay
Only:
**Which historical TD56-TD59 relational claims survive correction of the HVS/SEA physical-feature-axis defect under their exact original rules?**

Only after that should Stage-A representation qualification resume and separately test whether q-safe local/program information adds held-donor information beyond the surviving global/relational state.
