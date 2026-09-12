# T0 closeout handoff — everything a new agent needs

Date: 2026-09-11
Status: `T0_V21_T1_NOT_FROZEN__ONE_OPEN_SCIENTIFIC_BLOCKER`

Read this before touching T0. It is written to be self-contained: what T0 is,
what was decided and why, what the code does, where it lives, and the exact list
of things that must happen before T0 can close.

Re-fetch live heads before acting. Branch names confer no authority, and several
SHAs in older documents are stale.

---

## 1. What T0 is, and where it actually stands

T0 asks whether a representation learned from single-cell expression predicts
donor-level AT8 tau pathology in SEA-AD MTG. V20 ran it and returned two results.

**The broad immune-state result stands.** Its sensitivity analysis was recovered
after being omitted from the original report: composition β = 127.131, p = 0.019;
measurement β = 137.172, p = 0.030, with SE inflation of 25% against 2.2%,
consistent with the collinearity predicted beforehand.

**The rare-tail result was refused**, terminal
`RARE_TAIL_UNDERDETERMINED_MEASUREMENT`, and that refusal stands. A four-step
investigation established the tail is not resolvable with this estimand on this
data: the tail label is depth-fragile, the held-out program stays coherent but
the confound is preserved, restriction is insufficient and the statistic is
non-monotone under it, and matched-QC analysis works but has no power.

**Two things were learned that change how V21 must be built.**

A QC gate must not demand that a biological representation be independent of
observed QC across real cells — genuinely activated cells really do differ in RNA
complexity, so that demand rejects true signal. The right question is the
same-cell counterfactual: if only the measurement process changes, does the
biological conclusion move? Association diagnostics warn; same-cell intervention
gates qualify.

And V20 itself ran at roughly 42% power, so its own estimate is likely
winner's-curse inflated. That is what motivates a power gate before spending
fresh donors.

---

## 2. The one open scientific blocker

**Effect transport.** This is the thing standing between here and a frozen V21-T1.

The V21 power gate needs to carry an effect from the discovery procedure into a
prospective 12-donor confirmation design. The natural coordinate is
`δ = t / √n` from the assembled HC3 regression. **It is not established that this
transports**, and the reason is now measured rather than suspected.

The 28 out-of-fold predictions are mutually dependent: folds *i* and *j* share 26
of their 27 training donors, so `score_i` is a function of `y_j` for every
*j ≠ i*. Per-donor honesty holds — a donor's own prediction never sees its own
outcome, and that is tested — but that is weaker than joint independence, and the
single HC3 regression treats the 28 pairs as independent.

Measured by `scripts/v4/t0_v21_crossfit_null_calibration_v1.py`, under a strict
null with the whole 28-fold nested procedure re-run 400 times:

| inner selection | null SD ÷ nominal | rejection at α = 0.025 |
| --- | --- | --- |
| fixed ridge | **1.304** | 0.0325 |
| LOODO ridge selection | **1.477** | 0.0175 |

A null spread 30–48% wider than nominal means the HC3 standard error understates
the procedure's own variability, so `t / √n` overstates the effect it is meant to
carry. Evidence is committed at
`docs/agent/evidence/t0_v21_crossfit_null_calibration_20260911.json` with a
manifest recording the exact invocation, seed, replicate count and digests.

**The architectural rule this establishes, and which must not be eroded:**

| quantity | what it can support |
| --- | --- |
| whole-pipeline permutation | evidence of **association** under the procedure's own null |
| cross-fitted HC3 `t` | a **descriptive / studentized** statistic |
| an effect transported to a fresh n = 12 design | **not authorized** until separately derived and calibrated |

**Do not close this by inventing a correction factor from 1.304/1.477.** Those
numbers demonstrate that the assumption fails; they do not identify its
replacement, and a constant read off them is a constant chosen after seeing the
data. The executor encodes the tempting substitutions as forbidden by name: the
suspect quantity itself, permutation *significance* standing in for effect
*magnitude*, and any rescaling derived from the measured null spread.

The executor is fail-closed on this. `EFFECT_TRANSPORT_STATUS = "OPEN"`, and
`power_gate` refuses with `STOP_T0_V21_EFFECT_TRANSPORT_NOT_AUTHORITY_BOUND`
regardless of arguments. The arithmetic survives as `planning_power_projection`,
which returns no `clears_gate` key at all.

---

## 3. Two other measured facts that constrain the design

**A 1/11 sex split at n = 12 is not estimable.** That donor gets HC3 leverage
exactly 1.0000 and the frozen engine refuses. Measured maxima: 1 → 1.0000,
2 → 0.6579, 3 → 0.6965, 6 → 0.6978. **The fresh confirmation cohort must contain
at least two donors of each sex**, or the confirmatory test cannot run at all.
This is a cohort-admissibility condition to check when the validation population
is built — not a reason to inspect the sealed cohort during calibration.

**Predictor collinearity with the nuisance design is inert.** HC3's `t` cannot
see the in-span component: residualization removes it and the noncentrality is
scaled by the residualized norm, so the two cancel. Measured 0.8582 at ρ = 0 and
0.8582 at ρ = 0.75. The axis that does matter is the leverage profile: gaussian
0.8582, heavy-tailed 0.8136, single-leverage 0.5402. The frozen geometry class
sweeps leverage only, and the invariance is an explicit test.

---

## 4. The V21-T1 design in one page

Donor hierarchy: **28 discovery** (all method and ridge selection) → freeze the
estimator → **refit on all 46 development donors** → **one test on 12 fresh
donors** from `reader_validation`. The 12 take no part in any method choice,
including power calibration.

Power gate before spending the 12. Its construction, after several corrections:
28 nested models each trained on 27 donors with their own inner LOODO ridge
selection; exactly one out-of-fold prediction per donor; **one** HC3 regression
across the assembled 28 (df = 28 − 5 = 23). Not one regression per fold — under
leave-one-donor-out a fold holds a single donor and nothing is estimable there.

Confirmatory test, frozen: the same HC3-studentized **Freedman–Lane permutation**
procedure V20 uses, at n = 12. Since `p_upper = (1 + #{null ≥ t}) / (B + 1)`,
rejecting at α = 0.025 requires **B ≥ 39**; B is frozen at 9999.

Confirmation design: **not a caller argument**. The frozen age/sex authority
covers only the 46 development donors and would need extension from source for
the 12, and the owner's condition bars the 12 from power calibration. The gate
takes an age range carrying an authority string and evaluates a frozen envelope
of admissible 12-donor designs at its **worst case**.

Estimator family `S0`–`S4`, closed at five. Selection is admissibility on
held-out biology, then ranking by worst-case thinning displacement, ties to the
earliest declared candidate. Ridge is a frozen bracketing search with
recentring refinement; stability is judged per metric over all 28 LODO refits
with nothing averaged.

---

## 5. Code assets and what each one does

All under `scripts/v4/`.

| file | role |
| --- | --- |
| `t0_v21_selection_and_power_v1.py` | the numerical executor: cross-fit construction, sealed artifact, HC3 effect, influence minimum, ridge procedure, estimator selection, fail-closed power gate |
| `test_t0_v21_selection_and_power_v1.py` | its qualification suite |
| `mutation_audit_t0_v21_selection_and_power_v1.py` | breaks the executor 50 ways and requires the suite to catch each |
| `t0_v21_crossfit_null_calibration_v1.py` | the null-calibration experiment behind §2 |
| `t0_v21_authority_v1.py` | the production authority wrapper: source authority, fold provenance, permutation/design/geometry/calibration receipts |
| `t0_v21_measurement_artifact_v1.py` | schema for S0–S4 measurements (schema only, executes no biology) |
| `t0_v21_target_freeze_v1.py` | 46-donor target freeze receipt schema |
| `t0_v20_frozen/` | the immutable V20 code. Read, never written. `ols_hc3_last` and `nuisance_design` are reused rather than reimplemented |

Current evidence: **128 tests, 0 skipped**, and a mutation audit of **50
mutations — 47 caught, 3 unreachable by construction with written proofs, 0
survived**. Both reproduce from a clean `git archive` extraction.

---

## 6. Branch map — verified live 2026-09-11

| branch | head | what it is |
| --- | --- | --- |
| `handoff/jepa-t0-v2-claude-ready-20260911` | `f727a820` | the current entry point; carries the restored authority + the executor successor |
| `repair/t0-v21-authority-restoration-20260911` | `b27978af` | authority restoration lineage |
| `review/t0-v21-successor-20260911` | `3a8c8e3e` | the numerical executor with transport failing closed |
| `review/t0-v21-integrated-candidate-20260911` | `c8a1947e` | executor + authority wrapper merged |
| `review/t0-v2-api-surface-portability-20260911` | `2797c4d7` | one-file fix, still needed (see §7.0) |
| `review/t0-v20-replay-equivalence-20260910` | `3b5933f6` | **immutable.** Do not amend or rebase |
| `repair/t0-v21-authority-hardening-20260911` | `9f98320f` | **known bad.** See below |

**`9f98320f` is truncated and red on its own head** — 18 of its 22 tests fail. It
deleted every `seal_*` function, four `validate_*` functions, and
`decision_capable_power_gate` itself, while its tests still call them. The
known-good source before truncation is `a36fd209`. Do not build on `9f98320f`.

---

## 7. What must happen to close T0, in order

### 7.0 — trivial, do first
Fast-forward `2797c4d7` onto the handoff branch. The API-surface guard hashes raw
working-tree bytes, so it fails on any Windows checkout (`core.autocrlf=true`)
even though the content is right: the file is 34,463 bytes in the tree against
33,824 in the blob. The fix normalizes line endings and adds a negative control,
because the prescribed sensitivity check — check out the truncated branch and run
the guard — cannot work: the guard does not exist there, so pytest collects
nothing and **exits 0**.

### 7.1 — close or formally abandon effect transport **(the real blocker)**
Either supply a derivation showing what quantity legitimately transports from
this nested cross-fitted discovery procedure to a prospective 12-donor design, or
decide that none does and that V21-T1 ships as a methodology contribution
validated on development donors. Both are acceptable outcomes. What is not
acceptable is transporting `t / √n` while the design says it is unvalidated.

Candidate directions, none yet derived: standardize by the whole-pipeline
permutation null's spread rather than the HC3 SE; or reduce fold overlap so the
independence assumption is closer to true; or target a quantity that is invariant
to the procedure's own variance inflation. Each needs a derivation plus a
negative-control simulation, not an assertion.

### 7.2 — build and qualify the measurement layer
Nothing currently computes the inputs `select_estimator` consumes. Needed:
`S0`–`S4` score constructions; the discovery-derived common measured gene core;
the thinning ladder and the worst-case standardized displacement; the
held-out-biology preservation statistic; the three §3.3 ridge-stability
displacements (β direction cosine, cell-score rank correlation, donor-summary
correlation and maximum absolute difference); the QC gate's power-calibration
inputs; and the §7 provenance emitter. Tests first, synthetic fixtures, same bar
as the executor.

### 7.3 — get one integrated candidate green
Restore the functions `9f98320f` deleted, taking them from `a36fd209` while
keeping that commit's new `ALLOWED_EFFECT_ESTIMANDS` and ridge-metadata binding.
Then run the combined suites from a clean archive and report exact counts.

Flag while doing it: `ALLOWED_EFFECT_ESTIMANDS` admits
`whole_pipeline_permutation_standardized_effect_v1`. Standardizing by a
permutation null's *spread* could in principle be a scale rather than a
significance claim, but its transport to n = 12 is not derived anywhere, so the
allow-list entry does not close §7.1.

### 7.4 — freeze V21-T1
Only after 7.1–7.3, and only with owner approval of the prospective amendments
listed in `docs/agent/T0_V21_PROSPECTIVE_DESIGN_DRAFT.md`, which are marked as
requiring it.

### 7.5 — only then, spend the fresh cohort
Build the `reader_validation` population authority and expression store, extend
the age/sex authority to the 12, check the ≥ 2-per-sex admissibility condition
from §3, open AT8 once, run the single confirmatory test.

---

## 8. Hard boundaries, currently in force

Firewall in `docs/agent/CURRENT_WORK_CHECKPOINT.json`, all `true`:
`at8_values_closed`, `dev_expression_closed`, `pathology_closed`,
`production_training_forbidden`, `reader_oracle_closed`,
`reader_validation_closed`, `real_f1_forbidden`, `real_t0_forbidden`,
`sealed_expression_closed`.

```
EFFECT_TRANSPORT_STATUS                  = OPEN
POWER_GATE_PRODUCTION_VERDICT_CAPABILITY = DISABLED
S0_S4_EXECUTION_AUTHORITY                = FALSE
FRESH_CONFIRMATION_AUTHORITY             = FALSE
TRAINING_AUTHORITY                       = FALSE
```

V20 is immutable. `3b5933f6` is immutable. The V20 terminal
`RARE_TAIL_UNDERDETERMINED_MEASUREMENT` stands.

Standing rule: **if confirmation data could change a design choice, do not look.**

---

## 9. Two process lessons worth carrying

**A documented limitation the code does not enforce is a comment, not a
limitation.** The transport blocker was identified, written into the design, and
then transported anyway in the same commit. When a design says a path is
unvalidated, the executor must refuse it and a test must prove the refusal.

**A test that cannot fail is not evidence.** Pair positive tests with negative
controls, and mutation-audit the suite: break the module in each way the contract
forbids and require the suite to catch it. Apply mutations by textual
substitution with an asserted match count, so one that fails to apply is reported
rather than silently counted as caught. Two recurring traps: an anchor goes stale
the moment a second function carries the same line, and a test asserting only a
STOP marker cannot tell a named prohibition from a default refusal.
