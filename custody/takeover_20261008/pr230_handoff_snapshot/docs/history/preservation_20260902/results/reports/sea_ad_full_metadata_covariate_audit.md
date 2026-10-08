# SEA-AD Full Donor Metadata Covariate Audit

This audit checks whether the local SEA-AD donor workbook contains the covariates needed to harden v2.1 target validation.

Metadata workbook: `data\raw\metadata\sea-ad_cohort_donor_metadata_072524.xlsx`
Joined target table: `data\processed\metadata\sea_ad_mtg_donor_pathology_targets.csv`

## Covariate Fields Found

- `postmortem_interval`: `PMI`
- `rna_quality`: `RIN`
- `tissue_quality`: `Brain pH`, `Consensus Clinical Dx (choice=Multiple System Atrophy)`, `Fresh Brain Weight`, `Rapid Frozen Tissue Type`
- `technical_batch`: none found
- `demographic`: `Age at Death`, `Age of Dementia diagnosis`, `Age of onset cognitive symptoms`, `Highest level of education`, `Hispanic/Latino`, `Race (choice=American Indian/ Alaska Native)`, `Race (choice=Asian)`, `Race (choice=Black/ African American)`, `Race (choice=Native Hawaiian or Pacific Islander)`, `Race (choice=Other)`, `Race (choice=Unknown or unreported)`, `Race (choice=White)`, `Sex`, `Years of education`, `specify other race`
- `genetic`: `APOE Genotype`
- `clinical_cognitive`: `Cognitive Status`, `Consensus Clinical Dx (choice=Alzheimers Possible/ Probable)`, `Consensus Clinical Dx (choice=Alzheimers disease)`, `Consensus Clinical Dx (choice=Ataxia)`, `Consensus Clinical Dx (choice=Control)`, `Consensus Clinical Dx (choice=Corticobasal Degeneration)`, `Consensus Clinical Dx (choice=Dementia with Lewy Bodies/ Lewy Body Disease)`, `Consensus Clinical Dx (choice=Frontotemporal lobar degeneration)`, `Consensus Clinical Dx (choice=Huntingtons disease)`, `Consensus Clinical Dx (choice=Motor Neuron disease)`, `Consensus Clinical Dx (choice=Other)`, `Consensus Clinical Dx (choice=Parkinsons Cognitive Impairment - no dementia)`, `Consensus Clinical Dx (choice=Parkinsons Disease Dementia)`, `Consensus Clinical Dx (choice=Parkinsons disease)`, `Consensus Clinical Dx (choice=Prion)`, `Consensus Clinical Dx (choice=Progressive Supranuclear Palsy)`, `Consensus Clinical Dx (choice=Taupathy)`, `Consensus Clinical Dx (choice=Unknown)`, `Consensus Clinical Dx (choice=Vascular Dementia)`, `Interval from last CASI in months`, `Interval from last MMSE in months`, `Interval from last MOCA in months`, `Last CASI Score`, `Last MMSE Score`, `Last MOCA Score`
- `neuropathology`: `Braak`, `CERAD score`, `Highest Lewy Body Disease`, `LATE`, `Overall AD neuropathological Change`, `Overall CAA Score`, `Thal`, `Total Microinfarcts (not observed grossly)`, `Total microinfarcts in screening sections`

## Join Check

- joined donor rows: `84`
- `PMI` non-null rows: `84`
- `RIN` non-null rows: `84`
- `Brain pH` non-null rows: `84`
- `Braak` non-null rows: `84`
- `Thal` non-null rows: `84`
- `APOE Genotype` non-null rows: `84`
- `Cognitive Status` non-null rows: `84`

## Next Use

Use `results/tables/sea_ad_full_metadata_targets_with_covariates.csv` as the covariate-enriched donor table for rerunning the v2.1 target validation.

Important interpretation boundary: PMI, RIN, and brain pH are covariates for artifact control. They are not disease targets.
