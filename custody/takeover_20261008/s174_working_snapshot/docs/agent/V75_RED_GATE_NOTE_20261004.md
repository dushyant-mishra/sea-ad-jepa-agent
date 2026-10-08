# V75 RED gate note — 2026-10-04

The branch is intentionally left in a RED pre-repair state before importing the V73 protections.

Expected deciding failures before repair:

1. `tests/test_v73_population_geometry_authority.py::test_2k_smoke_preserves_all_feasible_operator_support` — V74 calibration-closure semantics realize only 36/42 operators at 2K.
2. `tests/test_v75_fragment_byte_linkage.py` — the independent fragment byte-linkage validator is absent from V74 and must be restored from the audited V73 stress-twin implementation.

The empirical-QC mutation test is a characterization/causal-consumption test of existing V74 behavior and is expected to pass if the observer truly consumes the QC distribution.

No production repair should be described as qualified until hosted CI demonstrates the expected RED state first and the subsequent exact-head GREEN state after repair.
