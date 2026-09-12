# JEPA new-chat handoff — dataset-first current state

Date: 2026-09-12

Status: `DATASET_FIRST_V5_PRODUCTION_QUALIFICATION_IN_PROGRESS__NO_TRAINING_AUTHORITY`

Repository: `dushyant-mishra/sea-ad-jepa-agent`

Active successor branch: `planning/v5-dataset-first-production-closure-20260912`

Branch head at handoff creation: `79feb8d6e38d9660faae8aebc17bfad8dd24477e`

Latest decision-bearing code head independently verified by GitHub Actions: `8683686bc138987cf6baa3662e7864f4c489db8c`

Verified workflow run: `34675056754` — `103 passed in 4.26s`; authority-source compile PASS.

This file is a startup pointer. The detailed current authorities are the referenced files below and must be re-fetched before execution.

## First actions in a new chat

1. Re-fetch the live successor head; do not assume the SHAs in this handoff remain current.
2. Read `START_HERE.md`.
3. Read:
   - `docs/superpowers/specs/2026-09-12-v5-dataset-first-production-closure-design.md`
   - `docs/agent/V5_DIMENSION_NUMERIC_AUTHORITY_BLOCKERS_20260912.md`
   - `docs/agent/V5_FULL104_HISTORICAL_PRODUCTION_RECOVERY_20260912.md`
   - `docs/agent/V5_FULL104_REMOTE_BINDING_EXECUTION_20260912.md`
   - `docs/agent/TEACHER_STUDENT_V5_DATA_FIRST_DESIGN_20260908.md`
   - `docs/agent/TARGET_DISCOVERY_TO_V5_INTEGRATION_CONTRACT_V1.json`
4. Preserve `repair/v5-qualified-target-guard-20260911`; do not overwrite it.
5. Training, reader-validation, reader-oracle, pathology and protected outcomes remain closed.
6. Re-fetch execution-critical hashes from the live authority files rather than copying them from chat prose.

## Governing principle

`DATA -> SUPPORT/ESTIMABILITY -> SCIENTIFIC ESTIMAND -> PRODUCTION GEOMETRY -> MODEL`

The pipeline is built around the real dataset; the dataset is not forced into historical mechanics/model geometry.

## Critical historical recovery

FULL104 is not an unbuilt dataset. Historical work already materialized and exercised the production reader-fit substrate:

- 4,553,407 cells
- 104 donors
- 42 operators / matrices
- 8,915 Level-4 expression blocks
- 41,238 addresses
- 17,186 common measured-core addresses
- 1,400 donor×operator groups

Historical physical root:

`outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/`

Historical full-population ALL execution completed. Final old shared-state adjudication ran 4,108 fits with 640 exact production/independent support rows. Historical terminal was `TEACHER_BIOLOGY_LIMIT` for that old shared-state estimand only; it is not current V5 numeric-D authority and does not mean the corpus lacks biology.

Therefore the current FULL104 task is:

`RECOVER/LOCATE EXISTING BYTES -> VERIFY -> CURRENT-V5 REBIND`

not rematerialization from scratch. Do not rebuild the 4.55M-cell store if the historical bytes are recoverable and valid.

## Current successor work already completed

- stale 42-shard / 4,726-row TRAIN cache is fail-closed for FULL104 production authority;
- production FULL104 closure requires `PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`;
- canonical artifact serialization/hash/parent binding implemented in `artifact_binding_v1.py`;
- explicit FULL104->dimension interface implemented in `full104_dimension_interface_v1.py`;
- authenticated metadata SQLite and historical materialization parents are pinned by current interface;
- remote heavy-data rebinding contract is frozen in `V5_FULL104_REMOTE_BINDING_EXECUTION_20260912.md`;
- missing `derive_full_stream_dimension_family_v1.py` now exists for prospective selection mechanics;
- D_shared selection explicitly includes held-donor predictability and uses contiguous support + one-SE rule;
- dimension firewall bug fixed so selected D_shared may be smaller than longest jointly supported prefix;
- D_private prospective candidate rule exists; zero lawful; incremental operator-native biology only;
- D_obs prospective candidate rule exists; held-operator observation reconstruction only; no source/matrix target;
- dimension metric/selection provenance implemented in `dimension_metric_artifact_v1.py` so caller-authored rows cannot become authority without execution/FULL104 parents;
- row-identity-only closure can no longer substitute for physical FULL104 expression closure.

## Current blockers to numeric production dimensions

1. Recover/rebind the existing historical FULL104 heavy store on the GPU laptop/attached drive.
2. Implement real current-V5 full-stream metric executors; existing selector functions do not compute metrics from expression.
3. Prospectively freeze an executable Monte-Carlo / donor-resample precision rule before viewing new V5 dimension outcomes. Historical 256/999/1000 counts are not authority.
4. Independently review the prospective D_private and D_obs rules before a numeric freeze.

Required current-V5 D_shared metrics include full-refit matched-null signal, donor-resampled subspace stability, held-donor cross-view predictability + SE, independent view/sketch agreement, and measurement-shortcut increment. Selecting nulls preserve donor, operator, Q_DEPTH, Q_DETECT, and support/measurability.

D_private starts only after D_shared freezes and uses held-donor increment, held-operator increment, measurement-shortcut increment, and same-cell technical stability. D_obs uses held-operator reconstruction of lawful observation descriptors and makes no biology claim.

## Reuse historical FULL104 engineering before rewriting

Audit `docs/history/full104_v014_20260826/03_phase2_state_derivation_v1/` and the old executor implementation before new metric code. Reuse lawful engineering patterns where semantics match:

- block-major full-population streaming;
- sufficient-statistic accumulation;
- deterministic matched-null machinery;
- restart/checkpoint and batch-boundary recovery;
- ALL execution;
- independent reconstruction;
- numerical-integrity checks;
- immutable scientific manifests and monitoring-sidecar exclusion.

Do not promote superseded scientific shortcuts: cap-4 strata, fixed rank-32, fixed 256 replicates, or old numeric D results.

## Runtime / anti-cheat state

Optimizer/target guard already includes resident deny-by-default optimizer hooks, exact schedule cursor at step time, stale/missing authorization burn, AMP path coverage, disarming of uncompleted calls, guard residency, and actual target-root binding. Same-cell cosine edge cases already cover zero/tiny/extreme/scale cases. Replay/red-team these; do not redesign without a failing test.

Validator-only anti-cheat reports still need executable evidence producers. Each decision-bearing gate must accept a minimally valid control and reject a minimally invalid control at exact adjudication geometry, with raw output hashes. Attack donor/operator/source/depth/library/specimen/same-cell/shared-view/duplicate/lookup/technical-only/biology-corrupted/technology-perturbed shortcuts, preferably donor-held-out.

## Production GPU / scientific activation

True production-geometry CUDA runner is still missing. Build only after FULL104 + numeric dimensions + schedule/proposal/packing close. It must prove protected gradients, Adam moments, motion beyond decay, EMA chronology, optimizer guard/cursor/AMP behavior and atomic checkpoint/telemetry. Historical 128x8 evidence is regression-only.

Correct scientific chain:

`existing FULL104 -> current V5 rebind -> current V5 metrics -> dimensions -> schedule/proposal/packing -> executable anti-cheat -> production CUDA -> bounded qualification -> lawful base EMA teacher -> TD60 -> partial-evidence relational student -> triplet/view policy -> independent review`

Relational objective remains inactive until lawful base teacher + TD60. TD60 retains exact frozen TD57B/TD59 semantics and requires 24/24 global + 24/24 mesoscale = 48/48.

## Parallel T0

T0 is separate. Broad immune result stands; rare tail is `RARE_TAIL_UNDERDETERMINED_MEASUREMENT`; V21 effect transport remains open. T0 must not supply the V5 biological target or block all main JEPA progress.

## Immediate next work

1. Re-fetch live successor head and review any newer pushes.
2. Audit old FULL104 executor machinery for reuse.
3. Freeze prospective Monte-Carlo precision/error-budget authority before current V5 numeric outcomes.
4. Implement real current-V5 full-stream metric executors under TDD.
5. Recover/rebind historical FULL104 heavy bytes when the GPU-laptop drive is accessible.
6. Continue small auditable GitHub commits and iterative RED/GREEN/self-review.

Permanent boundaries: no training; no protected outcomes; no TRAIN/50K substitution for FULL104; no cap-4/rank-32/historical-replicate promotion; no nearest-third production locality; no automatic nearest-half locality; no historical u40 biological clock; no self-attested gate booleans; no arbitrary artifact SHA; no relational activation before lawful base teacher + TD60 + student qualification.