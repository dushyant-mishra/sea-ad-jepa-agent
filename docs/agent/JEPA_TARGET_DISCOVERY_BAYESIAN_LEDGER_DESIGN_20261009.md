# JEPA target-discovery Bayesian spike — dependency-ledger implementation freeze

Date: 2026-10-09

Status: `LEDGER_DESIGN_FROZEN__HISTORICAL_ONLY__NO_FIT__NO_CORRECTED_REPLAY`

Parent preregistration:
`docs/agent/JEPA_TARGET_DISCOVERY_BAYESIAN_SPIKE_PREREG_20261009.md`

This document narrows the preregistered dependency rule into an executable evidence ledger before any Bayesian historical fit. It creates no scientific authority, target ranking, target promotion, G6/G7 authority, TD60 authority, Stage-4 authority, or training authority.

Hard terminal remains:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## 1. Why case rows are not replication units

TD57B and TD59 each contain 24 case rows, but those rows are repeated analyses of the same `A_NATURAL_MIXTURE` 25k biological substrate. Within a source, panels use disjoint molecular views but reuse the same source-level biological material; split/half rows are deterministic donor partitions rather than new experiments.

TD57C opened only HVS Panel 0 before its prospective sequential firewall stopped. NPH52, SEA_AD and Panel 1 were not opened.

Therefore the primary replication block for this spike is:

`stage × source`

not:

`panel × split × half row`.

Panel/split/half rows remain useful measurements of within-block heterogeneity, but they may not multiply effective replication count.

## 2. Cross-stage dependency

TD57B, TD57C and TD59 reuse the same historical source families and 25k substrate. The ledger therefore also records:

`substrate_source_root = A_NATURAL_MIXTURE_25K::<source>`

so, for example, `TD57B::HVS`, `TD57C::HVS` and `TD59::HVS` remain visibly linked rather than being represented as three unrelated external replications.

Any later model must preserve that shared-source/substrate dependency, for example through a shared source effect or an equivalently skeptical structure validated by synthetic calibration.

## 3. Frozen historical case topology

The ledger accepts exactly 52 historical case identities:

- TD57B: 2 panels × 3 sources × 2 splits × 2 halves = 24;
- TD57C: HVS Panel 0 × 2 splits × 2 halves = 4;
- TD59: 2 panels × 3 sources × 2 splits × 2 halves = 24.

No other historical case identity is accepted. Duplicate identities are a hard error. Missing or extra identities are a hard error.

This prevents duplicated rows or newly invented pseudo-cases from increasing apparent evidence.

## 4. Label blindness

Historical `pass` / `FAIL` / terminal labels are not emitted into the Bayesian ledger.

The ledger carries only the quantitative evidence required by the preregistration:

- stage;
- source;
- panel;
- split;
- half;
- observed statistic;
- comparator (`null_p95` for the current historical tables);
- margin = observed - comparator;
- dependency roots;
- evidence precision / eligibility;
- authenticated source path.

Historical verdict labels are reserved for post-fit sanity checking only, as already preregistered.

## 5. Current authenticated sources

Current committed historical sources used by the ledger builder are:

- `target_discovery/iterations/td57b_independent_triplet_recurrence/TD57B_CASE_TABLE.csv`
  - Git blob at the audited historical/current lineage: `922df89b56012842cb3eb883c297eafd09116c00`;
- `target_discovery/iterations/td57c_three_view_local_geometry/TD57C_RESULT.md`
  - Git blob: `cf285bda85e651bd3eaa58070e4a0d7432eef13e`;
- `target_discovery/iterations/td59_mesoscale_half_locality/TD59_CASE_TABLE.csv`
  - Git blob: `06926bb9260743941a177fc9d69076b43f293609`.

The TD57B and TD59 committed case tables expose full case-level numeric values suitable for ledger construction.

The committed TD57C result document exposes the four frozen HVS Panel-0 values only rounded to seven decimals and references the exact historical artifact `/mnt/data/td57c_p0_hvs.json`.

Rounded TD57C rows are therefore recorded only as provenance/shape placeholders and are explicitly `model_eligible = false`.

## 6. Exact TD57C blocker

Before any historical Bayesian fit, the exact `td57c_p0_hvs.json` must be extracted from the authenticated historical TD archive / custody material and bound without reconstruction or numeric inference.

The historical TD41-TD58 archive authority remains:

`c84849f5568f5260ac80b7c53e8af34f8bdad03fdbc16e0e8b29e7663dcf2417`

Do not reverse-engineer exact values from rounded markdown, fractions, PASS/FAIL labels or later diagnostics.

Until exact TD57C case values are supplied, the ledger terminal is:

`BLOCKED_EXACT_TD57C_CASE_VALUES_REQUIRED`

and `fit_authorized = false`.

## 7. TD57C source-generalization boundary

TD57C has only one opened source: HVS.

Accordingly:

- an HVS-specific TD57C quantitative summary is estimable once exact values are bound;
- TD57C source heterogeneity is not empirically estimable from that stage;
- a TD57C posterior for a new source would be hierarchical extrapolation informed by assumptions and other stages, not direct multi-source replication;
- it must never be reported as if TD57C replicated across HVS/NPH52/SEA_AD.

The historical frozen TD57C failure remains unchanged regardless of any future exploratory posterior.

## 8. Primary model-input reduction

For the initial skeptical spike, each `stage × source` block contributes at most one effective replication unit.

Within each block the current deterministic summary is the median case margin, accompanied by:

- median absolute deviation;
- minimum / maximum case margin;
- number of related case rows;
- panel membership;
- exact case identities.

The case count is descriptive only and does not enter as an independent-sample multiplier.

Exact duplicated case identities are rejected rather than averaged twice.

Panel/split/half effects may be reported as heterogeneity diagnostics, but the initial primary likelihood must not treat them as independent experiments. A richer correlated-case likelihood may replace this reduction only if it first passes the preregistered synthetic duplicate/dependency calibration without confidence inflation.

## 9. Model-family implication

The preregistered Student-t skeptical hierarchy remains the model family. The dependency-safe implementation should operate on the stage×source replication blocks and retain a shared source/substrate effect across stages.

Conceptually:

`block_margin(stage, source) ~ StudentT(nu, stage_effect + shared_source_effect, sigma_block)`

with skeptical zero-centered priors and explicit prior sensitivity.

This is an implementation clarification driven by the frozen sampling design, not by PASS/FAIL labels or corrected replay outcomes.

TD57C requires special reporting because it has only the HVS block.

## 10. Synthetic calibration still precedes historical fit

Even after the exact TD57C values are recovered, historical fitting remains disallowed until the preregistered synthetic controls pass, including:

1. null margins do not generate strong replication confidence;
2. one-source-only positive signal is not mistaken for source-general replication;
3. duplicate/dependent rows do not inflate certainty;
4. sign-flipping sources produce high heterogeneity / low predictive replication;
5. genuinely shared positive signal is recoverable;
6. conclusions are reported over at least three reasonable prior scales.

Failure terminates or revises the method spike prospectively; it must not trigger tuning toward the historical verdicts.

## 11. Current executable surface

Builder:
`scripts/v5/build_td_bayesian_historical_ledger.py`

Focused tests:
`tests/v5/test_build_td_bayesian_historical_ledger.py`

The builder emits case and stage×source block ledgers plus a receipt. In the current repository-only environment it intentionally stops short of historical fitting because exact TD57C values are not yet bound.
