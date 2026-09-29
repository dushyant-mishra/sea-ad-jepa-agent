"""Current V5 authority root vocabulary V3: V2 plus specificity/q-safety/provider execution."""
from .current_authority_roots_v2 import CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2
CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V3=(
    *CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V2,
    "biological_specificity_authority_sha256",
    "q_safety_authority_sha256",
    "critical_test_v2_authority_sha256",
)
CURRENT_V5_RECEIPT_AUTHORITY_ROOTS_V3=(*CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V3,"preexecution_authority_sha256")
