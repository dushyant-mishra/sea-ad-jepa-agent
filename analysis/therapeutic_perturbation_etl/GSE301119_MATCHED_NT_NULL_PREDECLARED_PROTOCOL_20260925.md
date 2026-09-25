# GSE301119 matched non-targeting control null — predeclared scientific protocol

**2026-09-25; DEVELOPMENT ONLY.** This branch is based on PR121 `aaf561cfdc60ffe29c4d79094c16ce5e524f7d2d`, not main. The historical PR121 producer, full-data results, and protected stores remain unchanged. No N1, FULL104 protected results, model training or therapeutic prioritization.

## Scientific question

Does the existing GSE301119 estimator — log2(CPM+1) target minus donor-matched pooled NT — generate large, recurrent apparent effects even when its "target" is a pseudo-target made entirely of non-targeting (NT) guides?

Opus's reported 18–22× NT/pseudobulk depth imbalance, near-monotonic association of top-effect magnitude with unit size, and recurrent downregulated CLU/CCL22/MMP12/CXCL10/CXCL11/MT1H/MT1G are **hypotheses and preliminary metadata/top-50 observations**. Their measured numerical values are not independently established by this protocol. The PR121 Python reproducer's own hand-computed fixture has a truly unchanged raw-count gene `gFLAT` whose normalized estimate is approximately -0.807. This is genuine evidence that normalization can create a nonzero effect under altered composition; it does NOT establish prevalence or cause of full-data effects.

## Frozen computational experiment

Two null mechanisms are deliberately separated rather than conflated: **cell-sampling/composition** and **read-depth-only**.

- Inputs: the *existing* authenticated PR121 neutral export for CRISPRi and CRISPRa: four required files per modality (`{mod}_counts_int32.bin`, `{mod}_shape.txt`, `{mod}_features.txt`, `{mod}_gd_meta.csv`), plus `NEUTRAL_EXPORT_RECEIPT_V1.json`. The script rejects count-bin and original RDS hashes inconsistent with the committed PR121 donor-aware receipt. Source RDS hashes: CRISPRi `e796504f41ddd65f3a5b72699d12431ce664974e0860ecb255858bd084283549`; CRISPRa `9fe028f508ce33a8c968ab05c363c345135b0b6227db4476838c70fb9d874d90`.
- Unit: each donor×target pooled across its authentic targeting guides. Only target units with >=10 cells enter a null; true independent biological units remain **two donors**. CRISPRi and CRISPRa remain separate feature universes and estimands.
- For each target unit, select donor-matched NT guide groups with **exactly the same guide count**, and total cell count within a prospective ratio of **1.5** in either direction. Select on guide and cell counts only, never sequencing depth, expression profile, or apparent effect. Random seed **301119**, 64 draws per unit, 256 cell-matching trial combinations per draw.
- **Cell-sampling arm:** for each selected NT pseudo-target, exclude *all* its selected guides from its own NT denominator, then compute **the identical legacy log2(CPM+1)** contrast as the original producer. Distinct selected guide sets only: duplicated Monte Carlo selections are not counted as additional evidence.
- **Depth-only arm:** retain the full donor NT pool as the biological composition, then independently binomial-thin each gene's pooled NT count with probability `p = target_unit_raw_depth / full_NT_raw_depth`. This changes read sampling/depth while preserving the full NT aggregate composition in expectation and does **not** remove cells/guides. Compare each thinned profile back to the unthinned full NT using the identical legacy estimator. If target depth is not lower than NT depth, mark this arm not estimable; never upsample.
- Failure is explicit: if fewer than 32 usable unique matches remain, mark that donor×target `NOT_ESTIMABLE_INSUFFICIENT_MATCHED_NT_NULL`. Record match count and real/pseudo group cell-count bounds. No cherry-picking after observing expression.
- Output per donor×target: actual effects; separate cell-sampling and depth-only sentinel nulls; empirical 2.5/97.5% quantiles and absolute exceedance fractions for each arm; recurrence among strongest 25 up and 25 down genes for each arm; median maximum absolute effect per arm; target/control RNA depth ratio. Calculate a *separate exploratory* positive-gene median-centred log-ratio sensitivity; missing zeros remain NaN, not zero.
- Deliver the single small versioned JSON receipt; it contains no high-dimensional count data and no new protected outcome. Repeat resamples overlap and are **not independent n=64 experiments**, independent donor observations, formal hypothesis-test p-values, or evidence of population transport.

## Falsifiable interpretation fixed before reading the full receipt

Interpret the two arms jointly:
- If the **cell-sampling arm** generates the recurrent negative sentinel/extreme-gene pattern but the **depth-only arm does not**, the leading mechanism is under-sampling of heterogeneous NT cell states rather than read-depth stochasticity alone.
- If **both arms** reproduce the pattern, low read depth / pseudocount / count-sampling effects are sufficient to explain an important component.
- If **neither arm** reproduces the pattern, these two null mechanisms are not sufficient; that still does not prove biological causality.

If either null regularly generates effects comparable to the actual top-effect lists, the affected GSE301119 transcriptome-wide outputs **cannot be used as interpretable target-specific molecular-response labels** without a redefined estimand and new validation. Directional on-target engagement remains a separate quantity.

If the NT null is well behaved but true-target effects remain extreme, **do not declare the effects causal**: guide-specific toxicity/selection, targeting-induced shifts in cell-state composition, genuine perturbation, and library-size differences can still coexist. Qualify measured cell-state balance, compositional sensitivity, donor consistency, and guide-level reproducibility before claiming a biological response. Two donors never justify population-level uncertainty.

A median-centred normalization that attenuates apparent effects is a sensitivity result, not ground truth; it assumes most positively detected genes are unchanged and cannot fix true zero/detection differences. A nonzero cell-sampling null can arise from differences among NT guides, heterogeneous cell-state composition, and measurement stochasticity. A nonzero depth-only null can arise from binomial read sampling, zeros, and pseudocount behavior. Neither arm is a biological replicate; record its scope without assuming the entire targeting signal is false.

**Never tune pseudocount, cell-matching tolerance, tail cutoffs, or sentinel selection after examining the null receipt and call that a predeclared result.** A future alternative-normalization full-matrix analysis must be separately versioned.

## Mandatory source-backed neutral-export identity certification

Independent CPU review found that the historical V1 neutral export receipt authenticated
the count binary and original RDS SHA, **but not the gene feature file or guide/donor
metadata bytes**. A donor swap or feature-name permutation could therefore pass
count-only integrity checks and change the biological comparison. This is a physical
input-integrity blocker, separate from the scientific CPM-estimand uncertainty.

Before executing the first physical null, run
`scripts/r/certify_gse301119_neutral_identity_v2.R` against the original
SHA-pinned CRISPRi and CRISPRa guide-donor raw-pseudobulk RDS objects.
It reserializes and **byte-compares all four neutral files per modality**
(count binary, shape, features, guide/donor metadata CSV) from the original
RDS rather than merely hashing untrusted neutral sidecars. A different
R/environment CSV encoding may require resolving the byte-level disagreement
before publication; NEVER silently skip the metadata check.

The certifier publishes only a new small
`NEUTRAL_EXPORT_IDENTITY_CERTIFICATION_V2.json` in a fresh output directory.
The Python null rejects absent, malformed, mismatched, or wrong-source
certification and pins its own copy of the certificate by SHA-256. This
attestation is a source-identity check, **not independent biological replication
or proof that the chosen CPM estimand is scientifically correct**.

## GPU laptop invocation

From the PR121-descendant branch, after verifying the source RDS and existing
PR121 export receipt hashes, first certify the EXISTING export against the original
RDS (illustrative physical paths; replace with verified local paths):

```powershell
Rscript analysis/therapeutic_perturbation_etl/scripts/r/certify_gse301119_neutral_identity_v2.R \`
  --pseudobulk-dir "D:/jepa_perturb_outputs_20260923/gse301119_rawpb_v1" \`
  --neutral-dir "D:/jepa_perturb_outputs_20260923/gse301119_neutral_export_v1" \`
  --out-dir "D:/jepa_perturb_outputs_20260923/gse301119_neutral_identity_cert_v2" \`
  --rlib "D:/jepa_rlib46"

python analysis/therapeutic_perturbation_etl/scripts/gse301119_matched_nt_null_v1.py `
  --neutral-dir "D:/jepa_perturb_outputs_20260923/gse301119_neutral_export_v1" `
  --out-dir "D:/jepa_perturb_outputs_20260923/gse301119_matched_nt_null_v1" `
  --draws 64 --max-cell-ratio 1.5
```

The neutral directory is an **illustrative path only**: point `--neutral-dir` to the *actual* location containing `NEUTRAL_EXPORT_RECEIPT_V1.json`. This script checks SHA binding to the signed source RDS via the earlier exporter receipt but does **not** re-open the original RDS or independently establish that the exporter's metadata CSV matches RDS contents. That upstream boundary remains subject to independent RDS/export review. Do not regenerate the 4.45 GB assets or re-stream GSE178317.

The CPU test suite uses planted synthetic count matrices only; passing it does not establish that a real matched NT null is estimable or that its biological conclusions are sound.
