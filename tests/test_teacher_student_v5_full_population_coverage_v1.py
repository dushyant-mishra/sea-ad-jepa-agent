from fractions import Fraction
import pytest
from sea_ad_jepa.v5.full_population_coverage_schedule_v1 import CoverageCell,build_coverage_first_schedule,expanded_presentation_keys,exact_target_mass_by_donor

def fixture_cells():
    return [CoverageCell(1,"D1","D1/O1","S1"),CoverageCell(2,"D1","D1/O1","S1"),CoverageCell(3,"D1","D1/O2","S1"),CoverageCell(4,"D2","D2/O1","S2"),CoverageCell(5,"D2","D2/O1","S2"),CoverageCell(6,"D2","D2/O1","S2"),CoverageCell(7,"D2","D2/O2","S2")]

def test_every_cell_is_covered_and_small_groups_are_topped_up():
    cells=fixture_cells(); s=build_coverage_first_schedule(cells,min_presentations_per_group=4,max_presentations_per_cell=8,authority_seed=17)
    assert s.unique_cells==7 and s.all_cells_covered
    expanded=expanded_presentation_keys(s); assert set(expanded)=={1,2,3,4,5,6,7}
    by_group={}; by_key={c.stable_cell_key:c for c in cells}
    for key in expanded: by_group[by_key[key].group_id]=by_group.get(by_key[key].group_id,0)+1
    assert min(by_group.values())>=4

def test_target_mass_stays_exactly_donor_uniform_despite_repeats():
    cells=fixture_cells(); s=build_coverage_first_schedule(cells,min_presentations_per_group=5,max_presentations_per_cell=8,authority_seed=23)
    assert exact_target_mass_by_donor(s,cells)=={"D1":Fraction(1,2),"D2":Fraction(1,2)}
    assert len({x.importance_weight for x in s.presentations})>1

def test_schedule_is_deterministic_and_seed_only_changes_topup_identity():
    cells=fixture_cells()
    a=build_coverage_first_schedule(cells,min_presentations_per_group=4,max_presentations_per_cell=8,authority_seed=1)
    b=build_coverage_first_schedule(cells,min_presentations_per_group=4,max_presentations_per_cell=8,authority_seed=1)
    c=build_coverage_first_schedule(cells,min_presentations_per_group=4,max_presentations_per_cell=8,authority_seed=2)
    assert a==b and a.unique_cells==c.unique_cells==7 and a.total_presentations==c.total_presentations

def test_cap_failure_is_fail_closed():
    with pytest.raises(ValueError,match="above the frozen cap"):
        build_coverage_first_schedule([CoverageCell(1,"D","D/O","S")],min_presentations_per_group=16,max_presentations_per_cell=8,authority_seed=1)

def test_group_cannot_span_donors():
    with pytest.raises(ValueError,match="one donor"):
        build_coverage_first_schedule([CoverageCell(1,"D1","G","S"),CoverageCell(2,"D2","G","S")],min_presentations_per_group=2,max_presentations_per_cell=2,authority_seed=1)
