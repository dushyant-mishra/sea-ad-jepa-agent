# PR #223 shared qualification interface — audit closure for runtime convergence — 2026-10-06

## Status

Draft PR #223 (`shared-qualification-interface-v1-20261006`) has completed the current whole-branch adversarial audit and is coherent enough to serve as the non-authorizing scientific/interface side of runtime convergence.

This is **not a merge authorization**. The branch remains draft while #221/#222 runtime/adapter proof binding is reconciled.

Latest verified head:

`f6d63b2f53209786e3c45e7545b9bd442838a3d4`

GitHub Actions:

`37547034207` — SUCCESS

The focused gate covers `tests/qualification/**` plus the V3 governance surface tests and retriggers on both governance tests and the frozen V3 state JSON.

## Major audit repairs closed

The RED/GREEN history is preserved in the earlier audit checkpoints. The final interface now closes these failure classes:

1. ordered biological feature identity mismatch;
2. source-roster/source-index/operator semantic mismatch;
3. reconstructed/scalar-only measurement support substitution;
4. support observation-order/feature-width/rule mismatch;
5. unbound measurement mask or operator context;
6. oracle truth from a different synthetic realization;
7. development/calibration data promoted to prospective challenge;
8. invalid challenge partition surviving into callback execution;
9. `evaluation_authorized=False` executing callbacks;
10. retry child reusing parent run identity;
11. governance changes bypassing the dedicated CI trigger;
12. P0 synthetic scientific authority executing a `REAL_RNA` batch.

## Authority/data-kind boundary

Current V1 execution rule is deliberately asymmetric:

- `SYNTHETIC` execution requires `ExperimentScope.SYNTHETIC_PIPELINE_VALIDITY` and affirmative evaluation authorization;
- `REAL_RNA` batches may be constructed for schema/interface qualification but cannot execute through the shared V1 runner because no real-RNA execution-authorizing scope exists;
- therefore `STAGE_A_EXECUTION=OFF` remains mechanically preserved.

P0 RED:
`7110f609346e84bebab9ba01e9a4a7df231d057a`, workflow `37546338516`, `1 failed / 132 passed`.

P0 GREEN:
`42087d72968e381c8e4e5a1eb1641581a2624398`, workflow `37546521656`, SUCCESS.

## Physical proof boundaries made machine-readable

### Mutation

Generic Python callbacks can mutate hidden state through closures. PR #223 therefore does not claim physical zero-mutation proof.

Default status:
`MutationProofStatus.NOT_PROVEN_BY_SHARED_INTERFACE`

The stronger state:
`MutationProofStatus.PROVEN_BY_BOUND_RUNTIME`

cannot be represented in provenance without a bound `runtime_successor_digest`.

### Q-safety

The shared interface validates the exact q-safety policy/forbidden-channel roster, but does not inspect arbitrary executed preprocessing descendants.

Default status:
`QSafetyExecutionProofStatus.POLICY_ONLY_NOT_EXECUTION_PROVEN`

The stronger state:
`QSafetyExecutionProofStatus.PROVEN_BY_BOUND_ADAPTER_RUNTIME`

cannot be represented in provenance without a bound `runtime_successor_digest`.

This status is propagated into both provenance and `FrozenQualificationOutputsV1`, so downstream consumers cannot silently lose the limitation.

Q-safety RED/GREEN:
- `d85bcfcf18f4d38a2d5b580dc5b749a6d483f666` — missing execution-proof type, expected RED;
- `a49cb9d45a8e14b9a4a8d8596266033a87d10de7` — provenance contract added;
- `37e60d1ac84a16289c4ba2d7673c798bb00dcaf0` — frozen-output propagation RED, `1 failed / 133 passed`;
- `f6d63b2f53209786e3c45e7545b9bd442838a3d4` — frozen-output propagation GREEN;
- workflow `37547034207`: SUCCESS.

## Oracle receipt semantics

`OracleUnblindingReceiptV1` is treated as an immutable historical event receipt, not current claim authority. `mark_post_unblinding_retune()` produces a new development/calibration receipt; the original historical receipt remains immutable. This is acceptable because oracle receipts do not carry claim authority and cannot by themselves authorize scientific promotion.

## What #221/#222 must now prove to bind into this interface

Runtime convergence must provide evidence sufficient to replace the two default limitation statuses with runtime-bound proof where applicable:

1. exact runtime successor identity/digest;
2. physically demonstrated no unauthorized parameter/optimizer/scaler/EMA mutation for zero-update qualification paths;
3. for mutation rehearsal, lawful optimizer/scaler advancement proof tied to the exact guarded optimizer rather than arbitrary caller counters;
4. EMA only after proven lawful optimizer completion;
5. deterministic authority-bound checkpoint/restart where mutation execution is eventually authorized;
6. adapter/runtime-level proof that executed preprocessing descendants satisfy q-safety, rather than policy declaration alone;
7. no real-RNA execution authority unless separately and prospectively approved by governance.

## Scientific boundary remains unchanged

S149 still reopens the calibration-target question in the real-data lane. This interface neither selects nor authorizes a replacement target.

No representation winner, target winner, estimand, deciding threshold, pathology claim, or protected-data execution is selected here.

## Hard state

- TRAINING = OFF
- STAGE_A_EXECUTION = OFF
- MULTIMODAL_TRAINING = OFF
- 500K = NOT_AUTHORIZED
- STAGE4 = NOT_AUTHORIZED
- TEST = SEALED
- MORABITO = PROTECTED
- no optimizer/EMA mutation authority from PR #223
- no real-RNA execution authority
