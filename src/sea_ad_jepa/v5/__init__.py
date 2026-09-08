"""Prospective data-first Teacher/Student V5 mechanics.

Nothing in this package is execution authority.  Only current canonical planning
modules are exported here; superseded prototype module names are intentionally
not retained as aliases.
"""
from .data_first_geometry import (
    PackedValidTokens,
    anchored_triplet_capacity,
    evidence_telemetry,
    mean_loss_weight,
    operator_homogeneous_microbatch_plan,
    pack_valid_tokens,
    partial_fine_derangement,
    ragged_relational_support,
)
from .finite_relational_sampling import (
    FiniteTripletKeySample,
    map_triplet_keys_to_rows,
    sample_finite_anchored_triplet_keys,
    unrank_anchored_triplet,
)
from .keyed_rng_reference import (
    dropout_counter_words,
    keyed_dropout_keep,
    keyed_dropout_u32,
    philox4x32_10,
    site_key_words,
)
from .support_geometry_v1 import balanced_block_sizes, fixed_visible_evidence
from .schedule_authority_v1 import ProductionScheduleAuthorityV1, QualificationMechanicsV1
from .data_contract_v2 import (
    ComputePackingAuthorityV2,
    EvidenceAuthorityV2,
    ProductionDataContractV2,
    ScientificSamplingAuthorityV2,
)

__all__ = [
    "PackedValidTokens",
    "anchored_triplet_capacity",
    "evidence_telemetry",
    "mean_loss_weight",
    "operator_homogeneous_microbatch_plan",
    "pack_valid_tokens",
    "partial_fine_derangement",
    "ragged_relational_support",
    "FiniteTripletKeySample",
    "map_triplet_keys_to_rows",
    "sample_finite_anchored_triplet_keys",
    "unrank_anchored_triplet",
    "dropout_counter_words",
    "keyed_dropout_keep",
    "keyed_dropout_u32",
    "philox4x32_10",
    "site_key_words",
    "balanced_block_sizes",
    "fixed_visible_evidence",
    "ProductionScheduleAuthorityV1",
    "QualificationMechanicsV1",
    "ComputePackingAuthorityV2",
    "EvidenceAuthorityV2",
    "ProductionDataContractV2",
    "ScientificSamplingAuthorityV2",
]
