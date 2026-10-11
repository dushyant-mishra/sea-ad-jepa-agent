# Donor-resampling dependence guard qualification — 2026-10-11

Status: `METADATA_ONLY_DONOR_DEPENDENCE_GUARD_QUALIFIED__NO_AUTHORITY`

Science branch:
`science/td-target-tournament-scaffold-20261011`

TDD commits:
- RED test-only: `eaaf83bbb5b2f19716cfab8f01b01488dcf7fb7c`
- GREEN implementation: `b61ff24c72729cad824409f5f0a71ae7b9026af7`

Exact Git blobs:
- `scripts/v5/td_donor_resampling_audit.py`: `4a5d0a08d6b1d1bdc4e0c188a909c39e5f0fb195`
- `tests/v5/test_td_donor_resampling_audit.py`: `f736c4b2c876a187bf9edff6a5fac266dcf13e5f`

Exact focused result:
`9 passed / 0 failed / 0 errors`

## What it enforces

Given metadata-only case membership for one source, the helper:

- requires unique case IDs;
- requires unique donor membership within each case;
- rejects mixed-source aggregation;
- reports pairwise donor overlap and Jaccard overlap;
- reports the number of unique biological donor units;
- reports maximum number of case memberships per donor;
- refuses to return an `independent_n_from_case_rows` when any case rows reuse donors;
- labels overlapping case tables `ROBUSTNESS_RESAMPLES_NOT_INDEPENDENT_REPLICATES`;
- even when case memberships are disjoint, labels only `CASE_MEMBERSHIPS_DISJOINT__NO_BROADER_INDEPENDENCE_CLAIM` rather than asserting statistical independence;
- emits all authority flags false.

This directly operationalizes the fresh historical TD57B/TD59 audit finding that split-0 and split-1 case rows repartition the same donor pool and therefore cannot be counted as independent biological replicates.

## Harness accounting

Previously qualified focused science harness:
`67 passed / 0 failed / 0 errors`

New unchanged-independent suite:
`9 passed / 0 failed / 0 errors`

Current focused synthetic/metadata-only harness total:
`76 passed / 0 failed / 0 errors`

No existing production helper or prior test was changed by this addendum.

## Authority boundary

This helper opens no biological values or files and creates no target, representation, corrected replay, Stage4 or training authority.

Terminal:
`SYNTHETIC_SCIENCE_HARNESS_76_GREEN__DONOR_RESAMPLE_DEPENDENCE_EXPLICIT__NO_REAL_VALUE_EXECUTION__NO_TARGET_AUTHORITY`
