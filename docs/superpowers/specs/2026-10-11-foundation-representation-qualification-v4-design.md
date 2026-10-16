# Foundation Representation Qualification V4 — Prospective Design

Date: 2026-10-11

## Purpose

Convert the already-preserved, pathology-blind Stage81A3 foundation-state evidence into a current, fail-closed qualification surface without silently promoting historical conclusions to production authority or rerunning expensive raw-data work merely because the evidence was archived.

This package is prospective governance/engineering. It does not authorize JEPA training, TEST/Morabito, pathology, target selection, target-discovery value reads, Stage4/500K, or a production representation freeze.

## Existing evidence to reuse, not duplicate

The repository already contains:

- `foundation_state_stability.py`: principal angles/canonical correlations, axis matching and eigengaps;
- `foundation_uncertainty_mechanics.py`: nested evidence masks, state deficits and count-depth thinning;
- `foundation_transfer.py`: donor-firewalled transfer and support distance;
- `foundation_domain_support.py`: separate measurement-distance and biological-support axes;
- `observation_process.py`: physical observation descriptors and explicit provenance-ID exclusion;
- a preserved Stage81A3 execution report and supporting tables over 36 matrices and a donor-balanced TRAIN-only sample.

The V4 package re-adjudicates those preserved results under current firewalls. It does not call the historical result current production authority.

## Scientific questions and prospective rulings

### 1. Basis/subspace stability

Use the preserved donor-balanced/leave-group-out stability evidence. A stable subspace with unstable individual axes must be classified as `SUBSPACE_ONLY`; coordinate-specific biological uncertainty is not allowed.

### 2. Biological-evidence versus measurement-depth uncertainty

Biological evidence and measurement quality remain separate interventions:

- evidence: nested fractions of molecular evidence;
- measurement: count-depth thinning of the same evidence.

A current receipt may acknowledge preserved evidence that the responses are distinct, but must not infer more than the preserved report supports.

### 3. Transfer ladder

The current ladder is ordered:

`held-out donor -> held-out matrix -> held-out dataset/study -> held-out technology`.

A production representation freeze requires all required levels to be qualified. Strong dataset/technology transfer cannot erase weak donor/matrix transfer.

### 4. OOD/domain support

Keep two independent support axes:

- measurement-domain distance;
- biological-support distance.

Do not collapse rare biology into a generic technical-OOD score.

### 5. Observation operator

Allowed measurement descriptors have physical/experimental meaning: assay/sc-vs-sn/platform/chemistry, measurement mask/vocabulary, sequencing depth/detected-feature quality, count-split noise and documented acquisition properties.

Forbidden model inputs include donor identity, arbitrary matrix identity, dataset identity, specimen/sample identity, pathology and target-discovery identity.

### 6. Production sampling

Freeze a hierarchy before real training:

`dataset -> donor -> cell`.

Dataset and donor masses use bounded sublinear size weighting `N^alpha`, with `0 < alpha < 1`, supplied explicitly by a prospective configuration. No biological outcome may be used to tune alpha. Conditional cell mass is uniform within donor unless a separately reviewed lawful cell-weight contract exists.

### 7. Resource/data-path guard

Full-registry dense materialization is not a default. Real analysis/training paths must estimate dense memory before allocation and prefer compact authenticated caches containing only selected columns plus lawful row-level covariates/indices. Historical Stage81A3 runtime measurements are evidence about that historical job, not a production resource guarantee.

## Fail-closed current state

The requalification receipt must always carry:

- `training_authorized=false`;
- `target_discovery_value_read_authorized=false`;
- `test_or_morabito_accessed=false`;
- `pathology_accessed=false`;
- `stage4_authorized=false`.

Current V79 factorial outputs and provisional Macha outputs are not inputs to this package.

## Completion definition

This engineering lane is complete when:

1. historical-report requalification is executable and fail-closed;
2. hierarchical sampling weights are executable and tested;
3. resource/dense-allocation guard is executable and tested;
4. focused CI passes;
5. an independent audit records exactly which scientific questions are already supported historically and which remain blocked;
6. target-discovery audit/handoff surfaces are cross-linked without changing their value-read authority.
