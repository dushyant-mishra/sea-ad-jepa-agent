# Target-tournament synthetic scaffold qualification — 2026-10-11

Status: `SYNTHETIC_SCAFFOLD_QUALIFIED_LOCALLY__NO_REAL_VALUE_EXECUTION__NO_TARGET_AUTHORITY`

Implementation branch: `science/td-target-tournament-scaffold-20261011`

Current qualified implementation/test head:
`9a13ccc606b21f1c7d23d57bd17731a7969d611f`

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
10. Adjudicator integration then failed broadly because the old API accepted naked gate booleans (`18 failed / 3 passed` in the scaffold file); evidence-manifest binding repair -> 64 combined passed.
11. Gate-schema relabeling self-audit: `f84407709f06554f9990fc0d4d445be55632efb2` added three RED attacks showing that the prior validator accepted generic or wrong-gate `evidence_schema` labels and lacked a gate-specific schema function.
12. `9a13ccc606b21f1c7d23d57bd17731a7969d611f` repaired this minimally by deriving a unique frozen evidence schema from each gate ID and requiring an exact match.

Post-repair affected-suite verification:

`32 passed in 0.05s` — 21 scaffold tests + 11 evidence-manifest tests.

The other 35 focused science-harness tests are unchanged from the prior 64-green qualification. Base-to-head inventory from `19a19a0e...` to `9a13ccc6...` confirms that only the evidence helper, its tests, the scaffold test fixture, and this qualification document changed. Therefore the current focused harness is:

`67 passed / 0 failed / 0 errors`

## Gate evidence is now role-bound as well as hash-bound

A candidate receipt is not accepted from gate booleans alone. For every common and candidate-specific gate, a candidate-specific evidence manifest must contain exactly:

- gate status: `PASS`, `FAIL`, or `NOT_ESTIMABLE`;
- the exact gate-derived evidence schema `JEPA_TD_GATE_EVIDENCE_<GATE_ID>_V1`;
- lowercase SHA-256 of the bound evidence artifact.

The manifest must contain the exact required gate set and all authority fields false. The candidate receipt binds the canonical manifest SHA-256. Adjudication verifies:

1. candidate ID and exact gate set;
2. exact per-gate evidence schema, preventing a hash for one evidence role from being relabeled as another gate;
3. syntactically valid SHA-256 for each evidence artifact;
4. canonical manifest SHA equals the receipt binding;
5. receipt gate booleans exactly equal `status == PASS` from the manifest;
6. supplied manifest candidate set exactly equals candidate receipt set;
7. altered, missing, mismatched, extra, generic-schema, wrong-gate-schema, or post-binding evidence fails closed;
8. `NOT_ESTIMABLE` never projects to PASS.

This remains a compact evidence-binding layer. It does not prove that an underlying evidence artifact is scientifically valid; each evidence artifact still needs its own qualified executor/schema.

## Scientific shortcut gates

- C2 requires q-count-only and q-address-only defeat plus q-free student/normalization controls.
- C3/C4 require conditional technology-imprint control and identity+support-only baseline defeat.
- C5 remains optional-specialist only and requires independent provenance/circularity control.

## Measurement/noise reference fixture

The fixture provides exact complementary 50/50 same-cell split and nested 25/50/75/100% thinning, with exact count conservation, support preservation, strict nonnegative integer address/count semantics, NUL-free deterministic PRF identities, and no file access. It defines no technology-equivalence margin and is not independent biological remeasurement.

## Static no-value/no-training audit

All seven production helpers use only Python standard-library functionality. Static inspection finds no biological matrix readers, `h5py`, `anndata`, `scanpy`, `torch`, `numpy`, `scipy`, optimizer, or model-fit path.

## Exact current Git identities for gate-schema hardening

Qualified head:
`9a13ccc606b21f1c7d23d57bd17731a7969d611f`

- `scripts/v5/td_target_tournament_evidence.py` Git blob: `131b8e89997f7e13262d2a7745f990f4a00b377b`
- `tests/v5/test_td_target_tournament_evidence.py` Git blob: `2f638f19cd2361f998e79802c17a75019b04611b`
- `tests/v5/test_td_target_tournament_scaffold.py` Git blob: `3457787a6bc1f17ed4a3a9bad95f60370a3f9409`

The production scaffold itself did not change in this hardening cycle.

## Limitation

Repository-wide pytest has not run in the reconstructed local harness. Draft PR #275 had no GitHub Actions run at the last check. This is focused synthetic qualification only.

## Authority boundary

No corrected values, raw-count execution, G6/G7, corrected replay, real tournament, target selection, representation selection, TD60, Stage4, pathology, or training are authorized.

Terminal:
`SYNTHETIC_SCIENCE_HARNESS_67_GREEN__GATE_EVIDENCE_ROLE_AND_HASH_BOUND__NO_REAL_VALUE_EXECUTION__NO_TARGET_AUTHORITY`
