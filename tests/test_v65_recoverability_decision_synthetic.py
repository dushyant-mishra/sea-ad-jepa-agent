from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def _load():
    p=ROOT/"scripts/v64/qualify_recoverability_decision_synthetic_v1.py"
    spec=importlib.util.spec_from_file_location("rq",p)
    assert spec and spec.loader
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def test_fully_recoverable_nested_fixture_selects_rank16():
    m=_load()
    full={k:[m.donor() for _ in range(4)] for k in m.RANKS}
    assert m.choose(full,"LARGEST_CONTIGUOUS_ELIGIBLE_RANK_FROM_2_UPWARD")==16
    assert m.classify(16)=="RNA_RECOVERABLE"

def test_partial_nested_fixture_selects_highest_contiguous_rank():
    m=_load()
    x={k:[m.donor() for _ in range(4)] for k in m.RANKS}
    x[8][0]=m.donor(pass_delta=False)
    x[16][0]=m.donor(pass_delta=False)
    assert m.choose(x,"LARGEST_CONTIGUOUS_ELIGIBLE_RANK_FROM_2_UPWARD")==4
    assert m.classify(4)=="PARTIALLY_RNA_RECOVERABLE"

def test_noncontiguous_higher_pass_does_not_skip_failed_rank():
    m=_load()
    x={k:[m.donor() for _ in range(4)] for k in m.RANKS}
    x[4][0]=m.donor(pass_delta=False)
    assert m.choose(x,"LARGEST_CONTIGUOUS_ELIGIBLE_RANK_FROM_2_UPWARD")==2

def test_shortcut_and_pairing_null_fail_closed():
    m=_load()
    shortcut={k:[m.donor(candidate_r2=.50,tech_r2=.495,global_r2=.20)
                 for _ in range(4)] for k in m.RANKS}
    permfail={k:[m.donor(pass_perm=False) for _ in range(4)] for k in m.RANKS}
    assert m.choose(shortcut,"LARGEST_CONTIGUOUS_ELIGIBLE_RANK_FROM_2_UPWARD")==0
    assert m.choose(permfail,"LARGEST_CONTIGUOUS_ELIGIBLE_RANK_FROM_2_UPWARD")==0

def test_current_contract_names_contiguous_rule_not_smallest_rule():
    t=(ROOT/"docs/agent/V65_PRIVILEGED_RECOVERABILITY_PRECISION_DECISION_CONTRACT_V2_20260930.md").read_text()
    assert "largest contiguous eligible rank" in t
    assert "Skipping over a failed lower-rank projection" in t
    assert "smallest-eligible rule is superseded prospectively" in t
    assert "aggregate-and-shell requirement" in t
    # This file is a narrow rank-policy regression. Incremental-shell software
    # qualification lives in the V2 decision-engine/numerical smoke tests.
