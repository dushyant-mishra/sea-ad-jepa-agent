"""Prospective data-first Teacher/Student V5 mechanics.

Nothing in this package is execution authority.
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
from .finite_triplets_v1 import sample_finite_anchored_triplets
from .keyed_rng_v1 import KeyedDropoutSpec, keyed_dropout, keyed_dropout_mask
from .scientific_estimand_v1 import (
    EstimandPolicy,
    GroupCount,
    group_masses,
    importance_diagnostics,
)

__all__=[
    "PackedValidTokens",
    "anchored_triplet_capacity",
    "evidence_telemetry",
    "mean_loss_weight",
    "operator_homogeneous_microbatch_plan",
    "pack_valid_tokens",
    "partial_fine_derangement",
    "ragged_relational_support",
    "sample_finite_anchored_triplets",
    "KeyedDropoutSpec",
    "keyed_dropout",
    "keyed_dropout_mask",
    "EstimandPolicy",
    "GroupCount",
    "group_masses",
    "importance_diagnostics",
]
