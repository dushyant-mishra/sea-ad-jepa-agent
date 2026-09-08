# T0 IMMUNE_FRACTION Successor Formula Freeze V1

Status: **EXTERNAL SCIENTIFIC FREEZE — 2026-09-08**

This resolves the V18 prose-only required covariate `donor IMMUNE_FRACTION within op31 MTG`.

## Frozen formula

For every donor in the accepted T0 broad-IMMUNE candidate membership:

`IMMUNE_FRACTION(d) = immune_n_donor(d) / total_op31_reader_fit_n_donor(d)`

where:

- `immune_n_donor(d)` is the exact number of accepted broad-IMMUNE cells for donor `d`, derived from the authenticated accepted T0 membership;
- `total_op31_reader_fit_n_donor(d)` is the exact number of operator-31 MTG reader-fit cells for donor `d`, derived from the authenticated Phase2 Level-4 op31 substrate.

The authenticated Phase2 op31 substrate has independently verified geometry:

- reader_fit: 638,150 cells;
- reader_validation: 173,736 cells, excluded;
- reader_oracle: 121,386 cells, excluded;
- Phase2 materialized op31 substrate: exactly 638,150 cells.

Therefore `all op31 cells in the authenticated Phase2 substrate` and `all reader-fit op31 cells` are the same denominator population for T0.

## Authority semantics

The exact integers are primary:

- `immune_n_donor`
- `total_op31_reader_fit_n_donor`

The floating fraction is derived only at the consumer boundary.

Required production invariants:

- 46 donors;
- exact donor-set equality between numerator and denominator;
- numerator total = 20,804;
- denominator total = 638,150;
- denominator > 0 for every donor;
- `0 < immune_n_donor <= total_op31_reader_fit_n_donor`;
- derived fraction finite and in `(0,1]`;
- no validation/oracle cells;
- no numeric pathology access.

## Scientific role

`IMMUNE_FRACTION` is a mandatory composition-sensitivity nuisance covariate.

It is **not**:

- an eligibility criterion;
- part of `technical_complete`;
- a target-selection variable;
- a donor-exclusion threshold.

## Provenance requirement

A production IMMUNE_FRACTION authority must derive the rows internally from authenticated parent bytes. It may not accept final rows plus detached digest labels.

This is a successor specification resolving an undefined executable input. It does not claim the exact ratio was recovered from frozen V18 code.
