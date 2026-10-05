# Therapeutic perturbation ETL lane — 2026-09-23

Status: `PERTURBATION_ETL_RECONNAISSANCE__NO_JEPA_TRAINING__NO_THERAPEUTIC_RANKING`

This lane turns the project's previously acquired perturbation resources into a governed ETL substrate before any intervention modeling, JEPA embedding analysis, compound matching, or therapeutic prioritization.

It deliberately mirrors the FULL104 dataset-ETL discipline:

`SOURCE BYTES -> HASH/FORMAT AUTHENTICATION -> SCHEMA/IDENTITY -> CONTROLS/GUIDES/REPLICATES -> FEATURE SUPPORT -> CANONICAL INTERVENTION TABLES -> ANALYSIS`

## Historical inputs already present

The project already acquired and hash-audited eight GEO studies / sixteen processed assets under Stage81A1C-P:

- GSE178317 — iTF/iPSC-derived microglia CRISPRi/a CROP-seq + bulk contexts
- GSE175721 — cortical organoid engineered-microglia CRISPRi
- GSE301119 — primary human macrophage CRISPRi/a Perturb-seq
- GSE293118 — HMC3 noncoding CRISPRi
- GSE311359 — iPSC-microglia MS-risk-locus Perturb-seq
- GSE254205 — APOE / amyloid-beta / GNE317 context
- GSE241858 — TREM2 R47H / cytokine context
- GSE240609 — APOE3 Christchurch microglia-neuron coculture

The large Replogle K562 genome-wide Perturb-seq object is retained separately as an engineering benchmark, not as microglial therapeutic evidence.

## Why a new ETL pass is required

Historical acquisition success is not perturbation-analysis readiness. The existing readiness registry explicitly leaves every perturbation asset blocked from perturbation training. Important unresolved items include guide-to-cell assignment, controls, sample/replicate semantics, stable feature identity, and unequal feature universes.

The old flat-vector JEPA/Kampmann benchmark is historical evidence, not a production therapeutic method: several real CRISPRi responses were poorly aligned with digital single-gene knockdown predictions. The new lane therefore starts from measured intervention effects and requires simple non-JEPA baselines before JEPA can claim added value.

## Phase 1 — dataset atlas

The first builder is:

`analysis/therapeutic_perturbation_etl/scripts/build_perturbation_etl_atlas_v1.py`

It consumes the existing Stage81A1C-P registries and produces:

- physical asset authentication table;
- study-level readiness table;
- machine-readable ETL summary;
- SHA-256 output manifest.

Use metadata-only mode for repository reconnaissance. On the GPU/Windows project disk, run with `--require-physical` to require every recorded asset to exist with the exact frozen size and SHA-256.

## Next ETL layers

After physical authentication:

1. resolve archive members and exact matrix orientation;
2. reconstruct stable feature identities without fuzzy aliases;
3. reconstruct guide/protospacer -> cell assignments where the source supports them;
4. classify non-targeting / positive / perturbation controls;
5. freeze sample, donor/line, lane, batch, time, dose, context and replicate fields;
6. distinguish measured zero from unmeasured/absent feature;
7. define canonical perturbation IDs without collapsing CRISPRi, CRISPRa, genotype, pharmacology or noncoding perturbations;
8. compute exactly-once cell/sample accounting and duplicate checks;
9. build control-relative intervention-effect tables;
10. only then qualify JEPA-state analysis and compound/morphology matching.

## Scientific firewall

This lane does not:

- train or unlock V5 JEPA;
- inspect protected FULL104 outcomes;
- use pathology to adapt ETL or thresholds;
- call a perturbation therapeutic because it reverses an embedding;
- merge microglia, macrophage, HMC3, organoid, bulk and cell-line systems into one population;
- treat historical in-silico perturbations as causal effects.

Therapeutic claims require independent intervention and functional evidence downstream.
