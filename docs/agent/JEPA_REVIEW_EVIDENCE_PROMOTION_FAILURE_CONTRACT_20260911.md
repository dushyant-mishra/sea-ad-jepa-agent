# JEPA REVIEW EVIDENCE, PROMOTION, FAILURE, AND LINEAGE CONTRACT

Date: 2026-09-11
Status: `CURRENT_MANDATORY_REVIEW_GOVERNANCE__NO_TRAINING_AUTHORITY`

**The goal is not to make V5 train successfully. The goal is to make it impossible for V5 to receive an unqualified biological target or obtain good training metrics through a shortcut, and to make every authority transition independently auditable.**

This contract is mandatory companion governance for the integrated target-discovery → frozen-target → V5 pipeline. It does not authorize S0–S4, protected-data opening, target freeze, FULL104 training, or production training.

## 1. Review evidence classes

Every material result, statistic, test count, mutation result, provenance assertion, power estimate, or review conclusion must carry exactly one evidence label at the point it is reported:

```text
PRODUCER_CLAIM
SOURCE_CODE_CONFIRMED
REVIEWER_REPRODUCED
REAL_DATA_EVIDENCE
NOT_YET_VERIFIED
```

Definitions:

- `PRODUCER_CLAIM`: stated by a producing lane/commit/report but not independently reproduced.
- `SOURCE_CODE_CONFIRMED`: reviewer inspected code/contract and confirmed what it implements, but did not reproduce the execution evidence.
- `REVIEWER_REPRODUCED`: reviewer independently executed the relevant test/probe from an adequately controlled checkout/environment and reproduced the result.
- `REAL_DATA_EVIDENCE`: result derives from authenticated legal real project data under the applicable provenance contract.
- `NOT_YET_VERIFIED`: a claim or required property remains open, unavailable, ambiguous, or has not yet met the evidence needed for a stronger class.

These labels are mandatory for claims concerning `3b5933f6`, including its reported `97 tests, 0 skipped`, mutation audit, exact-test power calibration, HC3 transport observations, nested-permutation legality, sealed-cross-fit provenance, and INVALID versus NOT_ESTIMABLE behavior.

Do not silently upgrade evidence classes. A `SOURCE_CODE_CONFIRMED` behavior is not `REVIEWER_REPRODUCED`. A producer-reported PASS is not reviewer evidence.

## 2. Exact definition of blocker closure

A scientific/statistical/anti-cheat/provenance blocker is closed only when the complete chain agrees:

```text
contract
→ implementation
→ failing adversarial/regression test
→ repair
→ focused tests
→ surrounding tests
→ mutation/adversarial checks
→ provenance verification
→ independent reread of contract vs implementation
→ closure verdict
```

"Tests pass" alone never closes a scientific blocker. If any link is absent, classify the blocker `NOT_YET_VERIFIED` or keep the relevant STOP terminal active.

## 3. Branch discipline

- Frozen V20 is immutable.
- All repairs occur on clearly named successor/review/fix branches.
- Re-fetch live heads before every substantial work batch and again immediately before committing or interpreting a peer lane's result.
- Do not trust SHAs copied from an older handoff without re-fetching.
- Do not blindly merge parallel branches that touch the same authority/statistical contract.
- First reconcile ancestry, changed files, evidence roots, and semantic overlap.
- A branch name never creates scientific authority.

Observed isolated repair lane on 2026-09-11:

```text
fix/f1-review-closeout-20260911
```

It does not supersede V20 or create training authority.

## 4. Durable statistical/semantic ledger requirements

The final formulas/authority ledger must carry exact executable semantics, not prose approximations.

### 4.1 Outer OOF construction

For discovery donors `i = 1..28`:

```text
hold out donor i
use only the remaining 27 donors
perform inner LOODO ridge selection entirely inside those 27
fit the target learner on those 27
generate exactly one prediction for donor i
assemble exactly 28 OOF predictions
```

Then fit one donor-level full-design regression over the 28 OOF rows.

If the frozen full design has five columns including intercept:

```text
df_resid = 28 - 5 = 23
```

The exact nuisance design, coefficient of interest, HC3 covariance computation, leverage guards, rank/estimability rules, and residual degrees of freedom must be copied from the reviewed executable implementation into the durable ledger.

### 4.2 Freedman–Lane confirmatory/permutation semantics

Candidate `3b5933f6` claims HC3-studentized Freedman–Lane with:

```text
B = 9999
alpha = 0.025
p_upper = (1 + #{T_null >= T_obs}) / (B + 1)
```

Evidence class at contract creation: `PRODUCER_CLAIM` until independently re-reviewed/reproduced.

The final ledger must explicitly freeze reduced/full model construction, residual-generation rule, permutation unit, nuisance handling, studentization, tail direction, `B`, `alpha`, RNG/seed authority, stopping rule, and invalid/non-estimable permutation handling.

### 4.3 Stage-C ridge search

Candidate `3b5933f6` claims movable Stage-C refinement with successive exponent steps:

```text
2
1
0.5
0.25
```

recentring on the winner each round under the frozen V20 tie rule. Claimed maximum displacement from a coarse anchor is:

```text
2 + 1 + 0.5 + 0.25 = 3.75
```

with coarse-anchor spacing 4. Evidence class until independent review: `PRODUCER_CLAIM`.

### 4.4 Empirical influence minimum

The leave-one-donor quantity must be described as an **empirical influence minimum** / observed-donor sensitivity minimum, not a population confidence lower bound.

The latest candidate claims the planning effect is the value nearer zero between the full estimate and empirical influence minimum. The final ledger must freeze exact sign handling, zero handling, direction-consistency STOP behavior, and standardization. Until re-reviewed: `PRODUCER_CLAIM`.

### 4.5 Thinning / robustness metrics

Before S0–S4 can run, the durable ledger must freeze the exact retention levels, draws per level, seed/random authority, standardized displacement definition, prospectively declared worst-case aggregation, held-out-biology preservation envelope, beta-direction displacement, cell-score-geometry displacement, and donor-summary displacement.

No post-result choice among alternative thinning summaries is permitted.

### 4.6 S0–S4 ranking

Candidate family stays exactly:

```text
S0, S1, S2, S3, S4
```

unless a new prospective contract is explicitly approved before observing selection outcomes.

Current prospective ranking semantics:

1. admissibility requires preservation of held-out biology inside S0's own LODO envelope;
2. among admissible candidates, rank by the prospectively defined worst-case standardized displacement;
3. ties against the declared envelope resolve in order `S0 < S1 < S2 < S3 < S4`.

No silent sixth candidate. No after-the-fact alternate ranking.

### 4.7 Final power definition

The decision-capable final power definition is not yet durable authority. The old `t/sqrt(n)` transport is not sufficient authority.

The final ledger may freeze power only after independent review confirms that the simulation/permutation power procedure matches the exact confirmatory test and legally propagates learner refitting, cross-fit dependence, nuisance handling, and HC3 geometry.

Until then:

```text
FINAL_POWER_DEFINITION = NOT_YET_VERIFIED
POWER_GATE_DECISION_AUTHORITY = FALSE
```

## 5. Formal promotion ladder

```text
mechanics-valid
→ provenance-valid
→ statistically-valid
→ biology-qualified
→ frozen target
→ V5-bound target
→ anti-cheat qualified
→ FULL104-qualified
→ production training authorized
```

Passing any level creates **no authority at the next level**.

Every promotion must name the exact input authority, output authority, immutable evidence root, reviewer verdict, and failure terminal.

## 6. Frozen failure terminals — no post-failure rescue design

Before any decision-capable run, freeze the response to foreseeable failure:

- **No admissible S0–S4 candidate:** STOP. Do not invent S5 or loosen admissibility after observing failure.
- **Ridge stability failure:** STOP. Do not widen thresholds or alter search after observing instability.
- **Power <80%:** fresh `reader_validation` remains closed. Do not open it "for information."
- **Effect direction inconsistent:** STOP using the frozen direction-consistency terminal.
- **FULL104 cannot be recovered/authenticated:** production training remains unauthorized.
- **Target binding fails:** optimizer/trainer remains disabled; no alternate/recomputed target substitution.
- **Anti-cheat attack succeeds:** qualification fails; do not redefine the attack away after observing success.
- **Provenance mismatch:** evidence is non-authoritative until corrected by a prospectively valid successor artifact.

A rescue procedure may be designed only as a new prospective successor contract that does not consume the protected result that triggered the failure.

## 7. Negative controls are first-class immutable artifacts

Negative/adversarial controls must not exist only as test functions or CI booleans.

For each control family, preserve immutable inputs, generator/configuration, code identity, raw outputs, verdict, and hashes/package root.

Required families include at least:

```text
deliberate shortcut controls
permutation controls
corrupted-biology controls
technical-only controls
donor-identity attacks
same-cell / shared-view leakage attacks
lookup / duplicate-identity attacks
```

Where controls are generated, freeze the generator version, seed authority, and source evidence. A report field such as `rejected=true` is not itself rejection evidence.

## 8. Target identity must propagate into every checkpoint

Once a V5 training lane is eventually authorized, every checkpoint must answer:

> Exactly which frozen target package generated the teacher signal for this checkpoint?

Required immutable chain:

```text
target discovery evidence root
→ qualified/frozen target package root
→ teacher-target artifact digest
→ pre-execution receipt
→ exact trainer/code head
→ training-run identity
→ checkpoint
→ downstream evaluation artifact
```

Every checkpoint must carry or resolve to the frozen target package root and all required data/code/receipt identities. A checkpoint lacking that lineage is mechanically inspectable but not scientifically attributable.

## 9. Governance drift check

`START_HERE.md`, `JEPA_LATEST_HANDOFF_POINTER.json`, `CURRENT_AUTHORITY_INDEX.md`, and `CURRENT_SUPERSESSION_MAP.md` must agree on the canonical startup handoff and current promotion state.

Reconcile them after the independent review of `3b5933f6`, after any durable repair branch is promoted, and before a new-chat handoff is declared current.

Governance files must never silently lag a promoted statistical/target/V5 contract.

## 10. Environment / reproduction limitation

Record the execution class of review evidence.

In the preceding review environment, direct container-to-GitHub networking failed. Some review work therefore used the GitHub connector plus small locally reconstructed adversarial probes.

Those are not equivalent to:

```text
clean-checkout exact-head execution
```

When a proper checkout/execution path is available, reproduce claimed suites from the exact candidate head and upgrade evidence classes only after successful reproduction.

Never report connector source inspection as local suite execution.

## 11. Future scientific architecture agenda — not current authority

The following are useful prospective hypotheses, not authority to alter the current frozen/under-review target-V5 contract:

- model technology as an observation operator rather than an unrestricted biological covariate;
- distinguish desired measurement invariance from legitimate biological variation;
- audit the 160-D basis/subspace for donor-resample stability using principal angles, canonical correlations, Procrustes alignment, coordinate stability, and eigenvalue gaps;
- separate biological-evidence convergence curves from count-depth/measurement curves;
- distinguish measurement-domain support from biological novelty/OOD;
- add held-out dataset/study and, where possible, held-out technology transfer tests;
- preserve legitimate donor biology rather than forcing all donor variation away;
- use bounded hierarchical dataset→donor→cell sampling before real production training;
- retain the molecular ledger as the high-resolution molecular state and lower-dimensional state as an accountable global coordinate;
- consider shared/context latent decomposition only if evidence shows a single-state representation is inadequate.

Evaluate these pathology-blind and prospectively. Do not add neural complexity merely because it is available.

**Do not optimize for reaching training quickly. Optimize for reaching a state where, if training succeeds, we can defend why the signal is biological, why it was discovered without circularity, why the student could not cheat, and exactly which immutable data/code/target lineage produced every checkpoint.**
