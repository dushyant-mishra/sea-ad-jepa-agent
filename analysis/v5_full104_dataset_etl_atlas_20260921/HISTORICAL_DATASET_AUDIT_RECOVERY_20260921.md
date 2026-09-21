# Historical dataset-audit recovery ledger — 2026-09-21

Status: `CURRENT_FULL104_RECONNAISSANCE__HISTORICAL_RECOVERY`

Purpose: recover and consolidate dataset/ETL findings that were already established in project history but were not consistently elevated into V5 pipeline design.

This ledger does **not** replace the original authorities. It points to them, records what they established, and states the design consequence that should now be carried forward.

## Core conclusion

The project did not lack dataset auditing entirely. It performed substantial dataset QA and metadata/support analysis in multiple phases. The deficiency was that these audits remained fragmented across V4, foundation construction, target discovery, census, population governance and red-team work.

The V5 pipeline therefore repeatedly rediscovered dataset facts instead of treating them as one coherent upstream scientific data model.

The corrective rule is:

> Every V5 sampling, masking, nuisance-control, target-construction, representation and evaluation decision must identify which authenticated dataset facts it assumes and whether those facts are source-specific, donor-specific, operator-specific, biological, technical or mixed.

## Historical authorities recovered

| historical/current artifact | what it established | current design consequence |
|---|---|---|
| `docs/history/full104_v014_20260826/01_full104_metadata_adapter/DATASET_FIDELITY_REVIEW.md` | 4,553,407 exact reader-fit rows, 104 donors, 42 operators, 1,400 donor×operator groups; exact row lineage and no heldout donor overlap | FULL104 row identity and population geometry are already authenticated; do not rebuild them casually |
| `scripts/v4/foundation_metadata_atlas_and_freeze.py` + calibration-bundle `FOUNDATION_METADATA_ATLAS.json` | full row-level metadata atlas, donor/operator/native-class imbalance, missing NPH broad-class annotation, 149-donor metadata context, zero duplicate stable keys | donor/class/operator composition is a first-class scientific property, not a loader detail |
| `scripts/v4/foundation_metadata_anomaly_tables.py` | duplicate IDs, source crossings and absent donor×operator / donor×class combinations were explicitly audited | absent combinations must remain structural absence; never fabricate balanced combinations |
| `docs/agent/READER_FIT_SUPPORT_OVERLAP_PROFILE_V1.json` | 17,186 addresses measured by all 42 operators; source-native support much larger, especially NPH52 and SEA_AD | native support is information-preserving; common core is comparability/calibration, not the only biological representation |
| `docs/agent/READER_FIT_OPERATOR_SEMANTICS_PROFILE_V1.json` | HVS/NPH operators are native-class-pure; SEA_AD operators are multi-class regional matrices; operator has no common cross-source meaning | operator cannot be an equal scientific-mass axis or generic technical covariate |
| `docs/agent/READER_FIT_RELATIONAL_SUPPORT_PROFILE_V1.json` | donor×operator groups are extremely ragged and exhaustive relational enumeration is impossible | scientific relation weighting, proposal sampling and compute packing must remain separate |
| `docs/agent/JEPA_POPULATION_ACCESS_AND_SEALED_HOLDOUT_CONTRACT_20260907.md` | 149 reader donors are split 104 fit / 22 validation / 23 oracle inside foundation/train; pathology is an independent firewall | validation/oracle are population shifts, not synonyms for foundation DEV/SEALED; expression access does not imply pathology access |
| `docs/agent/D1_REAL_DATA_SOURCE_INVENTORY_20260907.md` | recovered real-data assets, calibration bundle, 50k auxiliary expression sample and their hashes/roles | 50k sample is useful for mechanics only and must never set FULL104 adaptive values |
| `docs/agent/FULL104_READONLY_CENSUS_AUTHORITY_20260917.json` | strict core, measured-zero frequency, nonzero-per-cell distribution, target support, donor precision and mask-burden stress geometry | measured zero is evidence; donor count is the independent biological scale; sparsity must be built into masking/evaluation |
| `analysis/v5_full104_information_channel_redteam_20260920/NORMALIZATION_DENOMINATOR_AUDIT_REPORT.md` | full-source library contains outside-ledger biological mass, source-structured and visible through normalization | normalization is a possible source/domain channel and query-denominator path |
| `analysis/v5_full104_information_channel_redteam_20260920/TARGET_SOURCE_ESTIMABILITY_AUDIT_REPORT.md` | source-specific target estimability is heterogeneous and current scorer can map undefined terms to zero | non-estimability must be explicit in evidence and source×fold geometry must be measured |
| `results/reports/sea_ad_full_metadata_covariate_audit.md` | SEA_AD donor metadata contains PMI, RIN, brain pH, age, sex, education, APOE and clinical/pathology fields | lawful technical/demographic covariates exist for confounding audits; pathology fields remain protected from model/policy adaptation |
| `results/v4/stage81a1b_release_lineage.csv` and regional metadata schema audits | current SEA_AD multiregion release superseded older MTG lineage and expanded taxonomy/regions | V5 must be designed around the actual 2026 multiregion data, not assumptions inherited from older MTG-only work |

## Historical facts that should now be treated as upstream design inputs

### Population and objective geometry

- 4,553,407 fit cells / 104 donors / 42 operators.
- Source cell mass is extremely imbalanced: SEA_AD contributes ~90.4% of cells.
- Source donor mass is much less imbalanced: HVS 41, NPH52 17, SEA_AD 46.
- Donor cell counts range from 81 to 174,111; historical metadata-atlas donor-cell Gini is 0.612.
- Operator size Gini is 0.765.

Implication: cell-uniform, donor-uniform and source-donor-uniform objectives are different scientific estimands.

### Support geometry

- 41,238 canonical molecular addresses.
- 17,186 strict all-42 measured-scalar common core.
- HVS has 18,736 measured addresses/operator.
- NPH52 has 30,294–34,405 measured addresses/operator.
- SEA_AD has 35,076 measured addresses/operator.
- structural missingness and collision-unresolved states are distinct from measured zero.

Implication: feature availability is part of the observation process and itself can encode source/cell-class information.

### Operator semantics

- HVS operators are native-class-pure.
- NPH52 operators are native-class-pure and explicitly class-named.
- SEA_AD operators are brain-region matrices containing many native classes.
- equal operator-group weighting can upweight tiny groups by >100× relative to anchor-cell prevalence.

Implication: `operator` is mixed biological/technical provenance and cannot be treated as one common nuisance/batch axis.

### Taxonomy

- HVS and SEA_AD share many cortical native labels.
- NPH52 uses a coarser seven-class vocabulary.
- NPH52 broad_class is unavailable in the current reader metadata.

Implication: cross-source class balancing requires a reviewed taxonomy harmonization authority; string equality is insufficient.

### Expression sparsity

- strict-core measured-zero frequency is ~0.833.
- measured zero is evidence, not missing.
- remaining visible nonzero burden varies strongly by cell.

Implication: masking must be value-independent and must not privilege realized nonzero addresses.

## New whole-dataset findings added on 2026-09-21

These were derived from the same authenticated metadata/support authorities, not from protected terminal outcomes.

1. **Support fingerprints are highly identifying.**
   - one exact support fingerprint for every HVS cell;
   - one exact support fingerprint for every SEA_AD cell;
   - seven distinct NPH52 fingerprints, each tied to one NPH operator/native class.
   Therefore structural feature availability alone reveals source family and, within NPH52, cell-class/operator identity.

2. **SEA_AD region coverage is highly donor-dependent.**
   Among 46 fit donors:
   - 22 have 11 regions;
   - 2 have 10;
   - 3 have 9;
   - 16 have 3;
   - 3 have 2.
   Region availability is therefore coupled to donor identity.

3. **Reader validation/oracle are composition shifts.**
   - reader_validation: HVS 10, SEA_AD 12, NPH52 0;
   - reader_oracle: HVS 11, SEA_AD 10, NPH52 2.
   Median SEA_AD regional coverage is 10 regions in fit, 3 in validation, 5 in oracle.

4. **NPH reader expression is the control subset of the NPH52 study.**
   The foundation registry contains NPH_Ctrl / NPH_Abeta / NPH_AbetaTau cohorts, but reader expression uses only NPH_Ctrl donors (17 fit + 2 oracle).

5. **Class availability differs by donor.**
   - HVS fit donors: 21–24 of 24 native classes;
   - NPH52 fit donors: 1–7 of 7 classes, with one donor represented by a single class matrix;
   - SEA_AD fit donors: 24–46 native labels, strongly linked to region coverage.

## What previous audits did not sufficiently integrate

The following questions were either missing or not propagated into V5:

- a single source→donor→region→class→support→expression ETL data model;
- source acquisition/chemistry/preprocessing differences;
- full donor×region×class coverage as a model-design variable;
- fit-vs-validation/oracle composition-shift reporting;
- support-pattern leakage as an explicit source/class shortcut;
- cross-source taxonomy harmonization;
- full-population QC distributions by donor/source/region/class;
- reconciliation of public-study participant counts with the exact frozen reader registries;
- explicit treatment of demographics/PMI/RIN/brain pH as descriptive confounder diagnostics separate from model inputs;
- a requirement that every V5 design authority cite the dataset evidence it depends on.

## Current corrective state

This ledger does not change production authority.

```
DATASET_ETL_ATLAS = ACTIVE_WORKSTREAM
TERMINAL_MASKING_OUTCOMES = UNOPENED
D_SHARED = SEALED
DEV / SEALED = SEALED
PATHOLOGY_MODEL_INPUT = FORBIDDEN
PATHOLOGY_TERMINAL_ADAPTATION = FORBIDDEN
TRAINING_OFF
```
