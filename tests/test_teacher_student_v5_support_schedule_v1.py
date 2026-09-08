from __future__ import annotations
from dataclasses import MISSING, fields
import json
from pathlib import Path
import pytest
from sea_ad_jepa.v5.support_geometry_v1 import balanced_block_sizes, fixed_visible_evidence
from sea_ad_jepa.v5.schedule_authority_v1 import QUALIFICATION_MECHANICS_V1, ProductionScheduleAuthorityV1
ROOT=Path(__file__).resolve().parents[1]


def test_fixed_visible_budget_equalizes_universe_relative_evidence():
    h=fixed_visible_evidence(measured_count=18_736,visible_genes=10_000,vocabulary_size=41_238)
    s=fixed_visible_evidence(measured_count=35_076,visible_genes=10_000,vocabulary_size=41_238)
    assert h['visible_fraction_of_universe']==pytest.approx(s['visible_fraction_of_universe'])
    assert h['visible_fraction_within_measured']!=pytest.approx(s['visible_fraction_within_measured'])


def test_block_count_is_support_derived_and_has_no_default_budget():
    h=balanced_block_sizes(hidden_count=7_494,target_genes_per_block=512)
    s=balanced_block_sizes(hidden_count=14_030,target_genes_per_block=512)
    assert len(h)==15 and len(s)==28 and max(h)<=512 and max(s)<=512
    with pytest.raises(TypeError):
        balanced_block_sizes(hidden_count=100)  # type: ignore[call-arg]


def test_fixed_visible_budget_fails_if_data_cannot_supply_it():
    with pytest.raises(ValueError):
        fixed_visible_evidence(measured_count=18_736,visible_genes=18_737,vocabulary_size=41_238)


def test_support_overlap_profile_is_candidate_only_and_exact_common_core():
    p=json.loads((ROOT/'docs/agent/READER_FIT_SUPPORT_OVERLAP_PROFILE_V1.json').read_text())
    assert p['all_42_operators_measured_scalar']==17_186
    assert p['candidate_use_only'] is True and p['training_authorized'] is False
    assert p['common_core_materialization']['csv_sha256']=='8aa8dfebb481aa2e60b12ab0f581ba1a36063b6c12dc2d8514d5fe7a20ad07ac'


def test_production_schedule_schema_has_no_defaults_or_instance():
    assert QUALIFICATION_MECHANICS_V1.effective_batch==128
    for field in fields(ProductionScheduleAuthorityV1):
        assert field.default is MISSING
        assert field.default_factory is MISSING
    with pytest.raises(TypeError):
        ProductionScheduleAuthorityV1()  # type: ignore[call-arg]


def test_production_schedule_validation_fails_closed():
    bad=ProductionScheduleAuthorityV1(
        scientific_target_policy='donor_uniform',proposal_policy='donor_uniform',
        effective_cells_per_update=0,max_teacher_tokens_per_microbatch=1,masked_views_per_cell=1,
        evidence_policy_id='x',target_block_policy_id='y',training_presentations=1,
        ema_half_life_presentations=1,finite_relational_triplets_per_estimable_group=1,
        keyed_rng_authority_id='philox-v1')
    with pytest.raises(ValueError): bad.validate()
