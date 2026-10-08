# JEPA control-gene literature, historical NPH52 pilot and prospective implications

**Date:** 2026-09-27 EDT. **Scope:** CPU-based retrospective *method-development only*. Full real-data biological gate CLOSED; TRAINING=OFF; no reserved-readout numerical values accessed. No code was pushed to GitHub in this workstream.

## Relevant prior methods — what transfers and what does not

1. **Tirosh / Seurat `AddModuleScore`:** match a gene to random controls of similar average expression; Seurat's current documented default is 24 expression bins, 100 control genes per feature. This is a useful *abundance-only baseline*, **not** a false-positive guarantee for a directional cross-program test. https://satijalab.org/seurat/reference/addmodulescore
2. **scDRS (Zhang et al., Nat Genet 2022):** generate ~1,000 control gene sets matched on size, mean expression and variance; normalize scores against this empirical background. This motivates *mean+variance matching*, but the null is a different disease-association score and does **not** establish hidden-capture exchangeability for our count-based directed NB test. https://pmc.ncbi.nlm.nih.gov/articles/PMC9891382/
3. **CAMERA (Wu and Smyth, NAR 2012):** gene-set inference can be grossly anti-conservative when inter-gene correlation is ignored. This motivates matching whole four-gene covariance structures and measuring gene reuse across 199 shams; CAMERA itself does **not** calibrate our gate. https://pmc.ncbi.nlm.nih.gov/articles/PMC3458527/
4. **RUV (Risso et al., Nat Biotechnol 2014):** suitable control genes can estimate unwanted technical factors; however, the method *assumes* control genes do not respond to the biological contrast. Apply the concept to evaluate a nonreserved housekeeping **technical sensor**, not to pronounce those genes exchangeable program shams. https://pmc.ncbi.nlm.nih.gov/articles/PMC4404308/
5. **sctransform (Hafemeister & Satija, Genome Biol 2019):** regularized gene-wise NB modeling of depth; makes the case for matching variance/sampling noise and evaluating limitations of explicit library normalization. Its residuals are not a substitute for a valid joint conditional sham null. https://pmc.ncbi.nlm.nih.gov/articles/PMC6927181/
6. **muscat (Crowell et al., Nat Commun 2020):** donor/sample-level inference and pseudobulk are relevant to measuring *replicability*, not to removing single-nucleus hidden-capture bias merely by aggregation. https://pmc.ncbi.nlm.nih.gov/articles/PMC7705760/
7. **Human brain ambient RNA (2022):** neuronal transcripts can contaminate glial snRNA-seq; candidate genes enriched in neurons require a source/ambient-screen, not just an expression-bin match. https://pmc.ncbi.nlm.nih.gov/articles/PMC9789184/

## Actual local evidence, strictly bounded

- Input: SHA-256 authenticated Aug 24 historical 50k × 41,238 *normalized* discovery NPZ, known to have scrambled HVS and SEA-AD axes. **Only NPH52 operator 39** was used: **304 MG-labelled nuclei, 16 donors**. Historical NPH52 source feature axis was independently checked in the project; this does not authenticate any new full104 general reader. Sample A contains 78 of these NPH MG nuclei; sample B contains 226 and was selected for coverage, so the 304 are NOT population-representative or a new independent validation cohort.
- Reserved original six expression values were filtered at the CSR index stage **before** copying counts into analysis arrays. No reserved-readout statistic, heldout program correlation, or biological response was computed. Three program four-partner sets are predeclared, but the historical NPH52 archive has frozen HLA-DPA1 address **23673 structurally unmeasured**, while a different, `legacy_exact` HLA-DPA1 symbol is recorded at address 40452. We refused to substitute. Both APOE and P2RY12 programs were eligible for *screening only*. Do not assume this historical discrepancy affects the newer corrected 29-address artifact; resolve with the new source-authenticated decoder, not symbols.
- Expression inversion: raw UMI for nonreserved NPH52 rows was reconstructed by `round(expm1(log1p(10000 × raw / original source_library)) × original source_library / 10000)`. The original NPZ and sample freeze hashes were recomputed. Eight frozen housekeeping genes were **not available as shams**, but used here as a provisional *observed reference score*. A housekeeping score is not proven to be pure technical capture.
- Provisional candidate pool: NPH-measured, protein coding, `current_exact`, and **metadata-indicated** present in op19, op24–34 and op39; excludes all 48 frozen addresses (29 original +19 nuisance) and a limited prefix blacklist. A complete independent GO/pathway, neuronal ambient and source-native gene identity screen is still missing. Across four fitting folds, 6,686–7,042 genes survived all preliminary filters. Because HVS and SEA-AD historical axes are defective, the cross-source support filter is **metadata-only**, not a decoded-source qualification.

## Four balanced donor folds — actually executed

The four evaluation folds have **77, 78, 73 and 76 nuclei**, each from 3–5 donors; training folds contain 226–231 nuclei. Every candidate was selected exclusively using the training donors in its fold and then measured on that fold's held-out donors. The total 304 nuclei are repeatedly reused across folds: NOT 304 independent outcomes per method and not a prospective confirmatory test.

Methods: mean-only control draw, mean+variance draw, five-observable joint draw (mean, detection, Fano, depth correlation, housekeeping-sensor correlation) plus a within-quadruple covariance penalty, and three *generic biological challenger* families (proteasome, broad RNA splicing and basal transcription components). Per fold/program there were 45 candidate draws for each statistical match and 60 for each generic module; we report the best *training-fit* panel's held-out mismatch. These are fixed **heuristic development** configurations and are not tuned into gate acceptance criteria.

| Program | Control-family methodology | Median heldout absolute four-gene coherence mismatch | Median heldout housekeeping-sensor correlation mismatch | Median heldout depth correlation mismatch |
|---|---|---:|---:|---:|
| APOE | Mean only | 0.096 | 0.103 | 0.100 |
| APOE | Mean and variance | **0.053** | **0.016** | 0.130 |
| APOE | Five-observable joint | 0.079 | 0.142 | 0.097 |
| APOE | Proteasome-module challenger | 0.070 | 0.038 | 0.104 |
| APOE | Broad RNA-splicing challenger | 0.088 | 0.112 | 0.076 |
| APOE | Basal transcription challenger | 0.117 | 0.214 | 0.073 |
| P2RY12 | Mean only | 0.156 | 0.266 | 0.245 |
| P2RY12 | Mean and variance | 0.123 | 0.174 | 0.208 |
| P2RY12 | Five-observable joint | 0.194 | 0.166 | **0.044** |
| P2RY12 | Proteasome-module challenger | 0.127 | **0.151** | 0.144 |
| P2RY12 | Broad RNA-splicing challenger | 0.134 | 0.199 | 0.185 |
| P2RY12 | Basal transcription challenger | **0.066** | 0.175 | 0.095 |

**Interpretation:** scDRS-like mean/variance matching is a simple useful *baseline*, not established superior globally: in one single small split the joint method looked better, but it did not consistently generalize over the four folds. P2RY12's very abundant CX3CR1 partner makes precision matching especially hard. Basal transcription modules match some P2RY12 *coherence* but carry distinct biological signals and are **challengers, not nuisance-null shams**. Numeric closeness on the observed housekeeping sensor cannot establish matching on *latent* gene-specific capture. No result above is an NB true-negative calibration or a biological-fidelity outcome.

## Finite real-gene pool: 199 is not 199 independent null realizations

Sensitivity tiers (explicitly **NOT** formal thresholds) were applied only to FIT donors: observed per-gene mean within a factor of 1.25 (ratio range 0.8–1.25), optional detection within 0.10, optional Fano within factor 1.5, optional observed depth and housekeeping-sensor correlation within 0.15. Under this tier:

- For P2RY12's CX3CR1 partner, 57–60 *mean-only* candidates and just 13–22 candidates under all five criteria were available per training fold. For C1QA, just 4–10 survived all five. **199 globally nonoverlapping four-gene shams cannot be assembled with these constraints from the historical NPH subset.**
- For APOE's sparse APOC1 partner, only 0–52 candidates survived all five criteria, **zero in 3 of 4 fitting folds**. Low-count dispersion makes strict matching of every marginal characteristic untenable here, even before matching whole-panel correlation.
- In 40 combinatorial resampling repetitions per fold/matching tier, 199 P2RY12 shams from all-five pools shared at least one gene in **19–30%** of panel pairs; the most frequently reused gene appeared **27–56 times**. With looser mean+detect pools, sharing fell to about 2.7–2.8%. For APOE all-five matching was infeasible in 3 folds.
- An **illustrative variance-of-the-mean proxy** computed assuming each distinct gene makes an independent standardized contribution estimates only roughly 12–18 units for some 199-panel high-reuse P2RY12 constructions. **This proxy is not an effective Monte Carlo B, a validated p-value adjustment, or a biological finding; it excludes all real gene covariance.**

Thus a real-gene match must quantify overlap, correlation and joint exchangeability. The 199 sham budget is an execution target, **not evidence of 199 independent null replicates**.

## Preliminary functional annotation overturns apparently good numerical candidates

- **ITM2B/BRI2**, present in automatically selected P2RY12 panels, has a documented physical/functional interaction with microglial **TREM2**, and a disease-associated microglial response (2024): https://pmc.ncbi.nlm.nih.gov/articles/PMC10933458/ . It is **not a defensible biologically unrelated P2RY12 null** even when it passes a numerical expression-matching screen.
- **KCNQ5** appeared in one APOE joint-match example; human brain protein atlas reports neuronal cortical staining but no glial staining for its cited assay: https://www.proteinatlas.org/ENSG00000185760-KCNQ5/brain/cerebral%2Bcortex . A low KCNQ5 count in a microglial nucleus may reflect ambient RNA or low-level glial transcription; treat as **ambient risk requiring validation**, not a clean unrelated control.
- **NEXMIF**, found in other automated panels, is a neurite-extension gene with brain-biased expression: https://www.ncbi.nlm.nih.gov/gene/340533 . Review its source/cell-type distribution before any microglial sham nomination.
- Other selected lists contain CD83, NLRP1, BST2, BANK1 and FYB1. No completed GO/pathway risk screen exists here; the narrow symbol-prefix prefilter is demonstrably insufficient. The CSVs are *candidate inventories for biological curation*, **not approved sham lists**.

## Example real-gene generic challengers, *not* confirmed shams

These specific four-gene panels arose from the NPH52 fitting-donor optimization and are provided as examples for subsequent expert review, not recommendations to use as nulls: APOE proteasome **PSMD11, PSMB7, PSMD5, PSMC2**; P2RY12 basal transcription **GTF2A2, GTF2F2, GTF2B, POLR2F**. Other folds selected different genes within the same families. These modules can carry their own regulation, which is useful for a strong generic-biological comparator but disqualifies an automatic "no biology" assumption.

## Concrete handoff to Claude, without opening held-out readouts

**Do not pick an exact 199-gene null from this preliminary shortlist.** Use the larger corrected, source-decoded FULL104 fitting data to quantify the per-slot pool sizes and cross-source availability first. The historical 304-cell source is intentionally coverage-enriched and cannot establish production rarity or source transport.

Construct and keep **three separate roles**: (i) existing/nonreserved housekeeping-like and ambient genes as *technical-nuisance instruments* only, with an orthogonal check against biological-state variation; (ii) random per-partner mean+variance matched four-gene sets as the transparent baseline, with exact gene reuse/covariance report; (iii) unrelated-but-genuinely-co-regulated generic modules as *challenging biological comparators*, not automatically valid nuisance-exchangeable shams. Reserve the final biological null designation until true joint null behavior and nuisance coupling are established independently on fitting donors, including the corrected pairwise denominator and source-specific masks. Keep the six historical readout identities and their exposure firewall unchanged. If a credible real-gene sham is not available, record the count-based test as insufficiently identifiable per frozen v7; do not tune matching bands to induce a PASS.

The missing capabilities here are **full source-authenticated 41,238-address corrected counts**, multi-source fitting-donor coverage and independent hidden-capture ground truth. This report provides a reproducible feasibility study, not a resolution of those scientific questions.
