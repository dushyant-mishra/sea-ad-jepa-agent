# Retrospective baseline, actual numbers — the benchmark does not yet discriminate

Date: 2026-09-24
Artifact: workflow run `36056203584`, `Perturbation screen-profile retrospective
baseline`, at commit `86e6ee83`, artifact
`gse178317-RETROSPECTIVE-development-baselines` (4,816 B, not expired).

**This is the first real-data baseline result in the project.** It is recorded
from the artifact, not inferred from a green check.

```
VERDICT   the benchmark as currently scored is UNINFORMATIVE
          a fitted baseline beats "predict nothing happens" by 4.50% MAE,
          and by 1.30% on the responsive subset,
          while LOSING to it on 20 of 39 targets on that subset
```

## Input binding

The run consumed exactly the committed table. The artifact records
`source_uncompressed_csv_sha256`
`41eb533dfd50852d0ebd8f2c27d42d5f6bb3b1f1264ab0c721106cfbaed9fc39`, which equals
the SHA-256 of the uncompressed contents of
`outputs/crisprbrain/iTF_Microglia-Day-8-CROP-seq-CRISPRi.csv.gz`
(file digest `201e8fb28a63dfb91ae5f37a77f9641a90c3cdf4c618943a55699c512227079f`,
13,586,532 bytes) as manifested in WP3. Verified, not assumed.

## Design integrity — every check the brief required

| check | result |
|---|---|
| targets | 39, all `ESTIMABLE` |
| target-disjoint folds | **YES** — 39 unique targets, each appearing exactly once |
| fold sizes | 5 folds: 8, 8, 8, 8, 7 |
| genes in original screen | 10,549 |
| own-target gene excluded | **YES** — `measured_genes_excluding_target` |
| missing-as-zero substitution | **NONE** — `scored_genes < measured` on 27 of 39 targets, 0 to 262 genes dropped rather than zero-filled |
| exposure ledger | `DEVELOPMENT_RETROSPECTIVE_ALREADY_INSPECTED` |
| split semantics | `TARGET_HELDOUT_WITHIN_SAME_EXPERIMENT_NOT_INDEPENDENT_VALIDATION` |
| responsive-subset selection | top 10% by mean absolute effect, **train targets only**, with a per-fold selection digest |

The machinery is sound. The result below is therefore a statement about the
benchmark, not about the harness.

## The numbers

**Macro, over all scored genes, equal weight per target:**

```
no-change (predict 0)         MAE 0.07188    RMSE 0.10037
train-target-mean profile     MAE 0.06864    RMSE 0.09713
improvement over no-change    4.50% MAE
```

**Responsive subset** — top 10% of genes by mean absolute effect, selected from
training targets only, so the selection carries no held-out information:

```
no-change                     MAE 0.21898
train-target-mean             MAE 0.21613
improvement over no-change    1.30% MAE
```

**Where the fitted baseline loses to predicting nothing:**

```
all scored genes     train-mean worse on  8 of 39 targets
responsive subset    train-mean worse on 20 of 39 targets
```

The eight worst on all genes:

```
MAPK14    0.06866 -> 0.07107        MAP2K6    0.05170 -> 0.05213
PPM1D     0.04594 -> 0.04706        TRAPPC3   0.05751 -> 0.05785
MTHFD2    0.03802 -> 0.03871        TGFBR1    0.05226 -> 0.05238
RPS6KA6   0.03755 -> 0.03811        PLK1      0.10778 -> 0.10783
```

## What this means, and what it does not

**It does not mean the data are bad.** GSE178317 has 39 targets all showing
knockdown of their own gene, verified against the depositors' analysis. The
perturbations worked.

**It means the scoring is dominated by genes that do not respond.** Mean
absolute error over roughly 8,700 genes, most of which move negligibly under any
given perturbation, is minimised by predicting zero. A model could score well
here by learning only that most genes do not move, which is not the biology the
project is trying to test.

**The responsive-subset result is the more serious one.** Restricting to the
genes that respond most across training targets should be where a mean profile
helps most. It gives 1.30%, and the fitted baseline is worse than predicting
nothing on more than half the targets. That is not a metric-scale artifact. It
says something substantive: in this screen, **the average response profile of
other targets carries almost no transferable information about which genes a
held-out target will move.** Responses here are largely target-specific.

That cuts both ways, and both matter:

* there is genuine headroom, since no trivial profile-averaging solves the task;
* but any method must beat MAE 0.07188, and the obvious way to beat it is to
  predict small numbers everywhere, which would be scored as success while
  demonstrating nothing.

## Consequence for the JEPA evaluation

**Running a model against this scoring now would produce an uninterpretable
result.** A poor score would not distinguish a weak model from an unlearnable
benchmark, and a good score would not distinguish understanding from having
learned that most genes are quiet. That is the exact failure the benchmark
exists to avoid, and it has been caught before any model was run.

Required before a model result could mean anything, in order:

1. **A metric that rewards identifying which genes respond**, not average error
   over mostly-null genes. Per-target rank correlation over a
   training-derived responsive set, or precision on the top-k movers, are the
   obvious candidates. Any such choice must be frozen before it is applied to
   held-out outcomes.
2. **A stated floor**: whatever metric is chosen, publish the no-change and
   train-mean baselines under it first. A method is only interesting if it beats
   both.
3. **Confirmation outcomes that are still unread.** GSE178317 and the CRISPRbrain
   Day-8 screen are `INSPECTED`; this result adds to that. Any prospective
   confirmation must come from the neuron, astrocyte and iPSC transcriptome-wide
   tables, which remain unopened.

## Scope

Retrospective, development only. No model was run, no training occurred, no
independent confirmation is claimed, and no biological error bar exists for any
number here: the four capture wells are not biological replicates.

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED
D_SHARED_G5=UNOPENED · RARE_TAIL_MOLECULAR=UNOPENED · THERAPEUTIC_RANKING=OFF
```
