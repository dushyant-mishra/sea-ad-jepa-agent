# Prefreeze decision-family registry qualification — 2026-10-11

Status: `ROLE_EXPLICIT_DECISION_FAMILY_REGISTRY_BOUND__POSTFREEZE_FAMILY_SHRINKAGE_REJECTED__NO_AUTHORITY`

TDD sequence:
- RED: `e95fd142b63e23421106c489eb0ec0e82a1cfa92` — inherited prefreeze produced 6 failed / 7 passed under registry attacks.
- GREEN: `3b796d9d96b3b8cbf2499672beabf46d9380471d` — strengthened helper produced 13 passed / 0 failed / 0 errors.

Exact current Git blobs:
- `scripts/v5/td_target_tournament_prefreeze.py`: `24d3041429180eddc2085d3d01e5fcff78f5a951`
- `tests/v5/test_td_target_tournament_prefreeze.py`: `8ca08a78bb64822536fb0b85c24b037ae6c9257f`

## Closed weakness

Previously `decision_family_size = len(decision_cases)`, while each case carried only a free-form `case_id` and donor upper bound. The helper did not bind a case's candidate/gate/source/tier/endpoint role. A case could therefore be deleted or relabeled and the smaller family would silently produce a larger Bonferroni alpha.

The repaired prefreeze requires each case to contain exactly:
- `case_id`;
- `candidate_id`;
- `gate_id`;
- `source`;
- `analysis_tier`;
- `endpoint_id`;
- `available_donors_upper_bound`.

The complete role-explicit case list is canonicalized in case-id order and SHA-256 bound as `decision_family_registry_sha256` **before** family size, effective alpha, donor-resolution floor, or permutation-resolution floor are derived.

The helper now rejects:
- removal after registry freeze;
- role changes after registry freeze;
- duplicate semantic role tuples hidden behind different case IDs;
- missing role fields;
- malformed registry hashes.

The output carries the exact frozen registry SHA and role fields into every case-resolution row.

## Remaining scientific-governance limitation

This repair proves consistency with the supplied frozen registry. It does **not** prove that the initial registry contains every scientifically required decision case. Initial family completeness must be established by a reviewed prospective scientific registry/contract before outcomes. The helper intentionally does not infer missing scientific hypotheses.

## Harness accounting

Previous focused harness: 76 green, including the old 7-test prefreeze suite.

Current prefreeze suite: 13 green, replacing those 7 tests.

Current focused synthetic/metadata-only harness:
`82 passed / 0 failed / 0 errors`

## Authority boundary

No biological values or outcomes are opened. No real tournament, target selection, representation selection, corrected replay, TD60, Stage4, pathology or training authority is created.

Terminal:
`SYNTHETIC_SCIENCE_HARNESS_82_GREEN__DECISION_FAMILY_ROLE_REGISTRY_BOUND__NO_REAL_VALUE_EXECUTION__NO_TARGET_AUTHORITY`
