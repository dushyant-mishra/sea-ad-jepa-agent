# V5 external-review final verdict — 2026-09-13

Status: `REPOSITORY_IMPLEMENTATION_REVIEW_CLOSED__REAL_DATA_QUALIFICATION_NEXT__NO_TRAINING_AUTHORITY`

Reviewed live successor:

`planning/v5-dataset-first-production-closure-20260912 @ b7bdbadc7af11e9173627cacef6cc8bae48a6e2a`

This review was performed from three independent perspectives: computational biology, scientific/statistical inference, and ML/runtime engineering. It re-read the current external-review handoff and traced the current protected-registry, teacher/runtime, provenance, checkpoint, GPU/preexecution, dimension and postqualification boundaries.

## Verdict

No additional repository implementation defect was demonstrated that should be patched before real-data execution.

Two suspected defects were explicitly checked and rejected:

1. **Current V5 teacher runtime reachability** — not a defect. The current runtime intentionally quarantines historical T0/V21 teacher receipts and does not allow them to become current V5 production teacher authority. A dataset-derived teacher authority is intentionally deferred until FULL104 dimensions, production geometry, CUDA mechanics and bounded base-learning qualification close.

2. **Protected-registry historical 48-tensor assumption** — already repaired in the live successor. The current registry derives the number of protected tensors from the prospectively selected model depth and explicitly states that the historical six-block/48-tensor geometry is not production authority. The remaining protected attention-role vocabulary is an architectural mechanics contract, not a frozen historical depth.

## Intentionally open work — not repository defects

The following remain open by design and must not be papered over with arbitrary constants or synthetic evidence:

- physical locate/hash/rebind of the existing FULL104 bytes;
- current-V5 full-stream numeric metric execution for `D_shared`, then `D_private`, then `D_obs`;
- prospective Monte-Carlo/donor-resample precision authority **before current numeric outcomes are examined**;
- independent review of candidate `D_private` and `D_obs` selection rules before outcome-dependent revision is possible;
- executable raw-output anti-cheat evidence at adjudication geometry for all current postqualification gates;
- actual dataset-derived schedule/model/EMA geometry;
- production-geometry CUDA qualification;
- bounded base-learning-step qualification;
- lawful dataset-derived EMA teacher;
- TD60;
- relational student qualification;
- final integrated review and only then any explicit production-training authority.

These tasks require either the authenticated real substrate/model execution or prospective scientific choices. Inventing values now merely to make the repository appear complete would violate the dataset-first and fail-closed design.

## Scientific invariants carried forward

- Decision-bearing statistics are unconditional over the declared evaluation population; failed, undefined and non-estimable units do not silently disappear from denominators.
- `MEASUREMENT_FAILED`, `ESTIMATOR_FAILED`, `REPRESENTATION_FAILED`, `TECHNICAL_CONFOUNDING_UNRESOLVED`, `BIOLOGY_NOT_DEMONSTRATED` and a qualified biological negative remain distinct outcomes.
- Failure to measure is not evidence that biology is absent.
- No historical T0/V4 numeric threshold, fixed dimension, replicate count, batch/microbatch geometry, mask fraction or EMA momentum becomes current V5 authority merely because it existed historically.
- A pooled disease axis in the heterogeneous corpus is insufficient. Biological emergence must survive dataset/source/operator/technology/living-postmortem/PMI/region/sex-age/depth/support-family attacks and, where possible, replicate within-study or matched-context contrasts.
- Current anti-cheat gate vocabulary must ultimately be supported by executable, raw-output, hash-bound evidence; caller booleans alone are not evidence.

## Next action

The next scientific action is not another repository redesign. On the GPU/data machine:

1. locate the historical FULL104 Level-4 store;
2. verify the frozen parent hashes;
3. run the hardened current V5 binder;
4. require terminal `PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE`;
5. seal `V5_FULL104_DIMENSION_INPUT_ARTIFACT_V1.json`;
6. before inspecting current V5 dimension outcomes, freeze the metric-specific Monte-Carlo/resampling precision authority;
7. execute the current-V5 full-stream metric chain.

Hard boundaries remain closed: training, protected data, TD60 and relational-target activation are not authorized by this review.
