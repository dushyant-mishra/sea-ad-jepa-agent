"""Prospective V5 schedule schema separating science, proposal, and compute.

No instance and no numeric production value is created here.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class ProductionScheduleAuthorityV2:
    base_scientific_target_policy_id:str
    base_proposal_policy_id:str
    relational_scientific_target_policy_id:str
    relational_proposal_policy_id:str
    evidence_policy_id:str
    target_block_policy_id:str
    keyed_rng_authority_id:str
    compute_kernel_authority_id:str
    effective_base_cells_per_update:int
    relational_groups_per_update:int
    finite_relational_triplets_per_selected_group:int
    max_teacher_tokens_per_microbatch:int
    masked_views_per_base_cell:int
    training_presentations:int
    ema_half_life_presentations:int

    def validate(self)->None:
        for name,value in self.__dict__.items():
            if name.endswith('_id'):
                if not isinstance(value,str) or not value:
                    raise ValueError(f'{name} must be a nonempty authority string')
            elif isinstance(value,bool) or not isinstance(value,int) or value<1:
                raise ValueError(f'{name} must be an explicit positive integer')
