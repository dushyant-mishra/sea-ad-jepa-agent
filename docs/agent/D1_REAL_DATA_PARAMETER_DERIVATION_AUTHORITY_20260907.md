# D1 real-data parameter derivation authority

Status: `PROSPECTIVE_D1_REAL_DATA_DERIVATION_AUTHORITY__IMPLEMENTATION_MAY_BEGIN__PRODUCTION_VALUES_UNRESOLVED`

Date: 2026-09-07

## Scope and supersession

This document resolves one ambiguity in `D1_BIOLOGICAL_PROGRAM_ESTIMATION_RANKING_ATLAS_20260907.md`.

The D1-A synthetic/u0-safe milestone may use synthetic known-answer fixtures **only to validate estimator mechanics**. Synthetic outputs may not select, estimate, calibrate, or populate any production D1 value. The same prohibition applies to the historical 4,540-cell biology-evaluation cohort and to the historical 50,000-cell discovery sample when a quantity is intended to describe the full production discovery population.

This document does not reopen C2, F1-A, T0, the Molecular Ledger, the foundation split, normalization, or any other frozen upstream authority. It is additive D1 authority only.

## Governing production population

Every D1 quantity that adapts to observed biological or latent geometry must be derived from the full lawful foundation fit population:

- 104 fit donors;
- 4,553,407 fit cells;
- 42 operators;
- three source families: HVS, NPH52, SEA_AD;
- 41,238 Molecular Ledger addresses when expression/support is required.

The authoritative full-population counts are already recorded in `PHASE2_NUMERIC_AUTHORITY_LEDGER.csv` and independently reproduced by the calibration-bundle metadata tables.

Held-out, DEV, SEALED, pathology, reader-oracle, and other protected outcomes are excluded from D1 derivation unless a later prospective authority explicitly permits them.

The existing 50,000-cell real discovery archive is a valid real-data artifact for I/O, throughput, schema, replay, and implementation checks. It is not the production authority for selecting D, a score cutoff, a neighborhood scale, a stability threshold, a redundancy cutoff, or any other full-population adaptive value.

## Input semantics that remain frozen rather than re-derived

D1 must consume, not re-estimate:

1. Molecular-address identity and observation state from the controlling 41,238-address registry.
2. Real expression transformation: `log1p(raw_count * 10000 / full_source_library)` exactly once, while preserving measured zero versus structural unmeasurement.
3. The lawful foundation fit roster and source/operator/cell identity.
4. The exact mechanically healthy trained-teacher checkpoint once one exists.
5. The exact model readout seam used to define the D1 cell-level teacher state. Claude must not invent an averaging, pooling, slot collapse, or projection rule. If the current repaired successor does not yet freeze a unique cell-level state, this is a STOP requiring a prospective representation contract before production derivation.

The model width of 160 is an upstream architectural fact, not the value of D.

## Three classes of quantities

### Class A — frozen upstream constants

Examples: 41,238-address registry, fit roster, normalization transform, exact teacher checkpoint, exact teacher readout semantics. D1 does not tune these.

### Class B — prospective procedure constants

Examples: confidence level, numerical tolerances, deterministic hash/RNG namespace, file schemas, and Monte Carlo precision target. These are fixed before seeing D1 outcomes. They are not biological estimates and must not be selected by synthetic success.

### Class C — production data-adaptive quantities

These are the subject of this authority. Their numerical production values must come from the full real fit population and must be recorded with the exact input roots, derivation formula, diagnostics, and uncertainty.

## Primary D1 decomposition: no synthetic tuning and no overcomplete hard-code

The first D1 production implementation uses a donor-aware linear teacher-state decomposition as the primary discovery layer. Sparse rotation, nonlinear manifolds, clustering, and neighborhood-localized discovery remain optional later versions and may not silently introduce additional tuned parameters into v1.

Let `z_c` be the exact p-dimensional cell-level teacher state for lawful fit cell c. For the current architecture p is expected to be 160 only if the exact readout contract establishes that fact.

For donor d, let `O_d` be its observed operators and `n_do` its lawful cell count under operator o. Reuse the donor-primary weighting primitive:

`a_dc = 1 / (|O_d| * n_do)` for cell c in donor d, operator o.

Normalize weights across all fit cells only for numerical convenience. The denominators are computed from the full real fit metadata; no synthetic population may determine them.

Compute, by streaming over all lawful fit cells:

`mu = sum_c w_c z_c / sum_c w_c`

`C = sum_c w_c (z_c - mu)(z_c - mu)^T / sum_c w_c`

and the complete ordered eigenspectrum/eigenvectors of C. No coordinate-wise variance standardization is introduced unless separately frozen prospectively.

## D derivation

D is not `160`, not a historical hard-coded rank, not `2*d_gene`, and not a value selected on a toy cohort.

Production D is derived from the full real teacher-state population using two real-data criteria and a fail-closed combination:

### 1. Donor/operator-preserving parallel analysis

Build null replicas from the real teacher states by independently permuting each state coordinate among cells **within the same donor x operator stratum**. This preserves each coordinate's real marginal distribution and the donor/operator population while breaking cell-level cross-coordinate covariance.

For each null replica, compute the weighted eigenspectrum using the same full-population weights. For ordered component j, form the null eigenvalue envelope at the prospectively fixed confidence level.

`D_PA` is the largest leading rank for which the observed ordered eigenvalue remains above its corresponding null upper envelope. If the leading sequence is non-contiguous, STOP rather than skipping a failed axis and resuming later axes.

### 2. Donor-block subspace stability

Resample donors as blocks, carrying all of each sampled donor's lawful operator/cell rows. Recompute the weighted covariance and eigenspaces. Align only by sign for isolated eigenvectors; when adjacent eigenvalue-gap uncertainty includes zero, treat the block as a subspace and compare projection matrices/principal angles rather than forcing individual-PC identity.

For each candidate leading rank d <= D_PA, compare observed donor-bootstrap subspace overlap with the same statistic under the donor/operator-preserving null. A rank is stable only when its real-data lower uncertainty bound separates from the null upper envelope.

### 3. Production rule

`D = largest leading d <= D_PA whose donor-block subspace stability remains separated from the null envelope for every leading rank 1..d.`

If no positive d satisfies the rule, D1 emits a STOP for program decomposition. It does not insert a fallback D.

For transparency, always report entropy effective rank and participation-ratio effective rank as **distinct descriptive diagnostics**. They must never be aliased or substituted for one another, and neither alone defines D.

## Number of programs

For D1 v1, the primary unrotated program count is exactly D. There is no independent hard-coded candidate rank such as historical 320 and no `2*D` expansion.

Any sparse/rotated/overcomplete program family is a later prospective version requiring its own authority and real-data derivation.

## Component identity under near-degeneracy

Adjacent components are not assigned separate biological identities when their eigenvalue-gap uncertainty includes zero. The stable object is then the joint subspace. Individual axes inside such a block may be shown for visualization but cannot receive independent biological claims without a later prospective orientation rule.

## Cell scores and donor centering

For stable isolated program vector `v_p`:

`score_cp = (z_c - mu) dot v_p`.

For a stable multi-axis block, retain the block coordinates and subspace norm rather than inventing a preferred axis.

Within-donor centered score:

`centered_score_cp = score_cp - weighted_mean_{c in donor d}(score_cp)`.

Global and within-donor empirical percentiles are computed from the full real fit population with donor-primary weights.

## Extreme-tail views

The full continuous ranking is primary. Tail membership is descriptive only.

Do not tune a score threshold on synthetic data or the 4,540-cell cohort. Numeric tail cutpoints must be empirical weighted quantiles of the full real fit score distribution. To avoid creating a hidden single discovery threshold, D1 v1 reports a predeclared multiresolution family of two-sided tail views and records the actual real-data score cutpoints for each view. No tail view is a confirmatory PASS/FAIL gate.

## Stability and Monte Carlo resolution

Do not inherit historical values such as 256 donor resamples merely because they existed elsewhere.

Resampling count is a Class-B computational-precision quantity. Use deterministic sequential doubling from a prospectively fixed minimum until the reported CI endpoints/subspace summaries meet the prospectively fixed Monte Carlo precision target, or until a predeclared resource ceiling is reached. If precision is not achieved, report `INSUFFICIENT_MONTE_CARLO_PRECISION`; do not freeze a noisy production value.

## Neighborhood and density parameters

D1 v1 does not require a kNN graph to define the primary programs. Therefore historical fixed `k={15,30,60,120}` and community resolutions `{0.25,0.5,1.0,2.0}` are not imported as production D1 parameters.

If a neighborhood-localization layer is added later, its k/radius/density scales must be derived from the full real teacher-state geometry with donor-block stability and null diagnostics under a separately frozen prospective contract. The 50,000-cell sample may not choose those production values.

## Redundancy

Primary PCA axes are orthogonal by construction. D1 must still report molecular-loading similarity and any later rotated-program similarity continuously.

D1 v1 does not collapse programs by a hard-coded correlation/cosine threshold. If a later version needs collapse/deduplication, the cutoff must be derived from the full real-data null/stability distribution and frozen prospectively.

## Molecular interpretation from the full real expression population

Expression association is computed only where an address is physically measurable under the Molecular Ledger state.

For each program/subspace and address g, compute donor/operator-aware association using the full real fit cells and the exact CP10K->log1p values. Preserve donor identity. A valid implementation may stream sufficient statistics rather than materializing a 4,553,407 x 41,238 dense matrix.

The primary output is the complete signed association/effect table with uncertainty, not a thresholded gene list.

Program-level physical measurement support is a loading/effect-weighted real-data quantity. At minimum report:

`support_p = sum_g |effect_gp| * measured_fraction_gp / sum_g |effect_gp|`

where `measured_fraction_gp` is computed from the lawful full fit population using observation-state authority and the same donor-primary weighting. Also report source-specific and operator-specific support rather than hiding heterogeneity in one scalar.

No synthetic support distribution may calibrate this score.

## Donor recurrence and source/operator heterogeneity

For every program, derive donor-specific molecular association vectors wherever estimable. Align sign to the global program and report the distribution of donor-to-global cosine similarity, the fraction with positive aligned cosine, and donor-level score summaries.

Report source- and operator-stratified versions plus between-group heterogeneity. These are continuous D1 estimates; no hard-coded recurrence percentage is required for inclusion in the discovery catalog.

## Novelty and known-program annotation

Known pathway/gene-set annotations are interpretive and cannot define the discovered programs. Novelty may be reported only after the real-data program and molecular association objects are frozen.

Do not use novelty to select D, orient a near-degenerate eigenspace, choose a tail threshold, or decide whether a program exists.

## Ranking rule without tuned weights

D1 v1 must not invent an outcome-tuned weighted composite score.

Emit separate continuous ranks for:

1. real-data program magnitude;
2. donor-block stability;
3. donor recurrence;
4. source/operator consistency;
5. measurement support;
6. molecular interpretability/association concentration;
7. novelty (post-freeze annotation only).

The canonical catalog order is a deterministic lexicographic order defined before outcome inspection, with stable program ID as the final tie-breaker. Also publish the component ranks so the ordering is inspectable. No learned or hand-tuned rank weights are permitted in v1.

## Values explicitly prohibited as D1 production authority

The following historical values may be useful provenance but may not be copied into D1 v1 merely because they exist:

- 50 retained SVD components from the historical expression-geometry review;
- k values 15, 30, 60, 120;
- community resolutions 0.25, 0.5, 1.0, 2.0;
- candidate search rank 320;
- feature sketch dimension 512;
- donor resamples 256;
- matched-null replicates 256;
- any D, tail cutoff, correlation cutoff, density cutoff, stability cutoff, or score threshold learned from synthetic fixtures or the 4,540-cell cohort.

This prohibition does not revoke those numbers inside the historical artifacts that originally governed them. It prevents silent reuse as D1 production parameters.

## What may be implemented now

Before a mechanically healthy teacher exists, implementation may proceed outcome-blind for:

- input/hash/firewall audit;
- streaming weighted moment code;
- donor/operator-preserving null generator;
- donor-block bootstrap and subspace-comparison code;
- exact D derivation logic;
- output schemas and provenance;
- full-fit metadata/support derivations that do not require teacher states;
- known-answer synthetic tests of mathematical mechanics.

Synthetic tests must write only test fixtures/results explicitly labeled `MECHANICS_ONLY`. They may not populate production parameter files.

## Production execution stop

Actual production D, programs, cell scores, tail cutpoints, teacher-state stability, or molecular-program associations may not be frozen until:

1. the repaired F1-B/C3 successor has passed its attack suite and external review;
2. a mechanically healthy trained teacher exists;
3. the exact teacher checkpoint and exact D1 readout seam are byte/root-bound;
4. the full fit-population reader passes the population firewall;
5. all derivation inputs are frozen before biological interpretation.

Until then, the correct terminal for teacher-dependent production derivation is `WAIT_HEALTHY_TRAINED_TEACHER`.

## Required production provenance

Every derived production quantity must record:

- parameter/statistic ID;
- exact formula/algorithm version;
- full input root(s)/SHA-256;
- teacher checkpoint root;
- teacher readout contract hash;
- fit roster/split hash;
- Molecular Ledger/support hashes when relevant;
- cell/donor/operator/source counts actually consumed;
- no-protected-data audit;
- deterministic RNG namespace/seeds when stochastic computation is used;
- estimator diagnostics and uncertainty;
- final numeric value or explicit unresolved/STOP status.

No production value may be hand-entered into a config before its derivation artifact exists.
