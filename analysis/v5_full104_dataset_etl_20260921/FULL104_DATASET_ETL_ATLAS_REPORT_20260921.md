# FULL104 dataset ETL and composition atlas — 2026-09-21

Status: `CURRENT_FULL104_RECONNAISSANCE__DATASET_DESIGN_INPUT__NOT_MODEL_INPUT_AUTHORITY`

This report exists because pathology-blind modeling does **not** require the project team to be blind to the dataset. The purpose is to understand the lawful reader population, source/region/cell-class composition, feature-support geometry, identity harmonization, and ETL transformations before further pipeline decisions are frozen.

No terminal masking outcome, D_shared, DEV/SEALED expression, or training was opened. The calibration bundle used here explicitly reports `pathology_fields_included=false` and `dev_sealed_expression_included=false`.

## 1. Reproducible inputs

Top-level uploaded calibration bundle:

- file: `FOUNDATION_CALIBRATION_BUNDLE_20260824.zip`
- bytes: `410,278,055`
- SHA-256: `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`

Authenticated row metadata inside the bundle:

- member: `metadata/foundation_metadata_rows.sqlite`
- bytes: `2,709,786,624`
- SHA-256: `a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913`

Canonical molecular namespace:

- `contracts/address_namespace.csv`
- SHA-256: `7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd`

Operator×address observation-state authority:

- `support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz`
- SHA-256: `852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537`

The ETL uses named SQL aggregates so each row-level query can be rerun and authenticated independently rather than forcing one monolithic scan.

## 2. Population structure

The metadata universe contains:

- **6,351,753 cells**
- **149 donors**
- three reader partitions: `reader_fit`, `reader_validation`, `reader_oracle`
- donor overlap across reader partitions: **0**

The lawful reader-fit population contains:

- **4,553,407 cells**
- **104 donors**
- **42 operators/matrices**

Reader-fit source composition:

| source | cells | cell mass | donors | donor mass | operators |
|---|---:|---:|---:|---:|---:|
| HVS | 198,718 | 4.36% | 41 | 39.42% | 24 |
| NPH52 | 236,476 | 5.19% | 17 | 16.35% | 7 |
| SEA_AD | 4,118,213 | 90.44% | 46 | 44.23% | 11 |

This is a major scientific-design fact. A cell-uniform objective represents a very different population from a donor-uniform objective. The current donor-uniform base estimand is therefore not a cosmetic weighting choice.

## 3. Donor-size heterogeneity

Reader-fit donor cell-count ranges are strongly source dependent.

### HVS

- min 1,625
- median 4,292
- max 12,509

### NPH52

- min **81**
- median 14,874
- max 23,972

### SEA_AD

- min 9,127
- median 91,242.5
- max 174,111

The NPH52 81-cell donor is not a rounding artifact. Donor-uniform objectives and donor-level uncertainty therefore need to tolerate extremely unequal within-donor measurement precision.

## 4. Operator is not one scientific axis

The same metadata field has different biological/technical meaning across sources.

### HVS

- 24 operators
- every operator is native-class-pure in reader-fit
- each operator contains exactly one native class
- matrix IDs are opaque UUID-like identifiers

### NPH52

- 7 operators
- every operator is native-class-pure
- matrix names explicitly encode `Astro`, `Endo`, `ExN`, `InN`, `MG`, `OPC`, `Oligo`

### SEA_AD

- 11 operators
- operators are region matrices
- each contains 17–26 native classes
- no operator is native-class-pure
- dominant native-class share is only ~19.6–29.2%

Consequence: `operator` may be used as an admissibility/support boundary where justified, but must **not** be automatically treated as a cross-source scientific averaging axis or a pure technical nuisance.

## 5. SEA_AD region coverage is ragged by donor

Among 46 reader-fit SEA_AD donors, the number of region matrices represented per donor is:

| regions represented | donors |
|---:|---:|
| 2 | 3 |
| 3 | 16 |
| 9 | 3 |
| 10 | 2 |
| 11 | 22 |

Therefore region composition is not balanced across donors. Any region-sensitive analysis or comparator construction must account for donor×region support rather than assuming every SEA_AD donor spans the same anatomy.

## 6. Cell-class schemas are not harmonized by label

Reader-fit native-class vocabularies:

- HVS: 24 labels
- NPH52: 7 labels
- SEA_AD: 46 labels

Literal label overlap is poor for NPH52:

- HVS × NPH52: only `OPC` overlaps literally
- NPH52 × SEA_AD: only `OPC` overlaps literally
- HVS × SEA_AD: 22 HVS labels overlap literally

NPH52 `broad_class` is missing for all 236,476 reader-fit cells in the row metadata, whereas HVS and SEA_AD have populated broad-class fields. This means a naïve cross-source taxonomy join on existing labels is not a valid ETL operation.

Any cross-source biological class ontology should be a separately reviewed harmonization layer, with original native labels retained losslessly.

## 7. NPH52 reader cohort composition in the foundation split registry

The foundation split registry maps the NPH52 reader population as:

- `reader_fit`: 17 donors, cohort `NPH_Ctrl`
- `reader_oracle`: 2 donors, cohort `NPH_Ctrl`
- no NPH52 donors in `reader_validation`

This is a composition/provenance finding only. It is not a model-facing feature and must not be used to tune terminal masking. It does mean that “NPH52” in the lawful reader-fit population should not be interpreted as a generic representation of all possible NPH disease states.

## 8. Molecular-address support is a first-class data property

Canonical address universe: **41,238**.

Address recurrence across 42 operators:

- measured scalar by all 42 operators: **17,186**
- measured by all three source families: **17,346**
- measured by no operator: **289**
- median operators measuring an address: 18
- 75th percentile: 42

Source support:

| source | measured by every operator in source | measured by any operator in source |
|---|---:|---:|
| HVS | 18,736 | 18,736 |
| NPH52 | 29,136 | 35,098 |
| SEA_AD | 35,076 | 35,076 |

There are exactly **9 exact measured-support patterns** across the 42 operators:

- HVS: 1
- NPH52: 7
- SEA_AD: 1

This makes support geometry highly source-identifying and explains why measurement-support leakage has been a recurring shortcut channel.

## 9. Pairwise support overlap

For addresses measured by every operator within each source:

- HVS ∩ NPH52: 17,392; Jaccard 0.571
- HVS ∩ SEA_AD: 17,757; Jaccard 0.492
- NPH52 ∩ SEA_AD: 26,900; Jaccard 0.721

For addresses measured by any operator within a source:

- HVS ∩ NPH52: 17,595; Jaccard 0.486
- HVS ∩ SEA_AD: 17,757; Jaccard 0.492
- NPH52 ∩ SEA_AD: 29,955; Jaccard 0.745

The common core is therefore a comparability substrate, not an information-preserving replacement for native support.

## 10. Address identity harmonization is heterogeneous

Of 41,238 canonical molecular addresses:

- `current_exact`: 40,422
- `legacy_exact`: 773
- `source_native_anchored`: 43

Number of contributing source families:

- one source family: 9,990 addresses
- two source families: 13,679
- three source families: 17,569

Feature identity should therefore remain provenance-aware. A single integer token does not erase the fact that different canonical addresses entered the namespace by different mapping routes.

## 11. Collision state is real evidence, not missingness

The supplemental unregistered-collision ledger contains:

- 14 rows
- 7 matrices
- 2 affected molecular addresses
- source: NPH52

At the source-weighted support level:

- HVS collision-unresolved fraction: 0
- NPH52: ~1.321%
- SEA_AD: ~1.722%

The three observation states—measured scalar, structurally unmeasured, collision unresolved—must remain distinct through ETL and model-side masking semantics.

## 12. Reader partitions are lawful firewalls, not just train/test labels

Reader-fit, validation, and oracle donors are donor-disjoint. The ETL atlas does not open validation/oracle expression outcomes. The row metadata can be used to verify partition composition and donor separation without turning protected expression into a design input.

## 13. Immediate pipeline implications

These findings should feed back into pipeline design in the following ways.

### Sampling and scientific weighting

- Never let cell-count dominance silently define the scientific population.
- Keep donor-uniform scientific weighting explicit.
- Treat source-balanced weighting as a distinct diagnostic estimand, not a synonym for donor-uniform production weighting.
- Account for very unequal donor precision, especially NPH52.

### Operator/region/class handling

- Do not equal-weight operator groups as though operator semantics were shared across sources.
- Do not call `operator` a pure technical nuisance.
- Preserve SEA_AD region as biology/anatomical context unless a specific intervention says otherwise.
- Do not infer a cross-source cell taxonomy from literal labels.

### Feature support and masking

- Structural unmeasurement and collision-unresolved states must never become measured zero.
- Native support is the information-preserving view.
- Common-core support is useful for comparability/calibration but discards substantial NPH52/SEA_AD information.
- Support fingerprints can identify source; anti-shortcut qualification must explicitly challenge this route.

### Normalization

- Source-library normalization is part of ETL, not a neutral afterthought.
- Because source/library/support geometry differs strongly across sources, the Audit A denominator channel should be interpreted in the context of these dataset composition differences.

### Evaluation

- Source×fold estimability should be evaluated against the true donor geometry, not global donor thresholds transplanted per source.
- Region and native-class support should be treated as possible effect modifiers of measurement precision, while remaining separate from protected terminal adaptation.

## 14. What this atlas does not do

It does not:

- select a masking policy;
- change the target universe;
- choose a G5 margin;
- open terminal masking outcomes;
- inspect DEV/SEALED expression;
- claim causal pathology effects;
- harmonize cell types across sources;
- prove a normalization repair is needed;
- authorize training.

It is a dataset-engineering and composition authority candidate for **design input**, not a model-input authority.

## 15. Reproducibility

Two scripts are provided:

1. `extract_full104_dataset_sql_aggregates_v1_20260921.py`
   - authenticates the 2.7 GB SQLite against the bundle manifest;
   - exposes ten named aggregate SQL queries;
   - can run one query at a time to avoid monolithic rescans;
   - writes a content-addressed aggregate manifest.

2. `build_full104_dataset_etl_atlas_v3_20260921.py`
   - authenticates bundle inputs and the SQL aggregate cache;
   - derives source/operator/class/support/collision summaries;
   - emits compact CSV/JSON evidence plus SHA-256 output manifest.

The successful local assembly terminal was:

`PASS_FULL104_DATASET_ETL_ATLAS_V3`

Protected state remains:

```text
TERMINAL_MASKING_OUTCOMES = UNOPENED
D_SHARED                  = SEALED
PATHOLOGY                  = NOT_MODEL_FACING / NOT_TERMINAL_ADAPTIVE
DEV / SEALED              = SEALED
MASKING_POLICY_SELECTED    = NO
G5_MARGIN_SELECTED         = NO
TRAINING_OFF
```