# JEPA project consolidated state — 2026-09-07

Status: `CONSOLIDATED_COORDINATION_SNAPSHOT__NO_EXECUTION_AUTHORITY`

Purpose: preserve the work completed across the parallel 2026-09-07 lanes without modifying any frozen authority and without colliding with active Claude work.

This document is a coordination snapshot. Exact authority remains on the source branch/commit/package root named below.

## Critical distinction: training population versus D1 discovery population

Two different lawful populations are in play and must not be conflated.

### Healthy-teacher training base

The prospective training base is frozen to the existing reader-fit training inventory:

- 104 reader-fit donors;
- 3,292 training cells;
- 26,240 cap-8 scheduled presentations through u205;
- no reader-validation, reader-oracle, development, sealed, external, continuation expansion, or pathology access.

### D1 full-real discovery/parameter derivation

Production D1 data-adaptive quantities are to be derived from the complete lawful fit expression/state population:

- 104 fit donors;
- 4,553,407 fit cells;
- 42 operators;
- HVS: 198,718 cells;
- NPH52: 236,476 cells;
- SEA_AD: 4,118,213 cells;
- 41,238 Molecular Ledger addresses when molecular support/expression is required.

Synthetic fixtures, the 4,540-cell historical biology-evaluation cohort, and the 50,000-cell real discovery archive may not determine production D1 adaptive values.

## Lane registry

### 1. Population-access / sealed-holdout governance — frozen

Branch: `planning/sealed-holdout-registry-20260907`

Freeze commit:
`14c2d586239aa5af15ed7cd70fdfb196d1c99f5f`

Package root:
`e9903bbb9d56663790f5f5b298c5633d87a71548466089e7cc6aae7c45728ee7`

Terminal:
`PASS_POPULATION_ACCESS_REGISTRY_FREEZE__NO_NEW_DATA_ACCESS`

Final prefreeze CI:

- run `34078297227`
- head `45107e85e253ca9569fd03245604ae8b4c93f3cc`
- 6 adversarial tests passed
- `PASS_POPULATION_REGISTRY_GOVERNANCE_INVARIANTS`

Frozen split geometry:

- foundation rows 215;
- foundation train 166;
- development 24;
- sealed_holdout 24;
- whole-study external holdout 1;
- reader_fit 104;
- reader_validation 22;
- reader_oracle 23;
- continuation/train without reader partition 17.

This registry grants no new expression, holdout, pathology, F1, T0, D1, or training execution permission.

### 2. F1-B behavioral attack authority — frozen

Branch:
`f1b-executable-attacks-20260907`

Freeze commit:
`138e176baa10267833f1a2c1e347f8831eb8c269`

Package root:
`daa79afe19ab17f1f7cfa064754d671afd4ac4b284250605979f1d288862544b`

Four frozen attack-authority files:

- `.github/workflows/f1b_attack_audit.yml`
- `scripts/v4/f1b_reference_candidates_v1.py`
- `scripts/v4/f1b_successor_attack_suite_v1.py`
- `tests/test_f1b_successor_attack_suite_v1.py`

All 15 findings have behavioral coverage via 14 attacks. Correct candidates must be DEFENDED; known-vulnerable candidates must be VULNERABLE; refusal-only behavior cannot count as a PASS.

Do not edit this frozen attack authority to accommodate an implementation.

### 3. F1-B/C3 mechanics successor — useful kernel, not final trainer

Branch:
`f1b-c3-training-successor-v2-20260907`

Head:
`c0eaf2acc0a5edc837fb2a48f726b9d626772f06`

Known mechanics result:

- 21 tests passed;
- `PASS_F1B_ATTACK_SUITE`;
- `PASS_ATTACK_POLARITY`;
- `PASS_F1B_ATTACK_REGISTRY`.

Preserved mechanics include the C2 disabled-autocast backward repair, 48 mandatory backbone gradient gates, optimizer/moment/EMA sequencing, routing/refit/control behavior and per-tensor movement checks.

Important limitation: this commit is not an end-to-end production teacher-training runner and is invalid as the final healthy-teacher execution binding.

Important unresolved semantic issue: the implementation used a fixed `MOVEMENT_OVER_DECAY_MARGIN=2.0`, but the frozen attack authority does not authorize a hard-coded 2x margin. The prospective training base therefore explicitly sets `fixed_2x_decay_margin_authorized=false`. A reviewed analytical decay-only adjudicator must be bound before execution.

### 4. Healthy-teacher prospective training base — frozen, execution unauthorized

Branch:
`planning/healthy-teacher-training-contract-20260907`

Current head:
`26e1c27d3578b794a1d522061df6d57ff435a688`

Freeze commit:
`5f89093000fe0460de377eb129890bdb0cf85a90`

Prefreeze CI-tested commit:
`33218d536e5c4ea023cb326dffcca96159fdc5f4`

Package root:
`9e1ee362773a8329f783015a04af4f7699135cc0710b1ee1ea66abc0aafd8534`

CI run:
`34114608353`

CI evidence:

- 17 adversarial tests passed;
- `PASS_HEALTHY_TEACHER_BASE_IMMUTABILITY_AUDIT`.

Freeze terminal:
`PASS_HEALTHY_TEACHER_TRAINING_BASE_FREEZE__EXECUTION_UNAUTHORIZED`

The freeze commit adds only the package-root text file and freeze JSON. The current head adds only the external-review handoff after that freeze.

High-level frozen mechanics:

- training population 104 reader-fit donors / 3,292 cells;
- address universe 41,238;
- effective batch 128;
- microbatch 8;
- 4 views;
- 40% hidden measured-address fraction;
- 16 target blocks;
- AdamW lr 1e-4, betas 0.9/0.999, eps 1e-8, weight decay 0.01;
- EMA 0.996;
- forward CUDA fp16 autocast;
- scaled backward with autocast disabled;
- mandatory 48 backbone norm/Q/K/V weight+bias gradients;
- gate after unscale and before optimizer step;
- both Adam moments required after step before EMA;
- no generic small-gradient floor;
- exactly u0->u40 mechanical qualification;
- no automatic continuation;
- u40->u205 continuation only after reviewed u40 PASS plus explicit authority;
- no biology-driven early stopping;
- no inline reader-validation/oracle/pathology.

Historical clean u0:
`19fb0c25d9f7549c37de39285807d5b6a6e828ced94af63927e83fa3c5c6b7c4`

It is a clean state source/reference only. It cannot itself be the new execution checkpoint. Historical u10-u205 are defect-inherited and prohibited for resume/initialization.

The base intentionally leaves 11 execution-binding fields null. A separate immutable `HEALTHY_TEACHER_EXECUTION_BINDING_OVERLAY_V1` must later bind the integrated reviewed successor, source root, external-review artifact/commit, new successor-specific u0 and materialization attestation, predictor registry, and movement adjudicator. Even a valid overlay is not permission to run u0->u40; explicit execution authorization is still required.

### 5. T0 V20 independent-review result — ledger-bound, real T0 unauthorized

Ledger branch:
`ledger/t0-v20-binding-20260907`

T0 binding commit:
`6e247617b3849b86df317c83479cc1497b3f0d1d`

Current ledger head:
`03df000d4a618e6ebc17629c5bd70ccc1e663cc6`

Independent-review terminal:
`PASS_T0_V20_INDEPENDENT_REVIEW`

Bound identities:

- ZIP SHA-256: `a069cad258d278bf8d97e20ba1317ccc62b93265e7f93208a2ae1a4848561947`
- package root: `896dce257b8ed7330cfe9ac9a561e6d87090903485236dbf37f389d6432cb9e7`
- V20 contract: `b8e5a38f9a158d0436d38e6846a51692f9a949580c899768c7d7507ab8646f62`
- implementation manifest: `1f55741e83bf1b504c052975649ec3a8978428b311251c9b0bd5271cf20c6b9d`
- active-test manifest: `99b9aeacea525ff06d6ab6d64aaed2fd74167795c2da21c02ef912f867fb0d6b`
- public API map V3: `4aa3a3d11d7f851b106b8a2f33e1b4b345eddbcdd1f2baaab9f30b0aff1bec2c`
- superseded registry: `ef54a8d0cc2f2e9c160e459bd8e239c20c10a0e052a369cc2ec3688096de909c`
- constants: `d15a1773469f67140de199ddcaf784b3c811c92ae7ed3f8bc4d6ab9f90252833`
- full suite: 224/224 PASS.

Meaning only:
`T0_V18_SCIENTIFIC_SPECIFICATION_PRESERVED__V20_EXECUTION_BINDING_AND_INVALID_PRECEDENCE_ACCEPTED__REAL_T0_STILL_UNAUTHORIZED`

No pathology authorization was granted. Real T0 remains blocked.

### 6. F1-A real producer/replay prefreeze — repaired and source-frozen, real execution unauthorized

Branch:
`f1-real-producer-replay-prefreeze-20260907`

Current head:
`799eb3fb04839d0ebd18667ec7fa7ddf29843e72`

Current prefreeze root:
`b324fdd917d07c41ea3defdc16644ff0cf7e6eb3a401b1331a7feb479c1869c3`

Current producer SHA-256:
`8220f80aa1249ea49295489db5d0e19c939abdc1d0fe84bece91107c38b1b0a7`

Current replay SHA-256:
`2f804e3c76ffdc6af3b4bf782fbb621f92719d170c5cadc42618137655bc17f7`

Terminal:
`PRODUCER_AND_REPLAY_SOURCE_FROZEN__REAL_F1_STILL_UNAUTHORIZED`

Required real geometry remains:

- 44,496 assignments;
- 43,108 unique teacher query forwards;
- 222,480 assignment x evidence records;
- 474,188 total expensive forwards.

Post-report re-audit found and repaired two real issues before any real biological output existed:

1. mechanics-capture coverage over all 44,496 assignments had existed only as a prose/docstring requirement, not as enforced enumeration/coverage;
2. geometry-vs-derived-count checks could fail open to `pytest.skip` on a clean extraction lacking machine-local authority paths.

Current test semantics:

- 33 passed when external authorities are reachable;
- on a clean extraction, 29 pass and 4 are explicitly `NOT_MEASURABLE`;
- `F1_PREFREEZE_REQUIRE_AUTHORITIES=1` converts those 4 unavailable-authority cases to failures rather than skips.

Superseded roots remain historically visible:

- `bd7e301c...`: 13-member root before the review handoff itself became a manifest member;
- `88cc100d...`: 14-member root before capture-coverage/fail-open repairs.

No real output root is populated. External review and explicit real-execution authorization are still required.

### 7. D1 parent planning atlas — preserved

Original D1 planning commit:
`238d3e1baef714cf52eed95e27de083df5422cb0`

Original file:
`docs/agent/D1_BIOLOGICAL_PROGRAM_ESTIMATION_RANKING_ATLAS_20260907.md`

This established D1 as an estimation/ranking/discovery layer, not a confirmatory PASS/FAIL gate.

### 8. Earlier D1-A V2 synthetic/u0-safe implementation — preserve as mechanics scaffold

Implementation branch:
`d1a-synthetic-estimation-atlas-impl-v2-20260907`

Head:
`e5f49a12b7e6f2f202a58f5bb1337dbab9b879cc`

Frozen synthetic V2 contract package root:
`6af28682da4a5c37a212ad1926fbc6acf5a7fea88c46c49f69295cbaae8a3a81`

Contract freeze terminal:
`D1A_SYNTHETIC_CONTRACT_V2_FREEZE__REAL_D1_UNAUTHORIZED`

Implementation:
`src/sea_ad_jepa/v4/d1a_estimation_atlas.py`

Known-answer generator:
`scripts/v4/d1a_synthetic_known_answer_v2.py`

Behavioral tests:
`tests/test_d1a_estimation_atlas_v2.py`

CI run:
`34116235880`

CI head:
`e5f49a12b7e6f2f202a58f5bb1337dbab9b879cc`

CI conclusion: success.

Behavioral test file contains 18 `test_*` cases. CI also compiled the implementation, verified frozen V2 contract bytes, ran the standalone known-answer diagnostic, and bound implementation bytes.

This work remains valuable for reusable mechanics:

- PCA/SVD implementation structure;
- state-direction export;
- full cell ranking preservation;
- donor/source/operator summaries;
- molecular-effect machinery;
- measurement-mask semantics;
- bootstrap/subspace utilities;
- input-root provenance;
- protected-metadata refusal;
- known-answer biological-signal and measurement-artifact tests.

However, the synthetic V2 contract contains prototype constants and ranking choices that are **not production D1 authority** under the later real-data rule, including:

- explicit hand-supplied `n_components`;
- bootstrap resamples 128;
- tail fraction 0.05;
- fixed representative/top-feature counts;
- a synthetic-only priority-score product;
- prototype measurement-support R2 and source eta-squared ranking penalties.

These may remain immutable historical synthetic mechanics. They must not silently determine production D, K, cutoffs, ranking weights or resampling values.

### 9. Aborted one-commit synthetic ranking branch — superseded

Branch:
`d1a-synthetic-estimation-ranking-20260907`

Head:
`b2758044c7cad8c80307ed17f0eea1917620daf4`

Delta from the original D1 planning commit is one file:
`scripts/v4/d1a_estimation_ranking_v1.py` (367 added lines).

This was the false-start prototype begun immediately before the user restated the project rule that production adaptive values must come from the real full dataset. It is superseded for production purposes. Do not use it as D1 production authority.

### 10. D1 real-data parameter derivation authority — current planning authority

Branch:
`planning/d1-biological-estimation-atlas-20260907`

Last coordination head before Claude implementation:
`d85391c90eb1f767115e0f4d31cfaf6bff980e2b`

New additive files:

- `docs/agent/D1_REAL_DATA_PARAMETER_DERIVATION_AUTHORITY_20260907.md`
- `docs/agent/D1_REAL_DATA_PARAMETER_REGISTRY_20260907.csv`
- `docs/agent/D1_REAL_DATA_SOURCE_INVENTORY_20260907.md`
- `docs/agent/D1_REAL_DATA_DERIVATION_CLAUDE_HANDOFF_20260907.md`

The registry contains 30 explicitly classified D1 quantities.

Governing rule:

- frozen upstream semantics remain frozen rather than re-estimated;
- prospective procedure constants are fixed outcome-independently;
- every production quantity that adapts to the observed latent/biological geometry must be estimated from the complete lawful real fit population.

Production D rule:

1. compute the donor-primary weighted full-real teacher-state covariance/eigenspectrum;
2. run donor/operator-preserving real-data parallel analysis;
3. derive contiguous `D_PA`;
4. run donor-block subspace stability;
5. treat uncertain adjacent eigengaps as a joint subspace rather than forced individual axes;
6. set `D` to the largest leading rank up to `D_PA` whose real-data stability separates from the null for every leading rank;
7. no fallback D.

Entropy effective rank and participation-ratio effective rank remain separate diagnostics and do not define D.

For D1 v1, `K=D`; do not import historical 320 candidate rank, 512 sketch dimension, 50 PCs, k={15,30,60,120}, community resolutions, or 256-resample conventions as production choices.

Primary v1 has no required kNN graph. A later neighborhood-localization layer must derive k/radius/density scales from the full real teacher-state geometry under a separate prospective authority.

Molecular interpretation must use the full lawful fit expression population, exact 41,238-address observation states, exact CP10K->log1p semantics, measured-zero distinct from structural unmeasurement, donor/operator-aware effects and uncertainty, and continuous support/source/operator falsification views.

No trained-teacher D1 output is currently authorized.

## Local/session artifact inventory

Exact session-local files available during this work are recorded separately in:
`docs/agent/PROJECT_SESSION_ARTIFACT_INVENTORY_20260907.csv`

Important verified transport hashes include:

- calibration bundle:
  `07748d5bd21fe0857ccad3002fba3946d1791d25898b841d41056a3707117444`
- checkpoints.zip:
  `ab2885f98793fdb11b695371e981ca34677af83d2d196f33ff33fdf98686ef4c`
- expression.zip:
  `1098fd4c3fac7a991f2d51ac86ecd0a7ae94be9373e5cc30b9d81be392d32fd4`
- t1_checkpoint_u0200.zip:
  `0ec44d004b34d77ccc10445210fedafe5302b6482e509f9ed5752a5691c83a1c`
- split full-expression archive reconstructed SHA:
  `63239898b9c93f29c20b62b84dc9b94c2c87e3e3f2b7958b7435847e3b9541f7`

The split archive was independently reconstructed by concatenating part001+part002 and reproduced the manifest hash exactly.

## Current blockers / next actions

### Active Claude lane

Claude is to implement the D1 full-real derivation scaffolding/population firewall from the new D1 authority. It may use the previous D1-A V2 code as mechanics reference, but must not propagate synthetic prototype constants into production parameters.

The correct teacher-dependent production terminal remains:
`WAIT_HEALTHY_TRAINED_TEACHER`

until the mechanically healthy teacher and exact authorized cell-level readout seam exist.

### Healthy teacher

Before any u1:

1. obtain independent review of the frozen training base;
2. build the final integrated end-to-end successor trainer;
3. resolve predictor mandatory registry;
4. resolve reviewed analytical movement adjudicator without hard-coded 2x authority;
5. externally review that exact successor;
6. materialize and freeze a new successor-bound u0;
7. build an immutable execution-binding overlay bound to the training-base root;
8. obtain separate explicit u0->u40 execution authorization.

### D1 real execution

After healthy-teacher qualification/training, bind:

- exact healthy teacher checkpoint/root;
- exact teacher readout contract;
- exact full fit-population reader/input roots;
- exact D1 derivation implementation package.

Only then compute production D/programs/rankings.

### F1-A

Current producer/replay sources need external review and explicit real-execution authorization. Real outputs remain unpopulated.

### T0

V20 implementation/review is accepted only as the scientific-specification-preserving execution binding. Real T0 remains unauthorized.

## Never silently reuse

Do not silently reuse any of these as production D1 values:

- synthetic D or n_components;
- 4,540-cell-cohort-derived geometry;
- 50k-sample-derived production geometry;
- fixed 50 PCs;
- rank 320;
- sketch dimension 512;
- k 15/30/60/120;
- resolutions 0.25/0.5/1/2;
- historical 128/256 resample counts;
- synthetic 5% tail as a production numerical score cutoff;
- synthetic priority-score weights/product;
- fixed 2x movement-over-decay threshold.

Do not resume historical u10-u205.

Do not open reader-validation, reader-oracle, foundation development/sealed, external holdouts or pathology without explicit prospective authority.

## Snapshot terminal

`PASS_PROJECT_COORDINATION_CONSOLIDATION__NO_NEW_EXECUTION_AUTHORITY`
