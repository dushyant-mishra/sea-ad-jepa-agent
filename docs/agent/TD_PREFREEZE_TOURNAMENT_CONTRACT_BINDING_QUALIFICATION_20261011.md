# Prefreeze tournament-contract binding qualification — 2026-10-11

Status: `PREFREEZE_CASE_ROLES_BOUND_TO_FROZEN_TOURNAMENT_CONTRACT__NO_AUTHORITY`

TDD sequence:
- RED: `24d70d3ebd47def890fc86cac3dcfd7cecc1b441` — 4 failed / 13 passed against the role-registry implementation.
- GREEN: `54a04f708fbbe42d7f6f0db60b1b831815c3c337` — 17 passed / 0 failed / 0 errors.

Current production/test Git blobs:
- `scripts/v5/td_target_tournament_prefreeze.py`: `392d2c29f5e0958fd14a5699ab40c66238abde78`
- `tests/v5/test_td_target_tournament_prefreeze.py`: `1b38edb1f470733a8e84f44bde8fb12067205fee`

## Closed weakness

The prior role-registry repair prevented post-freeze case deletion or relabeling, but a role-explicit registry could still name a candidate or gate that did not exist in the actual tournament contract. The helper also accepted a supplied contract SHA without checking it against a contract object.

The repaired helper now requires the full fixture tournament contract object and:

- verifies its canonical SHA-256 equals `tournament_contract_sha256`;
- validates contract schema, fixture-only state and exact false authority mapping;
- validates unique candidate IDs;
- validates the disjoint foundation/specialist partition covers exactly the candidate set;
- validates unique common gates and candidate-specific gate lists;
- requires every decision case candidate to exist in the contract;
- requires every case gate to be either a common gate or a gate explicitly allowed for that candidate.

The RED attacks showed the inherited code accepted:
- a changed contract after its SHA was supposedly frozen;
- an unfrozen candidate ID after rehashing the decision registry;
- a gate belonging to another candidate after rehashing the decision registry;
- and lacked a canonical contract-hash function.

All are now rejected.

## Remaining boundary

The helper proves role validity and consistency with a supplied frozen tournament contract and decision-family registry. It still does not infer whether the initial prospective family omitted a scientifically desirable hypothesis. Initial family completeness remains a scientific-review responsibility before outcomes.

## Harness accounting

Prior focused harness: 92 green, including the 13-test prefreeze suite.

Current prefreeze suite: 17 green, replacing those 13.

Current focused synthetic/metadata-only science harness:
`96 passed / 0 failed / 0 errors`

## Authority boundary

No biological values/outcomes, real tournament execution, corrected replay, target/representation selection, TD60, Stage4, pathology or training authority is created.

Terminal:
`SYNTHETIC_SCIENCE_HARNESS_96_GREEN__PREFREEZE_CONTRACT_AND_DECISION_FAMILY_BOUND__NO_REAL_VALUE_EXECUTION__NO_TARGET_AUTHORITY`
