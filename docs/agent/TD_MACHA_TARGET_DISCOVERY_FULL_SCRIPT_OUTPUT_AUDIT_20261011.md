# Full Macha target-discovery script/output audit — 2026-10-11

Status: `AUDIT_COMPLETE__PR259_G4G5_PASS_RETAINS_NARROW_VALIDITY__G6_G7_SUCCESSOR_NOT_QUALIFIABLE`

Hard terminal remains:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Scope

This audit independently reviewed the Macha/canonical-machine target-discovery evidence and executable surfaces that currently control or feed the corrected TD56–TD59 replay lane:

- S174 upstream repair authority: `scripts/v77/rebuild_s174_train_cache.py`, `probe_v77_s174_cache_axis.py`, `gate_s174_g1b.py`, and their freeze/build/G1b outputs;
- replay-manifest builder: `scripts/v5/build_td_relational_replay_manifest.py`;
- G4/G5 value-blind mapping/driver: `scripts/v5/audit_td_relational_replay_mapping_preflight.py`, `run_td_relational_replay_preflight.py`;
- superseded V1 value path: `materialize_td_relational_corrected_sampleA.py`, `audit_td_relational_g7_s174_overlap.py`;
- standalone V2 value path: `td_relational_value_read_v2_common.py`, `materialize_td_relational_corrected_sampleA_v2.py`, `audit_td_relational_g7_s174_overlap_v2.py`;
- focused tests and real-PR259 compatibility test;
- execution/qualification outputs PR #245, #252, #254, #259, #266;
- implementation lineage PR #258 → #263 → #267 → #268.

Bayesian/V79 work is authority-separate and was not used to upgrade target-discovery conclusions.

## Executive ruling

### PR #259 remains a valid narrow G4/G5 value-blind technical/data-integrity PASS

Nothing in this audit shows that PR #259 opened corrected expression/count arrays or that its 35-file byte custody, 34-matrix Sample-A mapping, 9,216-address mapping, or exact cell-row checks were falsely reported. The driver and mapping scripts are consistent with the receipt semantics. The execution log's `16 passed, 1 skipped` is accurately reported, and the real driver subsequently exercised the exact external archives and exact physical source hashes.

PR #259 still does **not** establish corrected biological recurrence and creates no value-read/training authority.

### PR #267/#268 are not canonically qualifiable as the future value path

The previously identified G7 concurrent-start race is real, but it is not the only remaining blocker. This audit finds additional independent custody/authorization defects. Atomic G7 marker creation alone is insufficient.

## Findings

### F1 — HIGH — runtime authorization gate does not verify an immutable owner-decision record

`td_relational_value_read_v2_common.py::load_runtime_authorization()` validates schema/token/scope, false downstream-authority booleans, receipt hashes supplied by the runtime authorization, and implementation/code identities. It does **not** accept, hash, parse, or verify an owner-decision record.

This directly fails the already-frozen rule in `TD_VALUE_AUTH_OWNER_DECISION_BINDING_AUDIT_20261010.md`, which requires the runtime authorization to bind and the runtime gate to verify:

- `owner_decision_record_sha256`;
- a dedicated owner-decision schema;
- exact decision `AUTHORIZE_G6_G7_INTEGRITY_ONLY`;
- exact audited PR #259 driver/mapping SHAs;
- exact qualified implementation commit;
- false biological replay / target selection / TD60 / training flags.

The current common-module test helper `valid_auth()` also constructs a passing authorization with no owner-decision fields, confirming this is an implemented schema omission rather than merely missing documentation.

**Consequence:** no current V2 implementation head may execute G6/G7 under the frozen governance contract even after ordinary engineering tests pass.

### F2 — HIGH — runtime code does not itself pin the exact accepted PR #259 physical receipt SHAs

The common module computes SHA-256 of whatever preflight/mapping paths are supplied and checks that the runtime authorization contains those computed values. `load_bound_preflight()` then checks receipt semantics/frozen input hashes against the SHA values passed to it.

The exact accepted physical PR #259 receipt SHAs are:

- driver `PREFLIGHT_RESULT.json`: `62f2af4a97ce77c72907992dff673dcdea74ac17bcd080bd4d77d39e483e8bae`;
- mapping `TD_RELATIONAL_MAPPING_PREFLIGHT.json`: `6a97cb30ae1899fa249e2d4b6d292ed900283cc3c434749688de99a9cd8828e0`.

Those exact physical values are not hard-required by the runtime gate. The separate test `test_td_relational_pr259_real_receipt_compat.py` positively proves the exact PR #259 bytes are accepted, but it does not make the runtime gate reject a separately serialized semantically equivalent V3 pair if a matching authorization JSON is fabricated.

**Consequence:** the frozen requirement that future authority bind the exact CRLF-containing PR #259 physical bytes is not yet enforced in production code. This should be closed together with F1 by verifying the exact values from the immutable owner-decision record.

### F3 — HIGH — G6 execution-start marker is also concurrency-vulnerable for an already-existing empty namespace

`materialize_td_relational_corrected_sampleA_v2.py::begin_namespace()` checks that the output directory is empty, creates it only if absent, checks `G6_EXECUTION_START.json` does not exist, then writes it with ordinary `write_text()`.

When the output directory already exists and is empty, two concurrent starters can both pass the emptiness/marker checks and both write the marker. The current test is sequential only.

**Consequence:** the same single-spend defect found in G7 exists independently in G6. A corrected successor needs atomic exclusive marker creation and a deterministic concurrent single-winner regression for G6 as well as G7.

### F4 — HIGH — G7 attempt marker concurrent-start race

PR #267 `begin_g7_attempt()` checks `out.exists()` / `marker.exists()` and then writes the marker normally. Two concurrent launches can both observe absence and both proceed. This was deterministically reproduced and PR #268 currently contains a RED regression proving exactly-one-winner semantics are absent.

**Consequence:** PR #267 remains `DO_NOT_QUALIFY__DO_NOT_EXECUTE`; PR #268's test is valid but atomic G7 repair alone would still leave F1–F3 unresolved.

### F5 — MEDIUM/HIGH custody — G7 accepts an under-specified G6 PASS receipt

`load_g6_pass_receipt()` verifies schema, `PASS_TD_G6_SOURCE_LIBRARY_EXACT` status, exact authority trace, and false downstream-authority booleans. It does not validate the G6 receipt's `input_authority_hashes`, output values/meta hashes, materialized-cache manifest linkage, execution-start marker, row/coverage fields, or other execution evidence. A fabricated minimal PASS receipt with a matching authority trace can satisfy this gate.

G7 independently rereads physical/S174 values, so this does not by itself fabricate a G7 match; however it weakens the explicit claim that G7 requires a **genuine same-authority G6 PASS execution**.

**Required successor:** validate the complete minimum G6 receipt contract and bind it to the spent G6 namespace/materialized artifacts before G7 begins.

### F6 — MEDIUM upstream numerical-assumption gap — S174 builder/probe/G1b round physical count values

The upstream S174 repair builder uses `int(round(float(v)))` for physical H5AD values. The independent probe and G1b gate likewise round physical values before exact comparisons. Thus G1b proves exact equality to a **rounded physical reread**, not that the source slot itself was finite, nonnegative, and exactly integer-valued.

The later V2 G6/G7 code correctly implements `strict_raw_integer()` and explicitly forbids rounding.

No evidence found in this audit shows that the actual HVS/SEA source values were fractional; therefore this does **not** revoke the existing S174 G1b result or PR #259's value-blind result. It is nevertheless an untested assumption in the upstream raw-count authority.

**Required before relying on S174 raw values for target-discovery G7:** preserve strict finite/nonnegative/integer validation on the relevant S174 payloads and physical overlap rows. The current V2 G7 already does this for loaded overlap shards/rows.

### F7 — MEDIUM reporting precision — G6 receipt overstates independently reverified source-library rows

V2 G6 rereads HVS/SEA physical rows (23,690 Sample-A rows) and checks whole-row raw library totals against TD50. NPH52's 1,310 rows are an authenticated historical pass-through and their library totals are copied from historical TD50 rather than independently reread from a corrected physical source.

The receipt nevertheless reports `source_library_exact_rows = 25000`. This is too broad if interpreted as 25,000 independently physical-reread rows.

**Recommended receipt split:** report physical-reread exact rows (23,690), authenticated NPH52 pass-through rows (1,310), and total covered rows (25,000) separately.

### F8 — LOW/MEDIUM defense-in-depth — NPH52 historical CSR row conversion does not reject duplicate indices locally

`nph_historical_row()` converts historical CSR entries into a dictionary. Duplicate address indices would overwrite earlier values. Separate project audit evidence reports zero duplicate CSR-index rows for NPH52 Sample A and the exact historical CSR bytes are hash-bound, so this is not evidence of an actual corruption in the accepted bytes. The value-path script should nevertheless reject duplicates directly rather than relying on an external audit.

### F9 — LOW provenance completeness — TD57C panel 1 manifest is prospectively derivable but not independently cross-checked to a historical result artifact

`build_td_relational_replay_manifest.py` validates TD57C panel 0 against `td57c_p0_hvs.json`. It constructs TD57C panel 1 from the same frozen TD56 SHA-ranked common-core positions but does not open a panel-1 TD57C historical result file. The historical fixture ledger contains only TD57C P0 HVS because the frozen sequential screen failed at P0 and stopped before P1.

The P1 positions themselves are independently frozen in `TD57C_PROSPECTIVE_SCREEN.md` (Z 4608–5119, X 5120–5631, Y 5632–6143), so the generated addresses are not post-outcome inventions. The builder's phrase `PASS_EXACT_HISTORICAL_RELATIONAL_REPLAY_MANIFEST` should be interpreted as reconstructing the exact prospective experiment definition, not as proving a nonexistent historical P1 execution output.

A stronger builder could bind the exact prospective-screen/executor identity explicitly.

## Superseded V1 scripts

The V1 scripts in `scripts/v5/` must remain permanently non-executable historical code:

- `materialize_td_relational_corrected_sampleA.py` selects literal `sample == "A"` instead of `A_NATURAL_MIXTURE`, uses rounding for raw values, has materially weaker value-authorization binding, and only size-checks physical H5ADs immediately before opening them;
- `audit_td_relational_g7_s174_overlap.py` inherits the V1 materializer defects, does not require a same-authority G6 PASS, lacks later immediate-use/duplicate protections, and returns process exit 0 for `NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP`.

No current authority should ever point to these V1 entrypoints.

## Output-by-output adjudication

- PR #245: `PASS AS FAILURE EVIDENCE.` The reported Windows CRLF manifest serialization failure is consistent with the preserved record. It stopped before G4/G5 mapping and created no value-read authority/result.
- PR #252: `PASS AS FAILURE EVIDENCE.` The literal-`A` Sample-A geometry failure occurred before H5AD/value access. The post-hoc diagnosis correctly identified both the label defect and latent 34-vs-35 custody conflation.
- PR #254: `PASS AS INDEPENDENT FAILURE REPRODUCTION.` It reproduced the same failure without upgrading authority.
- PR #259: `ACCEPTED NARROW PASS RETAINED.` The committed record accurately limits itself to value-blind G4/G5 technical/data-integrity. Exact receipt bytes remain frozen. No biological claim is supported.
- PR #266: `PASS AS FAILED-QUALIFICATION EVIDENCE.` The `29 passed / 1 failed / 0 skipped` result and STOP are accurately represented; the failure was assertion wording after the gate correctly refused a failed G6 receipt. Compatibility/value steps were correctly not run afterward.
- PR #267: `BLOCKED.` Counterpart-auth ordering is improved, but G7 start is non-atomic and F1–F3/F5 remain.
- PR #268: `VALID RED TEST ONLY__NOT A COMPLETE REPAIR PLAN.` The concurrent G7 single-winner regression is useful and should be retained. Its current scope is insufficient because F1–F3/F5 were not yet represented when the PR was opened.

## Required engineering successor before any canonical qualification

A new or expanded successor must be test-first and must, at minimum:

1. require and cryptographically verify an immutable owner-decision record in the runtime authorization gate;
2. enforce exact audited PR #259 driver/mapping physical SHAs through that decision/authorization chain;
3. make G6 execution-start creation atomic/exclusive and prove exactly one concurrent winner;
4. make G7 attempt-start creation atomic/exclusive and prove exactly one concurrent winner;
5. strengthen G7's G6 PASS receipt validation to a complete minimum receipt/materialization contract;
6. add local duplicate-index rejection for NPH52 historical CSR rows;
7. correct G6 receipt wording/count fields so physical reread versus authenticated pass-through are explicit;
8. preserve strict raw integer semantics in V2; do not reintroduce S174-style rounding;
9. retain all existing PR #267 protections (physical counterpart auth before S174 count load, immediate S174 reauth, duplicate S174 cell/CSR rejection, G1b exact authority, zero-tolerance 9,216-address cross-check, mismatch/NOT_ESTIMABLE non-success semantics for qualification).

Then rerun the canonical focused suite plus exact physical PR #259 real-receipt compatibility test from a fresh worktree. A PASS still stops at the explicit owner-decision boundary; it does not itself authorize value reading.

## Final audit terminal

`PR259_G4G5_VALUE_BLIND_PASS_RETAINED__PR267_BLOCKED__PR268_RED_TEST_RETAINED_BUT_SCOPE_INCOMPLETE__G6_G7_NOT_QUALIFIABLE__NO_VALUE_AUTHORITY__NO_CORRECTED_BIOLOGICAL_REPLAY__NO_TRAINING`
