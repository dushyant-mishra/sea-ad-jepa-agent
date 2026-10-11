# TD G6 cache-content validation follow-up — 2026-10-11

Status: `NEW_CUSTODY_FOLLOWUP__G6_PASS_NAMESPACE_BYTE_SELF_CONSISTENCY_IS_NOT_SUFFICIENT`

Audited Macha successor head:
`ee06fe43dbec94085d5a4988a9f497cacd8f3e0b`

Branch:
`fix/td-g6g7-full-custody-successor-20261011`

## What is now correctly closed

At this head the successor materially closes the previously recorded gaps for:

- immutable owner-decision record verification;
- exact PR #259 driver/mapping/replay-manifest physical SHA pinning;
- atomic/exclusive G6 and G7 attempt markers;
- strict integer/no-round semantics;
- duplicate NPH52 and physical CSR/index rejection;
- corrected G6 row semantics: 23,690 HVS/SEA rows physically reread, 1,310 NPH52 rows authenticated historical pass-through, 25,000 rows total;
- G7 prerequisite requiring the exact five-file G6 PASS namespace, same authority trace, exact G6 input-authority hashes, artifact SHA agreement, manifest linkage, start marker, and false downstream-authority flags;
- preserved PR #267 G7 protections through synthetic end-to-end entrypoint tests.

These closures do not authorize a real value read.

## New remaining issue

`load_g6_pass_receipt()` currently authenticates the **bytes and cross-file self-consistency** of the G6 values/meta artifacts, but it does not open those artifacts to validate the materialization geometry they claim to represent.

Current checks include:

- exact five-file namespace;
- receipt/manifest/start-marker authority trace;
- values/meta SHA agreement between receipt and manifest;
- manifest-declared shape `[25000, 41238]`;
- coverage counters and authority hashes.

But the validator does not inspect the actual `TD_RELATIONAL_CORRECTED_SAMPLE_A_9216_VALUES_V2.npz` or `TD_RELATIONAL_CORRECTED_SAMPLE_A_META_V2.npz` contents. Therefore a self-consistent fabricated namespace can bind arbitrary bytes (including a malformed/empty cache) to matching receipt/manifest hashes and satisfy the prerequisite as presently written.

G7's independent S174/physical reread still protects the G7 overlap result itself. The defect is narrower but real: the statement "a genuine valid G6 materialization happened first" is not fully established by the prerequisite.

## Required minimal repair

Test-first on Macha's existing successor branch before final qualification:

1. RED: construct a complete, same-authority five-file G6 PASS namespace whose values/meta hashes are internally self-consistent but whose values NPZ has wrong CSR/shape geometry; `load_g6_pass_receipt()` must currently accept it and the new test must fail.
2. RED: same for malformed metadata geometry / missing required arrays.
3. GREEN: minimally inspect the G6 values NPZ and require a valid CSR payload with exact shape `(25000, 41238)`, internally consistent `data/indices/indptr/shape`, legal index bounds, and exact replay-address storage contract as applicable.
4. GREEN: inspect the G6 meta NPZ and require exactly 25,000 rows for the required arrays used to define the materialization (`source`, `donor`, `operator`, `global_row`, `cell_id`, `source_library`, `detected_historical`, `detected_corrected`), plus exact source counts and unique/expected row identity where available from the bound freeze contract.
5. Bind `stored_replay_addresses == 9216` and any other minimum manifest fields needed to make the cache claim non-vacuous.
6. These checks are prerequisite integrity checks only. G7 must continue to use its independent physical/S174 reread for the overlap comparison; do not substitute G6 cached values into G7.
7. Preserve `NOT_ESTIMABLE` as non-success and preserve all current owner-decision/value-read boundaries.

## Scope boundary

This is a focused custody follow-up. It does not reopen historical science, does not require real corrected values, and does not authorize G6/G7 execution. Synthetic malformed NPZ fixtures are sufficient for RED/GREEN qualification.

Hard terminal remains:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`
