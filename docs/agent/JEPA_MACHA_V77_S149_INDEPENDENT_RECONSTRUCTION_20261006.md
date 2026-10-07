# JEPA Macha/V77 — independent S149 reconstruction checkpoint

Date: 2026-10-06
Branch: `handoff/jepa-20261006-macha-audit-successor`
Parent handoff observed immediately before write: `dc627d728ec1522e9ddc3e0896e2a310a7428a44`
Working Macha head independently re-fetched: `a3e272ba5fcab65f3b0f613b1ba32c53df2e5ad2`
Status: `DOCUMENTATION_ONLY__TRAINING_OFF__NO_ESTIMAND_SELECTED`

## Scope

This checkpoint begins the required independent reconstruction of S149 from primary committed evidence. It does not modify V77 code, synthetic worlds, thresholds, target selection, population estimands, runtime code, Stage 4, TEST, Morabito, or any training state.

Hard boundaries remain:

- TRAINING=OFF
- STAGE_A_EXECUTION=OFF
- MULTIMODAL_TRAINING=OFF
- 500K=NOT_AUTHORIZED
- STAGE4=NOT_AUTHORIZED
- TEST=SEALED
- MORABITO=PROTECTED
- TARGET_WINNER=NONE_QUALIFIED
- REPRESENTATION_WINNER=NONE_QUALIFIED
- SELECTED_ESTIMAND=UNSET_REQUIRES_APPROVAL

## 1. Current head verification

The working Macha branch `claude/v77-synthetic-premise-custody-20261005` still resolves exactly to:

`a3e272ba5fcab65f3b0f613b1ba32c53df2e5ad2`

No post-handoff delta needed to be reconciled before this audit.

The head commit itself preserves the rehearsal limitations: seed 7302 is development/calibration, mutation proof is not established by the shared interface, q-safety is policy-only rather than execution-proven, and estimand/threshold/target/split/weights remain unset.

## 2. Primary S149 coverage-composition diagnostic

Primary result:

`results/v77/V77_REAL_COVERAGE_CONFOUND_DIAGNOSTIC_V1.json`

Result source commit:

`ef70461add57d9f2b740ee0a507ecc3f01c19389`

Primary executor:

`scripts/v77/diagnose_v77_real_coverage_confound.py`

### What the diagnostic actually computes

The executor loads the corrected TRAIN cache as one stacked cell matrix and selects the frozen 3,000-gene pooled expression-variance panel.

For each cell it infers the smallest cohort coverage capable of containing all observed detections. It then computes:

- A: pooled observed-cell topology on the frozen gene set;
- N: a coverage/composition null in which each cell retains its inferred coverage stratum and each gene retains its real per-stratum detection probability, but genes are sampled independently within stratum;
- S: topology within each inferred coverage stratum;
- G: pooled cells restricted to genes covered by all three cohort coverages.

The null therefore removes within-stratum gene-gene dependence while preserving:

- the observed number of cells in each inferred coverage stratum;
- stratum-specific marginal gene detection probabilities;
- structural-zero patterns implied by cohort coverage.

### Reconstructed pooled and null metrics

Observed pooled A:

- fraction |corr| > 0.3 = 0.6148062687562521
- median |corr| = 0.37697424394530443
- transitivity = 0.8870660483247294
- mean degree = 1843.804
- largest community fraction = 0.763

Coverage/composition-only N:

- fraction |corr| > 0.3 = 0.5462551961765033
- median |corr| = 0.3272843668581559
- transitivity = 0.8966553943940174
- mean degree = 1638.2193333333332
- largest community fraction = 0.6776666666666666

Therefore:

- N/A edge-density ratio = 0.5462551961765033 / 0.6148062687562521 = approximately 0.8885;
- N/A mean-degree ratio is the same approximately 0.8885 because degree is determined by the same thresholded edge fraction for fixed 3,000-gene width;
- null transitivity is not merely close to the pooled real value; it is slightly higher.

This independently supports the qualitative S149 conclusion that a large fraction of the old pooled detection topology can arise from measurement coverage/composition without within-stratum gene dependence.

## 3. New audit qualification: the ~89% figure is cell-mixture-specific, not a donor-population estimand

### Finding M-S149-1 — P1 scientific-interpretation limitation

The primary S149 diagnostic is cell-weighted.

Evidence from the executor:

- `load_real()` stacks all cached cells;
- the pooled gene selection, observed correlation topology and coverage-null topology are computed across rows/cells directly;
- the null draws an independent Bernoulli value for every cell × gene using the cell's inferred stratum;
- no donor-level aggregation or equal-donor weighting is performed in this diagnostic.

The inferred cell-stratum counts are:

- HVS: 3,072 cells
- NPH52: 246 cells
- SEA_AD: 1,408 cells

The later within-cohort receipt reports the corresponding donor counts:

- HVS: 62 donors
- NPH52: 19 donors
- SEA_AD: 68 donors

Thus the composition used by the ~89% calculation is materially different from equal-donor source composition. The exact 88.85% number is a property of this sampled cell mixture under the frozen pooled gene selection. It has not been shown stable to equal-donor weighting, equal-cell-per-donor sampling, or an explicitly selected population estimand.

### Classification

The qualitative claim:

`POOLED_DETECTION_TOPOLOGY_IS_STRONGLY_MEASUREMENT_COMPOSITION_CONFOUNDED`

is supported by primary committed evidence.

The stronger numerical claim:

`ABOUT_89_PERCENT_OF_THE_RELEVANT_REAL_TOPOLOGY_IS_COMPOSITION_EXPLAINED_AS_A_DONOR_POPULATION_PROPERTY`

is not established.

Current claim-ledger classification:

`SUPPORTED_BUT_NOT_A_SELECTED_POPULATION_ESTIMAND`

This does not reverse S149. It narrows the epistemic scope of the 89% statement.

## 4. Within-stratum evidence remains materially different from pooled topology

Using the original pooled gene set, the same diagnostic reports:

HVS:
- n=3,072 cells
- fraction |corr| > 0.3 = 0.07683916861175948
- median |corr| = 0.0955150310630642
- transitivity = 0.6721199430685819
- mean degree = 230.44066666666666

NPH52:
- n=246 cells
- fraction |corr| > 0.3 = 0.031228409469823276
- median |corr| = 0.046750386359602054
- transitivity = 0.4506366000243311
- mean degree = 93.654

SEA_AD:
- n=1,408 cells
- fraction |corr| > 0.3 = 0.06015827498054907
- median |corr| = 0.03694392114527012
- transitivity = 0.7053217633546778
- mean degree = 180.41466666666668

These rows are not themselves canonical within-cohort targets because they reuse the pooled gene selection, but they independently demonstrate that within-stratum topology is dramatically less dense than the pooled topology.

## 5. Audit of the proposed within-cohort replacement envelope

Primary result commit:

`6ab62c221634d7d0087a8063464744acfc4ef4c5`

Result:

`results/v77/V77_REAL_WITHIN_COHORT_ENVELOPE_V1.json`

Producer source commit:

`66bd9bed48753dd8eaae357e07a062364357688d`

Producer:

`scripts/v77/build_v77_within_cohort_envelope.py`

### Good properties verified

The producer does several scientifically preferable things relative to the pooled envelope:

- infers observation-process/coverage stratum before constructing per-stratum targets;
- assigns donor stratum by donor-level majority and reports mixed-stratum donors/violations;
- rebuilds the >5% gene universe separately inside each stratum;
- reselects the 3,000 variance-ranked genes inside each stratum;
- uses TRAIN-only, pathology-blind, read-only real data;
- keeps the pooled envelopes as historical composition-inclusive references instead of rewriting them;
- constructs the result before any synthetic world is scored against it;
- bootstraps donors rather than naively resampling individual cells.

HVS and SEA_AD are eligible under the inherited T5 cell-count floor. NPH52 is not, because no two classes reach the 200-cell floor.

### Finding M-S149-2 — P1: bootstrap clusters are donors, but the estimand remains cell-weighted

Inside each bootstrap replicate, donors are sampled with replacement, but the executor then concatenates **all cells** belonging to each sampled donor and computes topology on the concatenated rows.

Therefore donor resampling protects cluster dependence for uncertainty estimation, but it does not make the point or bootstrap statistic an equal-donor estimand. Donors with more sampled cells contribute more to the correlation/topology statistic each time they are selected.

This distinction is scientifically material because the project explicitly treats donors as biological replicates and cells as observations.

### Finding M-S159-1 — P1: nominal acceptance ranges can exclude the real point

The committed within-cohort envelope contains multiple cases where the point estimate is outside its own 5th–95th percentile donor-bootstrap interval.

Examples:

HVS:
- `t5.within_over_pooled` point = 0.7747191280512261
- accept_low = 0.827365883130477
- accept_high = 0.9097219373936616

SEA_AD:
- `t5.within_over_pooled` point = 0.809178800839818
- accept_low = 0.888079782254868
- accept_high = 0.9528620870717674

Additional SEA_AD examples include:

- detection largest-community point 0.23166666666666666 below accept_low 0.24516666666666667;
- expression median |corr| point 0.06648370528091659 below accept_low 0.0694746585473766;
- expression top-10-PC variance point 0.2793480021015319 below accept_low 0.2817799006196803;
- expression largest-community point 0.24833333333333332 below accept_low 0.24948333333333333.

The HVS result also shows expression median |corr| point 0.05454122382372603 below accept_low 0.05484297783336761.

This confirms S159 directly from the current proposed replacement target.

The pathology is not merely formatting: a percentile bootstrap interval around a resampled statistic can be shifted relative to the original sample statistic. Here that shift is large enough for several proposed acceptance envelopes to reject the real point from which they were supposedly derived.

### Finding M-S149-3 — P1: 24 bootstrap replicates are insufficiently justified as precision authority

The producer inherits `N_BOOT = 24` and 5%/95% empirical quantiles from the earlier pooled builder because they were already frozen. The current audit found no precision calculation in this producer showing that 24 cluster-bootstrap replicates are sufficient to estimate 5th and 95th percentile acceptance boundaries with the required error tolerance.

This does not make the diagnostic useless, but it is not adequate numerical authority for a future sealed challenge without a prospective Monte-Carlo/precision rule.

## 6. Current classification of the within-cohort envelope

Allowed classification from the handoff:

`NEEDS_REPAIR`

Reasons:

1. no externally approved population estimand/source weighting has been selected;
2. point statistics remain cell-weighted even though uncertainty resamples donors;
3. S159 is directly present: several real points fall outside their own nominal acceptance intervals;
4. the 24-replicate tail-quantile precision is inherited rather than prospectively justified;
5. NPH52 is excluded by the inherited class-count rule, leaving cross-source combination unresolved.

This classification is not `NONIDENTIFYING`: the within-cohort measurements are scientifically useful diagnostics and clearly expose residual structure that pooled composition alone cannot explain.

It is not `QUALIFIED_AS_CANDIDATE_CALIBRATION_TARGET_PENDING_EXTERNAL_REVIEW` yet because the interval construction itself requires repair before the object can function safely as an acceptance target.

## 7. Claim ledger update

### REPRODUCED

- the pooled observed detection point is reproduced exactly by the S149 diagnostic;
- a no-within-stratum-dependence null with real stratum composition and marginal detection rates recreates approximately 88.85% of the pooled thresholded detection edge density / mean degree;
- null transitivity is slightly greater than pooled real transitivity;
- within-stratum dependence is dramatically sparser than pooled dependence;
- the proposed within-cohort producer redoes gene selection inside cohort/coverage stratum;
- S159 point-outside-envelope behavior exists in the committed proposed replacement target.

### SUPPORTED_BUT_NOT_INDEPENDENTLY_REEXECUTED

- exact byte-for-byte numerical generation of the receipts from the original local TRAIN cache, because the underlying 42 local count shards are not present in this audit environment;
- the reported absence of mixed donor strata and stratum-coverage violations, pending direct local-shard replay.

### SUPERSEDED

- pooled topology as a biological calibration target;
- any old DR/sub-state biological conclusion whose threshold was defined by that pooled topology;
- any implication that the old pooled dynamic range is biologically selected.

### NONINFORMATIVE FOR POPULATION ESTIMAND SELECTION

- the exact 88.85% ratio by itself;
- current HVS/SEA_AD within-cohort acceptance limits by themselves.

### INDETERMINATE / OPEN

- donor-equal or otherwise selected-population version of the S149 composition-null fraction;
- equal-cell-per-donor sensitivity;
- source-balanced S149 sensitivity;
- final HVS/NPH52/SEA_AD combination rule;
- S159 repair choice;
- bootstrap replicate-count precision authority;
- selected real calibration estimand.

## 8. Cross-lane implications

### Shared qualification interface

No interface defect is inferred from S149 itself. However a future qualification interface should bind an explicit estimand identity, biological replicate unit, weighting rule and observation-process stratum definition rather than accepting an opaque calibration-envelope path.

### S149 target-salvage / observation-operator framework

This audit strengthens the principle:

`biology within observation process + transport across observation process`

It does not justify regressing out study or forcing study invariance. The current S149 result shows that observation-process composition can generate large topology even with no within-stratum biological dependence.

### Runtime lane

No runtime conclusion changes. Physical mutation proof and executed transitive q-safety remain separate open requirements.

### Future real-RNA qualification

Do not freeze synthetic challenge thresholds from `V77_REAL_WITHIN_COHORT_ENVELOPE_V1.json` in its current form.

## 9. Smallest prospective next sequence

Training remains OFF.

1. In the real-data scientific lane, prospectively select the population estimand and biological replicate weighting before examining new synthetic outcomes.
2. Recompute S149 A/N sensitivity under at minimum:
   - current cell weighting;
   - equal donor weighting or donor pseudobulk-equivalent weighting appropriate to the statistic;
   - equal-cell-per-donor sampling;
   - a prospectively declared source-combination rule.
3. Rebuild within-cohort point statistics under the selected estimand.
4. Replace or repair S159 interval construction so the real point is not accidentally excluded merely by bootstrap shift; predeclare the rule before synthetic scoring.
5. Derive bootstrap/Monte-Carlo replicate counts from a prospective precision/error budget rather than inheriting 24.
6. Re-audit NPH52 treatment and decide whether lack of two >=200-cell classes should exclude the entire cohort from all calibration statistics or only from T5-dependent endpoints.
7. Only after these are frozen should a fresh, uninspected synthetic development/challenge realization be generated.
8. Run the smallest zero-mutation challenge first.

No sealed or confirmatory claim is authorized by this checkpoint.
