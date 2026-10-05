# Therapeutic perturbation ETL audit and work plan — 2026-09-23

Status: `STARTED__METADATA_CONTRACT_IMPLEMENTED__PHYSICAL_EXECUTION_PENDING`

## Classification against historical audit rules

- Stage81A1C-P acquisition: **ALREADY_AUDITED** for source discovery, processed-only download policy, hashes and format-open checks.
- Pre-Stage81A2 perturbation readiness: **ALREADY_AUDITED** as a blocker inventory.
- New therapeutic perturbation ETL atlas: **CHANGED_INPUT_REQUIRES_REQUALIFICATION** because the question is no longer merely "were files downloaded safely?" but "can exact intervention effects be derived reproducibly and compared across datasets?"
- Historical digital perturbation / flat-vector JEPA benchmarking: **SUPPORTING/HISTORICAL**, not causal or therapeutic authority.

## Recovered project history

### Acquired study universe

Eight studies / sixteen processed assets are frozen in the historical acquisition registry. Five studies declare guide-assignment availability. GSE301119 has two fully audited Seurat objects with explicit guide identity, targeted gene, donor, CRISPR mode and non-targeting-control metadata.

### Historical readiness gap

The existing `pre_stage81a2_perturbation_readiness_registry.csv` marks every asset `perturbation_training_ready=False`. The main blockers are not download integrity; they are analytical semantics:

- exact matrix/member resolution;
- exact feature identity;
- guide/protospacer -> cell assignment;
- control definitions;
- sample/replicate structure;
- perturbation identity;
- measurement masks where feature universes differ.

GSE301119 is closest to per-cell readiness but its CRISPRa and CRISPRi feature universes differ and require stable feature alignment plus explicit measurement masks.

### Historical JEPA perturbation result

The old Kampmann DEG benchmark tested digital single-gene input knockdown against observed CROP-seq DEG-derived shifts. Several targets were anti-aligned (for example CSF1R, TGFBR2 and CDK8), while CDK12 was positive. This is a useful negative/partial result and argues against starting the therapeutic lane from an assumed JEPA counterfactual mechanism.

### Historical in-silico regulator work

Stage74/77 produced bounded model-input perturbation hypotheses and explicitly did **not** establish causal effects, therapeutic rescue, or validated regulation. Those outputs must not seed the new ETL outcome definitions.

## ETL design

The new substrate will have four authority layers.

### A. Physical authority

For every processed asset:

- exact path;
- byte size;
- SHA-256;
- format-open verification;
- archive-member manifest;
- no raw FASTQ/BAM/CRAM/SRA substitution;
- immutable source receipt.

### B. Experimental-schema authority

Per study/sample/object:

- organism and model system;
- cell type/model;
- modality;
- CRISPRi / CRISPRa / genotype / pharmacology / noncoding perturbation;
- guide/protospacer identity;
- target gene/element;
- control class;
- donor/line;
- lane/batch;
- replicate;
- dose;
- time;
- treatment context.

Unknown fields remain unknown. No semantic inference from filenames unless separately authenticated.

### C. Molecular measurement authority

For every matrix:

- orientation;
- exact feature namespace;
- stable Ensembl/symbol mapping;
- duplicate/collision policy;
- measured-feature mask;
- count/data layer semantics;
- normalization status;
- cell/sample count;
- exactly-once row accounting.

No zero-filling absent genes as biological zeros.

### D. Intervention-effect authority

Only after A-C pass:

- matched control definition;
- guide-level effect;
- target-level aggregate effect;
- replicate/donor transport;
- uncertainty;
- quality metrics;
- cross-study comparability.

This layer will first produce expression-space intervention vectors. JEPA-space effects are a downstream validation layer, not the ETL definition of effect.

## First implementation

`build_perturbation_etl_atlas_v1.py` now performs repository-level qualification and optional physical authentication. In `--require-physical` mode it fails closed unless each recorded asset matches the historical byte count and SHA-256.

The current chat runtime does not contain the multi-gigabyte perturbation files, so no physical PASS is claimed here.

## Next execution order

1. Run V1 physical authentication on `D:\\Jepa project`.
2. Produce archive/object member census for all 16 assets.
3. Promote GSE301119 through exact feature-ID + measurement-mask resolution.
4. Resolve GSE293118 protospacer-call joins; its archive already contains a per-cell protospacer-calls file.
5. Resolve GSE178317 lane-matched gene-expression/sgRNA-enrichment joins without inventing assignments.
6. Resolve GSE311359 processed sample matrices and perturbation metadata.
7. Keep genotype/pharmacology/bulk studies as separate validation strata rather than forcing a single-cell CRISPR schema.
8. Freeze a canonical perturbation ETL receipt before any disease-state reversal or compound matching analysis.

## Firewall

`JEPA_TRAINING=OFF`

`THERAPEUTIC_RANKING=OFF`

`PROTECTED_FULL104_OUTCOMES=UNOPENED`

`PATHOLOGY_ADAPTIVE_SELECTION=FORBIDDEN`

`HISTORICAL_IN_SILICO_PERTURBATIONS != MEASURED_INTERVENTION_EFFECTS`
