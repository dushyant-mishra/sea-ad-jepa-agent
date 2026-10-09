from __future__ import annotations
import dataclasses
import pytest
import torch

from sea_ad_jepa.v5.packing_cost_model_v1 import (
    CellExecutionWorkV1, LinearPackingCostModelV1, pack_frozen_slots_by_cost,
)
from sea_ad_jepa.v5.relational_reducer_v1 import weighted_group_mean_relational_loss


def _model() -> LinearPackingCostModelV1:
    return LinearPackingCostModelV1(
        teacher_token_cost=3,
        student_token_cost=5,
        predictor_query_cost=7,
        relational_triplet_cost=11,
    )


def test_full_path_cost_counts_teacher_student_predictor_and_relational_work():
    work=CellExecutionWorkV1(
        teacher_tokens=18_736,
        student_visible_tokens_total=4*10_000,
        predictor_target_queries_total=4*16,
        relational_triplets=8,
    )
    assert _model().cost(work)==18_736*3+40_000*5+64*7+8*11


def test_cost_model_has_no_numerical_defaults():
    for cls in (CellExecutionWorkV1,LinearPackingCostModelV1):
        assert all(f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING for f in dataclasses.fields(cls))


def test_packer_preserves_frozen_scientific_slot_order_and_membership():
    plan=pack_frozen_slots_by_cost((4,7,3,8,2),max_cost_per_microbatch=10)
    assert plan==((0,),(1,2),(3,4))
    assert tuple(i for batch in plan for i in batch)==(0,1,2,3,4)


def test_packer_fails_when_one_scientific_slot_exceeds_hardware_budget():
    with pytest.raises(ValueError,match="frozen scientific slot exceeds"):
        pack_frozen_slots_by_cost((4,11,3),max_cost_per_microbatch=10)


def test_triplet_sample_count_does_not_define_group_objective_mass():
    # Group 0 has one triplet at loss 2. Group 1 has four identical triplets at loss 8.
    loss=torch.tensor([2.,8.,8.,8.,8.])
    groups=torch.tensor([0,1,1,1,1],dtype=torch.int64)
    equal_group_weight=torch.tensor([1.,1.])
    result=weighted_group_mean_relational_loss(loss,groups,equal_group_weight)
    assert result==pytest.approx(5.0)
    # A raw triplet mean would be 6.8 and would wrongly give the larger sample more mass.
    assert result != pytest.approx(float(loss.mean()))


def test_duplicate_triplets_within_group_do_not_change_group_weighted_loss():
    a=weighted_group_mean_relational_loss(
        torch.tensor([2.,4.,8.]),
        torch.tensor([0,0,1]),
        torch.tensor([3.,1.]),
    )
    b=weighted_group_mean_relational_loss(
        torch.tensor([2.,4.,2.,4.,8.,8.,8.]),
        torch.tensor([0,0,0,0,1,1,1]),
        torch.tensor([3.,1.]),
    )
    assert a==pytest.approx(float(b))


def test_relational_group_weights_are_explicit_and_no_pooled_rescue():
    loss=torch.tensor([1.,9.])
    groups=torch.tensor([0,1],dtype=torch.int64)
    assert weighted_group_mean_relational_loss(loss,groups,torch.tensor([9.,1.]))==pytest.approx(1.8)
    with pytest.raises(ValueError,match="every weighted group"):
        weighted_group_mean_relational_loss(
            torch.tensor([1.]),torch.tensor([0]),torch.tensor([1.,1.])
        )
