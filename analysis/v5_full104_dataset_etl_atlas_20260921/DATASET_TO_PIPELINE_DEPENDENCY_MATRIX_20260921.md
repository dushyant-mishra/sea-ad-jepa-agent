# Dataset → pipeline design dependency matrix — 2026-09-21

Status: `PROSPECTIVE_V5_DATA_AWARE_DESIGN_RULES__TRAINING_OFF`

Purpose: make dataset understanding operational. Each pipeline component should identify which dataset properties it relies on and which failure modes must be tested.

| dataset fact | affected pipeline component | required design consequence | forbidden shortcut |
|---|---|---|---|
| SEA_AD is ~90.4% of cells but 46/104 donors | base JEPA objective, attacker fitting, evaluation | distinguish cell-weighted, donor-uniform, source-donor-balanced roles explicitly | letting row count silently define scientific population |
| donor cell counts range 81–174,111 | training weights, minibatching, uncertainty | preserve donor-uniform scientific mass independently of compute packing; report donor-level precision | treating millions of cells as independent biological replicates |
| reader-validation has no NPH52 and oracle has only 2 NPH52 donors | validation/oracle interpretation | source-stratified and composition-aware reporting; do not call aggregate degradation pure donor-generalization failure | tuning on heldout source mixture |
| SEA_AD donor regional coverage ranges 2–11 regions | relational target, context encoding, validation | make region availability explicit; evaluate within shared regional support where needed; separate region shift from donor shift | assuming every SEA donor represents all regions |
| HVS/NPH operators are class-pure while SEA_AD operators are regional multi-class matrices | operator use, relational sampler, nuisance controls | operator can constrain lawful comparisons but cannot carry equal scientific mass or be treated as generic batch | operator-balanced objective without correction |
| NPH reader population is NPH_Ctrl only | source interpretation, external validity | label the source as the control-subcohort reader slice of NPH52; keep original study cohorts as provenance context only | interpreting reader NPH expression as all NPH52 pathology groups |
| HVS is living surgical cortical tissue from epilepsy/tumor cases | source interpretation, domain challenge | model source as study/domain context, not “healthy control” | calling HVS disease-free or pathology-free |
| source-native class taxonomies differ; NPH broad_class absent | class balancing, G4 content, cross-source evaluation | freeze a reviewed source-aware taxonomy mapping and report unmappable states | string-join harmonization or invented NPH broad labels |
| one HVS support fingerprint, one SEA_AD fingerprint, seven NPH class-specific fingerprints | representation, attacker, anti-cheat | explicitly challenge source/class decoding from support/missingness alone; consider support-conditioned diagnostics | claiming metadata blindness when support geometry reveals domain |
| HVS support 18,736 vs SEA_AD 35,076 vs NPH variable 30–34K | representation and masking | preserve native support but use common support for matched diagnostics; encode missingness semantics explicitly | zero-filling structural absence and treating as measured zero |
| strict all-42 common core is 17,186 addresses | calibration, cross-source attacker | use as comparability substrate when equal feature availability is required | promoting common core to sole production input without scientific authority |
| ~83.3% strict-core measured values are zero | masking, target eligibility | measured zero remains eligible measured evidence; masks cannot depend on realized zero/nonzero | nonzero-conditioned masking |
| outside-ledger mass enters source_library normalization | normalization, F13, attacker | quantify source/donor/class distribution; test denominator exploitability | treating ledger-only values as normalization-closed |
| raw query count contributes to source_library | target hiding, F13 | distinguish stored-query isolation from upstream denominator dependence | claiming query scalar fully withheld merely because target column is absent |
| unresolved collision state exists, especially NPH/SEA support | ETL and feature identity | retain collision-unresolved state and provenance; exclude from strict scalar support | coercing collision ambiguity to zero |
| 40,422 current-exact + 773 legacy-exact + 43 source-native anchored addresses | tokenizer/address identity | bind address identity class and mapping provenance | assuming every feature has identical cross-source identity confidence |
| 289 addresses are never measured scalar | address universe | never treat them as biologically observed training targets | keeping namespace entries as if measured |
| SEA_AD release is 2026 multiregion and taxonomy-expanded | all V5 source assumptions | bind exact release/version and region/taxonomy semantics | inheriting MTG-only assumptions from older project versions |
| SEA_AD donor metadata includes PMI/RIN/brain pH/age/sex/APOE | confounding diagnostics | use lawful metadata for descriptive/QC confounding audits with explicit role labels | feeding protected/demographic variables into model without authority |
| pathology is independent protected channel | dataset analysis vs model | dataset team may characterize lawful fit-population provenance/confounding under explicit authority; model/mask/threshold paths stay pathology-blind | equating “we can inspect data” with pathology permission for adaptive modeling |

## Required authority interfaces going forward

### 1. DatasetCompositionAuthority

Must bind:
- fit population;
- source/donor/operator/region/class counts;
- donor×region and donor×class coverage;
- source mix;
- reader-validation/oracle composition context.

### 2. TaxonomyHarmonizationAuthority

Must bind:
- source-native labels;
- cross-source mapping;
- unmapped/region-specific classes;
- mapping rationale and source;
- no pathology-derived mapping.

### 3. MeasurementProcessAuthority

Must bind:
- molecular address identity;
- structural support;
- collision state;
- source library;
- normalization;
- observation-state encoding.

### 4. AcquisitionProvenanceLedger

Must bind where recoverable:
- study;
- tissue context;
- brain region;
- assay/chemistry;
- processing pipeline/version;
- taxonomy release;
- raw matrix provenance.

### 5. DatasetShiftReport

Before interpreting validation/oracle:
- source mix;
- donor cell count distribution;
- region coverage;
- class coverage;
- support fingerprints;
- lawful QC metadata;
must be compared against reader-fit.

## Design review rule

No V5 design change should be accepted with only:

> “the code is correct.”

It should also answer:

1. Which population does this operation represent?
2. Which source/region/class states are actually available?
3. Does measurement support reveal the label/domain being tested?
4. Is the variable biological, technical, mixed, grouping-only, or protected?
5. Is weighting correcting compute imbalance or redefining scientific mass?
6. Does heldout composition differ from fit composition?
7. Which historical dataset audit already constrains this choice?
8. What full-data ETL/QC evidence would falsify the design assumption?

## Protected boundary

Dataset understanding can be broad. Model adaptation remains narrow.

```
ALLOW_DATASET_PROVENANCE_AND_COMPOSITION_AUDIT = YES
ALLOW_MODEL_PATHOLOGY_INPUT = NO
ALLOW_MASK_SELECTION_FROM_PATHOLOGY = NO
ALLOW_G4_G5_THRESHOLD_TUNING_FROM_PATHOLOGY = NO
ALLOW_DEV_SEALED_ADAPTATION = NO
TRAINING_OFF
```
