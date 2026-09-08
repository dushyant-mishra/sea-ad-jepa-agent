from __future__ import annotations
import dataclasses
import pytest

from sea_ad_jepa.v5.data_contract_v2 import (
    EvidenceAuthorityV2,
    ScientificSamplingAuthorityV2,
    ComputePackingAuthorityV2,
    ProductionDataContractV2,
)


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
        ),
        compute_packing=ComputePackingAuthorityV2(
            effective_cells_per_update=128,
            max_teacher_tokens_per_microbatch=100_000,
            masked_views_per_cell=4,
            training_presentations=1,
            ema_half_life_presentations=1,
            rng_authority_id="RNG_PENDING",
            relational_compute_budget_id="RELATIONAL_COMPUTE_BUDGET_PENDING",
        ),
    )


def test_contract_validates_explicit_separated_authorities():
    _contract().validate()


def test_common_support_cannot_silently_become_objective_role():
    c=_contract()
    bad=dataclasses.replace(c.evidence, comparable_support_role="TRAINING_LOSS")
    with pytest.raises(ValueError):
        dataclasses.replace(c,evidence=bad).validate()


def test_relational_sampling_is_not_a_scalar_group_size_weight():
    fields={f.name for f in dataclasses.fields(ScientificSamplingAuthorityV2)}
    assert "relational_sampling_policy_id" in fields
    assert not any("triplets_per" in name for name in fields)


def test_compute_budget_is_separate_from_relational_sampling_policy():
    science={f.name for f in dataclasses.fields(ScientificSamplingAuthorityV2)}
    compute={f.name for f in dataclasses.fields(ComputePackingAuthorityV2)}
    assert "relational_sampling_policy_id" in science
    assert "relational_compute_budget_id" in compute
    assert science.isdisjoint(compute)


def test_target_and_proposal_are_distinct_required_fields():
    c=_contract()
    bad=dataclasses.replace(c.scientific_sampling, proposal_policy_id="")
    with pytest.raises(ValueError):
        dataclasses.replace(c,scientific_sampling=bad).validate()


def test_no_production_numerical_defaults_exist():
    for cls in (EvidenceAuthorityV2,ScientificSamplingAuthorityV2,ComputePackingAuthorityV2):
        for f in dataclasses.fields(cls):
            assert f.default is dataclasses.MISSING
            assert f.default_factory is dataclasses.MISSING


def test_boolean_cannot_satisfy_positive_compute_integer():
    c=_contract()
    bad=dataclasses.replace(c.compute_packing,effective_cells_per_update=True)
    with pytest.raises(ValueError):
        dataclasses.replace(c,compute_packing=bad).validate()
