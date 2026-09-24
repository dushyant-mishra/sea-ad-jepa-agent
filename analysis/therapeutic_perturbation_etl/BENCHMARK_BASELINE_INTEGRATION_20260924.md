# Perturbation benchmark: reuse, do not restart — 2026-09-24

Scope: CODE + RETROSPECTIVE DEVELOPMENT BASELINES. No FULL104 training, protected
outcome inspection, independent confirmation, brain-causal generalization or
therapeutic ranking.

## Integration

Byte-exact code/test/workflow files from the previously reviewed
#84 → #88 → #90 baseline/exposure chain were copied from PR #99 on top of the
current PR #77 experimental head. The guide×donor baseline module remains
appropriate for GSE301119 with real independent donor identities; do **not**
label GSE178317 capture wells as donors to satisfy that interface.

The exposure ledger was updated with September-24 inspected GSE178317 target
engagement and transcriptome-wide DE and its same-experiment CRISPRbrain
reference. These cannot become untouched held-out outcomes. No other unseen
assay/arm is automatically marked inspected or prospectively untouched.

## GSE178317 profile baseline

A small complementary adapter now handles one *published target×gene DE
profile screen*, never inventing donor replicates. Its only two candidate
predictions are: (1) no change (zero Log2FC); and (2) equal-weight mean of
OTHER training perturbation targets on the same screen. The target's own
perturbed gene is excluded from every downstream score. Only features present
in both held-out target and training predictions are scored for either
baseline; missing is never zero. Five folds are deterministic over target IDs,
and results macro-average across targets, not across the many genes/cells.

The Day-8 CRISPRbrain input is the *same experiment* as our recovered
GSE178317 SRA cells. Its processed CSV must match the frozen published
uncompressed SHA-256:
\`41eb533dfd50852d0ebd8f2c27d42d5f6bb3b1f1264ab0c721106cfbaed9fc39\`.

The CI workflow executes the baseline on the already-inspected committed
CRISPRbrain screen and attaches an explicitly labeled DEVELOPMENT report.
There is no significance test or biological error bar: no independent
differentiations/donors were established. The source's original gene labels
remain within-screen; **no FULL104 cross-study comparison is authorized**
without the real frozen HGNC/Ensembl/Entrez map and baseline culture-vs-brain
domain measurement.

## Stop conditions

- The test fold targets must be disjoint from fitting targets. No held-out
  outcome may affect model fitting.
- Every target's own perturbed gene must be absent from its scoring columns.
- Do not use source GSE178317 and the same experiment's CRISPRbrain output as
  independent train/test biology.
- The archived full GSE178317 count NPZ remains a valuable immutable
  DEVELOPMENT record. Its original object-string arrays do not satisfy the
  new non-pickle V2 runtime contract; do not relabel it as a newly reissued
  count without actual separately reviewed conversion/provenance.
- The gene identity mapping *schema* exists, but the frozen real annotation
  bytes and per-study mapping receipt remain open.
- Training, N1 and protected outcomes remain OFF/UNOPENED.
