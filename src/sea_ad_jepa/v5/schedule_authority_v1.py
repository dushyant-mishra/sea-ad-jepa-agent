"""Prospective separation of bounded qualification mechanics from production schedule.

No production schedule instance is created here. Every production field must be
explicitly supplied by a later reviewed authority derived from reader-fit data
and hardware calibration.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class QualificationMechanicsV1:
    effective_batch:int=128
    microbatch:int=8
    views:int=4
    mask_fraction_within_measured:float=0.40
    target_blocks:int=16
    qualification_updates:int=40
    historical_replay_cap:int=8


QUALIFICATION_MECHANICS_V1=QualificationMechanicsV1()


@dataclass(frozen=True)
class ProductionScheduleAuthorityV1:
    scientific_target_policy:str
    proposal_policy:str
    effective_cells_per_update:int
    max_teacher_tokens_per_microbatch:int
    masked_views_per_cell:int
    evidence_policy_id:str
    target_block_policy_id:str
    training_presentations:int
    ema_half_life_presentations:int
    finite_relational_triplets_per_estimable_group:int
    keyed_rng_authority_id:str

    def validate(self)->None:
        integer_fields={
            'effective_cells_per_update':self.effective_cells_per_update,
            'max_teacher_tokens_per_microbatch':self.max_teacher_tokens_per_microbatch,
            'masked_views_per_cell':self.masked_views_per_cell,
            'training_presentations':self.training_presentations,
            'ema_half_life_presentations':self.ema_half_life_presentations,
            'finite_relational_triplets_per_estimable_group':self.finite_relational_triplets_per_estimable_group,
        }
        for name,value in integer_fields.items():
            if isinstance(value,bool) or not isinstance(value,int) or value<1:
                raise ValueError(f'{name} must be an explicit positive integer')
        for name,value in {
            'scientific_target_policy':self.scientific_target_policy,
            'proposal_policy':self.proposal_policy,
            'evidence_policy_id':self.evidence_policy_id,
            'target_block_policy_id':self.target_block_policy_id,
            'keyed_rng_authority_id':self.keyed_rng_authority_id,
        }.items():
            if not isinstance(value,str) or not value:
                raise ValueError(f'{name} must be an explicit nonempty authority string')
