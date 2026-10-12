# Gate case-coverage bridge qualification — 2026-10-11

Status: `FROZEN_CASE_COVERAGE_BOUND__GATE_STATUS_INTENTIONALLY_NOT_ADJUDICATED__NO_AUTHORITY`

TDD commits:
- RED test-only: `49eecb7d084bcb3b8719511c0802746c5758fa33`
- GREEN implementation: `46cbfa5a0db37931afa55936d90d5439677474af`

Exact Git blobs:
- `scripts/v5/td_gate_case_coverage.py`: `40a4801a1df2172b18f1ee983570622ccdf903e2`
- `tests/v5/test_td_gate_case_coverage.py`: `9bd3357b9487f518681b9e624d49e0e418f18e62`

Exact result:
`10 passed / 0 failed / 0 errors`

## Purpose

The role-bound prefreeze registry prevents post-freeze family shrinkage, but candidate gate evidence still needs to prove that **every frozen case assigned to that candidate/gate** was actually accounted for.

This helper is coverage-only. Given an untampered prefreeze manifest and per-case evidence receipts, it requires:

- an existing candidate/gate pair in the frozen family;
- exactly the frozen case IDs for that candidate/gate, no missing or extra cases;
- exact candidate, gate, source, analysis-tier and endpoint role agreement for each receipt;
- case status in `PASS`, `FAIL`, `NOT_ESTIMABLE`;
- a syntactically valid evidence SHA-256 for every case;
- unique case receipts;
- intact prefreeze manifest self-hash.

It emits a deterministic `case_evidence_bundle_sha256` over the complete role-matched receipt set and status counts.

## Deliberate non-feature

The helper **does not aggregate case statuses into gate PASS/FAIL**. It emits `gate_status_not_adjudicated=true` and no `pass` field.

This is intentional. Different scientific gates can lawfully have different prospective treatment of source replication and `NOT_ESTIMABLE`; a universal policy would silently invent science. Gate adjudication policy must be separately frozen before outcomes.

## Harness accounting

Previous focused science harness: 82 green.

New independent suite: 10 green.

Current focused synthetic/metadata-only harness:
`92 passed / 0 failed / 0 errors`

## Authority boundary

No biological values, protected outcomes, real tournament execution, target selection, representation selection, corrected replay, Stage4 or training authority is created.

Terminal:
`SYNTHETIC_SCIENCE_HARNESS_92_GREEN__FROZEN_CASE_COVERAGE_BOUND__NO_REAL_VALUE_EXECUTION__NO_TARGET_AUTHORITY`
