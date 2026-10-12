# Target-discovery × V79 synthetic qualification crosswalk — design freeze

Date: 2026-10-11

Status: `PROSPECTIVE_TARGET_DISCOVERY_SYNTHETIC_CROSSWALK_FROZEN__NO_SYNTHETIC_RESULT_OPENED_FOR_TARGET_SELECTION__NO_TARGET_AUTHORITY`

## 1. Purpose

This document defines, prospectively and before any target candidate is evaluated on realized V79 qualification worlds, how the target-discovery lane may consume evidence from the separate V79 synthetic-data lane.

The synthetic lane remains operationally separate. This document does not modify PR #290/291, the V79 generator, V79 scientific authority, or world-generation authority. It only freezes the target-discovery interpretation contract for later evidence consumption.

The target-discovery question is:

> For each target candidate C1-C5, which claims can the existing V79 Q00-Q11 worlds genuinely adjudicate because the relevant truth is explicitly planted, which claims are merely diagnostic, and which claims are not estimable from the current synthetic generator?

The design is deliberately asymmetric:

- synthetic evidence may falsify a target candidate on an applicable, truth-backed mandatory falsifier;
- synthetic PASS may support only a claim whose ground truth is explicitly present in the V79 truth object;
- absence of planted truth is `NOT_ESTIMABLE`, never PASS;
- synthetic PASS never overrides real-data FAIL or real-data NOT_ESTIMABLE;
- no synthetic aggregate score may select a target winner.

## 2. Authority boundary

This crosswalk grants no authority for:

- V79 physical world realization;
- V79 qualification fitting;
- corrected TD56/TD57B/TD57C/TD59 replay;
- a real target tournament;
- target selection;
- representation selection;
- TD60;
- Stage4;
- real JEPA training.

Target-discovery hard terminal remains:

`TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED`

## 3. Source synthetic authority

Target discovery may later consume only synthetic evidence that is explicitly bound to the canonical V79 V2_CORE contract and exact realized-world manifests/truth tables.

Current canonical synthetic contract identity at freeze time:

- PR #290 canonical head: `5394d036ccd423f9c61267fbdfeef6edd4912d37`
- Contract V2 SHA-256: `57e19295be824dbbb023b60a57c5039dac1f9d74e66fefe1008fc27d30fdaf26`
- V79 generator branch: PR #291
- current generator head observed at this design freeze: `f45ee034d9bd0c603da5783fed2cf09ee2b16f20`
- current generator state: Q00-Q11 can be assembled in memory; physical realization remains disabled; zero qualification worlds and zero qualification fits have been emitted.

If V79 authority changes prospectively before physical realization, the target-discovery adapter must bind the final accepted synthetic authority and record the supersession. This document's scientific interpretation rules do not silently follow an altered generator.

## 4. Evidence classes

Every candidate × synthetic-world × target-discovery-claim cell must be classified as exactly one of:

### `DECISIVE_POSITIVE`

The synthetic world contains explicit ground truth for the claim and can provide positive qualification evidence if the candidate behaves as prospectively expected.

### `DECISIVE_NEGATIVE`

The world contains an explicit absence/null/counterfactual truth and can falsify a candidate if it manufactures biological structure, depends on nuisance, fails transfer, or mishandles support/uncertainty.

### `DIAGNOSTIC`

The world can reveal useful behavior, but its truth is not sufficient to promote or eliminate the candidate on the named biological claim by itself.

### `NOT_ESTIMABLE`

The current V79 generator does not contain the required planted truth. No PASS/FAIL is permitted for that claim from V79.

A gate may consume multiple worlds. A single world may adjudicate different claims at different evidence classes.

## 5. V79 world interpretation for target discovery

| World | Frozen perturbation | Primary target-discovery interpretation |
|---|---|---|
| Q00 `BASELINE` | Baseline donor/source/class/depth/support structure | Reference world for biological-content vs nuisance baselines and calibration of candidate behavior |
| Q01 `WEAK_DONOR` | Donor SD weakened | Weak-signal donor recurrence; uncertainty should increase rather than fabricate strong recurrence |
| Q02 `STRONG_DONOR` | Donor SD strengthened | Positive control for donor-recurrent information and new-donor transfer |
| Q03 `WEAK_SOURCE` | Source effect weakened | Source imprint should diminish without destruction of genuine non-source structure |
| Q04 `SOURCE_ABSENT` | Source effect absent | Decisive negative control against requiring source identity or manufacturing source-associated biology |
| Q05 `CLASS_ABSENT` | Broad class effect absent | Decisive negative control against hallucinating the planted broad-class component |
| Q06 `QUADRATIC_DEPTH_ABSENT` | Quadratic depth term absent | Negative control against manufacturing nonlinear depth-dependent biology |
| Q07 `DONOR_ABSENT` | Donor SD absent | Critical false-positive control: no candidate may claim donor-recurrent biological signal from an absent planted donor component |
| Q08 `SPARSE_DETECTION` | Very sparse detection | Support-aware abstention; separation of biological uncertainty from measurement/support uncertainty |
| Q09 `POSITIVE_TAIL` | Difficult positive-value residual/tail | Robustness to observation distribution; measurement difficulty must not masquerade as biological-state change |
| Q10 `S174_DESIGN_IMBALANCE` | Realistic imbalanced S174-like design | Transfer/robustness under donor/source/operator/support imbalance |
| Q11 `OMITTED_OPERATOR` | Q10-paired world with operator perturbation added | Paired counterfactual: non-operator truth is held fixed; biological components should remain stable while measurement/support uncertainty may respond |

Q10/Q11 must be interpreted as a pair. Target-discovery evidence from Q11 that is not compared to its paired Q10 counterpart cannot satisfy an operator-invariance claim.

## 6. Candidate families inherited from target-discovery tournament V2

The target candidates remain:

- C1 `C1_SHARED_EMERGENT`
- C2 `C2_RELATIONAL_SHARED`
- C3 `C3_QUERY_MEASURED`
- C4 `C4_STRUCTURED_COMPOSITE`
- C5 `C5_REGULATORY_SPECIALIST`

The existing target-discovery V2 gate inheritance remains controlling. This crosswalk adds synthetic evidence roles; it does not weaken or replace any real-data gate.

## 7. Candidate × synthetic-world crosswalk

### 7.1 C1 — `C1_SHARED_EMERGENT`

C1 claims that a learned shared state captures donor-recurrent, source-replicated biology without being reducible to technical/support shortcuts.

#### Decisive V79 evidence

- Q01 `WEAK_DONOR` — `DECISIVE_POSITIVE` for calibrated weak donor sensitivity; candidate must not turn weak donor truth into strong apparent recurrence.
- Q02 `STRONG_DONOR` — `DECISIVE_POSITIVE` for stronger donor-recurrent signal and new-donor transfer.
- Q04 `SOURCE_ABSENT` — `DECISIVE_NEGATIVE` for source dependence; candidate biological state may not require source identity when source truth is absent.
- Q05 `CLASS_ABSENT` — `DECISIVE_NEGATIVE` for hallucinated broad-class content attributable to the absent planted class term.
- Q06 `QUADRATIC_DEPTH_ABSENT` — `DECISIVE_NEGATIVE` for manufactured nonlinear depth structure.
- Q07 `DONOR_ABSENT` — `DECISIVE_NEGATIVE` for false donor recurrence.
- Q08 `SPARSE_DETECTION` — `DECISIVE_NEGATIVE` for forced state certainty or forced imputation where support is weak; abstention/measurement uncertainty must respond.
- Q10/Q11 paired — `DECISIVE_NEGATIVE` for operator leakage: the biological component must not materially change solely because Q11 adds the paired omitted-operator perturbation.
- held-out new-donor replicate — `DECISIVE_POSITIVE` for transfer where the planted donor component exists; memorization of training donor identity is insufficient.

#### Diagnostic V79 evidence

- Q03 `WEAK_SOURCE` — `DIAGNOSTIC` for monotonic reduction of source imprint.
- Q09 `POSITIVE_TAIL` — `DIAGNOSTIC` for observation robustness unless the final C1 gate executor prospectively defines a truth-backed state-stability estimand.

#### Not estimable from current V79

- exact recovery of a planted multigene `Z_shared(c)` latent state;
- subspace correspondence to a generator-defined shared biological manifold, unless such a manifold is explicitly added to future synthetic truth before outcomes.

Therefore V79 may falsify C1's nuisance/transfer/support behavior but may not by itself establish the full learned shared-state biological claim.

### 7.2 C2 — `C2_RELATIONAL_SHARED`

C2 inherits C1 and adds broad/mesoscale relational constraints supported by corrected real replay.

#### Decisive V79 evidence

C2 inherits all applicable C1 decisive synthetic tests for nuisance rejection, donor transfer, support and operator invariance.

#### Diagnostic V79 evidence

Candidate relational geometry may be inspected across Q00-Q11 as `DIAGNOSTIC`, including whether nuisance perturbations grossly distort neighborhood structure.

#### Not estimable from current V79

The following central C2 claims are `NOT_ESTIMABLE` because V79 does not currently plant an independent target-discovery relational truth:

- recovery of broad/mesoscale relational geometry;
- scale-free relational recurrence;
- correct locality bracket;
- fine-neighbor wrong-cell defeat as evidence of recovery of an independently planted relation;
- increment of relational constraints over C1 biological truth.

No relation may be derived from the same generated observations and then treated as independent planted truth for C2 promotion.

### 7.3 C3 — `C3_QUERY_MEASURED`

C3 is a measured q-conditioned, non-q same-cell contextual target. The student's q scalar is absent and primary normalization excludes q scalar.

#### Decisive V79 evidence

- Q08 `SPARSE_DETECTION` — `DECISIVE_NEGATIVE` for unsupported-query forcing: query-conditioned output must abstain or widen measurement uncertainty where required non-q context is structurally/observationally unsupported.
- Q10/Q11 paired — `DECISIVE_NEGATIVE` for operator leakage into query-conditioned biological context when non-operator truth is held fixed.
- Q04/Q06/Q07 — `DECISIVE_NEGATIVE` only for candidate-specific claims that the query target is exploiting source/depth/donor nuisance that is explicitly absent in the given world.

#### Diagnostic V79 evidence

The target-discovery q-count-only, q-address-only, query-agnostic, wrong-q and technical+q controls may be executed on V79 as `DIAGNOSTIC` unless and until the generator contains explicit cross-gene/query-conditioned truth that makes their expected ordering scientifically identified.

#### Not estimable from current V79

- genuine planted cross-gene query-conditioned biological context;
- positive proof that changing q identity should alter the correct non-q contextual target for biological reasons;
- recovery of an independently planted q-conditioned target manifold.

Because V79 genes are generated under a gene-wise model, q-conditioned biological truth is not inferred merely from correlated realized observations.

### 7.4 C4 — `C4_STRUCTURED_COMPOSITE`

C4 inherits C2 + C3 plus explicit support/abstention and biological-vs-measurement uncertainty components.

#### Decisive V79 evidence

C4 inherits every applicable decisive C1/C2/C3 synthetic falsifier.

Additionally:

- Q08 — `DECISIVE_POSITIVE/NEGATIVE` for whether explicit support and measurement uncertainty respond appropriately to sparse evidence without fabricating biological certainty;
- Q10/Q11 — `DECISIVE_POSITIVE/NEGATIVE` for decomposition: biological components should remain stable under the paired operator perturbation while measurement/support uncertainty is permitted and expected to respond;
- new-donor replicate — `DECISIVE_POSITIVE/NEGATIVE` for transfer of the biological components without donor memorization.

#### Not estimable from current V79

- biological increment of C4 over C2 and C3 on their central target truths;
- proof that the composite is superior because C2 relational and C3 query-conditioned truths are not independently planted in current V79.

C4 cannot use good support/uncertainty behavior to compensate for a real-data C2 or C3 mandatory-gate failure.

### 7.5 C5 — `C5_REGULATORY_SPECIALIST`

C5 is optional and never a universal foundation target.

Current V79 contract excludes SCENIC+/ATAC from truth. Therefore:

- regulatory/chromatin recovery: `NOT_ESTIMABLE`;
- source/donor/support/operator nuisance behavior may be `DIAGNOSTIC` if the specialist implementation can lawfully consume the synthetic RNA worlds;
- no V79 result may promote C5's regulatory biological claim without independently planted regulatory/chromatin truth.

## 8. Target-gate mapping

The following target-discovery promotion concepts may consume current V79 evidence when the candidate-specific truth is identified:

- `G2_NONTRIVIAL_BIOLOGICAL_CONTENT`: synthetic evidence is supportive only for planted components; never sufficient alone for real biological promotion.
- `G3_CORRECT_CELL_SPECIFICITY`: decisive only if the relevant cell-specific truth is explicit; otherwise diagnostic.
- `G4_DONOR_RECURRENCE`: Q01/Q02/Q07 plus new-donor replicate are the principal synthetic falsification set.
- `G5_SOURCE_REPLICATION`: Q03/Q04 are nuisance/source-dependence tests, not proof of human source replication.
- `G7_EVIDENCE_CONVERGENCE`: Q08 and evidence-depth manipulations may test monotonic uncertainty/support behavior where prospectively defined.
- `G8_MEASUREMENT_ROBUSTNESS`: Q08/Q09/Q10/Q11 are the principal synthetic set.
- `G10_COLLAPSE_SHORTCUT_RESISTANCE`: absent-component worlds Q04-Q07 and target-specific shortcut baselines are synthetic falsifiers.
- `G11_TRANSFER`: held-out new-donor replicate and Q10/Q11 design transfer may supply synthetic transfer evidence.
- `G12_COVERAGE_ABSTENTION`: Q08 and structural-support cases are decisive for unsupported forcing/abstention behavior.

The following candidate-specific gates remain non-promotable from current V79 unless future truth is added prospectively:

- C1 exact shared-latent recovery gates requiring planted multigene state;
- C2 R1-R4 central relational-truth gates;
- C3 Q4-Q8 positive biological superiority claims requiring planted query-conditioned truth;
- C4 `C4_INCREMENT_OVER_CONSTITUENTS` biological increment;
- C5 M1-M4 biological regulatory claims except generic circularity/provenance checks that do not require synthetic truth.

## 9. Paired Q10/Q11 counterfactual rule

For any candidate component claiming biological invariance to acquisition/operator perturbation:

1. compare Q10 and Q11 only as their canonical paired realization;
2. require exact truth/manifests showing non-operator truth is unchanged and the intended operator perturbation is the designated difference;
3. evaluate the candidate's biological component in a prospectively frozen representation-invariant metric appropriate to that candidate;
4. separately evaluate measurement/support uncertainty response;
5. do not reward a representation that is invariant only because it collapsed;
6. combine this check with C1/C2/C3-specific noncollapse and biological-content gates;
7. if Q10/Q11 pairing authority is absent or altered, return `NOT_ESTIMABLE` for the counterfactual claim.

## 10. New-donor transfer rule

A new-donor synthetic transfer claim requires:

- donor identities in the evaluation replicate were not available as training identities;
- fixed biological/source/class/depth truth fields remain bound as defined by V79;
- donor realization/noise uses the canonical held-out-donor streams;
- the candidate is evaluated without donor-ID leakage;
- improvement over lawful shortcut baselines is reported;
- repeated cells/queries within one donor do not inflate donor N.

Failure is candidate evidence against transfer. PASS is synthetic transfer support only and cannot establish human donor recurrence.

## 11. Support and uncertainty rule

Structural unmeasurement is measurement truth, never biological zero.

For all candidates:

- structurally unmeasured target components are excluded or cause explicit abstention according to candidate contract;
- measured zero remains a valid observation;
- unsupported queries/cells cannot be force-imputed to produce a biological PASS;
- biological uncertainty and measurement/support uncertainty are recorded separately;
- Q08 is the primary sparse-evidence stress test;
- Q10/Q11 may alter measurement uncertainty without requiring a biological-state change;
- a candidate that becomes more biologically confident as support is removed fails the applicable synthetic falsifier unless a prospectively frozen truth-backed exception exists.

## 12. Multi-candidate use

Synthetic evidence is a secondary discriminator only among candidates that remain biologically eligible under real target-discovery gates.

If several real candidates qualify:

1. eliminate any candidate that fails an applicable decisive synthetic falsifier;
2. do not rank candidates by an aggregate synthetic score;
3. prefer one candidate over another only under a separately prefrozen incremental/non-inferiority rule;
4. if candidates remain complementary or incomparable, preserve a multi-candidate terminal and require protected head-to-head confirmation rather than arbitrary selection.

If no real foundation candidate qualifies, synthetic PASS cannot rescue one.

## 13. Required future adapter artifact

Before consuming realized V79 outcomes, target discovery must instantiate a machine-readable crosswalk artifact with one row per:

`candidate_id × target_gate × synthetic_world_or_pair × claim`

Required fields:

- `candidate_id`
- `target_gate`
- `synthetic_world`
- `paired_world` if applicable
- `claim_id`
- `evidence_class` in `{DECISIVE_POSITIVE, DECISIVE_NEGATIVE, DIAGNOSTIC, NOT_ESTIMABLE}`
- `required_truth_fields`
- `estimand_id`
- `decision_rule_id`
- `expected_direction`
- `applicability_rule`
- `real_data_override_forbidden=true`
- `synthetic_can_select_winner=false`
- `contract_sha256`
- realized-world/truth/manifest SHA fields when later available

The adapter must fail closed if:

- the canonical V79 contract SHA differs from the bound value without an explicit supersession record;
- required truth fields are missing;
- a `NOT_ESTIMABLE` row is given PASS/FAIL;
- a diagnostic row is used as target-promotion authority;
- Q10/Q11 are used unpaired for operator-invariance authority;
- a synthetic PASS is used to override real FAIL/NOT_ESTIMABLE;
- an aggregate synthetic score is serialized as a winner decision.

## 14. Future synthetic extensions

The current V79 program should not be modified from this target-discovery lane. If later scientific review decides that additional synthetic truths are worth adding, they must be requested as a separate prospective synthetic extension before target outcomes are opened.

The highest-value missing truths are:

1. an explicit multigene shared latent state for C1;
2. independently planted broad/mesoscale relational geometry for C2, including negative worlds with no relational structure;
3. independently planted query-conditioned cross-gene context for C3, including wrong-q and q-agnostic negative worlds;
4. a composite world in which C2 and C3 truths coexist so C4 increment is identified;
5. independently planted regulatory/chromatin truth if C5 synthetic qualification is desired.

These extensions are optional. Current V79 remains useful for nuisance falsification, transfer, support and uncertainty without them.

## 15. Contingency terminals

Synthetic crosswalk execution must permit at least:

- `SYNTHETIC_CROSSWALK_INCOMPLETE__NO_SYNTHETIC_TARGET_AUTHORITY`
- `SYNTHETIC_DECISIVE_FALSIFIER_FAIL__CANDIDATE_INELIGIBLE_PENDING_REDESIGN`
- `SYNTHETIC_APPLICABLE_TESTS_PASS__SUPPORTING_ONLY__NO_TARGET_AUTHORITY`
- `SYNTHETIC_CLAIM_NOT_ESTIMABLE__NO_PASS_INFERRED`
- `MULTIPLE_REAL_CANDIDATES_SURVIVE_SYNTHETIC_FALSIFICATION__PROTECTED_HEAD_TO_HEAD_REQUIRED`
- `NO_REAL_TARGET_WINNER__SYNTHETIC_PASS_CANNOT_RESCUE`

## 16. Frozen interpretation law

The following law is controlling for target-discovery use of V79 synthetic evidence:

> Synthetic evidence is ground-truth evidence only for truth explicitly planted and authenticated in the generator. It may falsify a target design on an applicable truth-backed control, but it may not manufacture biological authority for a claim the generator does not contain. Real biological evidence remains authoritative for human target validity.

Terminal:

`TD_V79_SYNTHETIC_CROSSWALK_DESIGN_FROZEN__DECISIVE_VS_DIAGNOSTIC_VS_NOT_ESTIMABLE_SEPARATED__Q10_Q11_PAIRED_COUNTERFACTUAL_RESERVED__NO_TARGET_AUTHORITY__NO_TRAINING`
