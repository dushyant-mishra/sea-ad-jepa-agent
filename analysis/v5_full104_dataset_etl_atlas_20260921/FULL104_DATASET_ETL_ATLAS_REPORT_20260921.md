# FULL104 dataset / ETL atlas — first whole-dataset pass

Date: 2026-09-21  
Status: `CURRENT_FULL104_RECONNAISSANCE__DATASET_ENGINEERING_WORKSTREAM`  
Training: `OFF`

## Principle

Pathology-blind model/evaluation does **not** mean pathology-blind dataset engineering.
We need to understand the provenance, composition, support, taxonomy and processing geometry of the data before deciding what a JEPA objective, sampler, nuisance control, masking scheme or evaluation should mean.

This pass preserves the existing terminal firewall:

- terminal masking outcomes remain unopened;
- D_shared remains sealed;
- DEV/SEALED expression remains sealed;
- no masking policy, G5 margin or training authority is selected;
- cohort/provenance metadata examined here is descriptive only and is not a model input or terminal policy-selection variable.

The uploaded calibration bundle declares `pathology_fields_included=false` and `dev_sealed_expression_included=false`, so this pass does **not** inspect hidden SEA-AD pathology values or DEV/SEALED expression.

## Authenticated inputs

The reproducible atlas script authenticates key bundle files against `BUNDLE_SHA256_MANIFEST.csv` before analysis.

Main full metadata input:

- `metadata/foundation_metadata_rows.sqlite`
- bytes: 2,709,786,624
- SHA-256: `a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913`

Molecular namespace:

- 41,238 canonical molecular addresses
- registry SHA-256: `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd`

Generated summary SHA-256:

`d0dd402ba2c03b109d04ff3e2c125d0b04c07e95c9644f2f7067da013bdd7f3d`

## Population architecture

The metadata universe contains **6,351,753 cells from 149 donor IDs**. Reader partitions are donor-disjoint.

| reader partition | source | donors | cells |
|---|---:|---:|---:|
| reader_fit | HVS | 41 | 198,718 |
| reader_fit | NPH52 | 17 | 236,476 |
| reader_fit | SEA_AD | 46 | 4,118,213 |
| reader_validation | HVS | 10 | 53,933 |
| reader_validation | SEA_AD | 12 | 893,098 |
| reader_oracle | HVS | 11 | 55,848 |
| reader_oracle | NPH52 | 2 | 28,925 |
| reader_oracle | SEA_AD | 10 | 766,542 |

The lawful reader-fit population is therefore **4,553,407 cells / 104 donors**.

### Cell mass and donor mass are very different

| source | cell fraction | donor fraction |
|---|---:|---:|
| HVS | 4.36% | 39.42% |
| NPH52 | 5.19% | 16.35% |
| SEA_AD | 90.44% | 44.23% |

A cell-uniform objective is therefore approximately a SEA-AD objective. A donor-uniform objective is not. Scientific estimand, proposal sampler and compute packing cannot be allowed to collapse into one choice.

## NPH52 is a study label, not the reader cohort

The foundation registry contains 52 NPH study participants:

- `NPH_Ctrl`: 25
- `NPH_Abeta`: 19
- `NPH_AbetaTau`: 8

But the reader expression metadata contains only **19 `NPH_Ctrl` donors**:

- 17 reader-fit
- 2 reader-oracle
- 0 reader-validation

No `NPH_Abeta` or `NPH_AbetaTau` donor appears in the reader expression population.

Therefore references to the expression source as "NPH52" must not be interpreted as coverage of the full 52-donor NPH study. For model design it is a control-subcohort expression source from the NPH52 study.

This is a provenance/composition finding, not authorization to use those cohort labels as model features.

## HVS and SEA-AD are different source constructions

### HVS

Public Human Variation Study materials describe adult cortical tissue obtained from individuals undergoing epilepsy or tumor surgeries and a study designed to measure inter-individual cell-abundance and expression variation. It should not be casually labeled a simple "healthy control" source.

External provenance references:

- Johansen et al., *Science* 2023, "Inter-individual variation in human cortical cell type abundance and expression"
- https://pmc.ncbi.nlm.nih.gov/articles/PMC11702338/
- https://github.com/AllenInstitute/human_variation

The public study describes 75 adult individuals, whereas the foundation split registry contains 78 HVS person IDs. That difference requires provenance reconciliation rather than assuming the two universes are identical.

### SEA-AD

The public 2026 SEA-AD release includes processed snRNA-seq across eleven brain regions. The 11 SEA-AD reader operators here correspond to regional matrices including PFC/A9, MTG, caudate, MEC, LEC, hippocampus, ITG, STG, FI, angular gyrus and V1C.

External provenance references:

- https://brain-map.org/consortia/sea-ad/our-data
- https://brain-map.org/consortia/sea-ad/our-resources

The foundation registry contains 84 SEA-AD persons. The reader metadata uses 68 train-split SEA-AD donors, partitioned into 46 fit / 12 validation / 10 oracle donors.

## `operator` is not a common semantic axis

This is established over the complete reader-fit metadata.

### HVS

- 24 operators
- every operator is native-class-pure
- one operator effectively corresponds to one processed native cell class
- matrix IDs are opaque UUID-like identifiers

### NPH52

- 7 operators
- every operator is native-class-pure
- matrix IDs explicitly encode `Astro`, `Endo`, `ExN`, `InN`, `MG`, `OPC`, `Oligo`

### SEA_AD

- 11 operators
- regional matrices
- 17–26 native classes per operator
- dominant native class occupies only about 20–29% of an operator

Therefore operator is neither a common batch axis nor a common biological axis. It can be used as an exact support/provenance boundary, but equal operator weighting or generic "operator adjustment" has no source-independent scientific meaning.

## Cell-class metadata are not harmonized

Reader-fit native-class vocabularies:

- HVS: 24 labels
- NPH52: 7 labels
- SEA_AD: 46 labels

Literal overlap:

- HVS vs SEA_AD: 22 labels
- HVS vs NPH52: 1 label (`OPC`)
- NPH52 vs SEA_AD: 1 label (`OPC`)

`broad_class` is completely missing for all 236,476 NPH52 reader-fit cells. SEA-AD also contains region-specific `*Subclass` labels alongside cortical class labels, especially in caudate.

Consequences:

1. string equality is not a valid cross-source cell-type harmonization method;
2. a source-aware taxonomy mapping is required before class-balanced sampling or G4 content evaluation across sources;
3. HVS and NPH operator construction already embeds cell class, so operator-based nuisance correction can remove biological state;
4. region-specific SEA-AD classes should not automatically be collapsed into cortical labels.

## Molecular measurement support is strongly source-dependent

Cell-weighted support fractions over the 41,238-address namespace:

| source | measured scalar | structurally unmeasured | collision unresolved |
|---|---:|---:|---:|
| HVS | 45.43% | 54.57% | 0% |
| NPH52 | 80.71% | 17.97% | 1.32% |
| SEA_AD | 85.06% | 13.22% | 1.72% |

Measured addresses per operator:

- HVS: exactly 18,736
- NPH52: 30,294–34,405
- SEA_AD: exactly 35,076

Across all addresses:

- 17,186 are measured by all 42 operators;
- 17,346 are measured by at least one operator from all three source families;
- 289 are measured by no operator;
- median operator recurrence is 18 operators.

`MEASURED_ZERO` must remain distinct from structurally unmeasured and collision unresolved. A dense zero-filled matrix would destroy this distinction.

## Feature identity and collision ETL are scientific data-model components

Canonical address identity classes:

- `current_exact`: 40,422
- `legacy_exact`: 773
- `source_native_anchored`: 43

Address source-family provenance:

- one family: 9,990
- two families: 13,679
- three families: 17,569

Protein-coding addresses are 18,904 of 41,238. A future protein-coding-only simplification would therefore be a new scientific transformation, not harmless cleanup.

The supplemental unresolved-collision table has 14 rows, affecting 2 molecular addresses across all 7 NPH52 matrices. Collision state remains evidence and must not be silently coerced to zero or dropped.

## Auxiliary 50K expression sample

The separately uploaded frozen discovery sample contains 50,000 cells / 41,238 addresses and 246,702,069 nonzeros (density 11.96%). It contains all 104 fit donors and all 42 operators but uses two deliberate sampling schemes rather than being a simple population sample.

Source composition:

- SEA_AD 33,821
- HVS 10,958
- NPH52 5,221

Median `source_library` in the auxiliary sample:

- HVS: 14,149
- NPH52: 8,151
- SEA_AD: 19,243

These library-depth summaries are **supporting-only** because the 50K sample was deliberately constructed for natural-mixture plus coverage discovery. They motivate full-population QC summaries; they do not define FULL104 thresholds.

## ETL chain that must become explicit

```text
source study / donor / tissue / region / cell-class semantics
  -> source matrix and source feature namespace
  -> canonical donor/cell identity
  -> source feature -> 41,238 molecular-address mapping
  -> collision handling and observation-state assignment
  -> structural measurement support
  -> lawful reader partition
  -> raw source-library denominator
  -> mapped ledger counts
  -> log1p(10000 * raw_count / full_source_library)
  -> native-support representation
  -> comparable/common-core diagnostic view
  -> masking / target construction / JEPA
```

Every arrow can change scientific meaning. ETL is therefore part of the model contract, not an upstream implementation detail.

## Immediate design implications

### Keep / strengthen

- donor-uniform scientific objective remains much more defensible than cell-uniform for the current combined population;
- keep native support as the information-preserving view;
- keep the 17,186 common core as calibration/comparability support, not the only biological input;
- preserve explicit observation states;
- keep source/operator/support/depth shortcut tests;
- keep model pathology-blind.

### Add

1. **Taxonomy harmonization authority**
   - explicit mappings for HVS / NPH / SEA-AD native labels;
   - preserve regional/striatal specialization rather than forcing false equivalence;
   - never infer equivalence from string similarity alone.

2. **Full-population expression/QC atlas on the GPU lane**
   - source library, ledger mass, outside-ledger mass;
   - detected ledger/core addresses;
   - zero fractions and UMI burden;
   - mitochondrial/ribosomal and biotype composition where lawful;
   - summaries by source, donor, operator/region, native class and harmonized class;
   - donor-level distributions, not only pooled-cell summaries.

3. **Region × cell-state × donor coverage matrix for SEA-AD**
   - identify cells/states whose apparent source signal is actually region coverage;
   - identify donors represented in only a subset of regions;
   - prevent region availability from masquerading as disease/cellular-state signal.

4. **Source acquisition / chemistry / processing provenance ledger**
   - assay chemistry, tissue origin, nuclei processing, alignment/reference versions, filtering and taxonomy version when recoverable;
   - classify each field as biological, technical, mixed, grouping-only or protected.

5. **Population-shift diagnostics**
   - compare reader-fit vs validation/oracle using metadata only;
   - compare donor and class coverage without opening heldout expression;
   - quantify whether reader-fit is representative of each source's available train cohort.

6. **Expression ETL reconciliation tests**
   - raw source library -> mapped ledger -> strict core;
   - source-specific unmapped/collision loss;
   - exact normalization parser;
   - target contribution to denominator;
   - no accidental source-specific normalization convention.

## Pathology-aware dataset understanding without pathology leakage

The project should use a two-layer rule.

### Dataset-understanding layer

We may inspect lawful provenance and, when deliberately authorized, fit-population pathology or cohort composition to understand confounding, coverage and selection bias.

### Model/selection layer

Pathology must remain unavailable to:

- representation input;
- mask construction;
- target selection;
- G4/G5 threshold setting;
- attacker tuning;
- sampling/weight changes chosen to improve protected outcomes;
- DEV/SEALED confirmation adaptation.

If a future fit-only pathology composition audit is opened, its outputs should be quarantined as descriptive confounding analysis and must not be allowed to tune terminal criteria.

## What this pass does not yet know

- exact pathology composition of the 46 SEA-AD reader-fit donors;
- sex/age/APOE and other donor-demographic balance in the current fit104 population;
- exact acquisition/chemistry differences for every HVS matrix;
- why the foundation HVS registry has 78 IDs while the public HVS paper describes 75 adults;
- full-population per-cell expression/QC distributions beyond already-produced Audit A/B/C sufficient statistics;
- a reviewed cross-source cell-taxonomy harmonization.

These are now explicit dataset-engineering blockers rather than hidden assumptions.

## Protected state

```text
TERMINAL_MASKING_OUTCOMES = UNOPENED
D_SHARED                  = SEALED
PATHOLOGY                  = SEALED_FOR_MODEL_AND_TERMINAL_ADAPTATION
DEV / SEALED              = SEALED
MASKING_POLICY_SELECTED    = NO
G5_MARGIN_SELECTED         = NO
TRAINING_OFF
```
