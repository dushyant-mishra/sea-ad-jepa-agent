# Claude GPU lane deep audit — pre-outcome integration record

Date: 2026-09-21

Audited Claude head:

`cdac29eba5f08994bc3d8309a31c05cd21da50aa`

Audit base:

`ae5dc5c624fff341b8ef30c5359c55528383920a`

Integration branch:

`integrate/v5-full104-gpt-claude-20260921`

This audit is **pre-outcome only**. No Audit-B N1 burden result, terminal masking
outcome, D_shared result, protected/pathology-adaptive result, DEV/SEALED
expression, G5 margin, terminal target panel, or training result was opened.

## Bottom line

Claude's Phase-I/II/III **numerical findings are internally consistent** and the
exact Claude head executed its hosted masking suite with:

`537 passed / 0 skipped`

The deeper integration audit found additional **contract / provenance boundary
gaps**, not evidence-number reversals. These are being repaired prospectively on
the integration branch rather than rewriting Claude's historical evidence.

## Phase I — heavy sufficient statistics

### What is supported

The original Phase-I evidence establishes:

- exact heavy artifact SHA:
  `f77dff47df71e2b97895f6e850db4d2a2ebdab441d195dedf91f582b4d53b5ae`;
- authenticated FULL104 manifest:
  `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`;
- 8,915 blocks and 4,553,407 metadata rows traversed;
- 0 strict parser rejections;
- 0 legacy parser rejections;
- 0 parser/value mismatches;
- 512 decimal-syntax tokens, all integral under both parsers;
- global source-library total = 122,517,308,792 by all three reported routes;
- all 104 donor cell counts agree;
- a deterministic 12-donor sample of donor-level source-library totals agrees.

### Additional audit gaps

The V1 qualifier did **not** compare artifact source-library totals for all 104
donors. A cross-donor redistribution can preserve the global total.

It also loaded the artifact's per-cell `src_of_cell` vector without validating
it against authenticated donor/source identity. A source-code permutation can
preserve aggregate source counts.

These are addressed by the additive successor:

`qualify_heavy_sufficient_statistics_v2_20260921.py`

with adversarial controls for:

1. cross-donor library swaps that preserve the global total;
2. per-cell source-vector corruption that preserves aggregate source counts.

The real 242 MB artifact must still be run through V2 on the GPU machine before
this stronger qualification is closed.

### Ledger inconsistency found

Claude's Phase-I report declares reuse qualified, while Claude-head
`EXTERNAL_ARTIFACTS.json` still carries the older
`REQUIRES_METADATA_ONLY_STRICT_PARSE_EQUIVALENCE_CHECK_BEFORE_REUSE` status.
The integration ledger has been reconciled prospectively without changing the
heavy artifact bytes or historical producer hashes.

## Phase II — source × fold estimability

The reported counts are arithmetically internally consistent:

- undefined held-out terms: 30,451 / 1,773,512 = 1.7170%;
- targets with >=1 undefined held-out term: 6,653 / 17,053 = 39.01%;
- wholly vacuous source guardrails: 531 target-fold/source guardrails;
- affected targets with >=1 wholly vacuous source: 202;
- source split of vacuous target-fold guardrails:
  HVS=1, NPH52=1, SEA_AD=529;
- P1 retained target universe:
  17,053 - 6,653 = 10,400.

The independent row-level check used a different two-pass variance route on 384
target-donor pairs and reported 384/384 agreement, including 8 flagged
non-variable pairs.

This supports the existence and scale of the defect. It is still a verification
sample, not a proof of every one of the 1,773,512 terms.

## Phase III — evidence-state contract

Claude V2 correctly fixed the three previously known V1 faults:

1. non-estimable terms cannot carry finite numeric values;
2. joint target+prediction non-variability has its own state;
3. impossible correlations are rejected / classified invalid.

P3 wording is also corrected: the full intended estimand is not claimed as
point-estimated when aggregation is conditional on estimability.

### Additional edge cases found by integration audit

**Absent required group.**
If all supplied terms are estimable but a declared `required_group` is absent,
Claude V2's early all-estimable return can bypass the missing-group guard.

**Empty evidence.**
An empty `ScoreTerms` object is legal in Claude V2 and can aggregate to status
`ESTIMABLE` with a NaN statistic.

**Materially negative sums of squares.**
A materially negative `rss_y` or `pred_ss` falls through the
`<= EPS` non-variable route rather than becoming `INVALID_NUMERIC`.

The integrated successor closes all three:

`src/sea_ad_jepa/v5/evidence_estimability_contract_v2.py`

No P1/P2/P3/P4 consequence policy is selected.

## Phase IV — frozen target sample

The original sample freeze remains valuable and immutable:

- freeze digest:
  `c2c5e1b5addc50db7e9676ebf59e9c63b5d0b9eee882ef78aff5baa9d4a3b0ac`;
- N1=256, N2=1024, N3=4096;
- prefix sampling;
- seven source/input hashes bound;
- no burden result inspected before freeze.

### Important digest gap

The original `freeze_digest` hashes only:

- schema;
- salt;
- sample ladder;
- the seven bound inputs;
- target samples.

It does **not** hash:

- the primary burden-statistic definition;
- the 5% RSE threshold;
- the escalation semantics;
- the execution requirements.

Therefore the **sample is frozen**, but the complete scientific execution rule
is not cryptographically frozen by `c2c5e1b5...`.

This is being closed by the additive successor:

`src/sea_ad_jepa/v5/audit_b_execution_contract_v1.py`

The successor binds the original sample freeze together with the scientific
execution semantics and refuses N1 execution while precision scope remains:

`UNRESOLVED__EXECUTION_FORBIDDEN`

## RNG pre-panel issue

RNG V2 derives the global masking seed partly from target-panel authority.
Changing the eventual target panel can therefore reroll masks, which is
incompatible with a prospective pre-panel Audit-B burden audit.

The integration branch adds:

`src/sea_ad_jepa/v5/masking_rng_replay_authority_v3.py`

V3 removes target-panel authority from the global seed roots. A later panel may
only subset an already-defined family of target/fold-keyed masks.

This does not by itself change the existing terminal run contract; eventual
terminal integration requires an explicit successor/migration rather than a
silent fallback to RNG V2.

## Remaining pre-execution questions

1. Run the heavy-statistics V2 qualifier on the real GPU artifact.
2. Independently resolve the Phase-IV scientific execution scope without looking
   at burden:
   - does "RSE of the primary burden statistic" mean one predeclared statistic,
     or all 3 non-uniform policies x 6 burden rungs?
   - how are source x donor x fold strata weighted into the target-level primary
     statistic? The integration candidate is equal donors within source, equal
     sources within target, equal targets overall, but the original sample freeze
     did not explicitly freeze that weighting.
3. Freeze those decisions in the execution-contract digest.
4. Bind the exact RNG-V3 authority and burden-estimator source.
5. Only then may Audit-B N1=256 be executed.

## Protected state

Still closed:

- Audit-B N1 burden outcomes;
- terminal masking outcomes;
- P1/P2/P3/P4 terminal selection;
- D_shared;
- pathology-adaptive decisions;
- DEV/SEALED expression;
- G5 margin;
- terminal target-panel selection;
- training.
