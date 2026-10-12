# Target-discovery × V79 synthetic qualification crosswalk — design freeze

Date: 2026-10-12

Status: `PROSPECTIVE_TARGET_DISCOVERY_SYNTHETIC_CROSSWALK_FROZEN__NO_SYNTHETIC_RESULT_OPENED_FOR_TARGET_SELECTION__NO_TARGET_AUTHORITY`

Source design authority: target-discovery audit commit `57c08c18d4e96c497fb6436ca4464392ce7e67d7`.

## Purpose

Define prospectively how the target-discovery lane may consume evidence from the separate V79 synthetic-data lane. This document does not modify or authorize V79 world generation or fitting. It freezes only the target-discovery interpretation layer.

## Hard rules

1. Synthetic evidence may falsify a target candidate only on an applicable truth-backed claim.
2. Synthetic PASS may support only a claim whose relevant ground truth is explicitly planted and authenticated.
3. Absence of planted truth is `NOT_ESTIMABLE`, never PASS and never FAIL.
4. Synthetic PASS never overrides real-data `FAIL` or real-data `NOT_ESTIMABLE`.
5. No synthetic aggregate score may select a target winner.
6. A decisive synthetic falsifier may eliminate an otherwise real-PASS candidate.
7. C5 regulatory evidence cannot rescue the universal foundation-target terminal.
8. Q10/Q11 operator-invariance evidence is valid only as the canonical paired counterfactual with authenticated unchanged non-operator truth.
9. New-donor transfer requires donors not used as training identities.
10. Target-discovery authority remains off until separately authorized real execution.

Hard terminal remains:
`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## Evidence classes

Every candidate × world × claim entry is exactly one of:

- `DECISIVE_POSITIVE`: planted truth supports a positive qualification test.
- `DECISIVE_NEGATIVE`: planted null/counterfactual can falsify the candidate.
- `DIAGNOSTIC`: useful behavior but insufficient alone to promote or eliminate on the named biological claim.
- `NOT_ESTIMABLE`: required truth is absent from current V79.

## V79 worlds

- Q00 `BASELINE`: baseline donor/source/class/depth/support structure.
- Q01 `WEAK_DONOR`: weakened donor SD.
- Q02 `STRONG_DONOR`: strengthened donor SD.
- Q03 `WEAK_SOURCE`: weakened source effect.
- Q04 `SOURCE_ABSENT`: source effect absent.
- Q05 `CLASS_ABSENT`: broad class effect absent.
- Q06 `QUADRATIC_DEPTH_ABSENT`: quadratic depth absent.
- Q07 `DONOR_ABSENT`: donor SD absent.
- Q08 `SPARSE_DETECTION`: severe sparse detection/support challenge.
- Q09 `POSITIVE_TAIL`: difficult positive residual/tail.
- Q10 `S174_DESIGN_IMBALANCE`: realistic imbalanced S174-like design.
- Q11 `OMITTED_OPERATOR`: Q10-paired operator perturbation with non-operator truth preserved.

## Candidate rules

### C1_SHARED_EMERGENT

Decisive: Q01/Q02 donor sensitivity and new-donor transfer; Q04 source-null leakage; Q05 class-null hallucination; Q06 depth-null hallucination; Q07 donor false positive; Q08 forced certainty/imputation; paired Q10/Q11 operator leakage. Q03 and Q09 are diagnostic unless an executor prospectively binds a truth-backed estimand.

Current V79 cannot positively establish exact recovery of a planted multigene `Z_shared(c)` because no independent shared multigene latent truth is presently planted. That claim is `NOT_ESTIMABLE`.

### C2_RELATIONAL_SHARED

Inherits applicable C1 nuisance/transfer/support tests. Current V79 does not independently plant target-discovery relational geometry; therefore broad/mesoscale relational recovery, scale-free recurrence, locality bracket, fine-neighbor wrong-cell recovery, and relational increment over C1 are `NOT_ESTIMABLE`. A relation derived from the same generated observations is not independent planted truth.

### C3_QUERY_MEASURED

Decisive negative tests: Q08 unsupported-query forcing; paired Q10/Q11 operator leakage; Q04/Q06/Q07 only when the candidate-specific nuisance claim corresponds to the explicitly absent truth. q-count-only, q-address-only, query-agnostic, wrong-q, and technical+q are diagnostic unless future V79 truth prospectively plants cross-gene query-conditioned biology.

Positive cross-gene q-conditioned biological recovery is currently `NOT_ESTIMABLE`.

### C4_STRUCTURED_COMPOSITE

Inherits every applicable decisive C1/C2/C3 falsifier. Q08 tests support/measurement-uncertainty response. Q10/Q11 tests decomposition: biological components stable, measurement/support uncertainty permitted to respond. New-donor replicate tests transfer without donor memorization.

Biological increment over C2/C3 remains `NOT_ESTIMABLE` while their central synthetic truths are absent. C4 cannot rescue a failed or unresolved mandatory constituent.

### C5_REGULATORY_SPECIALIST

Regulatory/chromatin recovery is `NOT_ESTIMABLE` because current V79 excludes SCENIC+/ATAC from truth. Generic nuisance behavior may be diagnostic. C5 remains specialist-only and cannot alter the foundation-target terminal.

## Gate mapping

Current V79 can contribute synthetic evidence to G2/G3 only for explicitly planted components; G4 through Q01/Q02/Q07/new-donor; G5 only as source-nuisance testing through Q03/Q04; G7/G8 through Q08/Q09/Q10/Q11 where prospectively identified; G10 through absent-component and shortcut falsifiers; G11 through new-donor and design transfer; G12 through Q08/support cases.

C2 R1-R4 central relational truth, C3 positive query-biological superiority, C4 increment-over-constituents, and C5 regulatory biological recovery remain non-promotable from current V79.

## Evidence combination

For each foundation candidate:

- real `FAIL` => eliminated regardless of synthetic result;
- real `NOT_ESTIMABLE` => unresolved; synthetic PASS cannot rescue;
- real `PASS` + applicable decisive synthetic FAIL => eliminated by synthetic falsifier;
- real `PASS` + no decisive synthetic FAIL => eligible for target selection, subject to all other frozen gates.

Foundation contingency terminal:

- zero eligible foundation candidates => `NO_TARGET_WINNER__REDESIGN_BEFORE_PROTECTED_CONFIRMATION`;
- one eligible foundation candidate => `SINGLE_CANDIDATE_ELIGIBLE_FOR_PROTECTED_CONFIRMATION__NO_TARGET_AUTHORITY`;
- more than one eligible foundation candidate => `MULTIPLE_QUALIFIED_TARGETS__PROTECTED_HEAD_TO_HEAD_REQUIRED__NO_TARGET_AUTHORITY`.

C4 is eligible only when C2 and C3 are each independently eligible and C4 itself has no failed inherited or synthetic mandatory gate. C5 is reported separately as an optional specialist.

## Machine-readable implementation requirements

The implementation must provide:

- exact Q00-Q11 registry;
- exact C1-C5 registry;
- evidence-class enum;
- explicit claim entries with required truth fields and expected behavior;
- paired Q10/Q11 rule;
- new-donor rule;
- mandatory `NOT_ESTIMABLE` claims listed above;
- authority flags all false;
- fail-closed validator;
- candidate-level real+synthetic evidence combiner;
- foundation-level contingency adjudicator.

The validator must reject missing/extra worlds, candidates, evidence classes, unauthorized true flags, decisive entries without truth bindings, C4 eligibility without C2+C3 eligibility, and any attempt for synthetic evidence to rescue real FAIL/NOT_ESTIMABLE.
