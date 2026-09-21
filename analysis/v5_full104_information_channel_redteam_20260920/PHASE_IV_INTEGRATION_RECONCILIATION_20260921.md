# Phase IV integration reconciliation — 2026-09-21

Scope: pre-outcome only.

No Audit-B N1 burden result, terminal masking result, P1/P2/P3/P4 selection,
D_shared result, pathology-adaptive decision, DEV/SEALED expression, G5 margin,
terminal target panel, or training result was opened.

## Claude PR #39 audit

Reviewed exact Claude head:

`885c307583f9a773aebe2f9acf9885bbce30473c`

Its two path-triggered hosted workflows were green. The absence of the other two
V5 workflows is expected because PR #39 no longer touched their path filters.

Accepted into the integration lane:

- the real FULL104 Phase-I V2 qualification receipt;
- the reference Phase-III V2 fixes for:
  - absent required groups,
  - empty evidence,
  - materially negative sums-of-squares;
- the adversarial parity tests proving the reference and integrated contracts
  agree on those edge cases.

Not adopted unchanged:

- PR #39's execution-contract red-team assumption that changing
  `precision_scope_id` to a resolved value can make V1 execution-ready.

The integration lane intentionally uses a stronger rule:

`AUDIT_B_EXECUTION_CONTRACT_V1 = PREEXECUTION_ONLY`

V1 cannot represent a resolved precision scope and can never authorize N1.
Any scientific resolution requires a provenance-bearing successor contract.

## B1 — heavy artifact qualification: CLOSED

Real artifact:

`core_sufficient_statistics_v1.npz`

SHA-256:

`f77dff47df71e2b97895f6e850db4d2a2ebdab441d195dedf91f582b4d53b5ae`

Real V2 receipt:

`analysis/v5_full104_information_channel_redteam_20260920/evidence/phase_i/HEAVY_SUFFICIENT_STATISTICS_QUALIFICATION_V2.json`

PASS:

- 4,553,407 rows;
- 104 donors;
- 17,186 strict-core addresses;
- all 104 donor source-library totals agree;
- complete per-cell source vector agrees;
- three-route source-library total = 122,517,308,792;
- failures = [].

The external-artifact ledger now records V2 as the current reuse qualification.

## Phase-III evidence contract: reconciled

The integrated V2 contract and Claude reference V2 now agree on the additional
red-team edge cases:

1. absent required source cannot silently disappear;
2. empty evidence cannot become ESTIMABLE NaN;
3. materially negative SS is INVALID_NUMERIC rather than NON_VARIABLE.

No P1/P2/P3/P4 terminal rule is selected.

## Audit-B preexecution hardening added

### Scientific-resolution provenance

`audit_b_scientific_resolution_v1.py`

A future scientific decision must record:

- parent preexecution-contract digest;
- resolver identity;
- UTC resolution time;
- rationale;
- resolved precision scope;
- target aggregation / weighting;
- zero-mean RSE rule;
- explicit pre-outcome attestations.

No resolution record has been created.

### Held-out donor integrity

`measure_plan_burden` now requires the complete authenticated held-out donor set
for the requested fold. Training-side donors and partial held-out subsets are
refused before burden arithmetic.

### Plan/rung integrity

Before burden arithmetic the estimator verifies:

- rung is one of 5/10/15/20/30/50%;
- mask cardinality matches exact floor arithmetic on the non-target universe;
- every policy mask contains the target;
- UNIFORM equals the common-random base;
- declared ADDED/DROPPED sets equal actual mask differences;
- swaps preserve exact cardinality.

### Target aggregation integrity

A target-level source-balanced statistic requires the complete expected donor set
exactly once. Missing, duplicate, or unexpected donors are refused.

### Zero-mean RSE

The original sample freeze does not specify how undefined zero-mean RSE affects
sample-size escalation. Therefore zero-mean RSE now produces:

`STOP_ZERO_MEAN_RULE_UNRESOLVED`

It cannot silently trigger N2/N3.

### RNG V3 free-string closure

`MaskingRngReplayAuthorityV3.derive_seed()` now accepts only fixed masking RNG
namespaces:

- COMMON_RANDOM_BASE_MASK
- PREFIX3_INNER_GROUPING
- MASK_REMOVAL_ORDER

Arbitrary caller-derived strings, including panel- or policy-dependent content,
are refused. Only outer folds 0..3 are accepted.

### Original sample-freeze runtime binding

The execution preflight now re-hashes all seven files bound by the immutable
Phase-IV sample receipt against the runtime checkout. The sample JSON alone is
not enough to pass preflight.

## Remaining blockers before N1

### B2 — scientific execution scope: OPEN

Must be resolved prospectively, without burden outcomes:

1. one predeclared primary statistic vs all 18 policy × rung cells for RSE gating;
2. source/donor/fold weighting for the target-level primary statistic;
3. zero-mean RSE handling.

The current source-balanced / donor-uniform / target-uniform weighting remains a
prospective candidate, not a frozen scientific decision.

### B3 — real RNG V3 authority receipt: OPEN

The code and tests are ready. A real authority receipt must still be materialized
from the current pre-panel roots, including authentication of the canonical
registry artifact. No bypass is allowed.

### B4 — resolved successor execution contract: OPEN

Only after B2 and B3:

- create the scientific-resolution record;
- build a successor execution contract bound to that record;
- re-run preflight;
- only then may N1=256 be executed.

## Current protected state

`AUDIT_B_N1_EXECUTION_AUTHORIZED = FALSE`
