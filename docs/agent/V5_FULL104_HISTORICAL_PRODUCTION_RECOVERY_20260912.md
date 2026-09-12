# V5 FULL104 historical production recovery — 2026-09-12

Status: `HISTORICAL_FULL104_PRODUCTION_PREPARATION_CONFIRMED__CURRENT_V5_REBINDING_REQUIRED__NO_TRAINING_AUTHORITY`

## Purpose

This document records a 2026-09-12 historical-work discovery that corrects an overly pessimistic interpretation of the current FULL104 blocker.

The production dataset was **already prepared historically**. The present V5 work does not begin from an unmaterialized 4.55M-cell dataset. The immediate task is to recover/locate the historical heavy bytes, verify them against the frozen provenance chain, and bind those same bytes into the current V5 authority graph.

## What was historically completed

The recovered production lineage is rooted under:

`docs/history/full104_v014_20260826/03_phase2_state_derivation_v1/`

and references the historical physical expression root:

`outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/`

Production geometry recorded by the historical authority:

- reader-fit cells: `4,553,407`
- donors: `104`
- operators: `42`
- matrices: `42`
- Level-4 expression blocks: `8,915`
- molecular addresses: `41,238`

The materialization package preserves exact provenance for the physical store.

### Frozen expression-materialization parents

- block manifest:
  `66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29`
- materialization contract:
  `612b45742ad80498cbe2f061a75af08c0a10692dc731e0ac8e649417b7e62f17`
- materialization audit:
  `9fa0ede3135a606bb1fe4cd4cc11881c439b7726b6dec62147c1892967eba7cf`
- reader-fit selection:
  `edec0fe29d1425ecbe9fa889a610c4ce18621ae060c8144866315db57c3fc62b`
- selection manifest:
  `3db3614bf544b183143f39b27bad516b3a7a75284df4b2410d9f3e99f0b0842e`
- authenticated metadata SQLite:
  `a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913`

The historical materialization manifest also records the exact Python/R materialization scripts used to create the Level-4 store.

## Downstream production artifacts prove the store was actually used

Separate Level-4 downstream package roots are preserved:

- feature-matrix package manifest SHA-256:
  `c9a6ede6f33a4a9d4ce22cde0f1a8c0fb5e7e039bac3df364325c778487329ef`
- multiview-feature manifest SHA-256:
  `d6f70ee1bca777f3d2cbd89dd560395cc46ec25f6a648ae4ba0fd6e77c1c2cf1`

This is evidence that the historical lineage advanced beyond row selection or a planned materialization contract: the physical expression substrate fed derived production feature artifacts.

## Historical FULL104 ALL execution was completed

Repository state records a complete full-population `ALL` shared-state execution under implementation fingerprint:

`a0fe5bc7be0769c9880763b3831ea330a251dfa710a8635b05f678c5d6e94202`

Terminal run-manifest SHA-256:

`8f292673c84447ee88f3a78936aa88920b96f0ffd681237e2b5af3e7dfe4d60c`

The independent final adjudication package records:

- result state `FROZEN`;
- 4,108 fits;
- all fits numerically valid;
- maximum generalized residual `2.8467e-7`;
- 640 exact production/independent support rows;
- historical terminal `TEACHER_BIOLOGY_LIMIT`;
- `D_shared = null`;
- private-state derivation not authorized.

The interpretation boundary in that artifact explicitly states that this does **not** mean the corpus lacks biology. It means the prospectively frozen historical multiview shared-state estimand did not qualify a reproducible leading dimension under that historical gate family.

## What the historical result does and does not authorize now

### It DOES establish

1. FULL104 production preparation/materialization historically occurred.
2. A full-population streaming/execution path was operational.
3. Production-scale storage, fit execution, monitoring, restart/checkpoint, and independent reconstruction machinery existed.
4. There is substantial implementation history that should be audited before new full-stream executors are written.
5. The current inability of this ChatGPT runtime to see >30GB files is a location/access issue, not evidence that the production store never existed.

### It DOES NOT establish

1. current V5 physical-byte closure;
2. current V5 `D_shared`, `D_private`, `D_total`, or `D_obs`;
3. permission to promote historical cap-4 sampled diagnostics;
4. permission to inherit historical fixed replicate counts or search boundaries;
5. a current production locality rule;
6. training authority;
7. TD60 authority;
8. relational target activation.

The old `TEACHER_BIOLOGY_LIMIT` terminal is scoped to the historical estimand and cannot be silently reinterpreted as a global statement about FULL104 biology.

## Correct current recovery path

The present task is:

```text
historically materialized FULL104 store
        ↓
locate existing heavy bytes on GPU laptop / attached drive
        ↓
verify frozen block/materialization/metadata parent hashes
        ↓
run scripts/v5_anticheat/bind_full104_expression_blocks_v4.py
        ↓
PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE
        ↓
seal V5_FULL104_DIMENSION_INPUT_ARTIFACT_V1
        ↓
new V5 full-stream metric execution
```

The exact remote binding procedure is:

`docs/agent/V5_FULL104_REMOTE_BINDING_EXECUTION_20260912.md`

Do **not** rebuild FULL104 simply because the working runtime cannot see the original files.

If the historical physical store cannot be located or fails the frozen integrity checks, stop and open a separate recovery/reconstruction decision. A newly materialized store must have explicit successor provenance and may not inherit historical byte identity by assertion.

## Historical code that should be audited for reuse

Before implementing new full-stream metric executors, inspect the historical FULL104 ALL lineage for reusable mechanics, especially:

- block-major streaming;
- sufficient-statistic accumulation;
- full-refit loops;
- deterministic null execution;
- batch-boundary checkpoint/restart;
- storage and monitoring sidecar separation;
- immutable scientific-manifest construction;
- independent reconstruction;
- production-vs-independent comparison;
- numerical-integrity checks.

Reuse must be semantic and explicit. Historical scientific constants, sampled substrates, thresholds, search limits, and numeric conclusions remain non-authoritative unless independently requalified under the current V5 contract.

## Corrected project statement

Use this wording going forward:

> FULL104 was historically materialized and exercised at production scale. The current V5 blocker is recovery/location and current-authority rebinding of those historical production bytes, followed by new V5 metric qualification—not preparation of the dataset from scratch.

`training_authorized = false`
