from __future__ import annotations
import math
import pytest
from sea_ad_jepa.v5.proposal_policy_v1 import (
    DonorCapacity,
    derive_exposure_constrained_target_mixture,
    relational_anchor_cell_target_group_probabilities,
    relational_direct_target_group_probabilities,
)


def _toy_capacities():
    return [
        DonorCapacity('A', 10), DonorCapacity('A', 90),
        DonorCapacity('B', 20), DonorCapacity('B', 80),
    ]


def test_exposure_rule_has_no_default_horizon_or_cap():
    with pytest.raises(TypeError):
        derive_exposure_constrained_target_mixture(_toy_capacities())  # type: ignore[call-arg]


def test_largest_feasible_alpha_hits_declared_exposure_boundary():
    caps=_toy_capacities()
    # At H=400, donor-target q gives the 10-cell donor 10 expected exposures/cell.
    # Constrain it to <=5, forcing alpha away from 1.
    r=derive_exposure_constrained_target_mixture(
        caps,total_presentations=400,max_expected_per_cell_exposure=5.0)
    assert 0.0 < r.alpha_donor_target < 1.0
    assert r.expected_max_per_cell_exposure == pytest.approx(5.0, rel=1e-12, abs=1e-12)
    assert r.alpha_donor_target == pytest.approx(r.feasible_alpha_max)
    # Moving infinitesimally higher would violate the active boundary.
    assert r.effective_sample_size_fraction > 0.0
    assert r.importance_weight_max_to_min_ratio >= 1.0


def test_if_direct_target_sampling_meets_exposure_cap_alpha_is_one_and_weights_are_one():
    r=derive_exposure_constrained_target_mixture(
        _toy_capacities(),total_presentations=40,max_expected_per_cell_exposure=10.0)
    assert r.alpha_donor_target == pytest.approx(1.0)
    assert r.importance_weight_min == pytest.approx(1.0)
    assert r.importance_weight_max == pytest.approx(1.0)
    assert r.effective_sample_size_fraction == pytest.approx(1.0)


def test_infeasible_exposure_cap_fails_closed():
    # Every proposal distribution over 200 cells has some cell probability >=1/200.
    # H=1000 and cap=.1 is impossible by a wide margin for this restricted family.
    with pytest.raises(ValueError):
        derive_exposure_constrained_target_mixture(
            _toy_capacities(),total_presentations=1000,max_expected_per_cell_exposure=.1)


def test_relational_v2_direct_target_is_donor_then_anchor_cell_prevalence_not_equal_group():
    p=relational_anchor_cell_target_group_probabilities({'d0':{'o0':3,'o1':9},'d1':{'o2':6}})
    assert sum(p.values()) == pytest.approx(1.0)
    assert p[('d0','o0')] == pytest.approx(.5*(3/12))
    assert p[('d0','o1')] == pytest.approx(.5*(9/12))
    assert p[('d1','o2')] == pytest.approx(.5)
    assert p[('d0','o1')] == pytest.approx(3*p[('d0','o0')])


def test_relational_v2_group_probability_uses_linear_anchor_prevalence_not_triplet_capacity():
    p=relational_anchor_cell_target_group_probabilities({'d0':{'small':3,'large':30}})
    # Linear cell prevalence ratio 10x, not anchored-triplet capacity ratio 4060x.
    assert p[('d0','large')]/p[('d0','small')] == pytest.approx(10.0)


def test_relational_v2_direct_target_rejects_non_estimable_group_or_empty_donor():
    with pytest.raises(ValueError):
        relational_anchor_cell_target_group_probabilities({'d0':{'o0':2}})
    with pytest.raises(ValueError):
        relational_anchor_cell_target_group_probabilities({'d0':{'o0':3},'d1':{}})


def test_v1_equal_group_helper_remains_only_for_historical_replay_comparison():
    p=relational_direct_target_group_probabilities({'d0':['o0','o1'],'d1':['o2']})
    assert p[('d0','o0')] == pytest.approx(.25)
    assert p[('d0','o1')] == pytest.approx(.25)


def test_base_proposal_coverage_profile_is_descriptive_and_exposes_real_tradeoff():
    import json
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    p=json.loads((root/'docs/agent/READER_FIT_BASE_PROPOSAL_COVERAGE_PROFILE_V1.json').read_text())
    assert p['selection']['selected_policy_id'] is None and p['selection']['selected_alpha'] is None
    target=p['proposal_families']['TARGET_DONOR_UNIFORM_CELL_WITHIN_DONOR']
    source=p['proposal_families']['SOURCE_UNIFORM_CELL_WITHIN_SOURCE']
    coverage=p['proposal_families']['DONOR_UNIFORM_OPERATOR_GROUP_UNIFORM_CELL_WITHIN_GROUP__PROPOSAL_ONLY']
    assert target['importance_ess_fraction'] == pytest.approx(1.0)
    assert source['importance_ess_fraction'] == pytest.approx(0.40578068954821195)
    assert coverage['importance_ess_fraction'] == pytest.approx(0.4552965729369689)
    assert coverage['expected_group_presentations_at_H_equals_reader_fit_cells']['min'] > 1800
    assert source['expected_per_cell_exposure_at_H_equals_reader_fit_cells']['max'] < 8
    assert coverage['expected_per_cell_exposure_at_H_equals_reader_fit_cells']['max'] > 2000


def test_proposal_v2_reopens_base_derivation_instead_of_backdoor_selecting_source_mixture():
    import json
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    p=json.loads((root/'docs/agent/TEACHER_STUDENT_V5_PROPOSAL_AUTHORITY_V2.json').read_text())
    assert p['base']['final_derivation_policy_id'] is None
    assert p['base']['selected_policy_id'] is None
    assert p['base']['selected_parameters'] is None
    assert len(p['base']['required_before_final_derivation']) == 4
