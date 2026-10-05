"""Final current-V5 root vocabulary V4.

V4 extends V3 and makes validated regulatory evidence plus exact RNA+E2 target
integration first-class roots. Historical V1-V3 vocabularies remain immutable.
"""
from .current_authority_roots_v3 import CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V3

CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V4 = (
    *CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V3,
    "validated_e2_authority_sha256",
    "rna_e2_target_integration_authority_sha256",
)

CURRENT_V5_RECEIPT_AUTHORITY_ROOTS_V4 = (
    *CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V4,
    "preexecution_authority_sha256",
)
