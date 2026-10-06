# JEPA shared qualification pipeline — final self-audit correction

Date: 2026-10-06
Status: `BINDING_CORRECTION__NO_EXECUTION_AUTHORITY__TRAINING_OFF`

This correction resolves one ambiguity discovered during final self-audit of the failure-containment addendum.

## Mode-aware lifecycle

The lifecycle must not force zero-update scientific qualification through mutation-specific states.

A shared run has common states:

- `NOT_STARTED`
- `PREPARED`
- `QUALIFICATION_OUTPUTS_FROZEN`
- `VERIFIED`
- terminal failure states carrying the last proven completed stage and failure reason

For `ZERO_UPDATE_QUALIFICATION`, the lawful path is:

`NOT_STARTED -> PREPARED -> QUALIFICATION_OUTPUTS_FROZEN -> VERIFIED`

with optimizer/EMA mutation forbidden throughout.

For `BOUNDED_MUTATION_REHEARSAL`, mutation-specific substates are inserted after preparation and before frozen final outputs:

`NOT_STARTED -> PREPARED -> MUTATED -> EMA_APPLIED -> CHECKPOINTED -> QUALIFICATION_OUTPUTS_FROZEN -> VERIFIED`

where each transition requires explicit proof and may fail closed at the last proven stage.

Synthetic oracle unblinding remains downstream of `QUALIFICATION_OUTPUTS_FROZEN` and does not alter the run's ordinary qualification state. Oracle evaluation appends downstream artifacts under the same immutable `experiment_run_id`.

A zero-update run must fail if it ever emits a `MUTATED`, `EMA_APPLIED`, or mutation-checkpoint event.

This correction supersedes any reading of the earlier safeguards addendum that implied mutation states were mandatory for every qualification run.
