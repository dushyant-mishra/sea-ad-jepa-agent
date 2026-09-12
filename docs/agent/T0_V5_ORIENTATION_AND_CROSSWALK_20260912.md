# T0 ↔ V5 orientation, crosswalk and framework-gap audit

Date: 2026-09-12
Status: `READ_ONLY_ORIENTATION__NO_T0_SUCCESSOR_IMPLEMENTED__NO_AUTHORITY_CHANGED`

The §42 deliverable. Read-only pass over the live repository and the current V5
target-discovery framework, a V5→T0 crosswalk, an A/B/C audit of whether V5 would
have prevented each T0 mistake, and the minimal successor design that follows.

Nothing was merged, rewritten or executed. No protected data was touched.

---

## 1. Live provenance

`git fetch --all --prune` on 2026-09-12. **Six of the ten branches named in the
instruction do not exist on the remote.** Verifying before reading was load-bearing.

| named in instruction | live head |
| --- | --- |
| `governance/integrated-target-discovery-v5-handoff-20260911` | `dac11696` |
| `planning/v5-dataset-first-production-closure-20260912` | **`79feb8d6`** |
| `repair/v5-installed-target-root-binding-20260912` | `bb974896` |
| `planning/v5-target-discovery-plan-20260911` | **missing** |
| `feature/target-discovery-framework-v5-20260827` | **missing** |
| `planning/v5-integration-plan-20260911` | **missing** |
| `repair/v5-anticheat-final-production-guard-20260911` | **missing** |
| `feature/v5-dimensions-production-metrics-20260904` | **missing** |
| `feature/v5-dimensions-production-metrics-staging-20260905` | **missing** |
| `review/v5-dimensions-authority-closure-20260905` | **missing** |

The three "historical anchor" SHAs all resolve, and one correction matters:
**`79feb8d6` is not a historical ancestor — it is the live head** of the closure
branch. `c96f6fd8` and `6ce97ccb` are its immediate parents.

Nearest live substitutes for the missing refs, by subject:
`repair/v5-qualified-target-guard-20260911 @ da8bd7df` (the closure design's own
stated base), `repair/v5-executable-power-authority-20260911 @ 52fca8ab`,
`planning/v5-full-population-cheat-proofing-20260909 @ 1de20b1c`,
`planning/v5-pretraining-qualification-20260909 @ ae1709e2`,
`planning/v5-preexecution-hardening-20260909 @ 782f2c52`.

Documents read, all present on `79feb8d6`:
`docs/superpowers/specs/2026-09-12-v5-dataset-first-production-closure-design.md`,
`docs/agent/V5_DIMENSION_NUMERIC_AUTHORITY_BLOCKERS_20260912.md`,
`docs/agent/V5_FULL104_HISTORICAL_PRODUCTION_RECOVERY_20260912.md`,
`docs/agent/V5_FULL104_REMOTE_BINDING_EXECUTION_20260912.md`.

## 2. V5 authority map

| role | ref | head |
| --- | --- | --- |
| **controlling V5 design** | `planning/v5-dataset-first-production-closure-20260912` | `79feb8d6` |
| target-root binding | `repair/v5-installed-target-root-binding-20260912` | `bb974896` |
| stated base of the closure design | `repair/v5-qualified-target-guard-20260911` | `da8bd7df` |
| governance handoff | `governance/integrated-target-discovery-v5-handoff-20260911` | `dac11696` |
| repository main | `main` | `ba3f2a12` |
| T0 current work | `t0/v21-closeout-candidate-20260911` | `bc72e6e8` |
| T0 immutable | `review/t0-v20-replay-equivalence-20260910` | `3b5933f6` |
| T0 known-bad | `repair/t0-v21-authority-hardening-20260911` | `9f98320f` |

---

## 3. The finding that reframes this exercise

**V5 already encodes several of the lessons T0 learned the hard way.** Its
non-negotiable scientific rules include, verbatim:

> 1. The dataset is the authority. Synthetic fixtures may test mechanics/fail-closed
>    behavior only.
> 6. `NOT_ESTIMABLE`/`NOT_MEASURABLE` is not PASS.
> 7. A PASS receipt is not authority unless its exact bytes are hash-bound to the
>    validated content and parent artifacts.

Rule 1 is precisely the safeguard whose absence produced my 12-gene simulation.
It was already written down.

And V5 makes, unprompted, exactly the distinction I had to be corrected on twice.
Of the historical FULL104 `TEACHER_BIOLOGY_LIMIT` terminal with `D_shared = null`:

> This historical negative shared-state result is **not** evidence that FULL104
> lacks biology.

V5 also already carries T0's best idea: two of its seven canonical rejection gates
are *QC/measurement confounding closure* and *same-cell technical intervention*.

---

## 4. V5 → T0 crosswalk

| V5 concept | where | current rule | applies to T0 unchanged? | AT8 adaptation needed |
| --- | --- | --- | --- | --- |
| dataset-is-authority | closure design rule 1 | synthetic for mechanics only | **yes** | none |
| physical source identity | `bind_full104_expression_blocks_v4.py`, block-manifest SHA | exact byte identity or STOP | **yes** | T0 already has it; the pathology-file rejection is the live proof |
| derive parameters from data | rule 5 | never inherit historical constants or checkpoint outcomes | **yes** | none |
| effective dimension, not nominal | `D_shared`/`D_private`/`D_obs` | dimensions selected by held-donor predictability | **yes** | AT8 needs its own representation family |
| zero is a lawful result | blockers doc | `D_shared = 0` permitted | **yes** | the direct analogue of "the nuisance-only model may win" |
| held-donor predictability as a gate | `D_shared` rule | required before `D_private` | **yes** | T0's donor-held-out evaluation |
| full-refit matched nulls | `D_shared` rule | nulls recomputed through the whole fit | **yes** | AT8 needs candidate-specific nulls |
| donor-resampled stability | `D_shared` rule | required | **yes** | T0 needs concentration, not just stability — see gap G3 |
| prospective freezing | `D_private`/`D_obs` rules frozen before outcomes visible | candidate authority pending review | **yes** | none |
| two-sided gate calibration | `rejection_gate_power_calibration_v3.py` | each gate must accept a minimally-valid and reject a minimally-invalid control at exact adjudication geometry | **yes** | this is the negative-control discipline T0 kept rediscovering |
| receipt hash-binding | rule 7, Finding C | bytes bound to validated content and parents | **yes** | T0's authority wrapper has the same open issue |
| installed-root binding | runtime guard | installed target root must equal the qualified receipt root | **yes** | a T0 successor package must not declare its own authority |
| representation firewall | `representation_firewall_v2.py` | allowlist, frozen gradient destinations | conceptually | no gradients in T0 discovery |
| lane separation | rule 2 | `TD13/TD60 IS NOT T0 V18/V20/V21` | **yes** | do not import V5 estimands into AT8 |
| **not present** | — | measurement-model / loss qualification | — | **T0 must add it — gap G1** |
| **not present** | — | target-distribution characterization before estimand choice | — | **T0 must add it — gap G1** |
| **not present** | — | publish the simpler-model comparator beside any selection curve | — | **T0 must add it — gap G2** |

Explicitly **not** inherited, per §7 of the instruction: `D_shared`, `D_private`,
`D_obs`, the multiview equations, the anchored relational target
`q(i;j,k) = sign(d(i,j) − d(i,k))`, FULL104 estimands, and all historical V5
thresholds, replicate counts and search ranges.

---

## 5. Would V5 have prevented each T0 mistake?

`A` prevents · `B` partially · `C` does not yet.

| # | mistake | V5 | basis |
| --- | --- | --- | --- |
| 1 | formula from one target distribution applied to another | **B** | lane firewall (rule 2/3) stops cross-lane transfer; nothing requires distribution characterization before objective choice |
| 2 | predictor frozen before target characterized | **B** | ordering puts estimand before dimensions, but has no explicit target-characterization stage |
| 3 | measurement model not qualified before prediction | **C** | no loss/measurement-model qualification stage exists anywhere in V5 |
| 4 | transport before proving there is something to transport | **A** | held-donor predictability is a required gate; relational activation requires predictability PASS |
| 5 | toy geometry substituted for real | **A** | rule 1, verbatim |
| 6 | planning approximation promoted to decision authority | **B** | rule 7 and rule 8 are strong; Finding E shows gate tests building report dicts rather than executing gates |
| 7 | boundary optimum read as a successful estimate | **B** | search-envelope expansion specified and zero is lawful; nothing requires reporting the limit the search converges toward |
| 8 | nominal p mistaken for effective complexity | **A** | V5 is built on effective dimensions throughout |
| 9 | simpler-model comparator omitted | **B** | matched nulls required; a nuisance-only comparator is not a required published quantity |
| 10 | few units dominating without influence assessment | **B** | donor-resampled stability required; concentration/top-k influence not an emitted diagnostic |
| 11 | estimator failure confused with target failure | **A** | stated explicitly for `TEACHER_BIOLOGY_LIMIT` |
| 12 | estimand failure confused with absence of biology | **A** | same |
| 13 | confirmation information influencing target definition | **A** | no protected access anywhere in the design |
| 14 | plausible but unauthenticated input | **A** | rule 7, binder identity closure, Finding A (TRAIN cache cannot masquerade) |
| 15 | candidate declaring its own authority identity | **B** | repaired at FULL104→dimension and the optimizer path; design says the principle "still needs to remain true downstream" |
| 16 | negative controls whose geometry differs from the problem | **A/B** | two-sided calibration at exact adjudication geometry is the right rule; Finding E means it is not yet executed evidence |
| 17 | adaptive pivots without audit trail | **A** | prospective freezing before outcomes are visible |
| 18 | framework where the target cannot fail | **A** | zero lawful, `NOT_ESTIMABLE` is not PASS, and a real negative terminal already exists in the record |

### V5 framework gaps that T0 exposes

**G1 — no measurement-model qualification stage, and no target-distribution
characterization before the objective is chosen.** The single largest gap, and the
one that cost T0 most. V20 inherited squared error without ever asking whether it
matched the scientific question, and the target's distribution was never
characterized. Measured afterwards, the per-fold loss is strongly donor-dominated:
median/mean 0.47, one donor contributing 33.5%. V5 qualifies confounding of the
measurement (QC gates) but never qualifies the *measurement model* itself.

**G2 — the simpler-model comparator is not a required published quantity, and a
search is not required to report the limit it converges toward.** V20 published a
17-point CV curve for months without the one number that made it interpretable.
Had `L_∞` sat beside those 17 values in the output, the whole question would have
been visible immediately.

**G3 — influence concentration is not a first-class emitted diagnostic.**
Donor-resampled stability is required, which is necessary but not sufficient: a
result can be "stable" under resampling while one unit supplies a third of the
signal. T0's decisive comparison failed precisely here — the difference was
0.0076 SE while one donor moved the estimate 114× more.

These three are offered back to V5. **Not modified during this orientation**, per
§9.

---

## 6. Minimal T0 successor design

Following §16 ordering. Discovery-only throughout; no confirmation access.

**Stage 0 — authenticate.** Reuse the frozen discovery-only loader unchanged. It
already reproduces donor-set digest `4395fec7…` and endpoint digest `4cfb5727…`,
skips the 18 confirmation rows before their values are touched, and refused an
unauthenticated candidate source at the first attempt.

**Stage 1 — characterize the AT8 measurement (closes G1, first half).** From
discovery-only AT8: support, bounds, zeros, floor/ceiling, skew, tails, mass
points, resolution, missingness, nuisance association, heteroskedasticity, donor
leverage, and whether high-AT8 donors are biological extremes or measurement
anomalies. **No high-influence donor is discarded** — influence is understood, not
removed.

**Stage 2 — define the estimand from measurement semantics, not from fit quality.**
Magnitude, robust magnitude, ordering, burden state, or a monotone pathology axis
are different scientific questions. Choose on pathology meaning and the JEPA
target's purpose, and freeze before any candidate is scored.

**Stage 3 — qualify the measurement model (closes G1, second half).** Squared
error is not inherited by default; nor is it presumed wrong. If magnitude recovery
is the scientific requirement, high-pathology donors *should* carry weight.

**Stage 4 — small, prospectively frozen candidate family.** With 28 discovery
donors, unrestricted exploration is analyst-level overfitting. Each candidate
justified before it is scored.

**Stage 5 — representation from cells, without pathology.** Cell-state
composition, rare-state abundance, neighbourhood structure, state-specific
programmes — derived with no AT8 access, targeting low effective dimension.
`n_independent_pathology_units = 46`, never 638,150; the cells improve **X**, not
the sample size of **Y**.

**Stage 6 — donor-held-out prediction with nested selection**, every
data-dependent choice inside the training portion.

**Stage 7 — nuisance-only incremental test per candidate (closes G2)**, matched on
target representation, loss, folds, nuisance fit, scaling and evaluation
population — and the limit the search converges toward published beside the curve.

**Stage 8 — influence and stability (closes G3):** fold losses, top-donor and
top-k concentration, leave-one-donor sensitivity, direction stability, and whether
one or two donors determine qualification.

**Stage 9 — anti-cheat and biological necessity**, with candidate-specific nulls
built on real covariance, donor structure, cell counts and nuisance geometry,
breaking only the association under test. Not inherited from V5 or old T0.
`matched-null ≠ paired-wrong-query`; any such control must state exactly what is
changed, what is held fixed, and which null it tests.

**Only then** target qualification → transport → confirmation design → training.

### The bar that is knowable now

Confirmation power depends only on ρ and cohort size, so a successor must clear
**ρ ≥ 0.61** at n = 12 with the nuisance frozen from development at α = 0.05.
Check it at design time. A legitimate outcome remains
`TARGET QUALIFIED / CONFIRMATION DESIGN NOT ADEQUATE` (§41-H) — that is a
statement about the cohort, not about the target.

---

## 7. Boundaries observed

No confirmation AT8. No new protected population. No training, TD60 or relational
activation. V20/V21 historical meaning unchanged. No V5 controlling authority
modified. FULL104 not rematerialized — and per the recovered history it should not
be: the task there is locate → verify → rebind, not rebuild.
