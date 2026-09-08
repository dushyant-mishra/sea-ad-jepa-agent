from __future__ import annotations
import dataclasses
import importlib
import random
import pytest
import torch

import sea_ad_jepa.v5
from sea_ad_jepa.v5.data_contract_v2 import (
    ComputePackingAuthorityV2, EvidenceAuthorityV2, OptimizationScheduleAuthorityV2,
    ProductionDataContractV2, ScientificSamplingAuthorityV2,
)
from sea_ad_jepa.v5.finite_relational_sampling import anchored_triplet_capacity, sample_finite_anchored_triplet_keys
from sea_ad_jepa.v5.keyed_dropout_prototype import keyed_feature_dropout_reference
from sea_ad_jepa.v5.keyed_rng_reference import dropout_counter_words, philox4x32_10


def test_all_live_v5_modules_import():
    for name in (
        "data_first_geometry", "finite_relational_sampling", "keyed_rng_reference",
        "keyed_dropout_prototype", "schedule_authority_v1", "support_geometry_v1",
        "data_contract_v2",
    ):
        importlib.import_module(f"sea_ad_jepa.v5.{name}")


def test_philox_known_answer_and_full_reader_stable_key_domain():
    assert philox4x32_10((0,0,0,0),(0,0)) == (0x6627E8D5,0xE169C58D,0xBC57AC4C,0x9B00DBD8)
    lo=257_865_466_610; hi=9_223_371_444_004_343_451
    assert dropout_counter_words(cell_key=lo,canonical_token_key=41_237,feature_index=159) != dropout_counter_words(cell_key=hi,canonical_token_key=41_237,feature_index=159)


def test_proof_dropout_is_packing_and_row_order_invariant_on_real_key_range():
    torch.manual_seed(3)
    x=torch.randn(2,5,8)
    token=torch.tensor([[-1,0,4,9,11],[-1,0,4,9,11]],dtype=torch.int64)
    cells=torch.tensor([257_865_466_610,9_223_371_444_004_343_451],dtype=torch.int64)
    kwargs=dict(probability=.1,run_seed=77,update_index=5,view_index=2,layer_index=1,site_index=0,training=True)
    full=keyed_feature_dropout_reference(x,cell_keys=cells,token_keys=token,**kwargs)
    select=torch.tensor([4,0,2])
    packed=keyed_feature_dropout_reference(x[:,select],cell_keys=cells,token_keys=token[:,select],**kwargs)
    assert torch.equal(packed,full[:,select])
    rerow=keyed_feature_dropout_reference(x.flip(0),cell_keys=cells.flip(0),token_keys=token.flip(0),**kwargs)
    assert torch.equal(rerow,full.flip(0))


def test_finite_triplets_scale_to_max_observed_group_without_enumeration():
    keys=list(range(1_000_000,1_000_000+42_209))
    a=sample_finite_anchored_triplet_keys(keys,triplet_budget=128,authority_seed=7,update_index=11,group_key="SEA_AD::MAX")
    random.Random(19).shuffle(keys)
    b=sample_finite_anchored_triplet_keys(keys,triplet_budget=128,authority_seed=7,update_index=11,group_key="SEA_AD::MAX")
    assert a.triplet_cell_keys==b.triplet_cell_keys and a.sampled_ranks==b.sampled_ranks
    assert a.realized_count==128 and a.capacity==anchored_triplet_capacity(42_209)
    assert len(set(a.triplet_cell_keys))==128


def _contract() -> ProductionDataContractV2:
    return ProductionDataContractV2(
        evidence=EvidenceAuthorityV2(
            native_support_policy_id="NATIVE_MEASURED_SUPPORT_V1",
            comparable_support_policy_id="ALL_42_COMMON_MEASURED_CORE_V1",
            comparable_support_role="CALIBRATION_ONLY",
            target_block_policy_id="DATA_DERIVED_BLOCK_POLICY_PENDING",
        ),
        scientific_sampling=ScientificSamplingAuthorityV2(
            target_estimand_policy_id="TARGET_ESTIMAND_PENDING",
            proposal_policy_id="PROPOSAL_PENDING",
            importance_weight_policy_id="IMPORTANCE_POLICY_PENDING",
            relational_sampling_policy_id="RELATIONAL_SAMPLING_POLICY_PENDING",
            relational_weight_policy_id="RELATIONAL_WEIGHT_POLICY_PENDING",
        ),
        optimization_schedule=OptimizationScheduleAuthorityV2(
            effective_cells_per_update=128,
            masked_views_per_cell=4,
            training_presentations=1,
            ema_half_life_presentations=1,
        ),
        compute_packing=ComputePackingAuthorityV2(
            max_teacher_tokens_per_microbatch=100_000,
            rng_authority_id="RNG_PENDING",
            relational_compute_budget_id="RELATIONAL_COMPUTE_BUDGET_PENDING",
        ),
    )


def test_data_contract_separates_support_science_optimization_and_compute_without_defaults():
    c=_contract(); c.validate()
    science={f.name for f in dataclasses.fields(ScientificSamplingAuthorityV2)}
    optim={f.name for f in dataclasses.fields(OptimizationScheduleAuthorityV2)}
    compute={f.name for f in dataclasses.fields(ComputePackingAuthorityV2)}
    assert "relational_sampling_policy_id" in science and "relational_weight_policy_id" in science
    assert "effective_cells_per_update" in optim and "effective_cells_per_update" not in compute
    assert "relational_compute_budget_id" in compute
    assert science.isdisjoint(optim) and science.isdisjoint(compute) and optim.isdisjoint(compute)
    for cls in (EvidenceAuthorityV2,ScientificSamplingAuthorityV2,OptimizationScheduleAuthorityV2,ComputePackingAuthorityV2):
        assert all(f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING for f in dataclasses.fields(cls))


def test_common_core_cannot_silently_become_training_objective():
    c=_contract()
    bad=dataclasses.replace(c.evidence,comparable_support_role="TRAINING_LOSS")
    with pytest.raises(ValueError): dataclasses.replace(c,evidence=bad).validate()


def test_hardware_cannot_supply_scientific_or_update_geometry_fields():
    compute={f.name for f in dataclasses.fields(ComputePackingAuthorityV2)}
    forbidden={"target_estimand_policy_id","proposal_policy_id","importance_weight_policy_id","relational_weight_policy_id","effective_cells_per_update","training_presentations","ema_half_life_presentations"}
    assert compute.isdisjoint(forbidden)
