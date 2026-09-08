"""Prospective data-first Teacher/Student V5 mechanics.

Nothing in this package is execution authority.
"""
from .data_first_geometry import (
    PackedValidTokens, anchored_triplet_capacity, partial_fine_derangement,
    evidence_telemetry,
    ragged_relational_support,
    pack_valid_tokens,
    operator_homogeneous_microbatch_plan,
    mean_loss_weight, weighted_block_jepa_loss, weighted_loss_partition_weight,
)
__all__=[
    'PackedValidTokens','anchored_triplet_capacity','partial_fine_derangement','evidence_telemetry','ragged_relational_support',
    'pack_valid_tokens','operator_homogeneous_microbatch_plan','mean_loss_weight','weighted_block_jepa_loss','weighted_loss_partition_weight'
]

# Proposal algebra is prospective/design-only; importing this package does not activate it.
from .proposal_policy_v1 import DonorCapacity, derive_exposure_constrained_target_mixture, relational_direct_target_group_probabilities
