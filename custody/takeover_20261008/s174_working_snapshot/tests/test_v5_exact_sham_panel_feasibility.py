import itertools, random
import numpy as np
import pytest
import importlib.util, sys
from pathlib import Path

# Vendored unchanged from the independent CPU workstream
# (JEPA_CPU_FINAL_AUDITED_HANDOFF_20260928). Loaded by path so the test runs
# against the file actually committed under scripts/v5/independent/.
_P = Path(__file__).resolve().parents[1] / "scripts" / "v5" / "independent" /     "exact_sham_panel_feasibility.py"
_spec = importlib.util.spec_from_file_location("exact_sham_panel_feasibility", _P)
_m = importlib.util.module_from_spec(_spec)
sys.modules["exact_sham_panel_feasibility"] = _m
_spec.loader.exec_module(_m)
exact_disjoint_capacity = _m.exact_disjoint_capacity
witness_allocation = _m.witness_allocation


def brute_max(pools):
    """Independent exhaustive feasible-four-tuple DFS for tiny universes."""
    quads=[tuple(q) for q in itertools.product(*pools) if len(set(q))==4]
    def count(available):
        best=0
        for q in quads:
            s=set(q)
            if s<=available:
                best=max(best,1+count(available-s))
        return best
    return count(set().union(*(set(p) for p in pools)))

@pytest.mark.parametrize('roster,expected',[
    ([[0,3,6,8],[0,4,11],[3,7,10],[0,6,8]],2),
    ([[1,2],[1,2],[1,2],[1,2]],0),
    ([[0,1],[2,3],[4,5],[6,7]],2),
    ([[0],[1],[2],[3]],1),
    ([[],[1],[2],[3]],0),
    ([[0,1,2,3]]*4,1),
    ([list(range(199)),list(range(199,398)),list(range(398,597)),list(range(597,796))],199)
])
def test_hall_exact_with_expected(roster,expected):
    x=exact_disjoint_capacity(roster,199)
    assert x['max_exact_disjoint_panels']==expected
    assert x['requested_achievable']==(expected>=199)
    if expected and expected<=2:
        a=witness_allocation(roster,expected)
        assert len(a['panels'])==expected


def test_hall_random_small_universe_against_independent_bruteforce():
    rng=random.Random(20260928)
    for _ in range(120):
        universe=list(range(rng.randint(4,7)))
        pools=[rng.sample(universe,rng.randrange(1,5)) for _ in range(4)]
        want=brute_max(pools)
        found=exact_disjoint_capacity(pools)['max_exact_disjoint_panels']
        assert found==want,(pools,want,found)
        if found:
            a=witness_allocation(pools,found)
            flat=[g for row in a['panels'] for g in row]
            assert len(flat)==len(set(flat))==4*found


def test_hall_exposes_greedy_false_negative_witness():
    ps=[[0,3,6,8],[0,4,11],[3,7,10],[0,6,8]]
    assert exact_disjoint_capacity(ps)['max_exact_disjoint_panels']==2


def test_identical_many_gene_pools_do_not_falsely_claim_199():
    ps=[list(range(399))]*4
    result=exact_disjoint_capacity(ps,capped_at=199)
    assert result['max_exact_disjoint_panels']==99
    assert result['limiting_subset']['slots_n']==4


def test_sparse_matching_k199_exact_witness():
    ps=[list(range(i*199,(i+1)*199)) for i in range(4)]
    a=witness_allocation(ps,199)
    assert a['n_panels']==199
    assert len(set(g for row in a['panels'] for g in row))==796


def test_invalid_noninteger_address_fails():
    with pytest.raises(TypeError): exact_disjoint_capacity([[1,2.0],[3],[4],[5]])
    with pytest.raises(TypeError): exact_disjoint_capacity([[True],[3],[4],[5]])
    with pytest.raises(ValueError): exact_disjoint_capacity([[-1],[3],[4],[5]])


def test_conflicting_source_intersection_is_empty():
    src_a=[{100,101},{200,201},{300,301},{400,401}]
    src_b=[{102,103},{202,203},{302,303},{402,403}]
    combined=[a|b for a,b in zip(src_a,src_b)]
    intersection=[a&b for a,b in zip(src_a,src_b)]
    assert exact_disjoint_capacity(combined)['max_exact_disjoint_panels']==4
    assert exact_disjoint_capacity(intersection)['max_exact_disjoint_panels']==0
    # A pooled universe may be large despite no single sham valid in every source.
