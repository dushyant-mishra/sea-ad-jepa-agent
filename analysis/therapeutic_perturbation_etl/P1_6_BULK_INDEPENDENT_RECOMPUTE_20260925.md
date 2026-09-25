# P1-6 independent physical recompute: GSE241858 and GSE240609

**Date:** 2026-09-25 · **Branch:** `result/p16-bulk-independent-recompute-20260925`
**Audit item:** P1-6, the two studies left `NOT_DONE` when GSE254205 was completed.

---

## 1. The verdict first

**This is good news, and it closes P1-6.** Both studies were recomputed from the
original sequencing count files by code written separately from the code that
produced the published numbers, and the two agree on **every one of 179,384
compared values**. Nothing disagreed. No number had to be revised.

**What that does and does not mean.** It means the software is right: the
published effect sizes really are what the declared method produces from the raw
data, and are not the product of a bug, a mislabelled sample, or a lost gene. It
does **not** mean the biology is established. Reproducing a calculation proves
the calculation; it says nothing about whether the measured differences reflect
real biology. Both studies remain scientifically unqualified, and this document
claims nothing about their effects being real.

**What was already fine and stays fine.** The clone structure in GSE241858 was
handled correctly by the existing producer — the two iPSC clones per genotype are
treated as the biological units, and the repeated measurements inside a clone are
averaged first rather than counted as independent people. The one-sample-per-cell
limitation in GSE240609 was also handled correctly: no standard errors and no
p-values were invented anywhere. Both of those were checked adversarially, not
assumed.

**One thing to note, found and fixed before it mattered.** Two defects turned up
in my own reproducer code while the adversarial tests were running, and two
previously-cited depth numbers turned out to be labelled with the wrong
definition. All four are written up in sections 6 and 7. None of them changed a
scientific result; all were caught before anything was reported as final.

| Study | Verdict | Rows compared | Worst disagreement |
|---|---|---|---|
| **GSE241858** | `IMPLEMENTATION_REPRODUCED_TO_STORED_PRECISION` | 141,294 | 5.0e-07 (log2fc), 5.0e-07 (SE) |
| **GSE240609** | `IMPLEMENTATION_REPRODUCED_TO_STORED_PRECISION` | 38,090 | 5.0e-07 (log2fc) |

---

## 2. Why the verdict says "stored precision" and not "full precision"

The contract declared, before any of this ran, that agreement means
`max |difference| <= 1e-9` on every compared value. **That threshold failed, and
it was not widened.** This is the same outcome GSE254205 reached, for the same
reason.

The reason is mechanical, not scientific. The producer writes its numbers into a
CSV rounded to 6 decimal places. Once a number is stored as `-0.276267`, the
information needed to check it at the 9th decimal is simply gone. The largest
differences observed were `4.999965e-07` and `4.999712e-07` — just under
`0.5e-06`, which is exactly half of the last stored decimal. That is the
arithmetic signature of rounding and nothing else.

Widening the tolerance to `1e-6` would have made the test pass while making it
weaker. Instead, the check was replaced with a **stricter** one, following the
qualified GSE254205 template:

> round my independently computed value to 6 decimals; it must equal the stored
> value **exactly**, on every single row.

It does, on every row of both studies, for both the effect sizes and the standard
errors:

| Study | Field | Rows matching exactly on rounding |
|---|---|---|
| GSE241858 | `log2fc` | 141,294 / 141,294 |
| GSE241858 | `se_clone_level` | 141,294 / 141,294 |
| GSE240609 | `log2fc` | 38,090 / 38,090 |

Verifying at the declared `1e-9` remains impossible against these CSVs and would
require the producers to emit unrounded values. That limitation is recorded in
both receipts rather than papered over.

---

## 3. GSE241858 — clone-aware, and proven to be

**Design.** TREM2 R47H versus control iPSC-derived microglia. **Two independent
clones per genotype**, with two or three repeated measurements inside each clone.
A baseline arm (12 samples) and a cytokine arm (23 samples) — 35 samples total.

**The trap this design sets.** The repeated measurements inside one clone are the
same cell line measured again. They are not independent biology. Counting all six
control measurements as six independent units would triple the apparent
replication and shrink every standard error accordingly.

**Why simply getting the same answer would not have proved anything.** The
baseline arm is perfectly balanced — three replicates in every clone. When a
design is balanced, averaging within clones first and then across clones gives
*exactly* the same effect size as ignoring clones entirely. Measured here:
`3.55e-15`, i.e. zero to floating-point precision. So on the baseline effect
sizes, a clone-aware producer and a clone-blind one are **indistinguishable**.

The reproducer therefore refuses to believe its own agreement until it has shown
it could detect the error. Two controls run first, and both must fire:

| Control | Measured gap | Meaning |
|---|---|---|
| Baseline **standard error**, clone-aware vs clone-blind | **0.762** | balanced design hides the error in the effect size, but not in the uncertainty |
| Cytokine `LPS_vs_UNTR_in_CTRL` **effect size**, clone-aware vs clone-blind | **0.967** | this cell is *unbalanced* (clone CTRL_A has one LPS replicate, CTRL_B has two), so here the two estimators genuinely diverge |
| Reversed contrast negates exactly | yes | the comparator is direction-sensitive |

Having established that a clone-blind producer *would* have been caught — by
0.967 log2 units in one place and 0.762 SE units in another — the agreement that
follows is informative. **The producer matches the clone-aware estimator and not
the clone-blind one, everywhere.**

**Comparison result.** 6 contrasts, 141,294 rows.

| Contrast | Rows | max abs delta log2fc | max abs delta SE |
|---|---|---|---|
| `R47H_vs_CTRL_baseline` | 20,509 | 4.998727e-07 | 4.999599e-07 |
| `IFN_vs_UNTR_in_CTRL` | 24,157 | 4.999965e-07 | 4.999931e-07 |
| `IFN_vs_UNTR_in_R47H` | 24,157 | 4.999935e-07 | 4.999642e-07 |
| `LPS_vs_UNTR_in_CTRL` | 24,157 | 4.999593e-07 | 4.999993e-07 |
| `LPS_vs_UNTR_in_R47H` | 24,157 | 4.999183e-07 | 4.999176e-07 |
| `R47H_vs_CTRL_untreated` | 24,157 | 4.999919e-07 | 4.999857e-07 |

Also reproduced exactly, with zero mismatches: all 35 library sizes and the whole
sample identity table; every gene symbol; the clone-unit counts on every row
(2 vs 2 throughout); and the rule that only detected genes are emitted
(20,509 detected of 28,395 in the baseline arm, 24,157 of 28,395 in the cytokine
arm; 0 rows emitted for undetected genes).

---

## 4. GSE240609 — descriptive only, and proven to claim nothing more

**Design.** A 2x2: neuron genotype (WT vs PSEN) crossed with microglia genotype
(APOE3 vs APOE3-Christchurch). **One sample per cell of the design. Four samples,
four cells, no replication anywhere.**

Differences between conditions can be computed. Biological uncertainty **cannot**
be estimated — there is no second observation of any condition to estimate it
from. A standard error here would be measuring sequencing noise inside a single
library, and any reader would take it for biological replication that does not
exist.

The reproducer computes no standard error and no p-value, and it actively
**requires the producer to have emitted none**. Every row is checked for a
numeric `se`, for `n > 1` on either side, and for any claim that uncertainty is
estimable. Result: **0, 0 and 0** across all 38,090 rows. The producer claims
exactly what the design supports and no more.

**The headerless-file trap, and the A1BG check.** These four count files have no
header row. The first physical line is a real gene — `A1BG`. A parser that
assumes a header eats that line, ends up with 27,153 genes instead of 27,154, and
**shifts every gene label by one row** for the rest of the file. The shape still
looks plausible, so nothing downstream would flag it. A prior pass made exactly
this error.

The reproducer hard-asserts 27,154 genes and that `A1BG` is the first gene, and
then runs the bug deliberately as a control: it re-parses all four files
header-consuming and requires the answer to *disagree*. It does, by **7.61 log2
units** — so the comparator demonstrably distinguishes a correct parse from the
off-by-one before its agreement is trusted.

Measured directly from the files: A1BG carries **71** counts in GSM7703564 and
**63** in GSM7703571. (The task brief cited 63 for GSM7703564; 63 is the
GSM7703571 value. The load-bearing point — A1BG is a gene row, and there are
27,154 genes — is confirmed exactly.)

**Comparison result.** 2 contrasts, 38,090 rows.

| Contrast | Rows | max abs delta log2fc |
|---|---|---|
| `APOE3ch_vs_APOE3_microglia_in_PSEN_neurons` | 19,045 | 4.999108e-07 |
| `APOE3ch_vs_APOE3_microglia_in_WT_neurons` | 19,045 | 4.999712e-07 |

Also reproduced with zero mismatches: 27,154 genes parsed with A1BG first;
19,045 detected and 8,109 assayed-but-undetected; all four library sizes; and the
full sample identity table. The design cell for each sample was derived
**independently from the GEO filename** and then required to agree with the
producer's GEO-title-derived table — a disagreement would have been a stop, not a
warning. All four agree.

**Interpretation limit, carried forward unchanged.** The RNA comes from
CD11b-purified microglia recovered *after* neuron coculture. A difference is a
property of the coculture, not a cell-autonomous microglial effect.

---

## 5. Adversarial test suites

**41 tests, all passing** — 20 for GSE241858, 21 for GSE240609. Each damages
exactly one thing and requires a non-zero exit; exit status is asserted, never
message text.

Each suite opens with a **POSITIVE CONTROL that must pass**. Without it the
rejections would be worthless: a script that exited non-zero unconditionally
would satisfy every other test in the file. The fixtures' expected values come
from a small reference implementation inside each test module — a *third*
implementation, independent of both producer and reproducer — and the positive
control is what establishes the three agree before any rejection counts.

Degenerate and adversarial inputs covered, as required: empty contrast group,
missing sample, duplicated gene id, non-integer count, negative count, ragged
row, permuted column order, wrong gene count (27,153 and 27,155 vs 27,154),
unparseable sample label, unexpected header, gene order differing between files,
swapped sample contents, perturbed effect sizes, emitted undetected genes,
identity-table contradictions, source byte-root mismatch, and a populated output
directory.

The two scientifically load-bearing tests:

- **`test_clone_flattened_log2fc_rejected`** — a producer that treated
  within-clone replicates as independent units. The fixture deliberately mirrors
  the real unbalanced cytokine cell, because that is the only place the point
  estimates differ.
- **`test_fabricated_se_rejected`** (plus the `n > 1` and `uncertainty_estimable`
  variants) — a producer that attached a standard error to a design with one
  sample per cell.

Run:
```
python -m pytest tests/test_gse241858_independent_reproduce_redteam_20260925.py \
                 tests/test_gse240609_independent_reproduce_redteam_20260925.py -q
41 passed
```

No tests were skipped. No comparison was unavailable. Nothing was stubbed.

---

## 6. Defects found in my own code, and fixed there

Both were found by the adversarial suites, and both were fixed in the
**reproducer**, not worked around in the test.

1. **An empty contrast group produced an unnamed crash.** With every control
   sample removed, the group-difference function correctly returned "no result",
   but the sign control then tried to use that result and died with a raw
   `TypeError` traceback. The run still failed — it never produced a wrong
   number — but a fail-closed contract should refuse *by name*, not fall over. A
   degenerate preflight now checks every contrast has a non-empty numerator and
   denominator before any control runs, and refuses with
   `STOP_CONTRAST_HAS_EMPTY_GROUP`.

2. **A text value where a count belongs raised an unhandled exception.** If a
   header line appears in a file whose format declares it has none, the parser
   hit `float("count")` and crashed. Now `STOP_UNPARSEABLE_COUNT`.

A third defect was caught by inspection while writing the depth block: unit
selection had been keyed on **dictionary insertion order** rather than on the
`(clone, treatment)` identity. For the cytokine arm those two orders genuinely
differ, so it would have mismatched clones to library sizes. It never ran in that
state and never reached a receipt; it is recorded here because the class of error
— indexing a scientific unit by storage order instead of its identity — is one
this project has been bitten by before.

**No defect was found in either producer.** Both were already correct on every
point tested.

---

## 7. Depth susceptibility: numbers reconciled, and a labelling correction

Earlier screening cited **1.370x** for GSE241858 and **1.2509x** for GSE240609 as
"worst within-contrast library ratio", to show these studies are not exposed to
the sequencing-depth artifact that invalidated GSE301119. Both numbers reproduce
exactly — but neither is a within-contrast *sample-pair* ratio, and both receipts
now record the measurement under every definition so the figure is read against
the definition that produced it.

**GSE241858 — 1.3705 is the worst ratio between the two contrast groups' *mean*
library sizes** (`R47H_vs_CTRL_baseline`). The worst ratio between two individual
samples inside a contrast is **6.02x**, and the worst spread across clone-level
mean libraries is **2.32x**. Group means average over a considerably wider
per-sample spread, so 1.370x understates the raw variation.

**GSE240609 — 1.2509 is the study-wide max/min across all four libraries**, not a
within-contrast pair. The actual per-contrast pair ratios are **1.1520** (WT) and
**1.1448** (PSEN). Here the cited figure is an *upper bound* on every contrast, so
the conclusion is unaffected and is if anything conservative.

**This is a susceptibility screen, not qualification.** A depth ratio speaks only
to whether the GSE301119 artifact *could* apply. It does not qualify any effect
in either study as biologically real. Neither study is scientifically qualified
by this work, and no therapeutic ranking follows from it.

---

## 8. Provenance

Both runs executed from a **pristine git worktree checked out at commit
`e3b45332`**, with `git status --porcelain` verified empty at execution. Each
receipt records its own measured provenance — the SHA-256 of the script that
actually ran, the commit, and the worktree status — rather than an assertion
about it.

| | GSE241858 | GSE240609 |
|---|---|---|
| Executing script SHA-256 | `9ca458cfab31760f…` | `3f45f73812b274a8…` |
| Commit | `e3b45332` | `e3b45332` |
| Worktree clean at execution | `true` | `true` |

**Source byte roots verified before any number was computed.** The two GSE241858
count matrices matched the roots frozen by PR77 (`2c7811e2…`, `50f1e487…`), and
all four GSE240609 files matched the roots in the public GEO sample authority.

Receipts:
- `analysis/therapeutic_perturbation_etl/evidence/gse241858_independent_repro/GSE241858_BULK_INDEPENDENT_REPRODUCTION_V1.json`
- `analysis/therapeutic_perturbation_etl/evidence/gse240609_independent_repro/GSE240609_BULK_INDEPENDENT_REPRODUCTION_V1.json`

Reproducers:
- `analysis/therapeutic_perturbation_etl/scripts/independent_reproduce_gse241858_bulk_v1.py`
- `analysis/therapeutic_perturbation_etl/scripts/independent_reproduce_gse240609_bulk_v1.py`

Both are separately authored implementations, not refactors of
`build_bulk_disease_context_effects_v2.py`. This is deliberately **not** a
V1-versus-V2 parity check: showing V2 changed no number would not show either was
right.

---

## 9. Status

**P1-6 is complete.** GSE254205 was already done; GSE241858 and GSE240609 are now
done, at the same stored-precision standard and with the same declared tolerance
unwidened.

Not claimed, and still open: biological qualification of any effect in either
study; anything about effect sizes being real; any promotion or ranking.

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED · D_SHARED_G5=UNOPENED · RARE_TAIL_MOLECULAR=UNOPENED · THERAPEUTIC_RANKING=OFF
```
