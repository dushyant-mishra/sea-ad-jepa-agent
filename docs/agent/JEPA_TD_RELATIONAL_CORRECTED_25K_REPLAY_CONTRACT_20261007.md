# JEPA Target Discovery — corrected 25K relational replay contract

Status: `PREFREEZE_REPLAY_SCOPE_ONLY__NO_REAL_RNA_EXECUTION_AUTHORITY`
Date: 2026-10-07

## Purpose
Repair only the physical-feature-axis defect that contaminated the historical HVS/SEA-AD values used by the TD56→TD59 relational lineage. Preserve the original biological hypotheses, gene panels, cells, row order, normalization, donor/operator blocking, nulls, thresholds, sequential stop rules, and interpretation boundaries.

## Frozen molecular replay manifest
The exact historical all-42-operator common measured-scalar core is reconstructed from:
- `FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz` SHA-256 `852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537`
- `FOUNDATION_SUPPORT_ADDRESS_RECURRENCE.csv` SHA-256 `8f90c91e333eba6b58c39767069addef72bb4d9d6015ad8de14e7ff383c092da`

The reconstructed 17,186-row common-core CSV reproduces historical SHA-256:
`8aa8dfebb481aa2e60b12ab0f581ba1a36063b6c12dc2d8514d5fe7a20ad07ac`.

The full relational lineage uses only SHA-ranked positions 0..9215 under:
`SHA256("TD56S|gene|<molecular_address_index>")`.

Exact replay manifest:
`JEPA_TD_RELATIONAL_REPLAY_9216_MANIFEST_20261007.csv`
SHA-256: `4bde5f8041394410bf81e9c7c7edbf8553767a87bb31956f0b47bb50026f7660`.

The manifest reproduces preserved TD57B gene arrays/pair hashes, preserved TD57C Panel-0 gene arrays/pair hashes, and all prospectively frozen TD59 gene/pair hashes.

## Historical position allocation
- 0..1023: TD56 / TD57A / TD58, two 512-gene disjoint views.
- 1024..3071: TD57B, two independent 1024-gene panels.
- 3072..6143: TD57C, two independent three-view panels. Historical execution stopped after HVS Panel-0 failure; corrected replay must still follow the original sequential rule.
- 6144..9215: TD59, two independent three-view nearest-half panels.

No replacement gene is allowed. If a frozen address cannot be physically resolved under the corrected identity chain, replay is `NOT_ESTIMABLE` / STOP for the affected gate.

## Frozen cell population
Replay only historical `A_NATURAL_MIXTURE`, exactly 25,000 rows from the authenticated 50K harness:
- HVS: 1,129
- NPH52: 1,310
- SEA_AD: 22,561

`FOUNDATION_DISCOVERY_SAMPLE_FREEZE.csv` is authenticated at SHA-256:
`79eb005c719788119d9c3021e211148d34198301a59393707c9a2dc88dcef9a6`.

Exact historical Sample-A row identity has been recovered with PASS receipt:
`docs/agent/JEPA_TD_SAMPLE_A_ROW_IDENTITY_RECEIPT_20261007.json`.

Do not resample cells or infer row identity from the corrupted 50K value matrix.

## Corrected value chain
For every frozen Sample-A cell and every required address:

`matrix-native stable feature ID -> native physical column -> canonical molecular address -> raw count -> historical normalization`

HVS native feature identity must come from matrix-native `raw/var`; SEA-AD from matrix-native `var/gene_ids`; NPH52 retains its separately audited identity path. Never use the historical sorted provenance ordinal as a physical column.

## Normalization
Preserve the authenticated historical 50K transformation exactly:

`log1p(raw_count * 10000 / full_source_library)`

`full_source_library` is the whole-cell raw library size, not a 9,216-gene subset sum.

### G6 correction
The preserved TD50 `source_library` value is an exact replay sentinel because feature permutation/remapping cannot change the total raw molecule count. Recomputed whole-cell raw library totals must equal historical `source_library` exactly for every replayed cell.

The preserved TD50 `detected` value is **not** an exact PASS gate. Historical `compute_td50_source.py` defined `detected` as the nnz of the old 41K materialized CSR row. Corrected SEA-AD collision mapping can legitimately alter post-mapping nnz. Old and corrected detected/nnz counts must therefore be reported side by side as a diagnostic only.

Binding detail:
`docs/agent/JEPA_TD_RELATIONAL_G6_G7_PREFREEZE_20261007.md`.

## Minimal materialized matrix
Do **not** rebuild 41,238 values for these falsification replays.

Materialize a sparse CSR object with:
- rows: exactly 25,000 Sample-A cells in original global-row order 0..24,999;
- logical shape: `(25000, 41238)` so canonical molecular-address indices remain unchanged;
- stored value columns: only the 9,216 frozen replay addresses;
- unselected addresses absent from storage and forbidden to be queried by replay executors;
- selected measured-zero values remain implicit sparse zero, with measurability supplied by frozen support authority.

This preserves direct canonical-address indexing used by the frozen TD executors while reducing value-read scope from 41,238 addresses to 9,216.

## Source scope
- HVS and SEA-AD: rematerialize using corrected physical feature identity.
- NPH52: may be re-read through its separately qualified identity path for same-run consistency control; no new NPH target/search is permitted.
- No DEV, SEALED, pathology, Morabito, GSE214979, or other protected/external data.

## Replay order
No outcomes may be used to change order or rules.

1. TD56 exact original frozen screen.
2. TD57A exact original compute-safe triplet screen.
3. TD58 exact primary-60% partial-evidence screen.
4. TD57B exact independent donor-recurrent screen.
5. TD57C exact original nearest-third sequential screen. Historical FAIL is preserved as history but current scientific status is `REPLAY_REQUIRED`; proceed beyond HVS Panel-0 only if corrected replay passes under the already-frozen sequential rule.
6. TD59 exact nearest-half mesoscale screen.

No new locality fraction, pair width, mask fraction, threshold, gene replacement, donor split, or target family may be introduced.

## Decision semantics
This replay can only answer whether historical relational findings/failure survive correction of the feature-axis defect.

It cannot by itself:
- select a Foundation target;
- select a Stage-A representation winner;
- establish query-local incremental value;
- authorize TD60;
- authorize model/EMA training;
- authorize protected data.

## Required pre-execution gates

### Closed before value reads
1. exact 9,216 replay manifest receipt PASS;
2. exact historical Sample-A row identity PASS;
3. source asset identity and corrected identifier-join policy inherited from Macha S174 authority;
4. immutable namespaces frozen in `JEPA_TD_RELATIONAL_IMMUTABLE_NAMESPACE_FREEZE_20261007.json`.

### Still required on canonical local machine
5. value-blind G4/G5 mapping preflight must return `PASS_TD_RELATIONAL_MAPPING_PREFLIGHT_VALUE_BLIND` using `scripts/v5/run_td_relational_replay_preflight.py`;
6. under separately explicit value-read authority, every replayed cell's whole-row raw library total must exactly reproduce historical `source_library` (G6); historical `detected` is diagnostic only;
7. G7 must use Macha's final **G1b PASS** authority at commit `4ab8e2101f2e595d9a97df05517d6e672768ecec`, result `results/v77/S174_REBUILD_G1B_RESULT_V1.json`; compare every natural Sample-A/S174 overlapping cell/address exactly, with zero tolerance. If no natural overlap exists, report `NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP`; never manufacture overlap.

Historical 50K artifacts are never overwritten.

Terminal until G4/G5 pass:
`STOP_TD_RELATIONAL_CORRECTED_REPLAY_PREFLIGHT_INCOMPLETE_UNTIL_CANONICAL_LOCAL_G4_G5_PASS`.

## Identity-semantic warning
Macha's lane records 353 frozen historical-Ensembl-ID mappings with a different current symbol. Those identities remain frozen. Before biological interpretation, intersect the exact 9,216 replay addresses with the 353 identity-flag set when that identity-lane artifact is available and carry a warning flag; do not substitute genes based on symbol preference.

## Current operational entry points
- `docs/agent/JEPA_TARGET_DISCOVERY_CURRENT_TAKEOVER_HANDOFF_20261007.md`
- `docs/agent/JEPA_TD_RELATIONAL_PREFLIGHT_RUNBOOK_20261007.md`
- `scripts/v5/run_td_relational_replay_preflight.py`
