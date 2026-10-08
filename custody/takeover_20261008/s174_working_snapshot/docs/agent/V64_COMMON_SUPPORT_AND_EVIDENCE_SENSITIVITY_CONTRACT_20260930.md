# V64 common-support and evidence-sensitivity contract

**Date:** 2026-09-30  
**Status:** PROSPECTIVE METHODOLOGY CONTRACT — no E2 matching outcome opened

## 1. Why this is required

E2-anchored and unanchored measurable genes have strongly separated RNA-detection distributions.

Therefore a high-dimensional matching scheme can silently change the estimand by trimming a large fraction of E2, or can create bad matches if tolerances are relaxed to retain sample size.

The matching operator must be frozen before biological comparison outcomes are inspected.

## 2. Common support comes before matching

Before selecting a matching algorithm, report overlap for each proposed matching variable and for their joint support.

Candidate variables may include:

- RNA detection rate
- promoter activity/accessibility
- enhancer accessibility
- enhancer-promoter distance
- degree opportunity
- local peak density
- locus size
- cell-state/context indicators

For every proposed design report:

- E2 population size
- eligible comparison population size
- fraction of E2 with at least one lawful comparator
- trim fraction
- covariate balance among retained objects
- location of trimmed objects in covariate space

## 3. No rescue by distant controls

If a linked/E2 object has no comparator within the frozen support rule:

- trim it;
- count it;
- preserve its identity in a trim ledger.

Do not progressively widen tolerances after seeing outcome behavior.

Do not replace unmatched objects with distant controls merely to preserve N.

## 4. Estimand scope

Any matched comparison applies only to the retained overlap population.

The result must not be narrated as representing all E2 if substantial trimming occurs.

Report both:
- full E2 descriptive population;
- matched-overlap inferential population.

## 5. Matching operator freeze

Before outcome execution, freeze:

- distance metric;
- covariate transforms;
- exact/caliper rules;
- replacement policy;
- multiplicity per treated object;
- tie-breaking;
- trimming rule;
- random seed where stochastic;
- balance diagnostics;
- failure conditions.

No outcome-adaptive tuning.

## 6. Evidence 'independence' language

Do not use a point estimate after adjustment as proof of independence.

Use:

`incremental support under observed adjustment`

because adjustment variables are measured with error.

## 7. Sensitivity requirement

For every cross-family incremental-support result, accompany the estimate with sensitivity analysis addressing:

- measurement error in adjustment variables;
- residual/unmeasured common causes;
- alternative lawful adjustment specifications;
- support/trim dependence.

The final report must answer:

> How strong would an omitted or poorly measured shared driver need to be to remove the apparent increment?

No single sensitivity formalism is frozen here. A successor execution contract must choose and justify one prospectively.

## 8. Estimator robustness is not evidence-family independence

Two algorithms using the same NIH-CARD cells/donors/modalities are one measurement family unless a stronger argument is established.

Example:
- SCARlink
- SCENT

Their agreement is an estimator-robustness result.

It is not two independent biological confirmations.

Future ledger fields should include separately:
- measurement_source
- evidence_family
- estimator

## 9. Availability shortcut

The 379 E2-anchored but NIH-CARD-RNA-unmeasurable genes must remain a named diagnostic stratum.

They can test whether future support scores or models exploit evidence availability.

They must not be coded as negative evidence.

## 10. Held-out-family standard

Strong validation should construct a representation/support rule from some evidence families and evaluate it on a mechanistically distinct held-out family.

Reconstruction of the same evidence used in construction is development fit, not independent validation.

## Governance

No matching outcome or independence conclusion is authorized by this document.

Training OFF. Phase B stopped. Stage 4 sealed. Morabito protected.
