"""Non-authorizing shared qualification interfaces.

This package binds scientific qualification contracts and provenance only.
It does not create training, Stage-A execution, optimizer, EMA, or protected-data authority.
"""

from .canonical import canonical_digest
from .protocol import (
    APPROVED_V3_GOVERNANCE_DIGEST,
    ExecutionMode,
    QualificationProtocolV1,
    ThresholdStatus,
)

__all__ = [
    "APPROVED_V3_GOVERNANCE_DIGEST",
    "ExecutionMode",
    "QualificationProtocolV1",
    "ThresholdStatus",
    "canonical_digest",
]
