# JEPA measured-target and cross-modal fidelity lineage — 2026-10-07

Status: `AUDIT_CHECKPOINT__NO_EXECUTION_AUTHORITY`

## Purpose

This checkpoint reconciles the late-September teacher-target lineage that followed the failed/blocked contextual neural-target program. It separates:

1. teacher target measurability;
2. teacher biological fidelity;
3. student recoverability;
4. independent-modality validation;
5. production neural qualification.

These must not be collapsed into one score.

## Contextual Target V1 real F1 never completed

Historical Contextual Target V1 F0 passed implementation/leakage mechanics, but the planned real FULL104 F1 did not complete as a biological qualification.

The Sept-3 forensic handoff records:

- F0: PASS / CLOSED;
- F1 query design: frozen;
- 44,496 statistical assignments;
- 43,108 compute-unique cell/query pairs;
- 474,188 planned expensive forwards;
- real F1: `NOT RUN`;
- real reader/forward authority: `NOT FROZEN`;
- training: `NOT AUTHORIZED`.

It explicitly states real F1 remained blocked pending numerical and reader/forward/executor preflight.

Classification:

`CONTEXTUAL_TARGET_V1_F0_MECHANICS_PASS__REAL_F1_BIOLOGICAL_QUALIFICATION_NOT_EXECUTED`

## R5 — explicit measured q-conditioned developmental target

R5 was the first recovered historical experiment to distinguish a genuine teacher measurement from a proxy latent target.

Teacher target:

- same original cell;
- q-conditioned;
- eight non-q target genes selected on training donors only;
- target normalized only within the non-q panel;
- student receives complementary RNA with q and the teacher/evaluation panel removed;
- q is a conditioning identity, not a copied scalar target.

Executed five-fold donor-heldout developmental results:

- q-specific 32D RNA state + q-specific learned readout: heldout R2 `0.4300` overall, `0.3457` microglia/PVM;
- technical + q baseline: `0.3496` / `0.2784`;
- q-agnostic 32D state/readout: `0.2760` / `0.2022`;
- q-count-only teacher diagnostic: `0.1610` / `0.1347`.

q-specific minus technical+q averaged about `+0.0708` across 50 donor test units; all 50 donor differences were positive. This was exploratory/reused-population evidence, not prospective inference.

Classification:

`R5_QUERY_CONDITIONED_STUDENT_RECOVERABILITY_DEMONSTRATED_IN_DEVELOPMENT__INDEPENDENT_BIOLOGICAL_FIDELITY_NOT_ESTABLISHED`

## Teacher q visibility is not automatically leakage

R5 also tested whether teacher-visible q adds information about disjoint non-q outcomes:

- non-q context alone: R2 `0.3031` overall;
- non-q context + q scalar: `0.3106`;
- q scalar alone: `0.1210`.

Adding q contributed about `+0.00753` R2 and was positive in 38/40 dependent q-fold cases and all five fold means.

Therefore the historical evidence does not support a blanket rule that the rich teacher must be q-blind. The correct rule is stricter:

- q may be teacher evidence if scientifically justified;
- the supervised biological target must not be winnable by copying q;
- q-excluded teacher remains a required ablation/comparator;
- student q value remains forbidden unless explicitly part of a different approved task.

## R7/R8 — measurability and recoverability are not teacher fidelity

R7 tested separate prespecified same-assay RNA readouts for three named programs on 361 historical microglia / 50 donors / two microglial operators.

Teacher-only separate-readout R2:

- APOE: `-0.086`;
- P2RY12: `-0.095`;
- HLA-DRA: `-0.057`.

R8 then constructed a genuine same-cell non-q four-partner measured target with support-aware composition/activity/uncertainty semantics.

Student vs technical heldout R2 in the disjoint-reference diagnostic:

- APOE: `0.355` vs `0.088`;
- P2RY12: `-0.013` vs `0.018`;
- HLA-DRA: `0.119` vs `0.155`.

Interpretation:

- APOE showed an exploratory same-assay RNA recoverability signal;
- P2RY12/HLA-DRA did not consistently beat technical baselines;
- none of the three earned independent biological fidelity;
- positive student prediction of the measured anchor does not erase negative/weak teacher-fidelity evidence.

Classification:

`R8_MEASURED_TARGET_VALID_AS_DEVELOPMENTAL_ANCHOR__THREE_PROGRAMS_NOT_QUALIFIED_AS_SUFFICIENT_BIOLOGICAL_WORLD_STATE`

## R16 — normalization shortcut demonstrated physically

R16 used 84 authentic original cells, two per 42 operators, with four recorded masks each.

It demonstrated that dropping hidden gene tokens from already library-normalized RNA does not remove forbidden information if q / teacher-only partner/reference counts remain in the denominator.

Historical query-specific denominators changed otherwise identical q-swap inputs. A common 23-gene exclusion removed the tested swap artifact on this historical set.

This is a real information-flow finding, but not a universal 41K neural-reader qualification.

Classification:

`R16_HISTORICAL_NORMALIZATION_SHORTCUT_CONFIRMED__CURRENT_PRODUCTION_NEURAL_READER_NOT_REQUALIFIED`

## Independent-modality layer remained open

### Morabito GSE174367

Historical work authenticated:

- 4,126 microglial snRNA nuclei / 18 shared samples;
- 12,232 microglial snATAC nuclei / 20 samples;
- 18 shared microglial donors across modalities;
- separate nuclei, not same-nucleus pairs.

A donor-level ATAC evaluation was designed, but the later history still records it as not executed / not biologically adjudicated. Aggregate accessibility and feature coverage were inspected, so Morabito is not a pristine untouched holdout; it remains conditionally useful if endpoint/model/threshold lineage is shown independent of exposed aggregate outcomes.

### SCENIC+

Historical SCENIC+/Stage75F edges are RNA-coactivity/motif/proximity hypotheses and inference products, not independent ground truth.

### SEA-AD processed Multiome

The later pairing audit established a genuine public exact same-nucleus subset:

- 66,288 paired Multiome nuclei total, MTG only, 16 donors;
- candidate-myeloid subset: 1,594 paired nuclei, 15 donors.

But the historical handoff explicitly records that no biological RNA↔ATAC correspondence had yet been opened at that synchronization point.

### V64 Nott

V64 Nott P1S/P3/E2 work later established useful same-study ATAC/contact specificity and Nott-centered regulatory candidate structure, but this is not independent validation of the R5/R8 teacher target and must not be promoted as such.

Classification:

`INDEPENDENT_CHROMATIN_FIDELITY_FOR_TEACHER_TARGET__NOT_RECOVERED_AS_QUALIFIED_RESULT`

## Scientific consequence

The historical evidence hierarchy should be preserved exactly:

1. `MEASURED_TARGET_EXISTS` — yes, developmental R5/R8 style anchors;
2. `STUDENT_CAN_RECOVER_SOME_TARGET_STRUCTURE_FROM_COMPLEMENTARY_RNA` — yes, for some developmental targets, strongest historically for APOE;
3. `TARGET_HAS_ADDITIONAL_PRESPECIFIED_SAME_ASSAY_BIOLOGICAL_COHERENCE` — weak/negative for the three R7 programs;
4. `TARGET_HAS_INDEPENDENT_MODALITY_FIDELITY` — not qualified;
5. `NEURAL_TEACHER_TARGET_QUALIFIED` — no;
6. `PRODUCTION_TRAINING_AUTHORIZED` — no.

The key lesson is not that measured targets are useless. It is that **measurability, recoverability and biological fidelity are different gates**.

## Relation to current V3 premise governance

This history strongly supports the current V3 separation of:

- target meaning;
- component recoverability;
- transport/generalization;
- uncertainty;
- independent biological evidence.

It also supports the new audit finding that those component-level distinctions should be machine-enforced rather than collapsed into one family-level verdict.

## Boundaries

- target winner: none;
- representation winner: none;
- no historical R5/R8 program promoted to production target;
- no independent ATAC target validation claimed;
- training OFF;
- multimodal training OFF;
- Stage A execution OFF;
- TEST sealed;
- Morabito protected;
- 500K / Stage 4 not authorized.
