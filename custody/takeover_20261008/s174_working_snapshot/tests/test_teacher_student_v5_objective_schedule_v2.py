from __future__ import annotations
from dataclasses import MISSING,fields
import json, math
from pathlib import Path
import pytest
from sea_ad_jepa.v5.exposure_schedule_v1 import ema_momentum_for_presentations,cumulative_ema_decay_for_presentations
from sea_ad_jepa.v5.schedule_authority_v2 import ProductionScheduleAuthorityV2
ROOT=Path(__file__).resolve().parents[1]


def test_estimand_v2_quantifies_source_balanced_proposal_efficiency_without_selecting_it():
    p=json.loads((ROOT/'docs/agent/READER_FIT_SCIENTIFIC_ESTIMAND_ANALYSIS_V2.json').read_text())
    donor=p['candidate_estimands']['donor_uniform']['proposal_diagnostics']
    assert donor['cell_uniform']['effective_sample_size_fraction']==pytest.approx(0.09677462572795768)
    assert donor['source_uniform_cell_within_source']['effective_sample_size_fraction']==pytest.approx(0.4057806895482118)
    assert donor['source_uniform_cell_within_source']['importance_weight_max']<85
    assert p['selected_base_jepa_estimand'] is None


def test_donor_primary_candidate_has_no_proposal_or_triplet_budget_and_no_authority():
    p=json.loads((ROOT/'docs/agent/TEACHER_STUDENT_V5_DONOR_PRIMARY_OBJECTIVE_CANDIDATE_V1.json').read_text())
    assert p['proposal_policy']['selected'] is None
    assert p['relational_scientific_target']['triplet_budget'] is None
    assert p['training_authorized'] is False and p['execution_authorized'] is False
    assert p['relational_scientific_target']['group_capacity_weighting']=='NONE'


def test_exposure_based_ema_decay_is_partition_invariant():
    half=100_000
    a=cumulative_ema_decay_for_presentations(half_life_presentations=half,update_presentations=[25_000,25_000,25_000,25_000])
    b=cumulative_ema_decay_for_presentations(half_life_presentations=half,update_presentations=[10_000,30_000,60_000])
    assert a==pytest.approx(.5,rel=1e-14,abs=1e-14)
    assert b==pytest.approx(.5,rel=1e-14,abs=1e-14)
    assert ema_momentum_for_presentations(half_life_presentations=half,presentations_this_update=50_000)==pytest.approx(math.sqrt(.5))


def test_production_schedule_v2_has_no_defaults_and_separate_target_proposal_compute_fields():
    names={f.name for f in fields(ProductionScheduleAuthorityV2)}
    assert {'base_scientific_target_policy_id','base_proposal_policy_id','relational_scientific_target_policy_id','relational_proposal_policy_id','max_teacher_tokens_per_microbatch'} <= names
    for f in fields(ProductionScheduleAuthorityV2):
        assert f.default is MISSING and f.default_factory is MISSING
    with pytest.raises(TypeError): ProductionScheduleAuthorityV2()  # type: ignore[call-arg]
