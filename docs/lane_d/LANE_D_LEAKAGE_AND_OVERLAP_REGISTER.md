# Lane D - leakage and overlap register (GSE174367 / Stage75F)

`TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED ·
D_SHARED_G5=UNOPENED · RARE_TAIL_MOLECULAR=UNOPENED · THERAPEUTIC_RANKING=OFF`

Status: **RECONNAISSANCE. Every biological evaluation below is `NOT_EXECUTED`.**

This register names, one by one, every place where the same measurement could
appear on both sides of a comparison. A register entry is not an accusation of
a mistake that was made; it is a boundary that must hold in any evaluation
built on this data.

---

## 0. The one-sentence version

The GSE174367 **ATAC fragment counts** have never entered JEPA training or any
Stage75F statistic, so they can serve as an independent outcome; the Stage75F
**TF-target hypotheses cannot**, because they were computed from the GSE174367
RNA that would also supply the predictor.

---

## 1. Pre-existing governance record (recovered, not re-derived)

GSE174367's status was already adjudicated. These entries are cited, not
recomputed.

| Record | Finding |
|---|---|
| `results/v4/stage81a1_dataset_role_registry.csv` | `primary_role = context_only`; `clean_validation_status = "cannot be clean validation"`; `recommended_use = "Already used for Stage72/75 coactivity and chromatin support"`. `pretraining_use`, `feature_selection_use`, `architecture_choice_use`, `threshold_setting_use`, `candidate_filtering_use` are all **False**. |
| `results/tables/stage32c_holdout_protection_audit_v1.csv` | `registry_role = already_used_plausibility_only`; `normalized_role = excluded_plausibility_only`; `included = False`; `protection_pass = True`. |
| `results/tables/stage37b_rev1_dataset_claim_level_matrix_v1.csv` | `known_disqualified_from_clean_validation = True`; missing evidence recorded as *"local v2 artifacts visible; independence from candidate/model decisions not proven"*; `disallowed_use_now` includes clean validation before a contamination check. |

**Consequence.** GSE174367 is not, and cannot be made into, a clean external
validation set for anything its RNA already touched. It can host an
*independent-modality* test, which is a different and narrower claim.

---

## 2. Donor and sample overlap

| Axis | Finding |
|---|---|
| GSE174367 donors in the FULL104 foundation corpus | **0.** `results/v4/stage81a2_global_donor_registry.csv` contains 385 unique persons across 12 studies; `study_id == "GSE174367"` matches **0 rows**. The foundation scope is SEA-AD + HVS + NPH52 only. |
| Brain banks | GSE174367 is the UCI cohort (Morabito et al.); FULL104 draws on SEA-AD, HVS and NPH52. Different banks. |
| Residual risk | De-identified donor IDs share no namespace across cohorts, so donor disjointness **cannot be proven from identifiers**. It is inferred from non-overlapping study provenance. Recorded as a bounded statement, not a proof. |

### Within GSE174367

* processed snRNA: **18** samples, 61,472 cells, **4,126** microglia
* processed snATAC: **20** samples, 130,418 cells, **12,232** microglia
* shared donors: **18** (every RNA sample has an ATAC counterpart)
* ATAC-only: **Sample-40**, **Sample-101**
* donor covariates (Age, Sex, PMI, Tangle.Stage, Plaque.Stage, Diagnosis, RIN)
  agree on **0 mismatches across all 18 shared samples**, confirming `SampleID`
  is a donor-level key shared across assays.

### There is no cell-level pairing - and this must not be invented

The two assays are **separate nuclei from the same brains**, not a paired
multiome assay.

* The GEO deposit declares separate `RNA-Seq` and `ATAC-seq` library
  strategies, each from an independent "unbiased total nuclei isolation".
  No 10x Multiome library and no cell-correspondence table is deposited.
* Barcode arithmetic confirms it. 16-mer overlap between the two assays is
  **190** sequences, against **9,893** expected if both drew from one shared
  737,280-barcode whitelist - **1.9%** of the null. They draw from largely
  disjoint whitelists.
* The 7 raw barcode strings that do match are spurious: the GEM-group integer
  suffix is assay-local, and in **17 of 18** shared suffix values the same
  integer denotes a *different* sample in RNA than in ATAC.

> **Boundary.** Any RNA-ATAC join in this dataset is legitimate only at the
> donor/sample level (n = 18), never at the cell level. A cell-level pairing
> would be fabricated.

---

## 3. Circularity register

### C1 - Stage75F TF-target edges are RNA co-expression (SEVERE)

All 278 candidate edges in `results/tables/stage75f_candidate_tf_target_edges_v1.csv`
carry `edge_type = microglia_snrna_sample_coactivity` and `n_samples = 18`.
They are Spearman correlations of **sample-level microglial snRNA pseudobulk**
across the **same 18 GSE174367 RNA samples**, with bootstrap sign stability
(200 iterations, seed 7202, `min_abs_spearman = 0.20`).

* **Where circularity bites.** If a JEPA state built from RNA is scored for its
  ability to predict a Stage75F TF-target edge, both sides derive from the same
  transcript counts. The comparison measures re-description, not validation.
* **Permitted use.** Stage75F edges may serve as a **frozen predictor set** or
  an **annotation panel** fixed before the outcome is opened.
* **Forbidden use.** They must never be described as independent ground truth,
  a validated regulatory network, or a measured outcome.

### C2 - The screened region set is RNA-conditioned (MODERATE)

The 91 peaks sent to motif screening were chosen by TSS proximity to target
genes that were themselves selected by RNA coactivity. The screened region set
is therefore a function of the RNA.

* Screening covered **91 of 219,070 peaks = 0.0415%** of the peak universe.
* **Consequence.** Any enrichment computed over those 286 SCREEN regions is
  conditional on an RNA-driven selection and cannot be read as a genome-wide
  chromatin result.

### C3 - Stage75F peak-gene links are proximity, not measurement (MODERATE)

Stage75C assigns every peak exactly one nearest gene. That table has zero
unmapped rows *by construction*, which is a property of the method, not a
property of the data. The true relation is many-to-many.

* **Forbidden use.** Treating the nearest gene as the regulated target.
  All distal assignments stay `PROVISIONAL`.

### C4 - Stage73 graph priors already failed their own shuffled control (SEVERE)

The Stage72B context graph - built from the same GSE174367 RNA coactivity -
was evaluated in Stage73 against no-graph, STRING and shuffled controls. A
mode-label bug made the "shuffled" controls **bit-identical** to the real
graph (bootstrap deltas exactly 0 with zero-width CIs over 1,000 iterations).
Stage73R fixed the controls, verified them structurally distinct, and the real
graph then **lost to its own target-shuffled control**
(context 0.32361 vs target-shuffled 0.33229;
`beats_target_shuffled_mean = False`; `context_graph_prediction_lock = False`).

* **Consequence.** This graph family has already been measured and does not
  carry topology-specific value. Reusing it as a prior without re-passing
  shuffled-graph controls would repeat a known-failed claim.

---

## 4. Independence register - what *is* clean

### I1 - ATAC fragment counts (STRONG, and unused)

The microglial ATAC matrix
`data/processed/stage75f/gse174367_mg_snatac.csc.h5`
(219,070 peaks x 12,232 nuclei, 17,891,090 stored nonzeros) exists on disk and
**no Stage75F script reads it**. Region selection ranked peaks by TSS
proximity, and the batch BED files were written with `score = 0` hardcoded.
Accessibility magnitude, per-cell accessibility, differential accessibility and
peak-gene accessibility correlation are all **absent from every Stage75F
artifact**.

* **This is the crux for item 6.** A per-peak or per-donor accessibility
  quantity derived from these fragments uses **no RNA value of any kind** and
  is therefore available as an independent outcome.

### I2 - Motif database (STRONG)

cisTarget hg38 SCREEN `mc_v10_clust` region-based database - 1,837,304 regions,
5,876 motifs per batch. Vendor SHA-1 verified for both files. Carries no
GSE174367 information.

### I3 - Genome annotation (STRONG)

GENCODE v44 / hg38. External reference; carries no GSE174367 information.

### I4 - The two ATAC-only donors (WEAK but real)

`Sample-40` and `Sample-101` have ATAC and no processed RNA. Any statistic
restricted to them is RNA-free at the donor level. n = 2 is far too small to
carry a result on its own, but they are a useful negative-control stratum.

---

## 5. Gene-vocabulary overlap - overlap, not leakage

GSE174367 shares **38,838 of 41,238** FULL104 molecular addresses (94.18%).
This is vocabulary overlap and is *expected and required* for any cross-dataset
evaluation. It is recorded here so it is not mistaken for contamination: shared
gene identity is not shared measurement.

The leakage risk in this project runs through **donors, target selection and
outcome construction**, not through the gene axis.

---

## 6. The standing rule this register enforces

> A Stage75F hypothesis may be used as a **frozen predictor** or an
> **annotation panel**. It may never be used as **independent ground truth**
> for any comparison whose other side derives from the same GSE174367 RNA
> measurements. Wherever both sides trace to that RNA, the comparison is
> circular and must be labelled as such in the result, not only in the method.

Three claim levels stay distinct and are never merged:

1. **external observational validation** - the pattern recurs in an independent
   cohort;
2. **regulatory association** - accessibility and expression covary;
3. **causal validation** - perturbing the regulator changes the target.

Stage75F reaches none of these. It is *"model-based, enhancer-informed
perturbation hypotheses requiring experimental validation"* - 10 regulators,
96 TF-target rows, 3 negative-gate regulators - and its own frozen manifest
sets `validated_regulation`, `validated_grn_claim`, `causal_validation_pass`
and `therapeutic_target_claim` all to **false**.
