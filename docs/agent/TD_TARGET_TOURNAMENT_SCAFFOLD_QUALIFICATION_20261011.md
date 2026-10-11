# Target-tournament synthetic scaffold qualification — 2026-10-11

Status: `SYNTHETIC_SCAFFOLD_QUALIFIED_LOCALLY__NO_REAL_VALUE_EXECUTION__NO_TARGET_AUTHORITY`

Implementation branch: `science/td-target-tournament-scaffold-20261011`

Qualified implementation/test head before this qualification update:
`19a19a0eebff495baa38791988200340f2db59db`

## Qualified pure helpers

- `scripts/v5/td_target_tournament_scaffold.py`
- `scripts/v5/td_target_tournament_evidence.py`
- `scripts/v5/td_target_tournament_nulls.py`
- `scripts/v5/td_query_information_guard.py`
- `scripts/v5/td_target_tournament_precision.py`
- `scripts/v5/td_target_tournament_prefreeze.py`
- `scripts/v5/td_measurement_noise_fixture.py`

No helper implements a biological target statistic, biological file reader, neural model, or authorization path.

## Preserved TDD sequence

1. Initial scaffold modules absent -> RED; minimal implementation -> 18 passed.
2. Truncated authority maps -> 2 failed / 8 passed; fail-closed repair -> 21 passed.
3. Candidate-specific gate expansion -> 7 failed / 7 passed; repair -> 25 passed.
4. Precision helper absent -> collection RED; implementation -> 32 combined passed.
5. Prefreeze-manifest helper absent -> collection RED; implementation -> 39 combined passed.
6. Identity/support shortcut expansion -> old frozen contract failed broadly (`13 failed / 3 passed`); Q5/L6 repair -> 41 combined passed.
7. Measurement-noise fixture absent -> collection RED; implementation -> 49 combined passed.
8. Measurement PRF namespace attacks -> 2 failed / 8 passed; address/NUL hardening -> 51 combined passed.
9. Gate-evidence manifest helper absent -> collection RED; implementation -> 8/8 evidence tests GREEN.
10. Adjudicator integration tests then failed broadly because the old API accepted naked gate booleans (`18 failed / 3 passed` in the scaffold file). Evidence-manifest binding was implemented minimally.
11. Current complete focused science harness:

`64 passed in 0.07s`

## Gate evidence is now cryptographically bound

A candidate receipt is no longer accepted from gate booleans alone.

For every common and candidate-specific gate, a candidate-specific manifest must contain exactly:

- gate status: `PASS`, `FAIL`, or `NOT_ESTIMABLE`;
- nonempty evidence schema;
- lowercase SHA-256 of the bound evidence artifact.

The manifest must contain the exact required gate set and all authority fields false. The candidate receipt binds the canonical manifest SHA-256. Adjudication verifies:

1. the supplied manifest is structurally valid;
2. its candidate ID and exact gate set match the receipt/contract;
3. its canonical SHA equals the receipt binding;
4. receipt gate booleans exactly equal `status == PASS` from the manifest;
5. the set of supplied evidence manifests exactly equals the set of candidate receipts;
6. altered, missing, mismatched, extra or post-binding evidence fails closed;
7. `NOT_ESTIMABLE` projects to a failed eligibility gate, never a PASS.

This remains a compact evidence-binding layer, not proof that the underlying scientific evidence itself is valid. The underlying evidence artifacts still require their own qualified schemas/executors.

## Scientific shortcut gates

- C2 requires q-count-only and q-address-only defeat plus q-free student/normalization controls.
- C3/C4 require conditional technology-imprint control and identity+support-only baseline defeat.
- C5 remains optional-specialist only and requires independent provenance/circularity control.

## Measurement/noise reference fixture

The fixture provides exact complementary 50/50 same-cell split and nested 25/50/75/100% thinning, with exact count conservation, support preservation, strict nonnegative integer address/count semantics, NUL-free deterministic PRF identities, and no file access. It defines no technology-equivalence margin and is not independent biological remeasurement.

## Static no-value/no-training audit

All seven production helpers use only Python standard-library functionality. Static inspection finds no biological matrix readers, `h5py`, `anndata`, `scanpy`, `torch`, `numpy`, `scipy`, optimizer, or model-fit path.

## Exact SHA-256 identities for evidence-binding artifacts

- `scripts/v5/td_target_tournament_scaffold.py` — `3440ff951b3f6d9fa320d196ce2d1fab61d3c204c452bd4c24ee04d69fd22f72`
- `tests/v5/test_td_target_tournament_scaffold.py` — `d71d6b6158e0b2e62bf9c7f19facc8b99094273011a71d6b5a68e038c4248ea7`
- `scripts/v5/td_target_tournament_evidence.py` — `f97586605d2bbce34c042b4e707ae940daf938b3f8fd418e295f9763ba2e72f6`
- `tests/v5/test_td_target_tournament_evidence.py` — `be530f557533fb8bd1de5718e58f9911c7ecc3cb1c6ec50f36135ffc1fddcadc`

Current measurement fixture identities:

- module — `64357c8f45b22b6b765c761aa7497946a227452251b9aa582b57c3567d090e2b`
- tests — `728ab4ea198d5f93ccb2171fef78f989e037c8c3383faed3add4235712df5c21`

## Limitation

Repository-wide pytest has not run in the reconstructed local harness. Draft PR #275 had no GitHub Actions run at the last check. This is focused synthetic qualification only.

## Authority boundary

No corrected values, raw-count execution, G6/G7, corrected replay, real tournament, target selection, representation selection, TD60, Stage4, pathology, or training are authorized.

Terminal:
`SYNTHETIC_SCIENCE_HARNESS_64_GREEN__GATE_EVIDENCE_MANIFESTS_BOUND__NO_REAL_VALUE_EXECUTION__NO_TARGET_AUTHORITY`
