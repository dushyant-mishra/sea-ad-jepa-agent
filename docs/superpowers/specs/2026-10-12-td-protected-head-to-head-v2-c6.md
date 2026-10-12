# Protected target head-to-head V2 — C6 extension

Status: prospective design freeze only. No biological execution, target selection, representation selection, TD60, Stage 4, or training authority.

## Purpose

V2 preserves the complete protected comparison law from head-to-head V1 and prospectively extends the foundation candidate lattice with `C6_SHARED_QUERY_COMPOSITE` before corrected biological outcomes are opened.

## Foundation component sets

- `C1_SHARED_EMERGENT`: `{SHARED}`
- `C2_RELATIONAL_SHARED`: `{SHARED, RELATIONAL}`
- `C3_QUERY_MEASURED`: `{QUERY}`
- `C6_SHARED_QUERY_COMPOSITE`: `{SHARED, QUERY}`
- `C4_STRUCTURED_COMPOSITE`: `{SHARED, RELATIONAL, QUERY}`

Structural simplicity is defined only by strict subset of these component sets. Therefore C1 and C3 are each simpler than C6; C6 is simpler than C4; C2 and C6 are incomparable by complexity.

## Protected dimensions and statuses

Every pair reports exactly the same seven dimensions frozen in V1:

1. `BIOLOGICAL_INFORMATION`
2. `DONOR_TRANSFER`
3. `SOURCE_TRANSFER`
4. `SHORTCUT_RESISTANCE`
5. `COVERAGE_ABSTENTION`
6. `UNCERTAINTY_BEHAVIOR`
7. `MEASUREMENT_ROBUSTNESS`

Each dimension is exactly one of `BETTER`, `NONINFERIOR`, `WORSE`, `NOT_ESTIMABLE` for candidate A relative to candidate B.

## Dominance law

- No `WORSE` or `NOT_ESTIMABLE` and at least one `BETTER` -> A dominates B.
- At least one `WORSE` and no `BETTER` -> B dominates A.
- Both `BETTER` and `WORSE` across dimensions -> incomparable.
- Any `NOT_ESTIMABLE` -> pair unresolved.
- All dimensions `NONINFERIOR` -> only the strict component-subset simplicity rule may break the tie.
- No aggregate score, rank sum, average, or post-hoc weighting may replace these rules.

## Multi-candidate terminal law

A candidate is a unique head-to-head leader only if it dominates every other surviving foundation candidate under complete pairwise evidence.

- unique dominator -> `UNIQUE_HEAD_TO_HEAD_LEADER__PROTECTED_CONFIRMATION_REQUIRED__NO_TARGET_AUTHORITY`
- complete estimable evidence but no unique dominator -> `MULTIPLE_QUALIFIED_TARGETS__INCOMPARABLE__NO_TARGET_AUTHORITY`
- any missing pair or unresolved pair -> `HEAD_TO_HEAD_UNRESOLVED__NO_TARGET_AUTHORITY`

C5 remains outside the foundation head-to-head. A C6 leader still requires protected confirmation and does not become a target winner automatically.

## Authority boundary

This design and adjudicator are metadata-only. They cannot authorize value reads, corrected replay, target selection, representation selection, TD60, Stage 4, or training.
