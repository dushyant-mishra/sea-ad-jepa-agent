# Claude handoff — begin D1 real-data parameter derivation implementation

Date: 2026-09-07

## Branch and scope

Work only on:

`planning/d1-biological-estimation-atlas-20260907`

Before editing, fetch the branch head and verify the new D1 authority files are present. Do not modify C2, F1-A, T0 V19, the frozen F1-B attack authority, or the repaired F1-B/C3 successor branch.

D1 remains a discovery/estimation lane. This task does **not** authorize real trained-model D1 execution before a mechanically healthy trained teacher exists.

## Read first, completely

1. `docs/agent/D1_BIOLOGICAL_PROGRAM_ESTIMATION_RANKING_ATLAS_20260907.md`
2. `docs/agent/D1_REAL_DATA_PARAMETER_DERIVATION_AUTHORITY_20260907.md`
3. `docs/agent/D1_REAL_DATA_PARAMETER_REGISTRY_20260907.csv`
4. `docs/history/full104_v014_20260826/03_phase2_state_derivation_v1/preexpression_freeze/PHASE2_NUMERIC_AUTHORITY_LEDGER.csv`
5. `docs/history/contextual_teacher_target_v1_f1_nuisance_authority_recovery_20260902/F1_NUISANCE_FORMULA_CONTRACT.md`
6. `docs/v4/STAGE81A2_CANONICAL_DATA_VOCABULARY_SPLIT_FREEZE.md`
7. Current production loader / Molecular Ledger / support-mask implementation and manifests referenced by those authorities.

## Governing rule

Synthetic data may be used only for known-answer unit/mechanics tests. It may not produce any production D1 parameter value.

The historical 4,540-cell biology cohort may not produce any production D1 parameter value.

The historical 50,000-cell real discovery sample may be used for I/O, schema, throughput, and replay checks, but it may not select full-population production D, cutoffs, neighborhood scales, stability thresholds, or ranking parameters.

Production adaptive quantities are derived from the full lawful fit population:

- 104 donors;
- 4,553,407 cells;
- 42 operators;
- HVS, NPH52, SEA_AD;
- 41,238 Molecular Ledger addresses where expression/support is required.

No DEV, SEALED, pathology, reader-oracle, or held-out expression may be accessed.

## First implementation objective

Build the **derivation machinery and population firewall**, not a biological result.

Create additive v1 files. Suggested names:

- `scripts/v4/d1_real_data_derivation_core_v1.py`
- `scripts/v4/d1_full_fit_population_audit_v1.py`
- `scripts/v4/d1_teacher_state_stream_v1.py`
- `scripts/v4/d1_parameter_derivation_v1.py`
- `tests/test_d1_real_data_derivation_core_v1.py`
- `tests/test_d1_full_fit_population_firewall_v1.py`
- `configs/v4/d1_real_data_derivation_v1.yaml`

Do not put production D, rank, k, score threshold, stability cutoff, redundancy cutoff, or tail score cutoff in the config. The config may contain only procedure constants fixed prospectively, such as confidence level, numerical tolerances, deterministic RNG namespace, output schemas, minimum Monte Carlo batch, resource ceiling, and Monte Carlo precision target.

## Phase 0 — exact population/input audit

Implement a fail-closed audit that resolves the authoritative production reader and proves, before any teacher-state or expression derivation:

- exactly 104 fit donors;
- exactly 4,553,407 lawful fit cells;
- exactly 42 operators;
- exactly the three allowed source families;
- Molecular Ledger address count exactly 41,238 when molecular support is opened;
- every row maps to a lawful fit donor and operator;
- no DEV/SEALED/held-out/pathology/reader-oracle population is read;
- the exact split/registry/support/loader hashes are emitted;
- expression normalization is the existing exact CP10K -> log1p transform and is not recomputed differently.

The audit must STOP on mismatch. Do not silently filter unexpected protected rows and continue.

Expected historical population facts to verify against authority, not hard-code as a substitute for reading authority:

- fit donors 104;
- fit cells 4,553,407;
- source cell totals HVS 198,718; NPH52 236,476; SEA_AD 4,118,213;
- operators 42;
- addresses 41,238.

## Phase 1 — resolve the exact teacher-state readout seam

Trace the repaired/current teacher implementation and the already frozen F1/T0 representation semantics.

You may not invent a new cell-level representation. In particular, if the teacher exposes multiple latent slots, do not average, max-pool, concatenate, select slot 0, or otherwise collapse them unless an existing prospective authority already defines that exact operation.

Produce a small readout-contract report containing:

- source file/function/class;
- checkpoint tensor/state identity used;
- exact output shape;
- exact cell-level readout semantics;
- hashes/commit SHA;
- whether the readout is already frozen authority or requires a new prospective freeze.

If there is no unique authorized cell-level teacher state, emit:

`STOP_D1_TEACHER_READOUT_UNRESOLVED`

and stop production derivation. You may continue mechanics implementation.

## Phase 2 — implement full-population streaming estimators

Implement numerically stable, chunked/streaming calculations. Do not require a dense 4,553,407 x 41,238 materialization.

Required mechanics:

1. derive `O_d` and `n_do` from full real metadata;
2. cell weight `a_dc = 1/(|O_d| n_do)`;
3. weighted streaming mean;
4. weighted streaming covariance;
5. deterministic eigendecomposition with explicit dtype/tolerance;
6. entropy effective rank;
7. participation-ratio effective rank as a separate calculation;
8. donor/operator-preserving parallel-analysis null generator;
9. donor-block bootstrap;
10. principal-angle/projection-matrix subspace comparison;
11. near-degenerate eigengap handling;
12. fail-closed D derivation rule from the new authority.

Known-answer synthetic fixtures are appropriate for unit tests of these formulas. Every such fixture/result must be labeled `MECHANICS_ONLY` and must not write production parameter artifacts.

## Phase 3 — production D logic, but do not execute before healthy teacher

The production rule is exactly the authority document:

- derive observed full-real eigenspectrum;
- derive donor/operator-preserving real-data null envelope;
- compute `D_PA` from contiguous leading eigenvalues above the null envelope;
- compute donor-block subspace stability, treating uncertain adjacent eigengaps as a joint subspace;
- production `D` is the largest leading d <= `D_PA` whose real-data stability separates from null for every leading rank 1..d;
- no fallback D;
- report entropy and participation effective ranks only as distinct diagnostics.

For D1 v1, program count `K=D`. Do not import historical 320, 512, 50 PCs, or `2*D` rules.

If no healthy trained teacher is available, the production command must terminate:

`WAIT_HEALTHY_TRAINED_TEACHER`

with no production D file.

## Phase 4 — cell score and tail machinery

Implement, but do not run on an unauthorized teacher:

- raw program score;
- within-donor centered score;
- weighted global percentile;
- weighted within-donor percentile;
- multiresolution descriptive tail flags whose **numeric score cutpoints are computed from the full real score distribution**.

Do not collapse the full ranking into a tail-only table. No tail is a confirmatory gate.

## Phase 5 — molecular interpretation machinery

Implement a streaming, measurement-mask-aware gene/program association layer over the full fit population.

Requirements:

- exact 41,238-address identity;
- measured scalar only where lawful;
- measured zero stays zero;
- structural unmeasurement is never encoded as biological zero;
- exact CP10K->log1p values;
- donor/operator-aware effect estimation;
- full signed effect table, not thresholded genes only;
- donor-block uncertainty;
- source/operator stratification;
- effect-weighted measurement-support score from the real observation-state distribution;
- donor-specific molecular effect vectors and donor-to-global cosine recurrence;
- no pathology or known-pathway information in program fitting.

Known pathways/annotations may be joined only after the program and molecular-effect objects are frozen, for interpretation/novelty only.

## Phase 6 — ranking without tunable weights

Do not create a learned or hand-tuned weighted score.

Output separate ranks for magnitude, stability, donor recurrence, source/operator consistency, measurement support, molecular concentration/interpretability, and later novelty. Implement only a prospectively fixed deterministic lexicographic catalog order and publish every component rank.

## Historical values that must not leak into production D1 v1

Do not reuse as D1 production choices unless a new authority explicitly reintroduces them:

- 50 SVD components;
- k = 15,30,60,120;
- community resolutions = 0.25,0.5,1.0,2.0;
- candidate rank 320;
- sketch dimension 512;
- donor resamples 256;
- matched-null replicates 256;
- any synthetic-derived D/cutoff/threshold;
- any 4,540-cell-cohort-derived D/cutoff/threshold.

## Required tests before asking for review

At minimum add adversarial tests proving:

1. a synthetic known-answer covariance has correct mean/covariance/eigenvalues;
2. entropy effective rank and participation ratio are not aliased;
3. donor weights give equal donor mass and equal operator mass within donor;
4. a refusal-only implementation cannot be counted as valid;
5. non-contiguous parallel-analysis survival produces STOP;
6. degenerate eigenvalues are treated as a subspace rather than unstable individual axes;
7. a fake implementation that reads the 50k sample as production input is rejected;
8. a fake implementation that reads 4,540 biology-cohort rows as production input is rejected;
9. DEV/SEALED/pathology/reader-oracle rows cause STOP, not filtering;
10. no production parameter artifact can be written when teacher status is `WAIT_HEALTHY_TRAINED_TEACHER`;
11. no config contains a hand-entered production D/rank/k/tail-score/stability cutoff;
12. measured-zero and unmeasured expression states remain distinct in molecular association.

Run existing relevant regressions too. Do not weaken tests after seeing failures.

## First deliverable back

Commit only the implementation/audit/test scaffolding and a machine-readable status report. Do not freeze a production D or biological program yet.

Report back with:

1. branch head before and after;
2. exact files changed;
3. exact SHA-256 of each new D1 file;
4. test counts and exact terminals;
5. population audit result and exact authority hashes;
6. teacher-readout resolution result;
7. whether a healthy trained teacher is currently available;
8. any STOP condition;
9. confirmation that no synthetic/4,540/50k-derived production value was written;
10. confirmation that C2/F1-A/T0/F1-B frozen artifacts were untouched.

Do not start real trained-model D1 execution until the project explicitly reaches the healthy-teacher gate.
