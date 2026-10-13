# TD Real-Gate Prospective Contracts — Design

Status: `DESIGN_ONLY__OUTCOME_BLIND__NO_REAL_TD_AUTHORITY`

## Purpose

Materialize a prospective scientific contract for the 28 unique real-TD biological gate rules that remain `RULE_NOT_MATERIALIZED` after the audited structural-executor work. This design does not inspect candidate outcomes, execute real TD, select a target or representation, choose TD60/EMA/Stage4, or authorize training.

The design is stacked on controller convergence head `054a87a117aa0bbefafc5032fa354544e038162a`, where the sealed synthetic relational test is independently qualified but the real tournament remains blocked.

## Governing question

Every rule below must answer a previously unresolved qualification question. None is introduced to rescue or reinterpret a closed result.

- Synthetic phase-2 answered whether the relational TD test behaves correctly on sealed known-truth cases. It did **not** answer whether any human candidate is biologically valid.
- PR #313 materialized custody, case-ledger, falsifier, authenticated-gate-output and one-shot execution mechanics. It did **not** materialize gate-specific biological estimands or thresholds.
- PRs #333–#335 established the exact missing-rule inventory and reusable statistical components. They intentionally did **not** promote historical descriptive cutoffs.

## Frozen boundaries

1. Biological replication unit is donor.
2. Source/operator is an observation process, not a biological replicate.
3. `MEASURED_ZERO` is a valid measurement.
4. `STRUCTURALLY_UNSUPPORTED` means abstain; imputation is forbidden.
5. `NOT_ESTIMABLE` is not `FAIL`.
6. Every required constituent gate is non-compensating.
7. A composite PASS cannot rescue a constituent FAIL or NOT_ESTIMABLE.
8. C6/C4 failure cannot erase independently qualified constituent blocks.
9. C5 is specialist-only and can never become the sole foundation portfolio.
10. Historical descriptive thresholds are not promoted merely because they exist.
11. Candidate outcomes remain unread while this contract is defined and qualified.
12. Real-tournament QUALIFY remains ineligible until every required gate has a hash-bound callable rule.

## Design choice

Three approaches were considered.

### A. Fixed hard effect-size thresholds

Reject. There is no defensible frozen human-effect calibration for most gates, and selecting cutoffs now from historical or current candidate values would leak outcomes into qualification.

### B. Pure direction-only testing

Reject as a universal policy. It is appropriate for recurrence and baseline-defeat questions, but insufficient for stability/robustness questions unless the comparison is anchored to a prospectively defined nuisance/null process.

### C. Recommended: prospective donor-primary contrasts + independently defined null/nuisance comparators

Use one common inferential core and gate-specific estimands. Gates that ask whether a candidate adds information use paired donor-level loss/score contrasts against predeclared baselines. Gates that ask whether a structure is stable use a rotation/scale-invariant recurrence statistic compared with a donor-preserving null or measurement-noise comparator. Structural/provenance gates use exact predicates rather than p-values.

This avoids copying old numeric cutoffs, preserves donor-primary inference, and makes failures interpretable by gate.

## Common quantitative law

### Eligible observations

A case is value-eligible only if its support state is `MEASURED_POSITIVE` or `MEASURED_ZERO`. `STRUCTURALLY_UNSUPPORTED` cases contribute no numerical value and remain explicit abstentions.

### Base prediction loss

For a candidate target vector `T`, candidate student prediction `S`, and baseline prediction `B` on the same eligible case:

- `L_student = mean((T - S)^2)`
- `L_baseline = mean((T - B)^2)`
- `delta_case = L_baseline - L_student`

Positive `delta_case` means the candidate student contains more target-relevant information than the baseline.

For a donor, `delta_donor` is the arithmetic mean of eligible case deltas for that donor. Cells are never treated as independent replicates.

### Inferential family

Each gate owns one prospective familywise error budget:

`alpha_family = 0.01`

If a gate requires `m` simultaneous donor-primary subtests, each uses:

`alpha_eff = 0.01 / m`

using the already-audited exact two-sided sign test. A subtest PASS requires positive orientation, statistical resolution at `alpha_eff`, and the exact sign-test PASS. If the available nonzero donor count cannot attain the required resolution, the subtest is `NOT_ESTIMABLE`. A statistically resolved non-PASS subtest is `FAIL`.

Required subtests combine with frozen non-compensation:

`FAIL > NOT_ESTIMABLE > PASS`.

No donor-count floor is invented beyond the exact mathematical resolution requirement and gate-specific structural eligibility.

### Null/permutation comparisons

When a gate requires a stability or recurrence metric rather than a prediction baseline, the comparator must be generated without using candidate labels/outcomes for tuning. Allowed comparators are:

- donor-preserving random pairing/permutation;
- matched wrong-cell or fine-neighborhood wrong-cell pairing from the frozen case ledger;
- query-specific frozen falsifier baselines;
- measurement pseudoreplicates generated by a prospectively fixed thinning/split procedure;
- independently held construction/evaluation evidence declared by provenance before value read.

Permutation counts must be sufficient for `alpha_eff` using the already-audited minimum-permutation-resolution helper. Insufficient null resolution is `NOT_ESTIMABLE`.

### Rotation/scale-invariant recurrence statistic

For target geometries that may rotate, relabel axes, or change arbitrary latent sign, recurrence is assessed on the same held-out anchor cases using pairwise Euclidean-distance ranks rather than raw coordinates.

For each donor and each pair of independently constructed views/refits:

1. compute all eligible pairwise distances among held-out anchor cases in each view;
2. compute Spearman rank correlation between the two distance vectors;
3. compare that observed recurrence with donor-preserving random re-pairings of anchor identities;
4. form a donor-level positive-orientation contrast between observed recurrence and its null comparator.

The gate then uses the common donor-primary sign-test law. This metric does not assign biological meaning to individual latent axes.

## Gate contracts

### G2 — nontrivial biological content

**Question:** Does the target/student contain reproducible biological information beyond trivial and technical prediction?

Required subtests are candidate-specific mandatory trivial/technical baselines that apply to the candidate, at minimum `constant_train_mean` and `technical_operator_only`; `address_support_operator` is included wherever it is a mandatory falsifier.

Estimand: donor-level MSE improvement over each required baseline.

PASS: every required baseline-defeat subtest PASS.
FAIL: any required subtest FAIL.
NOT_ESTIMABLE: no FAIL and at least one required subtest NE.

No separate absolute effect-size threshold is introduced: “nontrivial” is defined prospectively as reproducible information beyond the frozen trivial/technical alternatives.

### G3 — correct-cell specificity

**Question:** Is target information specific to the correct biological cell rather than transferable from a matched wrong cell?

Estimand: donor-level `matched_wrong_cell_loss - correct_student_loss` using the frozen cross-donor matched-wrong-cell ledger.

PASS/FAIL/NE: common donor-primary law.

If no legal matched wrong-cell partner exists for enough donors to resolve the test, return NE rather than synthesizing a partner.

### G4 — donor recurrence

**Question:** Is the candidate advantage recurrent across donors rather than driven by a few high-cell-count donors?

Estimand: one predeclared candidate-primary donor delta. For foundation/query/regulatory blocks this is the G2 constant-mean defeat delta; for relational candidates it is the R1 recurrence delta once R1 is active.

PASS/FAIL/NE: common donor-primary law. The donor delta source is fixed by candidate class before outcomes are read.

### G5 — source replication

**Question:** Does the biological effect recur within every required source where the candidate is structurally measurable?

For each required source, run the G4 donor-primary estimand using only donors from that source. Source statuses combine non-compensatingly.

A source that is structurally unsupported for the candidate is not silently counted as failure. Its predeclared applicability determines either `NOT_APPLICABLE` at contract construction or NE if the candidate claimed that source but lacks resolvable support.

No averaging across sources is permitted.

### G6 — teacher information advantage

**Question:** Does the richer teacher evidence define target information not recoverable from the permitted student evidence alone, without q-scalar leakage?

Prerequisite: structural leakage gates Q1/Q2/Q3 where applicable, plus the qualified query-information guard.

Estimand: on held-out cases, compare a predictor permitted to use the declared richer teacher evidence with the strongest matched predictor restricted to the exact student evidence surface, both evaluated against the same target object. Donor delta is `student_only_loss - rich_teacher_loss`.

PASS/FAIL/NE: common donor-primary law.

This gate does not permit the queried scalar, target value, or target-normalization statistic to leak into the student-restricted comparator.

### G7 — evidence convergence

**Question:** Does the target definition stabilize as independent evidence increases rather than wander with sampling noise?

Before execution, freeze an evidence ladder of nested construction budgets using donor-balanced training evidence only. The ladder must contain at least three levels and must not be selected from candidate outcomes.

For each adjacent ladder pair, construct targets independently and evaluate recurrence on the same held-out anchor set using the rotation/scale-invariant distance-rank statistic. Each adjacent step is compared against donor-preserving random pairing.

PASS: all adjacent recurrence subtests PASS and the final two ladder levels do not show a direction reversal.
FAIL: any resolved adjacent recurrence subtest FAIL or a resolved final-step reversal.
NE: insufficient donor/null resolution without a resolved failure.

No historical convergence cutoff is imported.

### G8 — measurement robustness

**Question:** Is the claimed target relation robust to plausible measurement noise rather than sequencing depth/read allocation?

Use prospectively fixed measurement pseudoreplicates that preserve donor/cell identity and never convert structural absence into measured zero. The perturbation mechanism is fixed before candidate value read.

For each donor, compare target/student behavior between the original observation and its measurement pseudoreplicate using the candidate-primary score. The null comparator is the change expected from paired measurement pseudoreplicates themselves, not a historical human cutoff.

Donor delta is oriented so positive means biological signal degradation is no worse than the prospectively generated measurement-noise comparator.

PASS/FAIL/NE: common donor-primary law across all required measurement perturbations, non-compensating.

### G9 — learned-teacher continuity

**Question:** If a target depends on a learned teacher, is its target geometry recurrent under independent donor-balanced teacher refits?

Construct at least two independent teacher refits with donor-balanced training partitions and evaluate them on a fixed held-out anchor set. Use rotation/scale-invariant distance-rank recurrence against donor-preserving random alignment.

PASS/FAIL/NE: common donor-primary law.

Historical TD60 is not substituted for this generic gate. If a later selected portfolio contains the relational learned-teacher family, TD60 remains a separate conditional downstream continuity screen under its own authority.

### G10 — collapse/shortcut resistance

**Question:** Does the candidate defeat every mandatory shortcut/falsifier applicable to it?

For each mandatory falsifier in the frozen candidate registry, compute the donor-level MSE improvement already emitted by the falsifier engine.

PASS: every mandatory falsifier-defeat subtest PASS.
FAIL: any resolved falsifier-defeat subtest FAIL.
NE: no failure and at least one required falsifier lacks resolution.

Aggregate mean performance cannot rescue a failed falsifier.

### G11 — transfer

**Question:** Does the target relation survive the predeclared held-out transfer dimensions that are biologically meaningful for the candidate?

Transfer dimensions are frozen before value read from available metadata: donor is always required; source/operator/study/technology are required only where they represent a real held-out stratum for that candidate and are not structurally unsupported.

Within each required transfer stratum, compute the candidate-primary donor delta without pooling across strata. All required strata combine non-compensatingly.

PASS/FAIL/NE: common donor-primary law per stratum and frozen required-strata aggregation.

A source/operator failure limits the corresponding transfer claim; it is not evidence that the biological program is globally absent.

### G12 — coverage/abstention

**Question:** Is there enough lawful measured support to make every claim the candidate proposes?

This is an estimability gate, not a prevalence gate.

For each gate-required stratum, record eligible donors, eligible measured cases, structural unsupported cases, and the minimum nonzero donor count required by that gate's `alpha_eff`.

PASS: every claimed required stratum has sufficient lawful support to make its required downstream tests mathematically resolvable and all structural-abstention rules are obeyed.
FAIL: only a structural contract violation (imputation of unsupported values, counting unsupported as zero, or claiming support known to be absent).
NOT_ESTIMABLE: lawful support exists but is insufficient for inferential resolution.

No arbitrary minimum cell count is introduced.

### S1 — disjoint-view recurrence

**Question:** Does the shared target geometry recur when constructed from independent evidence views?

Construct two predeclared disjoint evidence views with no shared target-construction observations. Evaluate both on a common held-out anchor set. Use distance-rank recurrence against donor-preserving random alignment.

PASS/FAIL/NE: common donor-primary law.

### S2 — donor-balanced subspace stability

**Question:** Is shared-state geometry stable to which donors constructed it?

Create donor-balanced refits from predeclared disjoint donor partitions. Evaluate on a common donor-held-out anchor set. Use distance-rank recurrence against donor-preserving random alignment.

PASS/FAIL/NE: common donor-primary law across all required refit pairs.

No latent axis is interpreted biologically merely because the subspace recurs.

### S3 — identity/support baseline defeat

**Question:** Does the shared target contain information beyond cell identity and measurement-support structure?

Estimand: donor-level MSE improvement over `identity_support_only` baseline.

PASS/FAIL/NE: common donor-primary law.

### R1 — scale-free relational recurrence

**Question:** Does relational structure recur across independent donor-balanced constructions at the allowed broad/mesoscale support without reopening fine-scale mining?

For each independent construction, derive the candidate's relational pairwise ordering on a common held-out anchor set. Compare orderings using distance/rank recurrence against donor-preserving randomized pairing.

Only the already-frozen broad/mesoscale support is eligible. No new locality search is allowed.

PASS/FAIL/NE: common donor-primary law.

The qualified synthetic relational test validates this gate machinery conceptually; it does not provide the human biological answer.

### R3 — fine-neighbor wrong-cell defeat

**Question:** Does the relational target outperform the frozen fine-neighborhood wrong-cell null where such a partner is lawfully available?

Estimand: donor-level `fine_neighbor_wrong_cell_loss - relational_student_loss` from the frozen case ledger.

PASS/FAIL/NE: common donor-primary law. Lack of legal fine-neighbor partners yields NE, not a biological FAIL.

### R4 — increment over C1 shared

**Question:** Does C2 contribute relational information beyond an independently qualified C1 shared target?

Prerequisite: C1 must independently PASS its required gates; C2 cannot rescue C1.

On the same held-out cases, compare C2 prediction of its relational target with the strongest C1-only predictor permitted by the frozen field firewall. Donor delta is `C1_only_loss_on_relational_target - C2_relational_loss`.

PASS/FAIL/NE: common donor-primary law.

C2 failure affects the relational increment claim only and does not erase C1.

### Q4 — q-count-only defeat

Estimand: donor-level MSE improvement over the frozen `q_count_only` baseline on the query target.

PASS/FAIL/NE: common donor-primary law.

### Q5 — q-address-only defeat

Estimand: donor-level MSE improvement over the frozen `q_address_only` baseline.

PASS/FAIL/NE: common donor-primary law.

### Q6 — query-agnostic defeat

Estimand: donor-level MSE improvement over the frozen `query_agnostic` predictor.

PASS/FAIL/NE: common donor-primary law.

### Q7 — wrong-q defeat

Estimand: donor-level MSE improvement over the frozen `wrong_q` predictor using a different query identity under the same lawful support/operator constraints.

PASS/FAIL/NE: common donor-primary law. If no lawful wrong-q comparator exists, return NE.

### Q8 — technical-plus-q defeat

Estimand: donor-level MSE improvement over the frozen `technical_plus_q` predictor.

PASS/FAIL/NE: common donor-primary law.

### C6 increment over C1 + C3

**Question:** Does a fused shared+query implementation add information beyond keeping independently qualified C1 and C3 blocks separate, without degrading either constituent?

Prerequisites: C1 and C3 each independently PASS their required gates.

Primary estimand: donor-level held-out loss improvement of the fused C6 prediction over the concatenated/separate C1+C3 predictions evaluated on the same constituent targets.

Nondegradation subtests: C6 must not convert either constituent's required transfer, shortcut-resistance, coverage/abstention, or uncertainty status from PASS to FAIL/NE under matched evidence.

PASS: increment subtest PASS and all nondegradation subtests PASS.
FAIL/NE: common non-compensating rule.

C6 FAIL/NE never deletes independently qualified C1 or C3.

### C4 increment over constituents

**Question:** Does a fused shared+relational+query implementation add information beyond the strongest independently qualified constituent portfolio, without degrading constituent claims?

Prerequisites: relevant C1/C2/C3 constituents independently satisfy their own gates. C4 cannot create permission for a failed constituent.

Primary estimand: donor-level held-out loss improvement of fused C4 over the strongest lawful separate constituent prediction evaluated on the same target blocks.

Required nondegradation: transfer, shortcut resistance, coverage/abstention and uncertainty behavior for every retained constituent.

PASS/FAIL/NE: same non-compensating composite rule as C6.

C4 FAIL/NE never erases independently qualified constituent blocks.

## C5 regulatory-specialist structural contract

C5 remains specialist-only. These predicates are prospective structural gates; they do not assert that regulatory evidence is biologically correct.

### M1 — circularity control

Before value access, the C5 evidence manifest must classify every raw evidence object into exactly one or more declared roles: `TARGET_CONSTRUCTION`, `STUDENT_INPUT`, `EVALUATION_ONLY`, `SUPPORT_ONLY`.

PASS requires that no raw molecular value or deterministic transform of it is used both to construct the regulatory target and to serve as evaluation-only evidence for that same claim. Provenance is checked transitively through declared derivations.

Any undeclared lineage or construction/evaluation overlap is FAIL. Missing provenance needed to decide is NE.

### M2 — independent provenance

PASS requires at least one predeclared `EVALUATION_ONLY` evidence stream whose raw measurement lineage is disjoint from C5 target construction and student input for the claim being tested. Different file names derived from the same raw measurement do not count as independent.

If no such stream is structurally available, NE. If a supposedly independent stream is lineage-overlapping, FAIL.

This gate establishes independence of evidence provenance, not biological agreement; agreement is tested by applicable G2/G3/G4/G5/G10/G11 gates.

### M3 — causal-claim false

C5 output metadata must declare `claim_type = ASSOCIATIONAL_OR_PREDICTIVE` and must not expose a causal-promotion flag. The regulatory specialist may be used as a predictive/critic target but cannot by this gate claim intervention, necessity, sufficiency or causal direction.

PASS is the exact structural predicate above. Any causal claim is FAIL. Missing claim metadata is FAIL closed.

### M4 — support abstention

For every regulatory target dimension, the evidence manifest must declare the measurement/support operator. `STRUCTURALLY_UNSUPPORTED` values must be absent from numerical target construction and evaluation, never zero-filled or imputed. `MEASURED_ZERO` remains a valid measurement.

PASS if all values obey this rule. Any unsupported-to-numeric conversion is FAIL. If support provenance is missing, NE.

## Multiplicity and gate ownership

Multiplicity is local to a gate's frozen simultaneous subtests. It is not shared across candidates to create a hidden aggregate tournament score. Candidate status remains the non-compensating aggregation of its required gates.

Protected head-to-head/confirmation, if later reached, receives its own predeclared multiplicity family and cannot reuse exploratory tournament p-values as confirmation evidence.

## Qualification plan boundary

Implementing these contracts is a separate engineering phase. Before any real outcome read, that phase must:

1. encode the 28 rules in a machine-readable registry;
2. materialize callable executors with exact estimand and decision-rule hashes;
3. add hostile synthetic/unit fixtures for PASS, FAIL and NE for each rule family;
4. prove donor-primary aggregation, source non-compensation and support abstention;
5. bind the existing structural executor bundle without modifying it;
6. produce a new 198-row readiness matrix;
7. independently audit the launch package;
8. keep all real-execution/target/representation/TD60/Stage4/training authority false.

Only after every required candidate×gate role is `CALLABLE_AND_QUALIFIED` may the controller consider a separate real-tournament QUALIFY authorization.

## Explicitly unresolved by this design

This design does not choose:

- a target winner;
- a representation architecture;
- teacher topology;
- EMA half-life;
- TD60 execution;
- pathology-conditioned modeling;
- Stage4;
- multimodal training;
- JEPA training.

It also does not reinterpret historical closed experiments or convert synthetic qualification into human biological evidence.

Terminal:

`PROSPECTIVE_28_GATE_CONTRACT_DESIGNED__OUTCOMES_UNREAD__IMPLEMENTATION_NOT_YET_AUTHORIZED__REAL_TD_OFF`
