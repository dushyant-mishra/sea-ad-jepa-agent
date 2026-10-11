# 84-cell truth-table structural feasibility audit — 2026-10-11

Status: `STRUCTURAL_FALSIFICATION_ROLE_ONLY__PRIMARY_MATCHED_NULL_NOT_ESTIMABLE`

Source: authenticated `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`, SHA-256 `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`, file `truth_table/FOUNDATION_84_CELL_TRUTH_TABLE_METADATA.csv`.

No expression values were opened for this audit.

## Frozen metadata facts

The table contains:

- 84 cells;
- 54 donors;
- all 42 historical operators;
- HVS 48 cells;
- NPH52 14 cells;
- SEA_AD 22 cells;
- all 84 rows have `in_original_t1 = 0`;
- frozen metadata report `expression_read_before_freeze = false`.

## Matched-null feasibility

The target-tournament primary wrong-cell null is required to preserve at least donor and operator, and in the full design additionally support/depth/detection strata.

On the frozen 84-cell metadata:

- donor × operator × support-fingerprint strata: **83 strata**;
- **82/83 strata are singletons**;
- maximum stratum size is 2;
- only **2/84 cells** belong to a multi-cell donor×operator×support stratum.

Even before adding depth/detection matching, therefore, **82/84 cells have no lawful wrong-cell counterpart that preserves donor and operator**. Adding more matching constraints cannot improve this.

For comparison:

- operator × support-fingerprint gives 42 strata with 2 cells each;
- source × support-fingerprint gives 9 broader strata.

Those broader strata are useful for operator/support structural tests, but relaxing donor preservation to manufacture a primary biological wrong-cell null would violate the frozen tournament design.

## Binding role

The 84-cell set is appropriate for:

- query-information lineage/leakage fixtures;
- support/abstention logic;
- operator/source coverage checks;
- structural mask/measurement-state consistency;
- compact cross-operator falsification;
- deterministic code-path qualification where no donor-matched biological null is claimed.

It is **not** appropriate for:

- the primary donor+operator-preserving matched wrong-cell biological null;
- donor-generalized target promotion;
- source-generalized target promotion by itself;
- estimating rare-event prevalence;
- replacing the full held-out donor populations.

When a primary matched-null analysis encounters these singleton strata, the correct terminal is `NOT_ESTIMABLE` for that analysis. Do not broaden the stratum after seeing this limitation.

## Authority boundary

This role audit creates no value-read, corrected-replay, real-tournament, target-selection, representation, TD60, Stage4 or training authority.

Terminal:
`84_CELL_TABLE_QUALIFIED_FOR_STRUCTURAL_FALSIFICATION_ONLY__DONOR_OPERATOR_MATCHED_NULL_NOT_ESTIMABLE__NO_TARGET_AUTHORITY`
