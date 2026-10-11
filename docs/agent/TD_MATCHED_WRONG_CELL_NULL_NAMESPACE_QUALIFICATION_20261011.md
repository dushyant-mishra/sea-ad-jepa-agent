# Matched wrong-cell null namespace qualification — 2026-10-11

Status: `MATCHED_NULL_DERANGEMENT_PRESERVED__DETERMINISTIC_NAMESPACE_HARDENED__NO_AUTHORITY`

TDD sequence:
- RED: `599438a9c5453976f25d0c77a4d433f1b8e2cf25` — inherited helper produced 4 failed / 6 passed under namespace/schema attacks.
- GREEN: `a3a5dc241a0a602aa6a03ea41413463ee8a234c9` — 10 passed / 0 failed / 0 errors.

Exact Git blobs:
- `scripts/v5/td_target_tournament_nulls.py`: `fb8eab95f22708a7c50e939ff18e597148a30268`
- `tests/v5/test_td_target_tournament_nulls.py`: `fd5e106650e257c4603863550919eb131dea66dc`

## Scientific behavior preserved

The null remains a deterministic within-stratum wrong-cell derangement over the exact frozen stratum:

- donor;
- operator;
- support key;
- depth bin;
- detection bin.

Every source cell maps to a different destination cell. The mapping is a bijection within every stratum. Any singleton stratum remains `NotEstimableStratum`; this repair does not cross strata or relax matching to rescue estimability.

## Closed deterministic-custody weakness

The inherited helper formed PRF preimages using ad-hoc NUL-separated strings and `repr(key)` while seed/cell/stratum values were not type-pinned. This allowed ambiguous or non-portable namespaces under NUL-bearing or mixed-type metadata.

The repaired helper now:

- requires a nonempty NUL-free string seed;
- requires an exact row schema: `cell_id` plus the five stratum keys, no missing/extra fields;
- requires cell ID and every stratum value to be a nonempty NUL-free string;
- rejects duplicate cell IDs with a domain-specific contract error;
- uses versioned canonical JSON arrays as SHA-256 PRF preimages for both cell ranking and cyclic-shift selection;
- sorts validated string-valued stratum keys directly rather than by arbitrary Python `repr`;
- retains the deterministic nonzero circular shift and within-stratum bijection.

The new attacks cover empty/NUL seeds, empty/NUL cell IDs, mixed/non-string stratum metadata, missing/extra row fields, and explicit within-stratum bijection.

## Harness accounting

Previous focused science harness: 96 green, including the old 5-test matched-null suite.

Current matched-null suite: 10 green, replacing those 5.

Current focused synthetic/metadata-only science harness:
`101 passed / 0 failed / 0 errors`

## Authority boundary

This helper operates only on supplied compact metadata rows. It opens no biological files or values and creates no real tournament, target, representation, corrected replay, Stage4 or training authority.

Terminal:
`SYNTHETIC_SCIENCE_HARNESS_101_GREEN__MATCHED_NULL_NAMESPACE_AND_DERANGEMENT_BOUND__NO_REAL_VALUE_EXECUTION__NO_TARGET_AUTHORITY`
