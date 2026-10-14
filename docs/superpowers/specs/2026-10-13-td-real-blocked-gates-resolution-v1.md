# TD Real-Gate Blocker Resolution V1 — one-by-one prospective solutions

Status: `OUTCOME_BLIND_GATE_RESOLUTION_DESIGN__NO_BIOLOGICAL_EXECUTION_AUTHORITY`

This document responds to the Scientific Amendment V2 blocker list by attempting to solve every blocked gate rather than treating the set as a permanent quarantine. It is prospective and was written without opening current candidate outcomes. Where a gate still depends on a later-stage artifact, the dependency is named explicitly and the scientific rule is frozen as far as possible now.

Hard authority remains false for real TD execution, target selection, representation selection, TD60, Stage4, production EMA selection, pathology, and JEPA training.

## 1. Common decision principle

Direction alone is insufficient for magnitude/stability/increment claims. However, an arbitrary human-effect cutoff is also unjustified.

For gates that require substantive magnitude, use an **independent, prospectively frozen noise-relative margin** in the same metric as the gate. The margin must be derived without looking at the candidate's deciding outcome.

Two reusable reference classes are allowed:

1. `U_measurement` — measurement variability from independent same-cell count split / p-thinning realizations under a disjoint deterministic seed namespace, preserving cell, donor, source, operator, support, and address identity.
2. `U_refit` — algorithmic/refit variability from repeated, prospectively seeded fits of the same frozen estimator/probe on the same lawful training donors, evaluated on held-out donors.

For a donor-level effect `delta_d`, define the applicable substantive margin `m_d` prospectively from the matching reference class. When both are relevant, use the more conservative donor-level margin:

`m_d = max(U_measurement_d, U_refit_d)`

The deciding contrast is then `delta_d - m_d` (or the sign-reversed noninferiority form where smaller is better). Donor remains the biological replication unit. The existing exact donor sign/permutation machinery may adjudicate the donor contrasts at the already frozen gate-local alpha/family. Insufficient donor resolution returns `NOT_ESTIMABLE`.

This does not create a human biological effect-size constant. It asks whether the claimed increment/stability is larger than independently measured technical/refit variability in the same metric.

## 2. G2 — NONTRIVIAL_BIOLOGICAL_CONTENT

### Scientific question
Does the candidate carry held-out biological information beyond the strongest applicable frozen nuisance/shortcut baseline by more than expected technical/refit variability?

### Prospective estimand
For each held-out donor and applicable endpoint:

`delta_d = score(candidate)_d - max(score(B0), score(B1), score(B2), applicable score(B3))_d`

where the scoring orientation is prospectively standardized so larger is better. Baselines remain the frozen candidate-specific falsifier arms; no baseline may be added after outcome inspection.

### Margin
`m_d = max(U_refit_d, U_measurement_d)` for the same endpoint where both exist; otherwise the available qualified reference. The reference is generated under independent seed namespaces and cannot use candidate-selection outcomes.

### Decision
PASS only if the donor-primary contrast `delta_d - m_d` passes the frozen one-sided donor test for every required endpoint/source stratum with no aggregate rescue. FAIL when the contrast is estimably nonpositive in a required stratum. Insufficient resolution is `NOT_ESTIMABLE`.

### Resolution state
`DESIGN_RESOLVED__EXECUTION_REQUIRES_QUALIFIED_REFERENCE_ARTIFACT`

## 3. G6 — TEACHER_INFORMATION_ADVANTAGE

### Scientific question
Does richer lawful teacher evidence provide information about the frozen teacher target that is not recoverable from the student's permitted evidence?

### Comparator protocol
Use a diagnostic probe, not the JEPA architecture. The probe family is fixed to **multi-output ridge** because ridge is already a recurrent project diagnostic and supports exact matched-compute comparison without introducing a new neural architecture.

For every outer held-out donor:

1. standardize features using training donors only;
2. fit one ridge probe from student-permitted evidence to the frozen target;
3. fit the identical ridge protocol from teacher-lawful evidence to the same target;
4. choose ridge regularization only inside the training donors by deterministic nested donor-level CV under one frozen alpha-search procedure;
5. use identical outer splits, inner splits, target preprocessing, metric, optimization library/version, and model-selection rule for both probes;
6. no target or held-out donor values may influence alpha selection;
7. one and only one out-of-fold score is emitted per held-out donor.

The exact alpha bracketing/refinement implementation must be hash-bound before execution. A later implementation may reuse the already documented donor-level ridge bracketing/refinement machinery only after equivalence audit.

### Estimand
For loss orientation where smaller is better:

`delta_d = loss(student-evidence probe)_d - loss(teacher-evidence probe)_d`

### Margin
`m_d = U_refit_d`, measured from repeated prospectively seeded refits of the same probe protocol. Where target measurement noise is relevant, use `max(U_refit_d, U_measurement_d)`.

### Decision
PASS only when teacher evidence improves held-out donor prediction by more than the independent margin. FAIL when an estimable required contrast is nonpositive. Insufficient precision -> `NOT_ESTIMABLE`.

### Resolution state
`DESIGN_RESOLVED__IMPLEMENTATION_REQUIRES_PROBE_EQUIVALENCE_AUDIT_AND_HASH_FREEZE`

## 4. G7 — EVIDENCE_CONVERGENCE

### Scientific question
Does the candidate stabilize as lawful biological evidence approaches the full prospectively declared evidence set?

### Evidence ladder
For each candidate, the ladder is the ordered list of nested evidence-rights blocks declared in its frozen candidate manifest. It is not a tunable fraction grid. At least three nested biological-evidence levels are required. Measurement depth is excluded from this ladder and remains G8.

### Estimand
Let `Z_k(d)` be the held-out donor candidate state at evidence level `k`, aligned under the candidate's frozen representation-invariant metric. Define terminal displacement:

`delta_terminal_d = D(Z_full(d), Z_penultimate(d))`

Earlier levels are descriptive only; strict adjacent monotonicity is not required.

### Margin
Use the full-evidence `m_d = max(U_measurement_d, U_refit_d)` in the same state-distance metric.

### Decision
PASS when the terminal evidence increment is noninferior to the independently measured noise/refit floor, i.e. `m_d - delta_terminal_d` passes the donor-primary noninferiority test, while G2 remains independently PASS. No requirement is imposed that every earlier step decrease monotonically. If fewer than three lawful evidence levels exist, return `NOT_ESTIMABLE` rather than inventing a ladder.

### Resolution state
`DESIGN_RESOLVED__EXECUTION_DEPENDS_ON_G8_REFERENCE_AND_CANDIDATE_EVIDENCE_MANIFEST`

## 5. G8 — MEASUREMENT_ROBUSTNESS

### Scientific question
Does measurement-depth stochasticity alter the candidate more than expected from an independently generated measurement replicate at the same depth?

### Frozen mechanics retained
Depth grid remains exactly `25%, 50%, 75%, 100%`. Same-cell raw-count support, donor/source/operator/address identity and measured-zero semantics are preserved.

### Independent reference construction
For each donor/cell and each p in `{0.25, 0.50, 0.75}` generate two independent p-thinnings, `A_p` and `B_p`, under a calibration seed namespace frozen before candidate outcomes. Generate the deciding p-thinning `T_p` under a disjoint evaluation seed namespace. `100%` is the full-count anchor.

For each donor and p:

- `reference_d,p = D(candidate(A_p), candidate(B_p))`
- `test_d,p = D(candidate(full), candidate(T_p))`

The displacement metric D is candidate-specific but must be frozen before values and use the same scale on both sides.

### Decision
For each required p, test donor-primary noninferiority of `reference_d,p - test_d,p`. PASS requires no required depth to be worse than its independently generated same-depth measurement reproducibility reference. Any estimable worse depth is FAIL. Insufficient donor/support resolution at a required depth is `NOT_ESTIMABLE`.

This replaces the withdrawn shared-derivation zero-margin rule with an independent same-depth technical reference in identical units.

### Resolution state
`DESIGN_RESOLVED__REFERENCE_CAN_BE_GENERATED_BEFORE_CANDIDATE_ADJUDICATION`

## 6. G9 — LEARNED_TEACHER_CONTINUITY

### Scientific question
Does learned rich-state geometry recur under disjoint donor-balanced refits more strongly than donor-preserving null geometry and within the expected refit/measurement variability?

### Estimand
Construct two prospectively disjoint donor-balanced training views, fit the same frozen teacher construction independently, and align states only by the candidate's frozen invariant transform (e.g. orthogonal Procrustes when appropriate). On held-out donors compute:

- observed cross-view geometry displacement `D_obs_d`;
- donor-preserving identity-shuffled/null displacement distribution `D_null_d`;
- independent refit/measurement margin `m_d`.

Define null advantage `delta_d = median(D_null_d) - D_obs_d` (larger is better).

### Decision
PASS requires both:

1. `delta_d - U_refit_d` passes donor-primary recurrence testing; and
2. `m_d - D_obs_d` passes donor-primary stability/noninferiority testing.

If either required component is unresolved -> `NOT_ESTIMABLE`; an estimable failure of either is FAIL.

### Resolution state
`DESIGN_RESOLVED__IMPLEMENTATION_REQUIRES_FROZEN_ALIGNMENT_METRIC_PER_LEARNED_TARGET`

## 7. G11 — TRANSFER

### Scientific question
Does the candidate transfer on every population dimension that the prospective population/evidence contract says it is allowed to claim?

### Applicability law
The decision rule is resolved now. The exact candidate-by-transfer matrix must be generated and frozen from the **static real-tournament population/evidence-rights registry before biological outcomes are opened**. Runtime discovery of 'whatever strata exist' is forbidden.

For each candidate and dimension (`DONOR`, `SOURCE`, `OPERATOR_MATRIX`, `STUDY_FAMILY`, `TECHNOLOGY`, optional specialist dimension), the frozen matrix must contain exactly one of:

- `REQUIRED` — at least two lawful levels and the candidate claims transfer across them;
- `NOT_APPLICABLE_STRUCTURAL` — the candidate claim does not include that dimension by construction;
- `BLOCKED_DEPENDENCY` — the population/support registry needed to define the contrast is not yet frozen.

### Decision
Every `REQUIRED` entry receives a held-out-level donor-primary transfer contrast against the corresponding in-domain performance, with non-compensation across required dimensions. Required transfer may use the same noise-relative margin family as G2 when a substantive decrement margin is needed. `NOT_APPLICABLE_STRUCTURAL` is not a PASS. `BLOCKED_DEPENDENCY` yields `NOT_ESTIMABLE` for G11 until resolved.

### Resolution state
`DECISION_LAW_RESOLVED__EXACT_MATRIX_WAITS_FOR_REAL_TOURNAMENT_POPULATION_REGISTRY_FREEZE`

This is a stage dependency, not an unsolved scientific rule.

## 8. G12 — COVERAGE_ABSTENTION

### Scientific question
Does the candidate make claims only where support exists, without forced prediction, while accurately reporting its support envelope?

### Claim-scope solution
Do not invent a universal minimum percentage. Freeze the candidate's claim scope to the exact supported population strata represented by its pre-outcome support registry.

PASS requires all of the following:

1. every claimed unit is physically supported for the required evidence;
2. structurally unsupported units are abstained, never imputed;
3. measured zero remains a valid measurement;
4. every claimed donor/source/operator/query stratum meets the separate inferential-resolution requirement for the gate being interpreted;
5. all abstention reasons and denominators are reported;
6. no unsupported broader population statement is made.

Observed supported fraction is reported descriptively but is not itself optimized or thresholded. If a broader population claim is scientifically required, that broader claim must be frozen before outcomes and unsupported strata make G12 `NOT_ESTIMABLE` rather than shrinking scope post hoc.

### Resolution state
`DESIGN_RESOLVED_BY_PROSPECTIVE_CLAIM_SCOPE__NO_ARBITRARY_COVERAGE_PERCENTAGE`

## 9. S1 — DISJOINT_VIEW_RECURRENCE

Use the same disjoint-view recurrence engine as G9 but apply it to the candidate's shared-state recurrence endpoint. Observed recurrence must defeat the donor-preserving null by more than refit variability and satisfy the stability margin. No raw p-value alone is sufficient.

State: `DESIGN_RESOLVED__SHARES_QUALIFIED_RECURRENCE_ENGINE_WITH_G9`.

## 10. S2 — DONOR_BALANCED_SUBSPACE_STABILITY

Use donor-balanced repeated refits under frozen disjoint donor partitions. Align subspaces only by the frozen orthogonal-invariant transform. For each held-out donor compute subspace displacement and compare against both donor-label-shuffled null geometry and `U_refit/U_measurement` margin.

PASS requires null defeat and stability/noninferiority, non-compensating across required source strata.

State: `DESIGN_RESOLVED__SHARES_QUALIFIED_RECURRENCE_ENGINE_WITH_G9`.

## 11. R1 — SCALE_FREE_RELATIONAL_RECURRENCE

### Estimand
Within each held-out donor, compute the frozen scale-free relational statistic on two disjoint lawful views. The default scalar is Spearman correlation of the same prospectively frozen pairwise relational quantities; transform with Fisher z only for numerical comparability, not parametric inference.

Generate a donor-preserving relation-label permutation null under frozen seeds. Define:

`delta_d = z(rho_observed_d) - median(z(rho_null_d))`

and estimate `U_refit_d` from independent refits/views under a disjoint seed namespace.

### Decision
PASS only when `delta_d - U_refit_d` passes donor-primary testing in every required scale/source stratum. Fine-scale failure remains fine-scale only and cannot be generalized to absence of relational biology.

State: `DESIGN_RESOLVED__NO_FINE_LOCALITY_MINING_ALLOWED`.

## 12. R4 — INCREMENT_OVER_C1_SHARED

### Estimand
On identical held-out donor cases and the same primary endpoint:

`delta_d = score(C2)_d - score(C1)_d`

### Margin
`m_d = max(U_refit_d, U_measurement_d)` for the matched endpoint.

### Decision
PASS requires `delta_d - m_d` donor-primary PASS and no worsening on required transfer, shortcut, coverage/abstention, and uncertainty dimensions. C1 must already be independently qualified. C2 cannot rescue a failed C1 gate.

State: `DESIGN_RESOLVED__EXECUTION_DEPENDS_ON_C1_QUALIFICATION_AND_REFERENCE_MARGIN`.

## 13. C6 — INCREMENT_OVER_C1_C3

Comparator semantics remain the frozen factorial question: C6 must add information/robustness beyond the stronger independently qualified constituent among C1 and C3 on the matched held-out cases.

For each donor:

`delta_d = score(C6)_d - max(score(C1)_d, score(C3)_d)`

The stronger constituent identity is determined on the predeclared primary metric only and not selected separately per secondary dimension. Use `m_d = max(U_refit_d, U_measurement_d)`.

PASS requires donor-primary `delta_d - m_d` PASS plus non-worsening on transfer, shortcut dependence, coverage/abstention and uncertainty separation. Both C1 and C3 must already independently qualify. C6 FAIL/NE never deletes C1 or C3.

State: `DESIGN_RESOLVED__EXECUTION_DEPENDS_ON_C1_AND_C3_QUALIFICATION_AND_REFERENCE_MARGIN`.

## 14. C4 — INCREMENT_OVER_CONSTITUENTS

The later C6 factorial freeze controls: the prospective comparator is C6, not an opportunistically chosen constituent.

For each donor:

`delta_d = score(C4)_d - score(C6)_d`

Use the same matched endpoint and `m_d = max(U_refit_d, U_measurement_d)`.

PASS requires donor-primary `delta_d - m_d` PASS plus non-worsening on transfer, shortcut, coverage/abstention and uncertainty dimensions. C6 must be independently qualified first. If C6 is not qualified, the C4 increment is `NOT_ESTIMABLE`; no alternate comparator is permitted. C4 FAIL/NE never deletes independently qualified C1/C2/C3/C6 blocks.

State: `DESIGN_RESOLVED__EXECUTION_DEPENDS_ON_C6_QUALIFICATION_AND_REFERENCE_MARGIN`.

## 15. Dependency ordering

The previous flat '13 blocked rules' list is replaced by this prospective dependency graph:

1. qualify/generate reusable `U_refit` and `U_measurement` reference artifacts;
2. freeze the static real-tournament population/evidence/support registry;
3. materialize G11 applicability matrix and G12 candidate claim scopes;
4. qualify the G6 matched ridge-probe executor;
5. qualify the common recurrence/stability engine used by G9/S1/S2 and the relational recurrence specialization R1;
6. materialize G2 and G8;
7. materialize G7 after G8/evidence-ladder dependencies exist;
8. materialize R4 after C1 is independently qualified;
9. materialize C6 increment after C1+C3 independently qualify;
10. materialize C4 increment after C6 independently qualifies.

No current biological outcomes are needed to complete steps 1–5 as engineering/scientific qualification work. Steps 6–10 may compute biological gate outcomes only under separate real-TD authority.

## 16. Updated readiness semantics

A gate may now be classified as:

- `DESIGN_RESOLVED_READY_FOR_TDD` — complete prospective scientific rule exists;
- `DESIGN_RESOLVED_WAITING_STATIC_DEPENDENCY` — rule exists but a pre-outcome registry/reference artifact must first be frozen;
- `OUTCOME_EXECUTION_NOT_AUTHORIZED` — executor may be qualified on fixtures but real values remain closed.

None of the 13 gates remains in a generic 'no solution attempted' state under this V1 resolution.

## 17. Authority terminal

`BLOCKED_GATE_SCIENCE_RESOLVED_PROSPECTIVELY__REFERENCE_AND_STATIC_DEPENDENCIES_REMAIN__BIOLOGICAL_OUTCOMES_UNREAD__REAL_TD_EXECUTION_OFF__TARGET_NONE__REPRESENTATION_NONE__STAGE4_OFF__TRAINING_OFF`
