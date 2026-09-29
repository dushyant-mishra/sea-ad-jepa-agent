# V64 execution-readiness audit — parallel lane

Date: 2026-09-29  
Branch: `chatgpt/v64-parallel-execution-readiness-20260929`  
Parent authority at branch creation: live HEAD of `chatgpt/v64-e2-single-source-successor-20260929` after the C3/terms/P1S amendment.  
Governance: `TRAINING=OFF`; `TD60=BLOCKED`.

## Purpose

Audit whether the already-frozen V64 contracts can be executed mechanically, without introducing post-outcome choices. This lane does not change scientific thresholds, invent nuisance arms, open protected outcomes, or redesign the estimator.

## A. Statistical red-team tests

### A1. Depth-sensitivity leakage diagnostic

Authority:
`results/v64/V64_CONTINUOUS_ADJUSTMENT_DEPTH_SENSITIVITY_LEAKAGE_DIAGNOSTIC_V1.json`

Finding:
the frozen contract is sufficiently specific to execute, but the V63 estimator implementation did not expose this ablation. Its only CLI ablation was `intercept_only`.

Action on this parallel branch:
added
`scripts/v64/e2_continuous_adjustment_depth_sensitivity_ablation_v1.py`

The executor reuses the V63 estimator implementation and removes exactly:
- `rna_depth_sensitivity`
- `atac_depth_sensitivity`

It keeps the V63 worlds/arms/seeds, `M_MIN=.010`, ridge alpha 1.0, K=5 promoter cross-fitting, scoring and all remaining features unchanged. It compares the new result against the committed V63 primary result.

Status:
`EXECUTOR_ADDED__NOT_YET_EXECUTED_HERE`

### A2. Out-of-span TECH stress

Authority:
`results/v64/V64_CONTINUOUS_ADJUSTMENT_OUT_OF_SPAN_STRESS_CONTRACT_V1.json`

The scientific mechanism, frozen geometry function, amplitude, unchanged estimator, forbidden modifications, `M_MIN`, and interpretation are specified.

Status:
`EXECUTOR_ADDED__NOT_YET_EXECUTED_HERE`

Action on this parallel branch:\nadded\n`scripts/v64/e2_continuous_adjustment_out_of_span_stress_v1.py`\n\nThe wrapper imports the frozen V63 estimator and adds exactly the prospectively frozen `NEG_TECH_OUTSPAN_1` arm as its own `OUTSPAN_TECH` family. No estimator basis terms, alpha, M_MIN, existing arms, positive amplitudes or scoring rules are changed.\n\nDo not invent a second out-of-span nuisance.

## B. C3 coordinate harmonization

Authority:
`results/v63/V63_E2_DESIGN_CONTRACT_V1.json`, C3, plus
`results/v64/V64_NOTT_C3_TERMS_AND_P1S_CLAIM_SCOPE_AMENDMENT_V1.json`.

### B1. What is frozen

- direction: hg19 -> hg38
- named authenticated chain identity is available
- either-anchor failure is counted
- different-chromosome lifts are rejected
- round-trip hg19 -> hg38 -> hg19 is required
- ATAC source-coordinate re-liftover concordance is required
- denominator-preserving attrition reporting is required

### B2. Operational values still not frozen

V63 C3 explicitly says pairs with a length change beyond a **pre-declared tolerance** are dropped, but no numeric tolerance is supplied in C3 or the V64 amendment.

V63 C3 also says round-trip recovery must return the original interval for a **pre-declared fraction**, but no required fraction is supplied.

The authority chain also does not currently identify:
- the exact liftOver implementation/version;
- command-line/default mapping parameters such as minimum mapped fraction;
- split/multiple-map handling when a source interval maps to more than one target interval.

These choices can change retention and therefore downstream contact∩accessibility support.

Status:
`NOT_YET_MECHANICALLY_EXECUTABLE_AS_A_PASS_FAIL_GATE`

Required before reading liftover outcomes:
freeze these operational semantics or explicitly redefine C3 as descriptive-only. Do not choose them after seeing attrition.

## C. P1S Nott substrate-fit test

Authority:
`results/v64/V64_NOTT_SAME_STUDY_SUBSTRATE_FIT_CONTRACT_V1.json`

The purpose, same-pair three-cell-type comparison, promoter-fixed distal shuffle concept, nuisance families, hard stop and protected-outcome firewall are frozen.

However, the authoritative short contract does not yet fully specify several execution-level choices that can alter the result:

1. **Accessibility support rule**
   - no exact definition of whether distal-anchor support means >=1 bp peak overlap, a fractional overlap, anchor-center inclusion, or another rule.

2. **Promoter-fixed shuffle count / seed authority**
   - the null shape is frozen, but the number of shuffles and random seed authority are not specified.

3. **Distance-preservation implementation**
   - “preserving the promoter's empirical distance distribution” is specified conceptually, but the exact draw/matching rule is not.

4. **Contact-degree preservation**
   - “where feasible” leaves an outcome-sensitive degree of freedom unless operationalised before execution.

5. **Nuisance-control estimator**
   - nuisance variables are listed, but the exact adjustment/paired-contrast implementation is not stated in the P1S contract.
   - The continuous-adjustment estimator is frozen for the later RNA/ATAC correspondence problem; it should not be silently imported into P1S unless an authority document explicitly says so.

Status:
`BIOLOGICAL_HYPOTHESIS_FROZEN__EXECUTION_DETAILS_INCOMPLETE`

Do not inspect P1S outcomes until these mechanics are frozen.

## D. P3 non-trivial cell-type negatives

V63 C7 freezes the logical eligibility conditions:
- target gene expressed in microglia;
- distal element accessible in microglia;
- relationship absent from the microglial contact map.

But current authority inspected in this lane does not yet specify:
- which microglial expression artifact is authoritative;
- gene annotation/version for promoter->gene identity;
- expression threshold / detection rule;
- exact relationship-absence rule after liftover and possible coordinate equivalence.

Status:
`LOGIC_FROZEN__ELIGIBILITY_EXECUTOR_INPUTS_NOT_FULLY_SPECIFIED`

These must be defined prospectively before P3 counts are inspected.

## E. Parallel-lane conclusion

The immediate execution order should be split into two classes.

### Ready to execute without new scientific design
1. depth-sensitivity ablation;
2. out-of-span TECH stress, once the existing frozen mechanism is wired into an executor without changing it.

### Requires pre-outcome operational closure
3. C3 liftover/round-trip gate;
4. P1S substrate fit;
5. P3 eligibility.

This is not a request to redesign the framework. It is a fail-closed implementation audit: several biological contracts contain explicit references to predeclared values that have not yet been instantiated numerically or algorithmically.

No protected outcome was opened in this audit.


## F. Reproducibility clarification received during execution

A transient concern was raised because an 8-donor / 3-seed smoke-run summary was described as reproducing "the earlier run" while the committed authority is the 18-donor / 24-seed primary.

This has been resolved. At the matching 18/24 configuration, the new runner reproduces the committed `c4e78de2` primary exactly:
- POS_BIO_1 = 0.2282527590455996
- TECH margin = 0.01995560304936889
- TECH LCB95 = 0.01948446698612133
- Kish ESS = 935.4469599793607

The previously quoted approximately 0.22923 / 0.019928 / 0.019385 / ESS 908.55 values were from an explicitly smaller 8/3 smoke configuration and are not the authority baseline.

Status:
`REPRODUCIBILITY_CONCERN_RESOLVED__18x24_BIT_FAITHFUL`

Future run reports should state the exact artifact and donor/seed configuration in the same sentence as any reproduction claim.
