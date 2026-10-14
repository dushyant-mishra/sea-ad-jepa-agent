"""Non-authorizing target-semantics boundary for the canonical V5 mechanics runtime.

The deterministic teacher-block loss exercised by the inactive V5 runtime is a
mechanics fixture used to qualify packing, gradients, guarded mutation, EMA,
and restart behavior. It is not scientific authority to require a partial-RNA
student to reproduce an arbitrary realized rich-teacher state.

Rich teacher evidence may contain information unavailable from the student's
lawful observations. Scientific qualification therefore owns the decomposition
between shared/predictable state, teacher-private information, measurement
information, and uncertainty/abstention semantics. This runtime selects none of
those objects and grants no Stage-A or training authority.
"""

SCHEMA = "V5_RUNTIME_TARGET_SEMANTICS_BOUNDARY_V1"
SCIENTIFIC_TARGET_SEMANTICS_AUTHORIZED = False
REFERENCE_LOSS_ROLE = "MECHANICS_FIXTURE_ONLY__NOT_TARGET_AUTHORITY"
FULL_RICH_TEACHER_REALIZATION_MATCHING_AUTHORIZED = False
RICH_TEACHER_PARTIAL_STUDENT_CLASSIFICATION = (
    "RICH_TEACHER_DESIRABLE__FULL_RICH_STATE_NOT_GENERALLY_IDENTIFIABLE_FROM_PARTIAL_RNA"
)
TARGET_WINNER_SELECTED = False
UNCERTAINTY_MODEL_SELECTED = False
STAGE_A_EXECUTION_AUTHORIZED = False
TRAINING_AUTHORIZED = False


def assert_runtime_target_semantics_non_authorizing() -> bool:
    if SCIENTIFIC_TARGET_SEMANTICS_AUTHORIZED:
        raise RuntimeError("runtime mechanics cannot authorize scientific target semantics")
    if FULL_RICH_TEACHER_REALIZATION_MATCHING_AUTHORIZED:
        raise RuntimeError("runtime cannot authorize full rich-teacher realization matching")
    if TARGET_WINNER_SELECTED or UNCERTAINTY_MODEL_SELECTED:
        raise RuntimeError("runtime mechanics cannot select target or uncertainty semantics")
    if STAGE_A_EXECUTION_AUTHORIZED or TRAINING_AUTHORIZED:
        raise RuntimeError("runtime target-semantics boundary cannot authorize execution/training")
    return True
