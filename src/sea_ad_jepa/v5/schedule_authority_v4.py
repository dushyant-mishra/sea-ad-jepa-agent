"""Initial full-reader Teacher/Student V5 production-schedule schema.

This schema intentionally binds ONLY the base JEPA teacher stage. Relational
training is firewalled until a lawful learned teacher exists and TD60 plus the
prospective partial-evidence relational-predictability gate have passed.
No production values are defaulted here.
"""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ProductionTeacherScheduleAuthorityV4:
    base_scientific_target_policy_id:str
    base_proposal_policy_id:str
    presentation_horizon_policy_id:str
    evidence_target_policy_id:str
    evidence_view_schedule_policy_id:str
    family_loss_weight_policy_id:str
    target_block_policy_id:str
    target_query_sampling_policy_id:str
    support_mask_rng_authority_id:str
    keyed_dropout_rng_authority_id:str
    compute_kernel_authority_id:str
    final_checkpoint_milestone_id:str
    effective_base_cells_per_update:int
    singleton_target_queries_common_core:int
    singleton_target_queries_operator_native:int
    max_teacher_tokens_per_microbatch:int
    target_query_chunk_size:int
    training_presentations:int
    ema_half_life_presentations:int
    relational_training_active:bool

    def validate(self)->None:
        for name,value in self.__dict__.items():
            if name.endswith('_id'):
                if not isinstance(value,str) or not value:
                    raise ValueError(f'{name} must be a nonempty authority string')
            elif name=='relational_training_active':
                if value is not False:
                    raise ValueError('initial full-reader teacher requires relational_training_active=False')
            elif isinstance(value,bool) or not isinstance(value,int) or value<1:
                raise ValueError(f'{name} must be an explicit positive integer')

@dataclass(frozen=True)
class RelationalExtensionScheduleAuthorityV1:
    relational_scientific_target_policy_id:str
    relational_proposal_policy_id:str
    td60_pass_authority_id:str
    partial_evidence_relational_predictability_pass_authority_id:str
    learned_teacher_checkpoint_authority_id:str
    relational_integration_review_authority_id:str
    comparator_pair_sampling_policy_id:str
    relational_anchor_presentations_per_update:int
    comparator_pairs_per_selected_anchor:int
    relational_loss_coefficient_numerator:int
    relational_loss_coefficient_denominator:int

    def validate(self)->None:
        for name,value in self.__dict__.items():
            if name.endswith('_id'):
                if not isinstance(value,str) or not value:
                    raise ValueError(f'{name} must be a nonempty authority string')
            elif isinstance(value,bool) or not isinstance(value,int) or value<1:
                raise ValueError(f'{name} must be an explicit positive integer')
