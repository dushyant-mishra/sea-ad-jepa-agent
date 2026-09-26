# Lane D - GSE174367 RNA/ATAC benchmark-readiness package

`TRAINING=OFF · AUDIT_B_N1=UNOPENED · PROTECTED_FULL104_OUTCOMES=UNOPENED ·
D_SHARED_G5=UNOPENED · RARE_TAIL_MOLECULAR=UNOPENED · THERAPEUTIC_RANKING=OFF`

> **Provenance.** What was verified by direct execution in this session, what was read from the historical record, and what is explicitly unverified are separated in [`LANE_D_VERIFICATION_RECEIPT.md`](LANE_D_VERIFICATION_RECEIPT.md). Read it before citing any number here.

**Execution class: RECONNAISSANCE. Every biological evaluation in this package
is `NOT_EXECUTED`.** Nothing here is a scientific result about Alzheimer's
disease, about regulation, or about any gene. It is an audit of what data and
what evidence exist, and of what an honest test could be built on them.

---

## 1. The verdict first

**This is good news, with one boundary that has to be respected.**

Everything on disk is authentic, every historical number checks out, and there
is a genuinely independent chromatin measurement sitting unused that can
support a real test. The boundary is that the Stage75F regulator hypotheses
cannot be that test's answer key, because they were built from the same RNA
that would build the predictor.

| Question | Answer |
|---|---|
| Are the files real and unaltered? | **Yes.** All 10 physical assets authenticate. Zero downloads required. |
| Did we recover the Stage75F freeze? | **Yes.** All 7 source tables match by digest, row count and column schema; the 10 / 96 / 3 frozen outputs are intact. |
| Do the historical counts hold? | **Yes.** All 10 recorded inventory figures reproduce exactly, including 4,126 / 18 and 12,232 / 20. |
| Is there independent chromatin signal? | **Yes** - and it has never been used. |
| Can Stage75F serve as ground truth? | **No.** It is RNA-derived; using it against an RNA-derived predictor is circular. |

---

## 2. Physical asset authentication

All ten assets are present. **No download is required.**
Source: `results/lane_d/laneD_physical_asset_inventory_v1.csv`,
`results/lane_d/laneD_environment_and_asset_manifest_v1.json`.

| Asset | Bytes | Digest | Status |
|---|---:|---|---|
| `GSE174367_snRNA-seq_filtered_feature_bc_matrix.h5` | 273,975,534 | sha256 `6ba98a1a…69b77` | **AUTHENTICATED** (2 independent records) |
| `GSE174367_snRNA-seq_cell_meta.csv.gz` | 435,170 | sha256 `ab1a029d…cdb2b` | **AUTHENTICATED** (2 records) |
| `GSE174367_snATAC-seq_filtered_peak_bc_matrix.h5` | 360,317,403 | sha256 `ff7c46e7…ab87f` | **AUTHENTICATED** |
| `GSE174367_snATAC-seq_cell_meta.csv.gz` | 1,066,930 | sha256 `0657e92a…c81767` | **AUTHENTICATED** |
| `GSE174367_series_matrix.txt.gz` | 13,280 | sha256 `e36488f4…15928` | **AUTHENTICATED** |
| `gencode.v44.annotation.gtf.gz` | 49,721,965 | sha256 established here | present, no vendor digest published |
| `hg38.chrom.sizes` | 11,672 | sha256 established here | present, no vendor digest published |
| cisTarget `…rankings.feather` | 35,192,958,114 | sha1 `1688a925…b4924` | **AUTHENTICATED against vendor manifest** |
| cisTarget `…scores.feather` | 13,882,267,682 | sha1 `07b5e527…6129c` | **AUTHENTICATED against vendor manifest** |
| `motifs-v10nr_clust-nr.hgnc-m0.001-o0.0.tbl` | 98,718,421 | sha256 established here | present, no vendor digest published |

Total 49.86 GB on disk. A duplicate-copy scan over `data/` and `outputs/` ran
**before** any acquisition was proposed, so the plan asks for nothing already
present. The acquisition plan is empty.

> **Correction worth recording.** An earlier pass of this lane reported the two
> snATAC files as having no recorded digest. That was wrong. Their SHA-256
> values were recorded in `results/tables/stage72a_resource_inventory_v1.csv`
> all along. The lesson is the project's own standing rule: search the
> historical index before concluding that a record is absent.

### Recorded inventory figures - all reproduce

`results/lane_d/laneD_recorded_shape_checks_v1.csv`

| Quantity | Recorded | Observed |
|---|---:|---:|
| snRNA features / barcodes | 58,721 / 61,770 | **58,721 / 61,770** |
| snATAC peaks / barcodes | 219,070 / 143,401 | **219,070 / 143,401** |
| RNA microglia cells / samples | 4,126 / 18 | **4,126 / 18** |
| ATAC microglia cells / samples | 12,232 / 20 | **12,232 / 20** |
| RNA / ATAC metadata rows | 61,472 / 130,418 | **61,472 / 130,418** |

Two gaps worth carrying: **298** snRNA barcodes and **12,983** snATAC barcodes
in the matrices have no metadata row. Neither affects the microglial subsets,
where every barcode matched.

### Environment

Stage75F executed inside a Docker container `scenicplus:1.0a2-container.1`
under WSL2. The container Dockerfile, 16 Stage75F scripts and 11 WSL entrypoint
shell scripts were recovered and digested into
`laneD_environment_and_asset_manifest_v1.json`. The Lane D audit runtime
(Python 3.9 / numpy 1.24.2 / pandas 1.5.3 / h5py 3.2.1) is recorded separately
and is explicitly **not** the Stage75F execution runtime.

---

## 3. Stage75F recovery - and what it is not

**Recovered and fully authenticated.** Manifest
`results/reports/stage75_integrated_evidence_manifest_v1.json`, git commit
`67e47a6b63f652336cb8040b650b76ac30e0c40e`.

* **7 / 7** source tables match on SHA-256, row count **and** column schema.
* Frozen outputs intact: **10** regulators, **96** TF-target rows, **3**
  negative-gate regulators. Their digests are established in
  `laneD_stage75f_authentication_v1.csv` (the manifest recorded row counts but
  not digests).
* Tiers: **A** (direct motif support) STAT1, ELF1, SPI1; **B** (extended-only)
  IRF8, BACH1, CEBPA, RELA; **C** (no TF-annotated enriched motif) MITF, NRF1,
  STAT3.
* Frozen thresholds: overlap 0.4, AUC 0.005, NES 3.0, recovery rank fraction
  0.05, 5,876 motifs per batch, 1,837,304 database regions.

**What it is:** a compact, motif-screened TF-target evidence package -
10 regulators, 96 rows - over 0.0415% of the peak universe.

**What it is not:** a validated regulatory network, a complete SCENIC+ eRegulon
model, causal evidence, or a therapeutic ranking. Its own manifest sets
`validated_regulation`, `validated_grn_claim`, `causal_validation_pass` and
`therapeutic_target_claim` all to **false**, with the approved wording
*"model-based, enhancer-informed perturbation hypotheses requiring experimental
validation."*

---

## 4. Donor and sample overlap

`results/lane_d/laneD_sample_donor_overlap_v1.csv`

* processed snRNA **18 samples** / 61,472 cells / **4,126 microglia**
* processed snATAC **20 samples** / 130,418 cells / **12,232 microglia**
* **18 shared donors**; ATAC-only: **Sample-40**, **Sample-101**; RNA-only: none
* donor covariates agree with **0 mismatches** across all 7 covariates and all
  18 shared samples, so `SampleID` is a genuine donor-level key
* GEO declares 19 snRNA samples; Sample-101's snRNA did not survive processing
* **FULL104 overlap: zero donors.** `stage81a2_global_donor_registry.csv` holds
  385 persons across 12 studies and matches GSE174367 on **0 rows**; the
  foundation corpus is SEA-AD + HVS + NPH52. Different brain banks. Since
  de-identified IDs share no namespace across cohorts, disjointness is inferred
  from provenance, not proven from identifiers - stated as a bound, not a proof.

### No cell-level pairing - and none may be invented

RNA and ATAC are **separate nuclei from the same brains**.

* 16-mer barcode overlap is **190**, against **9,893** expected under one
  shared 737,280-barcode whitelist - **1.9%** of the null. Disjoint whitelists.
* The 7 exact barcode-string matches are spurious: in **17 of 18** shared GEM
  suffixes, the same integer names a *different* sample in each assay.
* The deposit declares separate RNA-Seq and ATAC-seq libraries from independent
  nuclei isolations. No multiome, no correspondence table.

---

## 5. Gene overlap with the FULL104 registry

`results/lane_d/laneD_gene_collision_register_v1.csv`, feature map referenced
by receipt.

Against the FULL104 authoritative address registry
(`stage81a2r_foundation_molecular_address_registry_candidate.csv`, **41,238**
addresses):

| Quantity | Count |
|---|---:|
| GSE174367 features | 58,721 (all versioned Ensembl, GRCh38.p12 pre-mRNA) |
| current Ensembl exact match | 38,489 |
| legacy Ensembl match | 381 |
| symbol-only, ambiguous, **not joinable** | 636 |
| no FULL104 address | 19,215 |
| **FULL104 addresses covered** | **38,838 / 41,238 = 94.18%** |
| FULL104 addresses **not** covered | 2,400 |

### Unresolved collisions - 294, reported not deduplicated

| Class | Count | Why it is left unresolved |
|---|---:|---|
| duplicate unversioned Ensembl id | 45 | all PAR_Y pairs |
| PAR_Y X/Y locus collision onto one address | 45 | X and Y pseudoautosomal copies are distinct physical loci; collapsing sums two chromosomes |
| symbol maps to multiple Ensembl ids | 172 | symbol is not a usable join key |
| many features to one FULL104 address | 32 | needs an explicit declared aggregation rule |

**Structural missingness.** The 2,400 absent addresses and 19,215 unmatched
features are an annotation-vocabulary difference (GRCh38.p12 CellRanger
pre-mRNA vs the Stage81A2R identity layer), **not** biological absence. Any
evaluation must mask them, never impute zero. Cross-version liftover:
`NOT_EXECUTED`.

---

## 6. Coordinate map and peak-to-gene over the full 219,070-peak universe

`results/lane_d/laneD_coordinate_map_audit_v1.json`,
`results/lane_d/laneD_peak_to_gene_manifest_v1.json`

**Conventions verified.** Declared genome `GRCh38`; UCSC `chr`-prefixed naming;
24 contigs (chr1-22, X, Y); **no alt scaffolds, no chrM**; peak ids
`chrN:start-end`; CellRanger-ATAC BED-like 0-based half-open start, reconciled
against the 1-based GENCODE GTF by `col4 - 1`. TSS is the gene-level,
strand-aware boundary. Annotation GENCODE v44 (62,700 genes, 20,046
protein-coding). Peak widths 1 bp to 55,680 bp, median 525; **14,590 peaks are
under 50 bp** and 445 exceed 10 kb.

**hg38 build check: `hg38_CONSISTENT`.** Zero peaks on unknown contigs, zero
ends beyond a contig length, zero negative starts; the largest end reaches
99.99% of its contig. This is a necessary, not sufficient, test - it rules out
hg19/T2T coordinates but does not prove per-peak build identity.

### Mapping counts

| Quantity | Count |
|---|---:|
| peaks total | 219,070 |
| peaks with a TSS within 2 kb (promoter) | 27,133 |
| peaks with a TSS within 100 kb | 199,488 |
| **peaks with no TSS within 100 kb (unassignable)** | **19,582** |
| peaks detected in ≥1 microglial nucleus | 210,137 |
| **peaks never detected in microglia** | **8,933** |

### Ambiguity - which a one-nearest-gene table structurally cannot record

| Quantity | Count |
|---|---:|
| peaks with a **tied** nearest TSS | 210 (max multiplicity 2) |
| peaks with ≥2 TSS inside the 2 kb promoter window | 6,099 |
| peaks with ≥2 TSS inside 100 kb | 169,076 |
| median candidate genes within 100 kb | 3 |
| max candidate genes within 100 kb | 90 |

Stage75C's frozen table has **zero** unmapped rows - but that is a property of
its method, not of the data: it assigns every peak exactly one nearest gene.
The true relation is many-to-many.

### cisTarget region mapping

| Quantity | Value |
|---|---:|
| overlap rule | query-fraction **or** database-fraction > 0.4 |
| unique query peaks | 91 |
| **mapped** | 86 |
| **never mapped** | **5** |
| exact coordinate matches | **0** |
| query rows / mapped / unmapped | 779 / 735 / 44 |
| unique SCREEN regions screened | 286 |
| median SCREEN regions per query peak | 2 (max 24) |
| **share of the peak universe screened** | **0.0415%** |

The five permanently unmapped peaks: `chr1:145991849-145992224`,
`chr5:150419807-150419967`, `chr5:55772581-55774021`,
`chr8:16509725-16510108`, `chrX:120452093-120452804`.

Median query-overlap fraction is 0.107 while median database-overlap fraction
is 1.000: GSE174367 peaks are much wider than SCREEN regions, so the
database-side arm of the OR rule carries nearly every mapping. Motif evidence
attributed to a peak is evidence about a *set of overlapping SCREEN regions*,
not about that peak's own interval.

### The five evidence classes, kept apart

| Class | Peaks | Status |
|---|---:|---|
| DIRECT ATAC accessibility at a promoter | 26,615 | measured |
| promoter overlap, not detected in microglia | 518 | measured absence |
| genomic proximity (provisional) | 165,095 | **PROVISIONAL** |
| genomic proximity, not detected in microglia | 7,260 | **PROVISIONAL** |
| no gene within 100 kb | 19,582 | unassignable |
| **coaccessibility** | — | **NOT_AVAILABLE** - never computed |
| **independent enhancer-gene links** | — | **NOT_AVAILABLE** - none present |

Gene-level over 61,228 GENCODE v44 symbols: **29,670** genes have an accessible
promoter in microglia; **285** have a promoter peak not detected in microglia;
**28,436** have a distal candidate only (provisional); **2,837** have no usable
ATAC evidence.

> The nearest gene is **never** treated as the true target. Every distal
> assignment is `PROVISIONAL_DISTAL_NEAREST_GENE_IS_NOT_THE_TARGET`.

### Reproducibility controls

| Control | Result |
|---|---|
| Independent brute-force implementation, 1,500-peak sample | **1,500 / 1,500** exact agreement on distance and gene |
| Stage75C frozen table replay | TSS distance **219,070 / 219,070 = 100%**; frozen gene among tied-nearest **219,070 / 219,070 = 100%** → **REPRODUCED** |
| Controlled coordinate perturbation, +50 kb, 20,000 peaks | **99.99%** of TSS distances changed; **63.8%** of nearest genes reassigned → **POSITION_SENSITIVE_PASS** |

The perturbation control matters: a mapping that survived a 50 kb rigid shift
unchanged would not be measuring position at all. The 1,354 apparent
gene-symbol differences against Stage75C are **symbol case only** - Stage75C
stored symbols upper-cased (`C1ORF159` vs `C1orf159`). After case
normalisation the frozen mapping reproduces exactly.

---

## 7. The independence verdict

**Verdict: CONDITIONALLY INDEPENDENT. An RNA-free chromatin measurement exists
and has never been used. The Stage75F regulator hypotheses are not independent
and cannot serve as the answer key.**

### What is independent

The microglial ATAC fragment matrix
`data/processed/stage75f/gse174367_mg_snatac.csc.h5` -
219,070 peaks x 12,232 nuclei, 17,891,090 stored nonzeros - is on disk and
**no Stage75F script reads it**. Peak selection ranked by TSS proximity; batch
BED files were written with `score = 0` hardcoded. Accessibility magnitude,
per-cell accessibility, differential accessibility and peak-gene accessibility
correlation are **absent from every Stage75F artifact**. Stage75C touched only
`features/name` - the interval strings - and never the counts.

A per-peak or per-donor accessibility quantity built from these fragments uses
**no RNA value of any kind**. That is the independent outcome this benchmark
can be built on.

Also independent: the cisTarget motif database (1,837,304 regions, vendor SHA-1
verified) and the GENCODE v44 annotation.

### What is not independent

All 278 Stage72B candidate edges carry `edge_type =
microglia_snrna_sample_coactivity` and `n_samples = 18`: they are Spearman
correlations of sample-level microglial snRNA pseudobulk across the same 18
GSE174367 RNA samples. If a JEPA state encoded from that RNA is scored against
those edges, both sides trace to the same transcript counts. That measures
re-description, not validation.

The screened region set inherits the same dependence: the 91 candidate peaks
were chosen by proximity to RNA-selected target genes.

### Governance already said so

`stage81a1_dataset_role_registry.csv` records GSE174367 as `context_only` with
`clean_validation_status = "cannot be clean validation"`; `stage32c` excludes
it from holdout protection as `already_used_plausibility_only`; `stage37b_rev1`
marks `known_disqualified_from_clean_validation = True`. This lane's finding
agrees with the existing record rather than competing with it.

---

## 8. The Stage73 lesson, stated as a requirement

The brief for this lane described the Stage73 mistake as "accepting a graph
because it beat a no-graph baseline." **The record shows something worse, and
the corrected version is what the evaluation spec now enforces.**

Stage73 *did* pre-register and run shuffled-graph controls. A **mode-label bug**
made them bit-identical to the real graph: `context_grn_aux`,
`gene_label_permuted_grn_aux` and `target_shuffled_grn_aux` agreed to every
decimal place, and the bootstrap deltas were exactly **0** with **zero-width
confidence intervals over 1,000 iterations**. A zero-width CI is only possible
if the "control" *is* the thing it controls for.

Stage73R repaired the controls, added a structural integrity audit (adjacency
SHA-256, `diff_nnz_vs_context`, `fraction_changed_edges`, weighted adjacency
correlation, `distinct_from_context`), proved the controls distinct - and the
real graph then **lost to its own target-shuffled control** (context 0.32361 vs
target-shuffled 0.33229; `beats_target_shuffled_mean = False`;
`context_graph_prediction_lock = False`).

**Therefore the requirement is stronger than "run shuffled controls":**

> Every negative control must pass a **structural distinctness gate** before
> any of its scores are interpreted, and that gate must itself be tested
> against degenerate inputs - including a control identical to the real
> structure by construction, which must **fail**. Beating a no-graph or
> no-prior baseline is never sufficient for a structure-specific claim.

This is written into `configs/lane_d/lane_d_atac_independence_evaluation_spec_v1.yaml`
as blocking gate `A3`.

---

## 9. Evaluation specification - designed, NOT executed

`configs/lane_d/lane_d_atac_independence_evaluation_spec_v1.yaml`

**Question.** Do frozen JEPA states, encoded from GSE174367 microglial snRNA,
explain independently measured microglial chromatin accessibility in the same
donors beyond cell-type composition, technical covariates, and a linear readout
of the same RNA?

* **Unit of inference: 18 donors.** The 12,232 microglial nuclei sharpen the
  measurement of each donor's state; they do not increase the independent n.
* **Outcome:** donor-level microglial accessibility from ATAC only, depth-
  adjusted.
* **Predictor:** frozen JEPA state, no refitting.
* **Baselines:** B0 intercept; B1 cell-type + technical; **B2 = B1 + linear PCs
  of the same RNA**; B3 = B1 + JEPA state. **B2 is the real bar** - beating B0
  or B1 only shows that RNA carries chromatin information, which is already
  known.
* **Scheme:** leave-one-donor-out over 18 folds, all preprocessing fit inside
  the training fold, common random numbers across every condition, bounded
  primary metric (out-of-fold Spearman), paired BCa bootstrap.
* **Negative controls:** shuffled TF labels (permuted within motif tier),
  shuffled region-gene links (permuted within chromosome x peak class),
  shuffled donor associations (permuted within diagnosis x sex), matched random
  feature sets (matched on chromosome, width decile, detection-fraction
  decile), and shuffled graph priors - each behind the blocking structural
  distinctness gate.
* **Acceptance frozen before execution**, including a power statement for
  n = 18. If only a large effect is detectable, that is the finding and is
  reported as a bound.

**Six prerequisite gates; five are `NOT_SATISFIED`.** Until they pass, every
biological result remains `NOT_EXECUTED`.

---

## 10. Artifacts

Compact manifests and registers are committed under `results/lane_d/`. Five
heavy tables are referenced by absolute path, byte size and SHA-256 in
`results/lane_d/laneD_artifact_receipts_v1.csv` rather than duplicated into
git, in line with the project's large-artifact rule.

| Artifact | Contents |
|---|---|
| `laneD_physical_asset_inventory_v1.csv` | 10 assets, digests, authenticity, actions |
| `laneD_environment_and_asset_manifest_v1.json` | container, scripts, runtime, acquisition plan |
| `laneD_file_authentication_v1.csv` | the five GSE174367 files against frozen digests |
| `laneD_recorded_shape_checks_v1.csv` | 10 historical figures vs observed |
| `laneD_stage75f_authentication_v1.csv` | 7 source tables + 3 frozen outputs + manifest |
| `laneD_sample_donor_overlap_v1.csv` | 20 samples, per-modality cells and microglia |
| `laneD_gene_collision_register_v1.csv` | 294 unresolved identity collisions |
| `laneD_provenance_manifest_v1.json` | authentication, overlap, gene, peak summary |
| `laneD_coordinate_map_audit_v1.json` | hg38 check, ambiguity, cisTarget mapping |
| `laneD_peak_to_gene_manifest_v1.json` | full-universe mapping, evidence ladder, controls |
| `laneD_artifact_receipts_v1.csv` | every artifact by path + size + SHA-256 |
| `docs/lane_d/LANE_D_LEAKAGE_AND_OVERLAP_REGISTER.md` | circularity and independence register |
| `configs/lane_d/lane_d_atac_independence_evaluation_spec_v1.yaml` | the test, not run |
| `docs/lane_d/LANE_D_VERIFICATION_RECEIPT.md` | what was verified, how, and what was not |

---

## 11. What would have to be true before anything is claimed

1. Identify and digest the frozen JEPA encoder checkpoint.
2. Freeze the GSE174367 → FULL104 projection rule, including masking for the
   2,400 absent addresses and an aggregation rule for each of the 294 collision
   classes.
3. Freeze the donor-level ATAC outcome definition and replay it from disk.
4. Implement the structural distinctness gate and test it on degenerate inputs.
5. Freeze acceptance thresholds and the n = 18 power statement before the
   outcome is opened.

Only then does any number in this package become a scientific result, and even
then the claim available is **regulatory association in an independently
measured modality** - never causal validation, never a validated network.
