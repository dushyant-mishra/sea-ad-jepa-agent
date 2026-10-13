# TD Real-Gate Prospective Contracts — Self-Audit Amendment

Status: `DESIGN_AMENDMENT__OUTCOME_BLIND__SUPERSEDES_CONFLICTING_SECTIONS_OF_2026-10-13_DESIGN`

Parent design:
`docs/superpowers/specs/2026-10-13-td-real-gate-prospective-contracts-design.md`

This amendment was produced by re-auditing the new design against the frozen multitarget V2, measurement/noise-floor prefreeze, C6 candidate freeze, PR #313 framework qualification, and the current controller convergence state. No candidate outcomes were opened.

Where this amendment conflicts with the parent design, this amendment controls.

## A1. Naming firewall: historical stage G6/G7 is not promotion-gate G6/G7

The historical documents named `G6/G7` for corrected value materialization/cross-lane corroboration stages. Those labels are historical execution-stage names and must not be conflated with current promotion gates:

- `G6_TEACHER_INFORMATION_ADVANTAGE`
- `G7_EVIDENCE_CONVERGENCE`

No historical G6/G7 PASS, receipt, cutoff, or implementation is evidence for the current promotion gates merely because the labels overlap.

## A2. G2 must preserve the frozen B0/B1/B2/B3 requirement

The parent design was too narrow in describing G2 baselines.

Authoritative G2 contract:

`G2_NONTRIVIAL_BIOLOGICAL_CONTENT` requires donor-primary defeat of:

- B0 `constant_train_mean`;
- B1 `technical_operator_only`;
- B2 `address_support_operator`;
- applicable B3 `matched_wrong_cell`.

Each required baseline is a separate subtest under the gate's Bonferroni family. All combine non-compensatingly.

G3 remains a separate interpretability gate for correct-cell specificity even though it reuses B3 evidence. Shared raw evidence may feed two prospectively distinct gate decisions; the gate identities and decision-rule hashes remain separate.

## A3. Relational G3 must include B4 where estimable

Authoritative G3 contract:

All candidates defeat B3 matched wrong cell.

Relational candidates additionally defeat B4 `fine_neighborhood_wrong_cell` where the frozen case ledger can lawfully construct it.

- B4 estimable and resolved non-PASS -> G3 FAIL.
- no legal B4 partner or inadequate donor resolution -> B4 subtest NE; G3 becomes NE unless another required subtest already FAILS.

R3 remains the relational-specific gate that preserves the fine-neighbor claim separately. As with B3/G2/G3, evidence may be reused while gate identities remain distinct.

## A4. G4 must not depend on R1

The parent design created an unnecessary dependency by proposing R1 as the recurrence delta for relational candidates.

Authoritative G4 contract:

G4 is the donor-recurrence adjudication of the candidate's primary predictive-information endpoint, independent of candidate-specific extension gates.

Primary endpoint by candidate block:

- shared block: donor-level improvement over B0 on `shared_target`;
- relational block: donor-level improvement over B0 on `relational_target`;
- query block: donor-level improvement over B0 on `query_target`;
- regulatory specialist: donor-level improvement over B0 on `regulatory_target`.

For a composite, each retained constituent block is evaluated separately and combined non-compensatingly. This prevents a strong shared block from hiding a nonrecurrent relational/query block.

G4 therefore never requires R1/C6/C4 to exist first and never averages constituent recurrence away.

## A5. G7 convergence rule made executable

The parent phrase “final two levels do not show a direction reversal” was underspecified.

Before any value read, freeze an evidence ladder with at least three nested donor-balanced biological-evidence budgets. Measurement depth/support universe must remain fixed; this is biological-evidence response, not G8.

For each donor and adjacent ladder pair `(j, j+1)` on the same held-out anchor cases:

- calculate rotation/scale-invariant geometry recurrence `rho_j` using pairwise-distance rank correlation;
- define adjacent instability `u_j = 1 - rho_j`.

Required subtests:

1. Every adjacent pair must show recurrence above its donor-preserving random-alignment null under the common inferential law.
2. For each pair of successive instabilities, define donor delta `u_j - u_{j+1}`; positive means instability shrinks as evidence increases. Every shrinkage subtest must PASS.

With exactly three evidence levels there is one shrinkage subtest. With more levels all shrinkage subtests are required.

Any resolved reversal is FAIL. Insufficient resolution without a resolved failure is NE. No historical convergence cutoff is imported.

## A6. G8 must preserve the frozen empirical measurement protocol

The frozen measurement/noise-floor prefreeze controls G8 mechanics.

Authoritative depth grid:

`25% -> 50% -> 75% -> 100%`

Preferred empirical perturbations:

- same-cell complementary raw-count split;
- same-cell nested raw-count thinning.

Input and perturbation invariants remain exactly as frozen: finite nonnegative integer counts, split conservation, no manufactured support, measured zero preserved, donor/source/operator/address identities unchanged, deterministic seed namespace frozen, and no change to the biological-evidence universe.

For each donor at each required depth `d`:

- construct two independent same-cell pseudoreplicates `A_d` and `B_d` under the frozen mechanism;
- compute candidate-primary displacement `D(A_d,B_d)` as the technical-noise reference;
- compute `D(full,A_d)` and `D(full,B_d)` with the same metric;
- define donor robustness delta:

`delta_d = D(A_d,B_d) - mean(D(full,A_d), D(full,B_d))`

Positive orientation means the full-to-thinned displacement is no worse than the empirical pseudoreplicate noise reference at the same depth.

Each depth is a required subtest under the gate's familywise alpha; all depths combine non-compensatingly.

This contract supplies the prospective comparison rule that the earlier prefreeze intentionally left unresolved. It does not call count splitting independent biological replication.

## A7. C6 increment must preserve the frozen candidate question

The parent design incorrectly raised the primary C6 comparator from the strongest qualified constituent to the full separate C1+C3 portfolio. That would silently redefine the frozen candidate.

Authoritative C6 increment gate:

Prerequisites: C1 and C3 independently satisfy their own required gates.

Primary increment estimand compares C6 against the **stronger qualified constituent** under matched held-out evidence. The stronger constituent is selected by a prospectively declared donor-primary base loss comparison, not post-hoc narrative preference.

C6 must show added donor-primary biological information **or** prospectively declared robustness benefit beyond that constituent, while not worsening:

- transfer;
- shortcut dependence;
- supported coverage/abstention;
- biological-versus-measurement uncertainty separation.

A diagnostic comparison against the separate C1+C3 portfolio may be reported later, but it is not the frozen C6 promotion criterion unless a future prospective candidate amendment is separately approved before outcomes.

C6 FAIL/NE never removes C1 or C3 from a valid multi-block portfolio.

## A8. C4 increment must preserve the frozen strongest-constituent comparator

Authoritative C4 increment gate:

Prerequisites: all applicable inherited C2/C3 gates PASS.

Primary increment compares C4 against the **strongest qualified constituent** exactly as frozen in multitarget V2, while requiring constituent interpretability and no degradation of transfer, shortcut dependence, coverage/abstention or uncertainty separation.

A separate C2+C3 portfolio remains representable under the repaired `TargetPortfolio`; C4 is not permission for those blocks to coexist.

C4 FAIL/NE never deletes independently qualified constituents.

## A9. G5 current source set is explicit

For the current foundation target tournament, source replication explicitly adjudicates:

- HVS;
- NPH52;
- SEA_AD.

No source abundance weighting or pooled rescue is permitted.

For C5 or future specialist instantiations, a source/operator combination that is structurally unsupported may be NE/not applicable only under a prospectively frozen applicability rule; it may not be silently omitted after outcomes.

## A10. G12 minimum coverage definition

The earlier multitarget V2 required a prospectively frozen minimum eligible coverage but did not supply a numerical floor.

This design prospectively defines the minimum as the support required to execute every required gate at its frozen statistical resolution, rather than inventing an independent cell-count cutoff.

Thus:

- enough lawful support for all required tests -> PASS if abstention semantics also pass;
- lawful support but inadequate donor/null resolution -> NE;
- unsupported-to-numeric conversion, imputation, or false support claim -> FAIL.

This is a qualification/estimability criterion, not a prevalence claim.

## A11. Spec self-review conclusion

After these corrections, the 28 unresolved gate IDs remain unchanged:

- G2–G12;
- S1–S3;
- R1, R3, R4;
- Q4–Q8;
- C6 increment;
- C4 increment;
- M1–M4.

No historical closed experiment is reopened, no old descriptive cutoff becomes a production threshold, no synthetic result becomes human biological evidence, and no real execution authority is created.

Terminal:

`28_GATE_DESIGN_SELF_AUDITED_AGAINST_HISTORICAL_FREEZES__IMPLEMENTATION_NOT_AUTHORIZED__OUTCOMES_UNREAD__REAL_TD_OFF`
