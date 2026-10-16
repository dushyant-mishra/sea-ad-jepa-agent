# PR #223 P0 closure — authority scope bound to batch data kind — 2026-10-06

## Defect

Whole-branch audit found that `ScientificExperimentAuthorityV1` scope was validated against the qualification protocol but not against `QualificationBatchV1.data_kind` at execution time.

Because `SYNTHETIC_PIPELINE_VALIDITY` may carry `evaluation_authorized=True`, a `REAL_RNA` batch could be passed to the shared zero-update runner under synthetic authority and execute representation/readout callbacks. That violated the explicit `STAGE_A_EXECUTION=OFF` boundary even though `REAL_RNA_PREFREEZE_ONLY` itself correctly rejects `evaluation_authorized=True`.

## RED evidence

Commit:
`7110f609346e84bebab9ba01e9a4a7df231d057a`

Test:
`tests/qualification/test_authority_data_kind_binding_v1.py`

Workflow:
`37546338516`

Result:
`1 failed / 132 passed`

The sole failure was `test_synthetic_scope_authority_cannot_execute_real_rna_batch`: no exception was raised, proving that the real-RNA callback path executed under synthetic scientific authority.

## GREEN repair

Commit:
`42087d72968e381c8e4e5a1eb1641581a2624398`

The execution preflight now binds authority scope to batch data kind before callbacks:

- synthetic batch execution requires `ExperimentScope.SYNTHETIC_PIPELINE_VALIDITY`;
- real-RNA execution is rejected unconditionally in shared-interface V1 because this slice contains no real-RNA execution-authorizing scientific scope;
- unknown data kinds fail closed;
- real-RNA batches remain constructible for schema/interface qualification only.

Workflow:
`37546521656`

Result:
SUCCESS across the full shared qualification/governance gate.

## Authority consequence

This closes the Stage-A execution bypass in PR #223 without minting any new authority.

Current state remains:

- TRAINING = OFF
- STAGE_A_EXECUTION = OFF
- MULTIMODAL_TRAINING = OFF
- 500K = NOT_AUTHORIZED
- STAGE4 = NOT_AUTHORIZED
- TEST = SEALED
- MORABITO = PROTECTED
- no optimizer/EMA mutation authority
- no real-RNA execution authority
- no representation/target/estimand/deciding-threshold winner selected

## Remaining convergence boundary

PR #223 still does not prove physical no-mutation or transformation-level q-safety for arbitrary callbacks. Those proofs remain reserved for a bound runtime/adapter successor during #221/#222 convergence.
