# JEPA V27 handoff — what this cycle physically executed, and the one boundary it stopped at

Date: 2026-09-25. Supersedes nothing by itself: **V25 on `main` remains the
controlling startup document until a reviewed successor merges.** This records
one execution cycle and its exact blockers.

---

## Read this first

**The headline is that the first real-data V5 diagnostic did not run, and should
not have.** Two independent authorization gates withhold it, both named below,
neither modified. Everything lawful around that boundary was executed, and the
integration is now one adapter and two signatures away from being runnable.

**The second headline is that a planned external benchmark is gone.** The
CRISPRbrain screen pair cannot serve as benchmark truth. That was caught before
any model was scored against it.

---

## 1. COMPLETED_AND_PHYSICALLY_EXECUTED

| what | result | where |
|---|---|---|
| V5 suite, zero-skip census, CUDA env | 1,620 collected, **1,617 passed, 0 skipped, 3 failed** | PR #147 |
| Teacher/student integration freeze **V4** | **PASS**, 21 source rows, 7 active tests, **0 failures** | PR #147 |
| Frozen pass1 authentication | **AUTHENTICATED** `37f79e49…`, 18,029,576 B, two byte-identical copies | PR #147 |
| Calibration bundle recovery + authentication | **AUTHENTICATED** `07748d5b…`, 410,278,055 B, reassembled from 7 parts | PR #147 |
| PR #132 pass1→reader_fit donor-count bridge | **`per_donor_exact_count_match = True`**, 104 donors, 4,553,407 cells, **0** Level-4 blocks opened | PR #147 |
| P1-6 bulk independent recompute | **179,384 rows, zero disagreements** | PR #131 |
| GSE301119 identity certification (v2 R certifier) | both modalities byte-identical reconstruction from RDS | PR #127 |
| GSE301119 tie-safe two-arm null | negative control **FAILS**; finding survives the tie fix | PR #127 comment, branch `result/gse301119-tiesafe-null-executed-20260925` |
| CRISPRbrain screen reliability | **NOT usable as benchmark truth** | PR #137 |
| Layer-2 LODO input authentication | **PENDING_PHYSICAL_INPUT_AUTHENTICATION** — inputs absent | PR #133 |

## 2. SYNTHETIC_TESTED_ONLY

**Bounded V5 mechanical integration diagnostic**, 40 updates, 1,488.754 s,
`PASS`. Optimizer steps exactly once (1..40, every delta +1); EMA residual
**0.0** exactly; parameters move every update (min max-delta 2.935e-04); Adam
moments 59/59; checkpoint restart reproduces the uninterrupted run with
identical fingerprints; protected-gradient gate **40/40 affirmative**
(`missing 0, nonfinite 0, exact_zero 0, teacher_gradients 0`).

Loss fell 62.7 % on synthetic tensors. That is gradient flow, not biology, and
the receipt says so in its own text.

PR #132's 51 tests, PR #136's baseline and the other lanes' synthetic suites
remain synthetic and are **not** relabelled.

## 3. BLOCKED_BY_AUTHORIZATION — the boundary this cycle stopped at

Two gates, independent, neither bypassed:

**B1 — population registry.** `reader_fit.current_state =
ELIGIBLE_POOL__NOT_EXECUTION_AUTHORITY`. `"new teacher training"` is listed under
`forbidden_without_new_authority`. The registry names its own remedy: a
**separate frozen training contract**. What *is* permitted, and what the
mechanical diagnostic ran under, is `"D1-A synthetic/u0-safe development when no
real reader-fit expression is consumed"`.

**B2 — code.** `issue_training_authority_v1` is the only schema allowed to carry
`training_authorized=True`. It requires a `receipt_v2` validated against a
**frozen teacher-target package root**. `target_package_root` appears **only in
source code**, in no committed artifact; no `CLOSURE_V2` artifact exists. The
function is fail-closed and would raise.

**To unblock, in order, and neither is an engineering step:**

1. Freeze the teacher-target package and record its root so `receipt_v2` can
   validate. This is a scientific decision about target semantics.
2. Issue a named frozen training contract scoped to a development diagnostic on
   `reader_fit`, naming candidate, masking configuration, update budget and
   prospectively recorded DEVELOPMENT scoring.

Then the remaining engineering is **one adapter**: FULL104 streaming readers →
the update harness signature. Every other stage exists and the V4 freeze covers
it.

## 4. NOT_EXECUTED

* FULL104 all-104 raw-count verification (PR #120) — the lane was running at
  ~25 min per 1,000 blocks and terminated on a session limit before completing.
  **No verdict exists; do not infer one.** It is a raw-count integrity task and
  still does not authorize N1 masking outcomes.
* The FULL104→harness adapter, deliberately.
* Per-cell donor lineage, pass1-to-raw-Level4 binding, source-library and
  proposal-q validation — all declared `NOT_PERFORMED` by the count bridge.

## 5. Scientific results that changed what we can claim

**GSE301119 negative control fails, and survives correction.** Observed median
log2FC −1.3446 against a cell-sampling NT-vs-NT null median of **−1.5040**: the
fake effects are the same size and direction as the real ones. 72.8 % of
sentinel observations have at least half the null draws beating the real effect.
Under PR #127's tie-safe algorithm the tail recurrence is observed **17.4642 %**
vs null **17.4470 %**, and the up-tail is still *higher* under the null
(4.8036 % vs 3.6023 %). Effects and null medians were **bit-identical** across
the tie-unsafe and tie-safe runs, which is the control proving the fix touched
only tail membership.

Bias decomposition, measured: depth-only thinning leaves −0.046; adding
composition variation moves it to −1.504. **Cell-state under-sampling is the
leading term (~95 %)**; depth/zeros/pseudocount is a smaller, independently
non-clean second term. This rules out expression-stratification and an NB-GLM
with library-size offsets as fixes — both address the ~5 % term and would pass
their own diagnostics. The empirical-null calibration direction is recorded as
**DESIGN DIRECTION ONLY**.

**CRISPRbrain cannot be benchmark truth.** Engagement demonstrated in 1/31
targets jointly (STAT2). Concordance at chance: Pearson 0.0723, sign agreement
0.5181. **50 of 54 jointly significant rows are one target, ZNF644, whose two
profiles correlate at 0.0016.** The pair is not independent replication — same
lab, same paper, row-for-row identical guide library, same vector, same WTC11
line, same pipeline. Four preliminary figures failed to reproduce for one
reason: they were computed at FDR<0.10; at 5 % the screens point in **opposite
directions on 33 of 54** jointly significant rows.

**The historical Layer-2 LODO baseline is not currently reproducible.** All three
inputs are absent across a completed full scan of both drives, and the producer
scripts are gone from git and disk. The recorded SEA-AD 0.2410 / HVS 0.0451 /
NPH52 0.0546 are a documented prior result from a **94-donor, unweighted,
256-dim VALUE_ONLY linear proxy** whose target is the same cell's other view —
not pathology, not a JEPA, not 104 donors. Cite them with those caveats; do not
present a new 104-donor baseline as a replay of them.

## 6. Self-audit S8–S16

| | finding | status |
|---|---|---|
| S8 | I read the three failing freeze audits as byte drift and nearly reported the seam as broken. Current freeze is **V4** and passes; V1–V3 are superseded. | corrected before reporting |
| **S9** | **The CUDA env `sea-ad-jepa` has a broken numpy BLAS** — every matmul crashes (`0xc06d007f`), including 3×3, while torch is fine. `sea-ad-jepa-v3` is healthy. **Earlier results computed there using numpy linear algebra should be re-checked.** | **open, environment defect** |
| S10 | V1–V3 freeze tests fail permanently instead of declaring supersession, which would mask a real V4 regression. | open |
| S11 | `scripts/v4/contextual_target_f1_preflight_core_v1.py` imports POSIX-only `resource`; uncollectable on Windows. A preflight that cannot run on the execution machine is not a preflight. | open |
| S12 | Harness unit tests pass `ema_momentum=.996` as a fixture argument; the historical constant is still readable as an example. The diagnostic uses 0.99 so inheritance shows as a mismatch. | mitigated |
| S13 | My published 17.69 %/17.69 % agreement might have been a shared tie-breaking artifact; my collapse check ruled out aliasing but **not** mechanism-sharing. Rerun under the tie-safe rule: it survives. The original check was **insufficient, not wrong**. | resolved |
| **S14** | **My driver read two report keys that do not exist.** `optimizer_step` defaulted to −1 and failed loudly; `gradient_report` defaulted to `None` and **silently** recorded nothing, so the protected-gradient gate was never inspected. The loud bug exposed the silent one. | fixed — missing keys now raise |
| **S15** | **My gate assertion was `is not None`** — close to a tautology; it would pass on an object reporting dead gradients. Now requires four zero counters and `max_abs_gradient > 0`, re-evaluated over 40 stored records (40/40). | fixed |
| **S16** | **I pointed two subagents at one worktree.** They collided: one committed onto the other's branch and reset its ref. PR #131 carries two commits from an unrelated workstream. Neither agent rebased them away — receipts cite exact commits, so rewriting would make a truthful record point at hashes that no longer exist. | **disclosed, carried, not rewritten** |

## 7. Live lanes not owned by this cycle

PRs #135, #136, #138, #139, #140, #141, #142, #143, #144, #145, #146 were
produced by other lanes during this cycle. They are **not** merged and not
implied reviewed here. PR #141 is a cross-PR ownership and collision map and is
the right place to reconcile S16. PR #120/#124 remain the raw-count lane.

## 8. Standing boundaries, unchanged

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED
D_SHARED_G5=UNOPENED · RARE_TAIL_MOLECULAR=UNOPENED · THERAPEUTIC_RANKING=OFF
```

`reader_validation`, `reader_oracle`, foundation development, sealed foundation
holdout, whole-study Siletti, pathology, `D_shared` and N1 masking outcomes all
remain closed. No promotion is claimed anywhere in this cycle. No PR was merged.
