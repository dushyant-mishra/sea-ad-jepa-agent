# TD G6/G7 Standalone V2 with V3 Preflight Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an unexecuted, fail-closed standalone G6/G7 V2 value-path candidate that can only consume the repaired PR #255 V3 preflight contract and a later exact owner authorization.

**Architecture:** Preserve historical V1 scripts unchanged. Add a small shared V2 custody module for exact receipt/authorization/code/source authentication, then add standalone G6 V2 and G7 V2 entrypoints that own their authorization gates, source hashing, raw-value semantics and V2 receipts. G6/G7 must remain unusable without a separately created runtime authorization after a reviewed V3 G4/G5 PASS.

**Tech Stack:** Python 3.9-compatible stdlib, NumPy, pandas, h5py, scipy sparse, pytest.

**Spec:** `docs/superpowers/specs/2026-10-10-td-g6-g7-standalone-v2-design.md` plus controlling amendment `docs/superpowers/specs/2026-10-10-td-g6-g7-standalone-v2-v3-preflight-amendment.md`.

## Global Constraints

- Historical V1 G6/G7 files are never modified into the future path.
- Accept only `JEPA_TD_RELATIONAL_PREFLIGHT_DRIVER_RECEIPT_V3` + `JEPA_TD_RELATIONAL_MAPPING_PREFLIGHT_V3`.
- Frozen Sample A is `A_NATURAL_MIXTURE`, 25,000 cells; HVS 1,129 / NPH52 1,310 / SEA_AD 22,561.
- V3 mapping evidence must prove 34/34 Sample-A H5 mapping plus 35/35 S174 source custody.
- Runtime authorization schema/token are V2-only and bind exact preflight/mapping receipt SHAs, exact G6/G7 script SHAs and exact entrypoints.
- HVS/SEA raw values must be finite, nonnegative, exactly integer-valued; no rounding.
- Each physical H5AD must be SHA-authenticated immediately before value access independently in G6 and G7.
- NPH52 is exact historical pass-through after frozen CSR/TD50 hash checks.
- G7 `NOT_ESTIMABLE` is non-success.
- No execution authority, biological replay authority, target authority, TD60 authority or training authority is created by implementation/tests.

## Review Focus

- A syntactically valid but stale V2 preflight PASS must fail before value access.
- A same-size byte-modified physical H5AD must fail before its value slot is opened in both G6 and G7.
- A fractional value such as 1.5 must fail rather than round; NaN/inf/negative must also fail.
- A runtime authorization bound to the wrong script SHA/entrypoint must fail even if all other fields are valid.
- G7 zero natural overlap must write a truthful receipt and return nonzero.

---

### Task 1: Shared V2 custody gate

**Files:**
- Create: `scripts/v5/td_relational_value_read_v2_common.py`
- Test: `tests/v5/test_td_relational_value_read_v2_common.py`

**Interfaces:**
- Produces: `sha256_file(path)`, `load_bound_preflight(preflight_path, mapping_path, auth)`, `load_runtime_authorization(path, expected_g6_path, expected_g7_path, actual_g6_sha, actual_g7_sha)`, `verify_source_file(path, source_rec)`, `strict_raw_integer(value)`.
- Consumes: V3 driver/mapping receipt JSON plus later V2 runtime authorization JSON.

- [ ] Write failing tests for stale/bare PASS, wrong V3 schema, each missing required mapping check, wrong receipt SHA, V1 token/schema, wrong G6/G7 SHA, wrong entrypoint, and any authority boolean not exactly false.
- [ ] Run the focused common-module test file and observe RED failures because module/functions do not exist.
- [ ] Implement the minimal common module with exact known frozen authority hashes and V3 check names from the amendment.
- [ ] Add failing tests for same-size byte change and strict raw values (fractional/NaN/inf/negative rejected; exact integer floats accepted).
- [ ] Implement exact source SHA verification and strict raw integer conversion without rounding.
- [ ] Run `python -m pytest -q tests/v5/test_td_relational_value_read_v2_common.py` and require 0 failures.

### Task 2: Standalone G6 V2 materializer

**Files:**
- Create: `scripts/v5/materialize_td_relational_corrected_sampleA_v2.py`
- Test: `tests/v5/test_materialize_td_relational_corrected_sampleA_v2.py`

**Interfaces:**
- Consumes Task 1 common gates.
- Produces V2-only cache manifest schema `JEPA_TD_RELATIONAL_CORRECTED_SAMPLE_A_CACHE_V2` and receipt schema `JEPA_TD_RELATIONAL_G6_RECEIPT_V2` with terminal `PASS_TD_G6_SOURCE_LIBRARY_EXACT` only on exact source-library agreement.

- [ ] Write failing tests proving literal `A` is not used, `A_NATURAL_MIXTURE` geometry is exact, output namespace is immutable, and historical V1 authority cannot enter.
- [ ] Run focused G6 V2 tests and observe RED.
- [ ] Implement independent input loading and exact authority validation; pure mapping helpers may be copied from historical V1 but authorization/output logic must be V2-owned.
- [ ] Write failing tests proving whole-row library total is computed before replay filtering, fractional/non-finite/negative values fail, and a changed same-size H5AD is rejected before value access.
- [ ] Implement immediate physical H5AD SHA verification before opening the value slot and strict raw-count decoding.
- [ ] Write failing tests for NPH historical CSR/TD50 hash drift and V2-only output schemas/receipt fields.
- [ ] Implement NPH exact pass-through, V2 receipt/cache hashes, verified source SHA ledger, exact preflight/auth/code bindings, and all authority booleans false.
- [ ] Run `python -m pytest -q tests/v5/test_materialize_td_relational_corrected_sampleA_v2.py tests/v5/test_td_relational_value_read_v2_common.py` and require 0 failures.

### Task 3: Standalone G7 V2 cross-check

**Files:**
- Create: `scripts/v5/audit_td_relational_g7_s174_overlap_v2.py`
- Test: `tests/v5/test_audit_td_relational_g7_s174_overlap_v2.py`

**Interfaces:**
- Consumes Task 1 common gates and the frozen inputs; does not depend on G6 execution success as authority.
- Produces schema `JEPA_TD_RELATIONAL_G7_S174_OVERLAP_V2`.

- [ ] Write failing tests for changed S174 shard, wrong 41,238-column geometry, fractional/non-finite S174 values, zero overlap non-success, mismatch non-success, exact-overlap success, and same-size changed physical H5AD rejection before reread.
- [ ] Run focused G7 V2 tests and observe RED.
- [ ] Implement independent G1b shard authentication, geometry checks and strict S174 integer semantics.
- [ ] Implement immediate physical H5AD SHA verification before every G7 value reread, exact 9,216-address zero-tolerance comparison, and no-manufactured-overlap behavior.
- [ ] Implement process exits: PASS=0, mismatch=2, NOT_ESTIMABLE=3.
- [ ] Run `python -m pytest -q tests/v5/test_audit_td_relational_g7_s174_overlap_v2.py tests/v5/test_td_relational_value_read_v2_common.py` and require 0 failures.

### Task 4: Cross-entrypoint authorization/code binding

**Files:**
- Modify: `scripts/v5/td_relational_value_read_v2_common.py`
- Modify tests from Tasks 1-3.

**Interfaces:**
- Produces one exact runtime-authority validator used identically by both entrypoints.

- [ ] Add tests where G6 is valid but G7 code SHA/path is wrong and vice versa; both entrypoints must refuse before source/value access.
- [ ] Add test that changing the V3 mapping receipt bytes while leaving semantic JSON unchanged invalidates authority by SHA.
- [ ] Run affected focused tests and observe RED if any binding is not enforced.
- [ ] Implement/fix only the missing binding behavior.
- [ ] Run all three focused V2 test files plus common tests and require 0 failures.

### Task 5: Qualification documentation and execution firewall

**Files:**
- Create: `docs/agent/TD_G6_G7_STANDALONE_V2_QUALIFICATION_20261010.md`
- Create: `custody/target_discovery/TD_G6_G7_STANDALONE_V2_CANDIDATE_STATE_20261010.json`

**Interfaces:**
- Records exact candidate code SHAs/test commands and explicitly states no runtime authorization exists.

- [ ] Document that #255 V3 G4/G5 PASS is a prerequisite and that candidate code remains non-executable without a later owner authorization object.
- [ ] Record exact entrypoint paths, required runtime schema/token, V3 schemas/checks, and all stop conditions.
- [ ] Run the complete relevant suite: `python -m pytest -q tests/v5/test_td_relational_value_read_v2_common.py tests/v5/test_materialize_td_relational_corrected_sampleA_v2.py tests/v5/test_audit_td_relational_g7_s174_overlap_v2.py tests/v5/test_audit_td_relational_replay_mapping_preflight.py tests/v5/test_run_td_relational_replay_preflight.py`.
- [ ] Record actual pass/fail/skip counts; do not claim CI unless a real CI run exists.
- [ ] Compare branch against its #255 base and verify historical V1 scripts are unchanged.

## Completion boundary

Implementation completion does not create execution authority. Before any G6/G7 execution, #255 must have a reviewed V3 G4/G5 PASS, the standalone branch must be reconciled to that exact accepted lineage, focused qualification must be green, and the owner must separately authorize creation of the exact V2 runtime authorization object.
