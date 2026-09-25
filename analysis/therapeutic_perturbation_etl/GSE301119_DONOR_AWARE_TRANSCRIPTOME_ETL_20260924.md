# GSE301119 — donor-aware transcriptome-wide development ETL

Date: 2026-09-24
Status: `PASS_DEVELOPMENT_ETL` — two donors, not population generalizable.

```
source authenticity        VERIFIED   both Seurat5 RDS rehashed against sidecars
pseudobulk inputs          VERIFIED   4 heavy outputs rehashed against manifest
PR #91 support census      REPRODUCED independently, before any effect computed
donor-aware effects        PASS       206 targets per modality, strata separate
population SE              NOT PRODUCED   n biological donors = 2
```

## Provenance

Source objects, rehashed from disk and matching their acquisition sidecars and
the raw-pseudobulk manifest exactly:

```
GSE301119_CRISPRa_seurat5.rds  345,798,341 B  2f700baff2390e257a7ae1b301204bceb5feeb823671c21f10fd3f1038450829
GSE301119_CRISPRi_seurat5.rds  406,836,813 B  fc2584fad6327defb32b939c94e89fa174d3287399ab66e91b6189569b108eb3
```

All four heavy guide×donor pseudobulk outputs rehashed OK against
`RAW_PSEUDOBULK_PROVENANCE_MANIFEST.json`. Toolchain is the manifest's pinned
one: R 4.6.1 with **SeuratObject 5.4.0** from `D:/jepa_rlib46`. That pin matters
— Seurat 4 accessors can silently misread `Assay5`.

Task-1 raw pseudobulk was already independently reproduced at normalization
max-abs-delta **0.0** and engagement max-abs-delta ~5e-15 against a tolerance of
1e-9 declared before inspection. This work starts from that, and does not
recompute it.

## PR #91 support census, reproduced before any effect was computed

Reading the pseudobulk directly reproduces the independent census exactly:

```
CRISPRi  2,137 guide×donor groups   28,466 cells   206 targets   D1 1,106 / D2 1,031
CRISPRa  2,098 guide×donor groups   23,584 cells   206 targets   D1 1,084 / D2 1,014
```

And independently rediscovers its key limitation: **CRISPRa HEXA is the one
target whose within-donor guide variance is not estimable.** The producer was
not told which target to expect.

## Design, fixed before results

* **The biological unit is the donor, and there are two.** Cells are not donors;
  guides are not donors. No population standard error is produced. Each donor's
  value is reported separately alongside their range, labelled descriptive.
* **CRISPRi and CRISPRa are separate strata, never pooled.** They are opposite
  interventions on the same gene list.
* **Raw integer counts are summed across a target's guides within a donor before
  normalisation.** Averaging per-guide log ratios instead would weight a 6-cell
  guide equally with a 200-cell guide.
* **Controls are donor-matched.** A target in D1 is contrasted against
  non-targeting guides from D1, so donor is never confounded with perturbation.
* **Missingness is explicit.** A gene absent from the assayed feature space is
  `STRUCTURALLY_UNMEASURED`; a gene present with zero counts is
  `ASSAYED_UNDETECTED`. Neither is collapsed to zero effect.

## Results

```
                              CRISPRi        CRISPRa
guide×donor groups              2,137          2,098
cells                          28,466         23,584
targets                           206            206
genes assayed                  36,601         19,162
genes detected in perturbed    29,378         17,432
genes assayed-undetected        7,223          1,730
NT guides / cells  D1          98 / 1,425     99 / 1,446
NT guides / cells  D2          90 /   759     93 /   671
cross-donor mean estimable        204            198
guide variance estimable          206            205
engagement measured               204            205
median engagement log2FC      -1.0518        +1.9731
```

Heavy outputs, referenced not committed:

```
CRISPRi_donor_aware_log2fc_matrix.rds  29,391,063 B  7f550f436333cf6159f54ff7b3221617952fcc13ac2b9d68c4cf572d53b39e43
CRISPRa_donor_aware_log2fc_matrix.rds  21,338,886 B  474202c0705a57bdc939ce483fe7612d9082fb57d80d94eefd8bd3d3c509ba93
```

### The direction asymmetry is the internal validation

CRISPRi moves the targeted gene **down** (median −1.05); CRISPRa moves it **up**
(median +1.97). Opposite interventions, opposite signs, computed by the same code
from the same pipeline. Nothing was tuned to produce that.

The own-gene status split is coherent with it and was not designed:

```
                      CRISPRi   CRISPRa
ASSAYED_DETECTED          176       204
ASSAYED_UNDETECTED         29         1
STRUCTURALLY_UNMEASURED     1         1
```

Silencing a gene can push it below detection, so 29 CRISPRi targets end
assayed-undetected. Activating one cannot, so only TREML4 does under CRISPRa.
Recording these as `ASSAYED_UNDETECTED` rather than as zero effect is the whole
point of the distinction: a silenced gene reading zero is a successful
perturbation, not a missing measurement.

`FCGR2C` is `STRUCTURALLY_UNMEASURED` in both modalities — it is targeted but
absent from the assayed feature space, so its engagement cannot be measured at
all and is reported as such rather than as a null result.

## Two structural limits that must travel with these numbers

**The modalities do not share a feature space.** CRISPRi assays 36,601 genes;
CRISPRa assays 19,162. Any cross-modality comparison must run on the
intersection, and must not read a gene's absence from the CRISPRa space as a
missing measurement in a CRISPRi contrast. The two matrices are stored with
their own feature vectors for that reason.

**Targets lacking a cross-donor mean are reported, not dropped silently.**
CRISPRi: HAVCR1, SYK. CRISPRa: C1QC, CLDN7, CLEC2B, EPHA1, HEXA, NFATC1, NFATC2,
TYROBP. These failed the declared 10-cell-per-(target, donor) floor in at least
one donor, so their effect rests on a single donor and no cross-donor value is
emitted.

## Scope

Development ETL. No predictor was fitted, no therapy ranked, no reserved outcome
opened. **Two donors do not license a population or in-brain generalization
claim**, and engagement success says nothing about downstream prediction.

```
TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED
D_SHARED_G5=UNOPENED · THERAPEUTIC_RANKING=OFF
```
