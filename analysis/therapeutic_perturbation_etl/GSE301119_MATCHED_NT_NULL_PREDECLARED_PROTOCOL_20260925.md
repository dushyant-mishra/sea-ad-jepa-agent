# GSE301119 matched non-targeting control null — predeclared scientific protocol

**2026-09-25; DEVELOPMENT ONLY.** This branch is based on PR121 `aaf561cfdc60ffe29c4d79094c16ce5e524f7d2d`, not main. The historical PR121 producer, full-data results, and protected stores remain unchanged. No N1, FULL104 protected results, model training or therapeutic prioritization.

## Scientific question

Does the existing GSE301119 estimator — log2(CPM+1) target minus donor-matched pooled NT — generate large, recurrent apparent effects even when its "target" is a pseudo-target made entirely of non-targeting (NT) guides?

Opus's reported 18–22× NT/pseudobulk depth imbalance, near-monotonic association of top-effect magnitude with unit size, and recurrent downregulated CLU/CCL22/MMP12/CXCL10/CXCL11/MT1H/MT1G are **hypotheses and preliminary metadata/top-50 observations**. Their measured numerical values are not independently established by this protocol. The PR121 Python reproducer's own hand-computed fixture has a truly unchanged raw-count gene `gFLAT` whose normalized estimate is approximately -0.807. This is genuine evidence that normalization can create a nonzero effect under altered composition; it does NOT establish prevalence or cause of full-data effects.

## Frozen computational experiment

- Inputs: the *existing* authenticated PR121 neutral export for CRISPRi and CRISPRa: four required files per modality (`{mod}_counts_int32.bin`, `{mod}_shape.txt`, `{mod}_features.txt`, `{mod}_gd_meta.csv`), plus `NEUTRAL_EXPORT_RECEIPT_V1.json`. The script rejects count-bin and original RDS hashes inconsistent with the committed PR121 donor-aware receipt. Source RDS hashes: CRISPRi `e796504f41ddd65f3a5b72699d12431ce664974e0860ecb255858bd084283549`; CRISPRa `9fe028f508ce33a8c968ab05c363c345135b0b6227db4476838c70fb9d874d90`.
- Unit: each donor×target pooled across its authentic targeting guides. Only target units with >=10 cells enter a null; true independent biological units remain **two donors**. CRISPRi and CRISPRa remain separate feature universes and estimands.
- For each target unit, select donor-matched NT guide groups with **exactly the same guide count**, and total cell count within a prospective ratio of **1.5** in either direction. Select on guide and cell counts only, never sequencing depth, expression profile, or apparent effect. Random seed **301119**, 64 draws per unit, 256 cell-matching trial combinations per draw.
- For each selected NT pseudo-target, exclude *all* its selected guides from its own NT denominator, then compute **the identical legacy log2(CPM+1)** contrast as the original producer. Distinct selected guide sets only: duplicated Monte Carlo selections are not counted as additional evidence.
- Failure is explicit: if fewer than 32 usable unique matches remain, mark that donor×target `NOT_ESTIMABLE_INSUFFICIENT_MATCHED_NT_NULL`. Record match count and real/pseudo group cell-count bounds. No cherry-picking after observing expression.
- Output per donor×target: actual and null sentinel effects, empirical null 2.5/97.5% quantiles and absolute exceedance fractions; recurrence among strongest 25 up and 25 down genes; median null maximum absolute effect; target/control RNA depth ratio. Calculate a *separate exploratory* positive-gene median-centred log-ratio sensitivity; missing zeros remain NaN, not zero.
- Deliver the single small versioned JSON receipt; it contains no high-dimensional count data and no new protected outcome. Repeat resamples overlap and are **not independent n=64 experiments**, independent donor observations, formal hypothesis-test p-values, or evidence of population transport.

## Falsifiable interpretation fixed before reading the full receipt

If matched NT pseudo-targets regularly generate the same large negative sentinel effects or comparably recurrent extreme genes, the apparent GSE301119 top-effect lists **cannot be used as interpretable target-specific molecular-response labels** without a redefined estimand and a new validation run. Directional on-target engagement must then be analysed separately from the transcriptome-wide response.

If the NT null is well behaved but true-target effects remain extreme, **do not declare the effects causal**: guide-specific toxicity/selection, targeting-induced shifts in cell-state composition, genuine perturbation, and library-size differences can still coexist. Qualify measured cell-state balance, compositional sensitivity, donor consistency, and guide-level reproducibility before claiming a biological response. Two donors never justify population-level uncertainty.

A median-centred normalization that attenuates apparent effects is a sensitivity result, not ground truth; it assumes most positively detected genes are unchanged and cannot fix true zero/detection differences. A nonzero null can arise from differences among NT guides and measurement stochasticity; record its scope without assuming the entire targeting signal is false.

**Never tune pseudocount, cell-matching tolerance, tail cutoffs, or sentinel selection after examining the null receipt and call that a predeclared result.** A future alternative-normalization full-matrix analysis must be separately versioned.

## GPU laptop invocation

From the PR121-descendant branch, after verifying the source RDS and existing PR121 export receipt hashes:

```powershell
python analysis/therapeutic_perturbation_etl/scripts/gse301119_matched_nt_null_v1.py `
  --neutral-dir "D:/jepa_perturb_outputs_20260923/gse301119_neutral_export_v1" `
  --out-dir "D:/jepa_perturb_outputs_20260923/gse301119_matched_nt_null_v1" `
  --draws 64 --max-cell-ratio 1.5
```

The neutral directory is an **illustrative path only**: point `--neutral-dir` to the *actual* location containing `NEUTRAL_EXPORT_RECEIPT_V1.json`. This script checks SHA binding to the signed source RDS via the earlier exporter receipt but does **not** re-open the original RDS or independently establish that the exporter's metadata CSV matches RDS contents. That upstream boundary remains subject to independent RDS/export review. Do not regenerate the 4.45 GB assets or re-stream GSE178317.

The CPU test suite uses planted synthetic count matrices only; passing it does not establish that a real matched NT null is estimable or that its biological conclusions are sound.
