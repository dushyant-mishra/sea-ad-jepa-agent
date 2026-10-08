# V5 dependency-aware masking qualification — findings, 2026-09-16

Branch `authority/v5-masking-qualification-20260916`, from Stage-A head `c15233aa`.
Contract frozen **before** any evaluation: `V5_MASKING_QUALIFICATION_CONTRACT_20260916.json`
sha256 `509ca69723485d7c6ea5795b9f6a30f54c42344f2e916adc57081b62d89a5bfb`.

No training. No `D_shared`. No protected outcome. FULL104 read-only.

## Disposition

### `MASKING_AUTHORITY_REMAINS_OPEN`

No masking family qualified under the frozen contract. The frozen (K, R) grid was
exhausted — all nine cells — and **no new threshold was introduced to make something pass**.

---

## What was established

### The dependency estimator is sound (qualified before touching FULL104)

`DONOR_STRATIFIED_RANK_RECURRENCE_V1` passes all seven fixtures the contract required, plus
two harder attacks I added because the required seven passed on the first run:

| attack | result |
|---|---|
| independent addresses | density 0.000 |
| planted pairwise latent | recovered |
| donor-only effect | density < 0.05 |
| operator-only effect | density < 0.05 |
| source-only effect | density < 0.05 |
| shared missingness | no edge; strata counted correctly |
| unmeasured ≠ negative vote | genuinely dependent pair still recovered |
| unequal source size | balancing reduces the large source's authority |
| **within-donor depth factor** (added) | density 0.0036 |
| **within-donor global shift** (added) | density 0.0109 |
| **specificity under both confounds** (added) | planted pair still recovered |

The required fixtures 3–5 perturb each stratum by a *constant*, which within-donor ranking
removes trivially. The confound that actually threatens real data varies *within* donor and
lifts every address at once. The recurrence rule is what suppresses it: a universal confound
leaves top-K neighbour sets near-tied, so they do not recur, while a specific relationship
does. Specificity is asserted separately so "suppress confounds" can never be satisfied by
returning nothing. `fit_dense` is verified equal to the reference `fit` on three seeds.

### Recurrent dependency structure exists, but it is sparse and scale-dependent

| address universe | donors | edges (half A) | split-half Jaccard | null p95 | above null |
|---|---|---|---|---|---|
| 600 (400 common + 200 native) | 85 | 135 | **0.3700** | 0.0037 | **yes** |
| 2,000 common core | 80 | 1–3 | — | — | effectively none |
| 6,000 common core | 76 | **0** | 0.0000 | 0.0000 | no |

At 600 addresses the structure is unambiguously above null (~100×). At 2,000 and 6,000 it
essentially vanishes at the frozen thresholds.

**This is a rank-threshold scaling effect, not a contradiction.** Top-10 is the top 1.7% of a
600-address pool but the top 0.17% of a 6,000-address pool. The recurrence-fraction
distribution at 2,000 addresses makes the ceiling explicit:

| K | max recurrence | p99.99 | pairs ≥ 0.5 | ≥ 0.6 | ≥ 0.75 |
|---|---|---|---|---|---|
| 5 | 0.564 | 0.282 | 2 | 0 | 0 |
| 10 | 0.641 | 0.333 | 2 | 2 | 0 |
| 20 | 0.692 | 0.359 | 5 | 2 | 0 |

Out of ~4M ordered pairs, at most **5** reach a recurrence fraction of 0.5. Some real
structure exists — one pair recurs in 69% of donors — but it is far too sparse to drive a
mask.

---

## Why no candidate qualified

### Metric D (anti-interpolation exposure) at 600 addresses — FAIL

| candidate | exposure | vs uniform | structural expansion |
|---|---|---|---|
| U uniform baseline | 0.1946 | — | 1.0 |
| **H historical pooled Pearson** | 0.2129 | **+9.4% WORSE** | 12.5 |
| R donor-recurrent | 0.1853 | −4.8% | 1.0 |
| C source-balanced recurrent | 0.1947 | +0.0% | 1.0 |

The contract required ≥20% reduction. R achieved 4.8%.

`structExp = 1.0` for R and C means the structural component added **nothing** — most targets
had no recurrent partner, so the dependency-aware mask degenerated into the uniform baseline.
Conditioning on the 43 targets that *did* have an observable partner only moved it to 3.0%.

**Candidate H is actively worse than uniform.** Masking pooled-Pearson partners consumes mask
budget without covering the held-out recurrent partners, so exposure rises. That is concrete
evidence about why historical graph masking was superseded, and it is the strongest argument
in this lane against reviving it. `HISTORICAL_COMPARATOR_ONLY` stands.

### The one apparent pass was vacuous, and is reported as a FAILURE

The K=10, R=0.50 grid cell produced U exposure 1.0000 → R exposure 0.0000, a 100% reduction.
It rests on **2 targets and 1 edge**. The contract states that a test executing zero eligible
targets is a failure; two is not materially different. Reporting this as a qualification would
be exactly the "adjust until something passes" failure the contract forbids.

### Anti-circularity

Masks were built from edges estimated on donor half A and scored against edges estimated
independently on donor half B. Scoring a dependency-aware mask against its own edges would be
tautological, and would have manufactured a large apparent win.

---

## Honest diagnosis: under-powered, not disproven

The limiting factor is per-donor depth, not the estimator. With ~700–880 cells per donor and
highly sparse single-cell counts, per-donor top-K neighbour lists are noisy, so recurrence
across ~40 donors per half is hard to achieve. The correct statement is:

`RECURRENT_DEPENDENCY_STRUCTURE_ABOVE_NULL_BUT_TOO_SPARSE_TO_QUALIFY_A_MASK_AT_THIS_POWER`

This is **not** a finding that molecular dependence is absent, and it is **not** a licence to
lower the thresholds. What would change the answer — to be decided by authority, not by me,
and frozen before the next run:

1. far more cells per donor (all blocks per operator rather than 3), raising per-stratum
   neighbour-list reliability;
2. a dependence statistic with more power under sparsity than per-donor rank correlation;
3. an explicit decision about whether the *ordered-pair* top-K formulation is the right
   neighbourhood definition at 41,238-address scale.

None of these may be chosen by trying them until one passes.

---

## Authority-scope finding (settles §14)

`MaskingAuthorityV1` does **not** own the numeric mask fraction. It carries
`dependency_source_authority_id`, a random/structural mixture ratio, and *references* to a
separate `target_evidence_budget_authority_id` and `rng_authority_id`. This lane therefore
had no standing to freeze a mask fraction, and did not. Historical `0.40`, `16 blocks`,
`GRAPH_K` and historical seeds carry zero current authority.

A second, unfixed defect: every identifier field on `MaskingAuthorityV1` is a free-form
string, the same weakness that was repaired for the target-address provider authority. It
also binds **no** SHA roots — no registry, support, or dependency artifact. Any future masking
authority must fix both before it can bind anything. No masking authority was frozen in this
lane, so nothing depends on that defect yet.

---

## Test accounting

| category | count |
|---|---|
| PASSED | 19 estimator qualification tests (7 required fixtures + 2 added confound attacks + specificity ×3 + determinism + config + 3 equivalence) |
| FAILED | 0 |
| SKIPPED / DESELECTED | 0 / 0 |
| NOT ESTIMABLE | metric B (cross-source recurrence) — too few surviving edges to compare across sources; metric G (source/operator leakage) — not reached, no policy selected |
| NOT EXECUTED | mask-policy authority implementation and its attack suite — deliberately not written, since no candidate qualified |
| ENVIRONMENT BLOCKED | 0 |
| HEAVY/DATA-DEPENDENT | 3 read-only FULL104 passes executed (600, 2,000 and 6,000 address universes); no training, no `D_shared` |

---

## Residual risks

1. The negative result is power-limited. A larger per-donor cell budget could change it, and
   the thresholds must stay frozen when that is tried.
2. Production geometry is still unchosen; a different query width or objective could change
   the shortcut landscape entirely, so this lane's conclusion is conditional on that.
3. `MaskingAuthorityV1`'s free-string fields and absent SHA bindings remain unrepaired.
4. Native/non-common-core targets were never evaluated for cross-source consensus; the
   contract's declared fallback was never exercised because no policy was selected.

## Readiness for subsequent lanes

Measurement-robustness authority, EMA presentation/timescale authority, production geometry,
runtime integration, preexecution closure and training authority all remain **not started**.
Masking must close first. Training remains unauthorized.
