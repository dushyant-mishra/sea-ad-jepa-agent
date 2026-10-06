# JEPA foundation-population estimand — V3 prefreeze

Date: 2026-10-06
Status: `PREFREEZE_ONLY__SELECTED_ESTIMAND=UNSET_REQUIRES_APPROVAL`

Purpose: define what population a future foundation model is intended to represent before optimization begins.

No estimand is selected here.

## Why this matters

FULL104 is not a simple random sample of one biological population. Sources, donors and cell counts are highly unequal. Therefore "average performance over cells" and "average performance over donors" answer different scientific questions.

The sampling/weighting estimand must be fixed before production training because changing it changes the biological population the model is optimized to represent.

## Candidate A — `CELL_WEIGHTED_EMPIRICAL`

### Target population

The empirical distribution of observed cells/nuclei in the training corpus.

### Weighting

Each cell receives equal weight.

### Biological interpretation

A randomly selected observed cell from the corpus has equal influence regardless of donor/source.

### Strengths

- simple;
- matches raw empirical cell prevalence;
- efficient for abundant states.

### Failure modes

- donors with many recovered cells dominate;
- large sources dominate smaller sources;
- technical yield/capture can become population weight;
- donor-level uncertainty can be badly understated if cell count is treated as independent biological replication.

### Donor-inference compatibility

Low unless evaluation and uncertainty are separately donor-aware.

## Candidate B — `DONOR_WEIGHTED`

### Target population

The empirical donor population represented by the corpus.

### Weighting

Each donor receives equal total weight; cells are weighted within donor so donor mass sums equally.

Conceptually:

`w(cell i in donor d) proportional to 1 / n_cells(d)`

with later normalization across donors.

### Biological interpretation

A donor, rather than an observed cell, is the primary population unit.

### Strengths

- aligns better with donor-level transport and uncertainty;
- prevents high-yield donors from dominating;
- more faithful when the scientific unit is the person.

### Failure modes

- very small donors may receive high per-cell weights;
- source imbalance remains if one source contributes many more donors;
- rare but legitimate high-cell-count biological states are not automatically represented in proportion to prevalence.

### Donor-inference compatibility

High.

## Candidate C — `SOURCE_BALANCED_DONOR_WEIGHTED`

### Target population

A deliberately source-balanced mixture, then donor-balanced within each source.

### Weighting

Each source receives prospectively fixed total mass; donors within source split that mass equally; cells split donor mass.

### Biological interpretation

The model is trained to represent each source/study approximately equally rather than reproducing empirical corpus prevalence.

### Strengths

- prevents SEA-AD or another large source from overwhelming smaller source/study populations;
- encourages cross-source representation;
- aligns with a transport-oriented foundation objective.

### Failure modes

- changes the target population away from empirical prevalence;
- a small or unusual source can receive disproportionate influence;
- source can confound technology, region, age or disease composition;
- source balancing alone does not solve donor imbalance within source unless donor balancing is explicit.

### Donor-inference compatibility

High if donor-level uncertainty remains explicit.

## Candidate D — `HIERARCHICAL_TEMPERED`

### Target population

A prospectively chosen compromise between empirical prevalence and equal source/donor weighting.

### Sampling concept

Hierarchical sampling:

`source -> donor -> cell`

with a prospectively fixed tempering rule, for example a source or donor sampling mass proportional to `N^alpha` for `0 < alpha < 1`.

### Biological interpretation

Large strata receive more weight, but sublinearly, reducing domination without forcing complete equality.

### Strengths

- flexible compromise;
- can retain prevalence information while limiting extreme imbalance;
- naturally maps to hierarchical batch construction.

### Failure modes

- alpha is a scientific estimand parameter, not a tuning knob;
- post-hoc alpha selection based on biological outcomes would invalidate the prefreeze;
- more complex to explain and audit;
- can conceal effective weighting unless every level is reported.

### Donor-inference compatibility

Potentially high if final weights and uncertainty are donor-explicit.

## Required rare-population handling

Whichever estimand is selected later must state how it treats rare populations.

Do not automatically upweight or downweight rarity based on desired downstream performance.

At minimum report:

- effective mass assigned to rare cell classes/states;
- effective mass assigned to small donors;
- effective mass assigned to small sources;
- whether rare states are rare biologically or rare because of measurement/capture;
- whether support limitations come from `D_biological_support` or `D_measurement`.

## Required reporting under any selected estimand

Future training/evaluation must report:

- exact target population statement;
- exact weighting/sampling formula;
- source weights;
- donor weights;
- effective sample size at cell and donor levels;
- maximum single-donor contribution;
- maximum single-source contribution;
- sensitivity of primary metrics to at least one reasonable alternative estimand as a diagnostic, not as a threshold-tuning device.

## Selection criteria for later approval

The later authority selecting an estimand must justify it from the intended scientific use of the foundation model, not from whichever weighting makes evaluation metrics look best.

The decision should explicitly answer:

1. Is the desired unit a cell, a donor, a study/source mixture, or a hierarchical population?
2. Should empirical source prevalence be preserved or intentionally balanced?
3. What amount of influence may one donor/source carry?
4. How should rare but well-measured biology be represented?
5. Which weighting is compatible with the planned donor-level uncertainty and transport claims?

## Current state

`selected_estimand = UNSET_REQUIRES_APPROVAL`

No candidate is the default.

## Non-authority statement

This document authorizes no training, sampling schedule or production batch construction.

`TRAINING=OFF`; Stage A remains prefreeze only; TEST sealed; Morabito protected.
