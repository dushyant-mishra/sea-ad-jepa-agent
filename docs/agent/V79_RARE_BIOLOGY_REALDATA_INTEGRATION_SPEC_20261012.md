# V79 real-data-matched rare-biology integration spec

Date: 2026-10-12
Status: `PROSPECTIVE_DESIGN__NOT_EXECUTION_AUTHORITY`

## Purpose

Restore the project's established rare/private biology objective on top of the already-qualified V79 measurement/nuisance machinery without modifying or regenerating Q00-Q11.

This is not a new biological goal. Historical project work already required rare5/rare1, weak/local/sparse/private biology, donor-disjoint evaluation, uncertainty under partial evidence, and explicit rare-biology vetoes. The defect was that V79 V2_CORE narrowed to gene-wise observation-model qualification and did not carry a cell-level rare biological truth forward.

## Non-negotiable separation

### Layer A — V79 V2_CORE observation qualification

- frozen Q00-Q11;
- Bernoulli detection + lognormal positive magnitude;
- depth/class/source/donor handling;
- structural missingness;
- sparse detection/tails/imbalance/omitted operator;
- no cell-level multimodal rare biological truth.

Passing Layer A does not qualify rare biology.

### Layer B — rare biological truth

New additive synthetic family. The truth object is a donor-structured cell program, not a rare marginal gene.

### Layer C — teacher/student qualification

The teacher must preserve/discover the planted rare state. The student must recover it when RNA evidence is sufficient and express uncertainty/abstention when the relevant evidence is teacher-private or genuinely absent.

Training remains OFF until all required layers have their own authority.

## Real-data constraints that define the synthetic family

See `results/v79/rare_biology_integration/V79_RARE_BIOLOGY_DATASET_CAPABILITY_MATRIX_20261012.csv`.

1. FOUNDATION RNA is the main population-calibration substrate: many donors/operators and the frozen 41,238-address measurement contract.
2. Morabito supports donor-level RNA/ATAC concordance only because RNA and ATAC are separate nuclei.
3. GSE214979 supports conditional same-nucleus RNA+ATAC correspondence.
4. GSE272082 can be a secondary paired-multiome transport set only after the remaining authentication gap is closed.
5. SCP2167 plus eligible Fang STG MERFISH provides an already-identifiable real context route.
6. Stage75-79/cisTarget assets can define realistic regulatory topology/annotation but are not causal truth.
7. GSE178317 can calibrate perturbation response/support but cannot define the latent rare state.

## Latent biological object

For a selected lineage such as microglia, each synthetic donor d receives a latent program propensity `pi_d`.

For cell i from donor d:

`R_i ~ Bernoulli(pi_d)`

where `R_i` is biological state membership/activity. `pi_d` is allowed to vary strongly across donors, including exact zero in some donors. Donor recurrence is prospective truth, not a post hoc filter.

The biological state produces a coherent program:

- RNA module effect;
- regulatory/ATAC module effect;
- optional context dependence;
- optional perturbational response.

Technical variables do not cause R. Source/operator/depth can change how R is observed.

## Required program families

### RB00 — recurrent RNA-recoverable

Purpose: canonical real rare biology.

- rare1-like and rare5-like prevalence regimes;
- present across multiple donors;
- heterogeneous donor prevalence;
- coherent RNA module sufficient for recovery under adequate evidence;
- regulatory module concordant with RNA but not required for basic student recovery.

### RB01 — teacher-private regulatory rare state

- weak/subtle RNA signal;
- stronger planted regulatory/ATAC signal;
- rich teacher recovers R;
- partial-RNA student should become uncertain rather than confidently invent R.

### RB02 — technical pseudo-rare twin

Frequency matched to RB00/RB01 but `R=0` biologically.

Plant one or more observation-side anomalies:
- low/high depth;
- source/operator shift;
- dropout/detection shift;
- ATAC quality/accessibility artifact;
- spatial density/context artifact.

The system must reject these as biological state.

### RB03 — donor-restricted real biology

- true program present in a subset of donors;
- absent in others by truth;
- state is legitimate biology, not automatically a batch/domain error;
- prevents correction machinery from erasing real donor heterogeneity.

### RB04 — donor-level RNA/ATAC concordance

Morabito-matched world:

- RNA nuclei and ATAC nuclei are separate samples from a shared donor-level latent program;
- no same-cell pairing in the truth surface exposed to evaluation;
- primary endpoint is donor/program-level concordance and transport.

### RB05 — same-nucleus multiome

GSE214979-matched world:

- RNA and ATAC observed from the same synthetic nucleus;
- used to test cell-level multimodal state correspondence;
- separate from RB04 so the simulator does not overstate what Morabito can validate.

### RB06 — context-conditioned rare state

Spatial-matched world:

- intrinsic R variant: neighborhood does not affect R;
- context-conditioned variant: neighborhood changes `P(R)` or program amplitude;
- true physical-neighbor context can help only when biology supports it;
- shuffled/random/distant matched context must not help equivalently.

### RB07 — perturbation-response support

- intervention changes amplitude or direction of an already-defined program;
- perturbation is an orthogonal consistency test, not the definition of R;
- matched null intervention required.

## Regulatory topology

Do not generate rare RNA genes independently.

Use a frozen program topology template derived from existing Stage75-79/cisTarget evidence:

`regulator -> enhancer/motif-supported elements -> target module`

Allowed use:
- module size and sparsity;
- overlap between regulators;
- target-weight heterogeneity;
- motif/edge annotation;
- matched graph controls.

Forbidden use:
- treating historical coactivity sign as validated activation/repression truth;
- calling the frozen graph a causal GRN;
- selecting a program from protected external outcomes.

The first implementation should include at least one coherent regulatory module and a degree/size-matched random-module control.

## Empirical calibration rules

The existing 50K 41K-address TRAIN discovery sample and exact V6R5A weights were reverified read-only in `V79_REALDATA_RARE_PROGRAM_ASSIMILATION_20261012.md`.

Important result: the historical innovation/rare direction is strongly source-shifted in the heterogeneous 50K sample. Therefore:

- do not define new rare truth by globally thresholding `innovation_tail`;
- do not set donor prevalence from that score alone;
- use empirical summaries only to choose realistic ranges after controlling lineage/source/operator;
- freeze calibration rules before examining protected external outcomes.

Required calibration summaries before realization:

1. lineage-restricted cell counts per donor;
2. donor prevalence distribution for candidate RNA modules;
3. source/operator conditional score distributions;
4. RNA module effect-size distribution;
5. measurement-depth sensitivity;
6. module support/measurement fraction;
7. regulator-target module size/overlap;
8. expected ATAC-vs-RNA relative signal strength from lawful development data only.

No pathology fields are permitted for these calibration summaries.

## Teacher/student evidence ladder

For the same synthetic cell, create prospectively frozen evidence levels such as 20/40/60/80/100% lawful RNA evidence. Separately create measurement-depth levels such as 25/50/75/100% of the same underlying information.

These answer different questions:

- evidence ladder: how much biological information is needed before state stabilizes?
- depth ladder: how sensitive is inference to measurement quality?

Do not collapse biological uncertainty into measurement uncertainty.

## Hard qualification families

Rare biology can never be hidden in one aggregate score.

Required independent gate families:

1. teacher discovery/preservation of R;
2. teacher rejection of pseudo-rare technical twins;
3. student recovery when RNA evidence is sufficient;
4. student uncertainty/abstention when R is underidentified from RNA;
5. donor recurrence/generalization;
6. donor-restricted real-biology preservation;
7. source/operator/depth shortcut control;
8. same-nucleus RNA/ATAC correspondence in RB05;
9. donor-level separate-nucleus RNA/ATAC concordance in RB04;
10. spatial true-neighbor advantage over shuffled/distant controls in RB06;
11. regulatory-module recovery versus matched random graph/module controls;
12. perturbation-response consistency in RB07;
13. rare1-like and rare5-like results reported separately;
14. evidence-response and measurement-depth curves reported separately.

A hard rare-program failure cannot be rescued by a broad/common-state average.

## Blinding and trust domain

Before realization, freeze:
- world family definitions;
- prevalence regimes;
- donor recurrence rules;
- module topology templates;
- evidence/depth ladders;
- negative controls;
- gate definitions;
- seed derivation;
- truth/controller custody.

Fit/student processes must not see:
- rare-world names;
- R labels;
- planted program identities beyond lawful inputs;
- pseudo-rare truth class;
- scoring outcomes.

Controller truth remains physically separate, following the V79 trust-domain pattern.

## Relationship to current V79 campaign

Q00-Q11 are immutable and still useful. This spec does not change their contract, worlds, realization or scorer.

The repaired engineering benchmark at evidence commit `586e5ea5af73bbc28637a4cbab0eb7c108c67d42` completed 4/4 fits with a projected 1.52 h campaign runtime. That evidence supports engineering feasibility only. It does not close the rare-biology gap.

A future controller may authorize Q00-Q11 fitting as Layer A while this rare-biology family is built in parallel. Neither Layer A nor Layer B alone authorizes JEPA training.

## Immediate implementation order

1. freeze this real-data capability matrix and assimilation report;
2. build TRAIN-only empirical rare-program calibration summaries from already-existing caches;
3. recover exact Stage75-79 module topology needed for one initial coherent module plus controls;
4. write the prospective rare-world contract with fixed ranges/seeds/gates;
5. implement generator tests first;
6. realize new rare worlds exactly once only after controller approval;
7. implement teacher/student scorer and falsifiers;
8. map each synthetic gate to its lawful real validation asset.

## Current terminal

`V79_LAYER_A_ENGINEERING_BENCHMARK_PASS__Q00_Q11_FITS_STILL_REQUIRE_CONTROLLER_AUTHORITY__RARE_BIOLOGY_LAYER_REQUIRED_AND_NOW_SPECIFIED__NO_NEW_ETL__NO_PATHOLOGY__NO_TRAINING`
