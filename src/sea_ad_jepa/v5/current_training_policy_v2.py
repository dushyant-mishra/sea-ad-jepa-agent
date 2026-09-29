"""Canonical current training-policy pointer after the V61 governance repair.

Historical V1 training authority and V3 optimizer guard remain importable only
as historical schemas. New execution code must pass through this module.
"""
from __future__ import annotations
from typing import Any

from .current_training_authority_v2 import CurrentTrainingAuthorityV2, issue_training_authority_v2
from .qualified_optimizer_guard_v4 import CurrentOptimizerStepGuardV4, install_current_optimizer_guard_v4

CURRENT_TRAINING_AUTHORITY_SCHEMA = "V5_CURRENT_TRAINING_AUTHORITY_V2"
CURRENT_OPTIMIZER_GUARD_SCHEMA = "V5_CURRENT_OPTIMIZER_GUARD_V4"


def require_current_training_authority(value: Any) -> CurrentTrainingAuthorityV2:
    if not isinstance(value, CurrentTrainingAuthorityV2):
        raise ValueError("current training policy requires CurrentTrainingAuthorityV2")
    value.validate()
    return value


__all__ = [
    "CURRENT_TRAINING_AUTHORITY_SCHEMA",
    "CURRENT_OPTIMIZER_GUARD_SCHEMA",
    "CurrentTrainingAuthorityV2",
    "CurrentOptimizerStepGuardV4",
    "issue_training_authority_v2",
    "install_current_optimizer_guard_v4",
    "require_current_training_authority",
]
