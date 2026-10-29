# JEPA V2 shape/content contract split — 2026-10-29

**Classification:** synthetic fixture mechanics only. A new versioned content contract; no retroactive acceptance of #479 or #496 and no real source/rights issuer.

## Reason for split

The immutable V2 author test at #479 explicitly allows a counted base scalar to be changed to 999 if its type and re-signed *shape* are valid. The independently reviewed Macha #481 A1/A2 requires the consumer to refuse this exact kind of falsification because D1 depth must be derived from the base-visible scalar counts and source-bound rights. A single method cannot satisfy both semantics.

- Existing `observation_normalization_view_v2_fixture.py` and its `validate_fixture_observation_view_v2` retain historical shape-only semantics, including the 999 re-signed scalar characterization. The inherited A3 metaclass dispatch fix #495 remains.
- New `observation_normalization_view_v2_bound_content_v1.py` reuses the exact same producer (source-side conservation check) and original V2 shape validator, but changes the published schema to `TD_OBSERVATION_NORMALIZATION_VIEW_V2_BOUND_CONTENT_V1_FIXTURE`, adds a cooperative **process-local** producer-issued rights/query/role binding, checks full address coverage and exact per-cell `D1 = Σ base MEASURED_SCALAR count`, and refuses unissued or forged receipt digests.
- Both have distinct entry points and cannot be confused by schema. The original V2 shape receipt never becomes a content-qualification token.
- No teacher/private hash or physical source total is released in the student payload. No source/data holder, physical nucleus, donor, QC/selection or feature alias is authenticated. A hostile same-process actor can still mutate the fixture map.

## Immutable review reuse

Macha #481 reviewer source is retained byte-identically at Git blob `3dda6c2cc9be19d5daececfb07967e94067519f6` in `tests/v5/td_unified/macha481_review_source_immutable.py` (not pytest-auto-discovered). The original review remains under its original filename on frozen PR #481. Broader repository suites intentionally must not auto-execute expected-RED historical tests on the historical shape-only API. The **new, explicitly named test adapter** binds the original three producer/consumer test functions to the distinct content interface and replays all non-A4 cases, including the 240-world positive noninterference experiment, A1 fake-depth, A2 unauthorized rights/query, and A3 hostile metaclass attacks. This is **not** unmodified #481 on old V2. A4 is excluded by exact test name; it remains RED at upstream #474, unchanged and needs Macha's independent repair and review.

The original V2 author tests execute against the original, unchanged shape entry separately. New arithmetic tests use explicit test-only binding injection to prove refusal of bad depth even if a purported issuer record exists, rather than passing only because the digest was not issued. A passing count is mechanical scope only.

## Future real source and G7 contract

Audit #322 contains `JEPA_D1_D2_DEPTH_INTERFACE_DECISION_20261029.md`: D1 selected only as prospective V2 covariate; D2 rejected as default. The producer must still supply externally authenticated frozen rights/aliases, physically mapped units, donor/specimen/QC provenance, query-independent row selection, and nonleaking zero-base refusal. A future independently reviewed G7 E3 V2 content law must connect source → lawful student/teacher view → bound G7 decision without weakening G7 V1 physical `library_size` constraints.

Unchanged authority:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`.
