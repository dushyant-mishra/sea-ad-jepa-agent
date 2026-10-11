# TD G6/G7 standalone V2 authorization-boundary design

Date: 2026-10-10

Status: `DESIGN_SPEC__NO_EXECUTION_AUTHORITY__NO_VALUE_READ`

## 1. Purpose

This design replaces the first PR #251 wrapper-based hardening with a standalone V2 custody boundary before any corrected expression-value read is ever authorized.

It is strictly an engineering/custody redesign. It does not create scientific authority, does not select a target, does not run G6/G7, does not run TD56/TD57B/TD57C/TD59 replay, does not authorize TD60, and does not authorize training.

Hard terminal remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## 2. Why the first V2 wrapper is insufficient

The first PR #251 hardening correctly identified two dormant hazards: historical G6 V1 silently rounded fractional physical values, and G7 returned process success for `NOT_ESTIMABLE`. A later self-audit found additional boundary defects that require a standalone V2 implementation rather than more monkey-patching.

### 2.1 Bare-status preflight acceptance

The wrapper inherits V1 `load_preflight_pass()`, which accepts a JSON file solely because `status == PASS_TD_RELATIONAL_PREFLIGHT_DRIVER_VALUE_BLIND`.

That is insufficient after PR #248 self-audit hardening. Future G6 must authenticate the exact V2 driver receipt and its required evidence, not a bare status string.

### 2.2 Time-of-check/time-of-use gap

PR #248 G4/G5 re-hashes all 35 HVS/SEA H5AD files. Historical G6, however, checks only source presence/size immediately before opening value arrays. A same-size replacement after G4/G5 could therefore reach a value read.

Future G6 and G7 must re-authenticate the exact source SHA immediately before first opening the corresponding expression/count array.

### 2.3 Runtime authority is not bound to exact evidence/code

The first V2 authorization design binds schema/token/scope and entrypoint strings, but not:

- exact G4/G5 preflight receipt SHA;
- exact G4/G5 receipt schema;
- exact G4/G5 mapping receipt schema/check set;
- exact G6 implementation SHA;
- exact G7 implementation SHA.

A runtime value-read authorization must bind all of these prospectively.

### 2.4 V2 execution currently emits V1 custody schemas

The wrapper calls historical V1 `main()`, so a hardened V2 run would still emit `JEPA_TD_RELATIONAL_G6_RECEIPT_V1` and `JEPA_TD_RELATIONAL_CORRECTED_SAMPLE_A_CACHE_V1`.

That is too ambiguous for a new authorization boundary. Future V2 must emit V2-only receipts/manifests.

## 3. Chosen architecture

Create a standalone V2 materializer and V2 G7 auditor on a successor branch based on the exact audited PR #248 execution lineage after G4/G5 returns.

Historical V1 files remain byte-preserved lineage and must never be edited to become the future authorized path.

The standalone V2 implementation may reuse pure, non-authorizing helper logic only when its custody semantics are explicit and covered by tests. It must not delegate its authorization gate, preflight gate, source authentication gate, or output receipt generation to V1 `main()`.

## 4. V2 preflight binding

Future G6 and G7 must reject the preflight unless all of the following hold:

- receipt schema is exactly `JEPA_TD_RELATIONAL_PREFLIGHT_DRIVER_RECEIPT_V2`;
- status is exactly `PASS_TD_RELATIONAL_PREFLIGHT_DRIVER_VALUE_BLIND`;
- receipt SHA-256 equals the SHA prospectively written into the runtime value authorization;
- `real_value_replay_authorized` is false;
- `training_authorized` is false;
- mapping receipt schema is exactly `JEPA_TD_RELATIONAL_MAPPING_PREFLIGHT_V2`;
- required mapping checks are present and true:
  - `all_35_h5_source_sha256_verified`;
  - `source_files_exactly_hash_bound`;
  - `all_9216_addresses_one_to_one`;
  - `all_sample_A_h5_cell_rows_exact`;
  - `count_arrays_never_opened_by_design`;
- frozen input hashes inside the receipt match the known authorities for Sample-A freeze, provenance, collision ledger, calibration archive, TD archive, Macha freeze, and replay manifest.

No hand-written or stale PASS-only JSON may satisfy the gate.

## 5. V2 runtime authorization contract

A runtime authorization does not exist until explicitly created after owner approval following successful G4/G5 review.

Required runtime schema:

`JEPA_TD_RELATIONAL_VALUE_READ_AUTHORIZATION_V2`

Required authorization token:

`AUTHORIZE_EXACT_TD_SAMPLE_A_9216_CORRECTED_VALUE_MATERIALIZATION_V2_ONLY`

The authorization must bind:

- exact narrow 25,000-cell / 9,216-address scope;
- exact preflight-result SHA-256;
- exact G6 V2 script SHA-256;
- exact G7 V2 script SHA-256;
- exact G6 entrypoint path;
- exact G7 entrypoint path;
- `training_authorized=false`;
- `biological_replay_authorized=false`;
- `target_selection_authorized=false`;
- `td60_authorized=false`.

Historical V1 schema/token must be rejected.

## 6. Immediate source authentication before value access

For each HVS/SEA matrix, V2 G6 must:

1. resolve the source path from the authenticated Macha/S174 freeze;
2. verify file exists and size matches;
3. compute SHA-256 and require exact match to the freeze;
4. only after the hash succeeds, open the H5AD and access its count/value slot;
5. record the verified source SHA in the G6 receipt/manifest.

V2 G7 must independently repeat the same source-file SHA check immediately before its own physical H5AD value read. It must not inherit the fact that G6 or G4/G5 previously hashed the file.

## 7. Raw-value semantics

Every HVS/SEA physical value must be:

- finite;
- nonnegative;
- exactly integer-valued.

Fractional/transformed, NaN, infinite, or negative values stop before normalization. No rounding is permitted.

Whole-cell source-library total must be accumulated from the full physical row before replay-address filtering, preserving the frozen historical normalization contract.

Normalization remains:

`log1p(raw_count * 10000 / verified_whole_cell_library_total)`

## 8. NPH52 boundary

NPH52 remains the authenticated historical clean-path pass-through because it did not share the HVS/SEA positional-axis defect.

V2 must preserve the existing exact historical CSR hashes and TD50 hashes before reading/pass-through.

No new NPH biological reinterpretation is introduced by this design.

## 9. G6 V2 outputs

Future successful G6 must emit V2-only custody objects, including at minimum:

- `JEPA_TD_RELATIONAL_G6_RECEIPT_V2`;
- `JEPA_TD_RELATIONAL_CORRECTED_SAMPLE_A_CACHE_V2`.

The receipt/manifest must record:

- exact preflight receipt SHA;
- exact authorization object or its SHA;
- exact G6 code SHA;
- exact verified source H5AD SHAs used for value reads;
- exact input-authority hashes;
- output cache/meta hashes;
- source-library equality result;
- `biological_replay_authorized=false`;
- `training_authorized=false`.

G6 success terminal remains:

`PASS_TD_G6_SOURCE_LIBRARY_EXACT`

Any source-library mismatch remains a hard stop.

## 10. G7 V2 outputs and semantics

G7 remains an independent cross-lane corroboration against the G1b-authorized S174 cache.

It must:

- authenticate the same exact preflight and runtime authority as G6;
- bind exact G7 code SHA;
- independently hash S174 shards against the G1b freeze;
- require full 41,238-address S174 cache geometry;
- independently hash each physical HVS/SEA H5AD immediately before rereading values;
- use every natural HVS/SEA Sample-A × S174 cell overlap;
- compare all exact 9,216 replay addresses with zero tolerance;
- never manufacture overlap.

V2 schema:

`JEPA_TD_RELATIONAL_G7_S174_OVERLAP_V2`

Terminals:

- `PASS_TD_G7_S174_EXACT_OVERLAP` — process success;
- `STOP_TD_G7_S174_CROSSCHECK_MISMATCH` — non-success;
- `NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP` — non-success and not a PASS.

## 11. Immutable namespace behavior

G6 output namespace must be absent or empty before execution and must never be reused after partial failure.

G7 receipt path must not already exist.

A failure preserves artifacts exactly and requires a new namespace for any later attempt.

## 12. Required tests before implementation can be considered qualified

TDD is mandatory. RED tests must be committed and observed failing before production implementation.

Required behavioral tests include at least:

1. bare/stale PASS-only preflight JSON is rejected;
2. wrong preflight schema is rejected;
3. missing/false required V2 mapping check is rejected;
4. altered preflight receipt SHA is rejected by runtime authority;
5. old V1 runtime schema/token is rejected;
6. wrong G6 or G7 code SHA binding is rejected;
7. wrong entrypoint binding is rejected;
8. `training_authorized != false` is rejected;
9. `biological_replay_authorized != false` is rejected;
10. fractional, NaN, infinite, and negative HVS/SEA raw values are rejected;
11. whole-row library total is computed before mapping filter;
12. same-size but byte-changed H5AD is rejected before value access;
13. exact source SHA is recorded after successful authentication;
14. historical NPH CSR/TD50 hash drift is rejected;
15. G6 emits V2 receipt/cache schemas only;
16. changed S174 shard is rejected;
17. S174 wrong 41,238-column geometry is rejected;
18. G7 fractional/non-finite S174 values are rejected;
19. G7 no-overlap returns non-success;
20. G7 mismatch returns non-success;
21. G7 exact overlap PASS returns success;
22. G7 independently rejects same-size changed physical H5AD before reread.

After focused tests pass, the repository's broader relevant suite must be run and every failure reported. No CI claim may be made unless an actual CI run exists.

## 13. Sequencing

1. Claude/Macha first runs only self-audit-hardened G4/G5 from PR #248 exact execution code freeze `b3ff8366f28280e7d3269c305efa6317a05c8834`.
2. Any G4/G5 failure stops the target-discovery lane.
3. A G4/G5 PASS is reviewed; it does not authorize values.
4. Rebase/reconstruct standalone V2 successor from the exact G4/G5 execution lineage.
5. Run TDD qualification for standalone V2.
6. Only after a separate explicit owner decision may a runtime V2 authorization object be created.
7. If later authorized, run G6 then G7 only.
8. G6 mismatch, G7 mismatch, or G7 NOT_ESTIMABLE stops.
9. Even G6+G7 PASS stops before TD56/TD57B/TD57C/TD59 corrected biological replay.
10. Biological replay requires another explicit owner decision.

## 14. Supersession rule

The first wrapper-based PR #251 implementation is `SUPERSEDED_BY_STANDALONE_V2_DESIGN__DO_NOT_EXECUTE`.

Its findings remain useful historical review evidence, but its current executable files are not future-authorized candidates.

No old authorization template or old V1/V2 wrapper may be promoted by documentation alone.
