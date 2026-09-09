from fractions import Fraction
import pytest

from sea_ad_jepa.v5.full_population_conditioning_authority_v1 import (
    FullPopulationConditioningAuthorityV1,
    full_coverage_weight_ratio_lower_bound,
    validate_realized_schedule_summary,
)

DONORS={"small":81,"large":174111}

def make_auth(num=58037,den=864):
    return FullPopulationConditioningAuthorityV1(
        reader_fit_population_authority_id="POP",
        donor_size_geometry_authority_id="DONOR_GEOM",
        donor_uniform_target_authority_id="DONOR_UNIFORM",
        full_unique_cell_coverage_required=True,
        minimum_group_presentations=16,
        max_presentations_per_cell=32,
        minimum_importance_ess_fraction=0.50,
        maximum_importance_weight_ratio_numerator=num,
        maximum_importance_weight_ratio_denominator=den,
    )

def test_exact_real_dataset_lower_bound_fraction():
    assert full_coverage_weight_ratio_lower_bound(DONORS,max_presentations_per_cell=32)==Fraction(58037,864)

def test_old_64x_rule_is_rejected_fail_closed():
    auth=make_auth(64,1)
    with pytest.raises(ValueError,match="mathematically incompatible"):
        auth.validate(DONORS)

def test_exact_lower_bound_is_feasible_as_a_constraint_boundary():
    check=make_auth().validate(DONORS)
    assert check["passed"] and check["weight_ratio_lower_bound"]==Fraction(58037,864)

def test_realized_summary_must_meet_every_frozen_constraint():
    auth=make_auth(68,1)
    summary={
        "all_cells_guaranteed_at_least_once":True,
        "minimum_group_presentations":16,
        "max_cell_multiplicity":32,
        "importance_ess_fraction":0.5009,
        "importance_weight_max_to_min_ratio":67.17245370370371,
    }
    assert validate_realized_schedule_summary(summary,authority=auth,donor_sizes=DONORS)["passed"]
    bad=dict(summary); bad["importance_ess_fraction"]=0.49
    with pytest.raises(ValueError,match="ESS floor"):
        validate_realized_schedule_summary(bad,authority=auth,donor_sizes=DONORS)

def test_no_numeric_defaults_exist():
    import inspect
    sig=inspect.signature(FullPopulationConditioningAuthorityV1)
    assert all(p.default is inspect._empty for p in sig.parameters.values())
