"""Exact current-V5 authority root vocabulary."""
CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS = (
    "full104_substrate_sha256",
    "representation_authority_sha256",
    "support_estimability_authority_sha256",
    "base_training_estimand_sha256",
    "teacher_target_semantics_sha256",
    "target_address_query_authority_sha256",
    "masking_authority_sha256",
    "model_geometry_authority_sha256",
    "schedule_authority_sha256",
    "ema_authority_sha256",
    "anti_cheat_authority_sha256",
    "runtime_source_sha256",
)
CURRENT_V5_RECEIPT_AUTHORITY_ROOTS = (
    *CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS[:-1],
    "preexecution_authority_sha256",
    CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS[-1],
)
