# Healthy Teacher Training Base V1 — External Review Handoff

## Candidate identity

Review exactly:

- branch: `planning/healthy-teacher-training-contract-20260907`
- freeze commit: `5f89093000fe0460de377eb129890bdb0cf85a90`
- package root: `9e1ee362773a8329f783015a04af4f7699135cc0710b1ee1ea66abc0aafd8534`
- prefreeze CI-tested commit: `33218d536e5c4ea023cb326dffcca96159fdc5f4`
- CI run: `34114608353`
- CI evidence: `17 passed`; `PASS_HEALTHY_TEACHER_BASE_IMMUTABILITY_AUDIT`

The freeze commit itself adds only:

- `docs/agent/HEALTHY_TEACHER_TRAINING_BASE_PACKAGE_ROOT_20260907.txt`
- `docs/agent/HEALTHY_TEACHER_TRAINING_BASE_FREEZE_20260907.json`

The five manifest-bound authority files are unchanged from the CI-tested parent.

## Scope

This is a review of the **prospective, outcome-independent training base contract** only.

A PASS must mean only:

`PASS_HEALTHY_TEACHER_TRAINING_BASE_INDEPENDENT_REVIEW__EXECUTION_UNAUTHORIZED`

It must **not** authorize:

- u1 or any optimizer update;
- u0→u40 qualification;
- u40→u205 continuation;
- reader-validation/oracle;
- development/sealed/external holdouts;
- pathology;
- real F1/T0;
- real D1.

## Required review questions

### 1. Population firewall

Confirm the contract is bound to the frozen population registry root:

`e9903bbb9d56663790f5f5b298c5633d87a71548466089e7cc6aae7c45728ee7`

Confirm:

- 104 reader-fit donors;
- 3,292 cells;
- no continuation/train expansion;
- no reader-validation/oracle;
- no foundation development/sealed;
- no pathology.

### 2. Historical schedule and corpus

Confirm the contract preserves the exact outcome-independent authorities:

- reader split `efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511`;
- fit inventory `7ac13973162a46cafa5baa24c5bea14beb64bd5859e8f58900801eee07083a30`;
- training schedule `4657d669658712234d7ee8ede9496297009b808d4902766a9e43f7591ca640fc`;
- 26,240 scheduled presentations;
- cap 8;
- 128 effective batch;
- 8 microbatch;
- 4 views;
- 40% measured-address masking;
- 16 target blocks;
- 41,238-address namespace.

### 3. C2/F1-B mechanics

Confirm:

- forward may use CUDA fp16 autocast;
- scaled backward is under `autocast(enabled=False)`;
- `unscale -> mandatory gradient gate -> proved optimizer step -> both Adam moments -> EMA`;
- mandatory 48 backbone tensors are gated after unscale and before step;
- missing/nonfinite/exact-zero gradients reject;
- no arbitrary small-gradient floor;
- target gradients must be absent;
- both `exp_avg` and `exp_avg_sq` are required;
- EMA occurs only after a proved valid step;
- movement is per tensor and pooled movement is forbidden;
- the contract does **not** promote the current non-authoritative hard-coded 2x decay margin.

### 4. Qualification versus full training

Confirm exact separation:

- formal mechanical qualification is exactly `u0 -> u40`;
- qualification does not auto-continue;
- full continuation is at most `u40 -> u205`;
- continuation requires a hash-bound u40 package, independent review, unchanged roots, and explicit continuation authority;
- no biological/readout result is an early-stopping or continuation criterion.

### 5. Initialization

Confirm:

- historical u0 SHA `19fb0c25d9f7549c37de39285807d5b6a6e828ced94af63927e83fa3c5c6b7c4` is only a clean state source/reference;
- historical u10-u205 are prohibited;
- a **new successor-bound u0** must be materialized and frozen before u1;
- if schemas changed, changed components are prospectively initialized; unchanged components require equivalence audit.

### 6. Immutable-overlay design

Confirm the frozen base execution-binding fields are all null and `ready=false`.

Confirm future successor/u0 facts must be supplied by a separate:

`HEALTHY_TEACHER_EXECUTION_BINDING_OVERLAY_V1`

and that the overlay:

- hash-binds this base root;
- cannot modify the base;
- must bind exact successor source/review/u0/predictor/movement authorities;
- is not itself permission to execute u0→u40.

### 7. Integrity

Recompute all five manifest entries and the manifest root.

Expected package root:

`9e1ee362773a8329f783015a04af4f7699135cc0710b1ee1ea66abc0aafd8534`

Run:

`python -m pytest -q tests/test_healthy_teacher_training_contract_v1.py`

Expected: `17 passed`.

Then independently inspect `scripts/agent/validate_healthy_teacher_training_contract_v1.py`; do not rely only on test names.

## STOP conditions

Return STOP if any of the following is true:

- the package root does not reproduce;
- a manifest-bound file differs;
- the base can be mutated to populate execution bindings and still pass;
- any protected population/pathology can enter training;
- u40 can be overridden or auto-continued;
- 300 updates can replace u205;
- C2 backward repair can be removed;
- a biology metric can drive training continuation;
- historical defect-inherited checkpoints are allowed;
- the future overlay can modify the base or directly authorize execution;
- any major authority used by the base is unsupported.

Do not repair the candidate during review. Report exact STOP evidence instead.
