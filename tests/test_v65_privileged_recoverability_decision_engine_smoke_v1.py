from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def _load():
    p=ROOT/"scripts/v64/privileged_recoverability_decision_engine_smoke_v1.py"
    spec=importlib.util.spec_from_file_location("v65_recoverability_engine",p)
    assert spec and spec.loader
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_v65_decision_engine_smoke_passes():
    out=_load().run_smoke()
    assert out["pass"] is True
    assert out["results"]["partial_contiguous_selected_rank"]==4
    assert out["results"]["partial_classification"]=="PARTIALLY_RNA_RECOVERABLE"
    assert out["results"]["full_rank_selected"]==16
    assert out["results"]["lower_shell_failure_blocks_higher_ranks"]==0
    assert out["results"]["technical_shortcut_selected_rank"]==0
    assert out["results"]["validation_failure_locked_rank"]==0
    assert out["results"]["tie_fails_closed"] is True
    assert out["test_values_used_for_rank_selection"] is False
    assert out["privileged_private_assignable"] is False
    assert out["training_authorized"] is False
    assert out["real_paired_outcome_opened"] is False


def test_aggregate_success_cannot_hide_failed_incremental_shell():
    m=_load()
    sc=m.synthetic_scenarios()
    agg,shell=sc["partial"]
    assert m._validation_metric_set_eligible(agg[8])
    assert not m._validation_metric_set_eligible(shell[8])
    assert m.select_validation_rank(agg,shell)==4


def test_full_nested_fixture_selects_rank16_only_when_all_shells_pass():
    m=_load()
    agg,shell=m.synthetic_scenarios()["full"]
    assert all(m.validation_rank_eligible(agg[k],shell[k]) for k in m.RANKS)
    assert m.select_validation_rank(agg,shell)==16


def test_lower_shell_failure_blocks_higher_ranks():
    m=_load()
    agg,shell=m.synthetic_scenarios()["lower_fail"]
    assert not m.validation_rank_eligible(agg[2],shell[2])
    assert m.select_validation_rank(agg,shell)==0


def test_technical_shortcut_is_unqualified_despite_high_r2():
    m=_load()
    agg,shell=m.synthetic_scenarios()["shortcuts"]
    assert all(d["candidate_r2"]>0.9 for d in agg[2])
    assert m.select_validation_rank(agg,shell)==0


def test_validation_failure_cannot_be_rescued_by_test():
    m=_load()
    vA,vS=m.synthetic_scenarios()["weak"]
    tA,tS=m.synthetic_scenarios()["spectacular"]
    selected=m.select_validation_rank(vA,vS)
    assert selected==0
    assert m.classify(selected,vA,tA,vS,tS)=="UNQUALIFIED"


def test_test_confirmation_cannot_retune_rank():
    m=_load()
    vA,vS=m.synthetic_scenarios()["partial"]
    selected=m.select_validation_rank(vA,vS)
    assert selected==4
    bad=[
        m.donor(.12,.05,.08),
        m.donor(.13,.05,.08),
        m.donor(.11,.05,.08),
        m.donor(.12,.05,.08),
    ]
    tA={k:bad for k in m.RANKS}
    tS={k:bad for k in m.RANKS}
    assert m.classify(selected,vA,tA,vS,tS)=="UNQUALIFIED"
    assert selected==4


def test_test_must_replicate_every_shell_through_locked_rank():
    m=_load()
    vA,vS=m.synthetic_scenarios()["partial"]
    selected=m.select_validation_rank(vA,vS)
    assert selected==4
    good=[
        m.donor(.36,.07,.16),
        m.donor(.35,.07,.15),
        m.donor(.34,.08,.15),
        m.donor(.37,.08,.16),
    ]
    fail=[
        m.donor(.12,.05,.11,geometry=False),
        m.donor(.13,.05,.11,geometry=False),
        m.donor(.14,.05,.11,geometry=False),
        m.donor(.15,.05,.11,geometry=False),
    ]
    tA={k:good for k in m.RANKS}
    tS={k:good for k in m.RANKS}
    tS[4]=fail
    assert not m.test_confirmed(selected,vA,tA,vS,tS)


def test_materiality_margin_is_median_not_per_donor():
    m=_load()
    donors=[
        m.donor(.22,.10,.20),  # delta 0.02
        m.donor(.40,.10,.20),
        m.donor(.42,.10,.20),
        m.donor(.41,.10,.20),
    ]
    assert all(d["delta_r2"]>0 for d in donors)
    assert np.median([d["delta_r2"] for d in donors])>=m.DELTA_MARGIN
    assert m._validation_metric_set_eligible(donors)


def test_test_confirmation_does_not_inherit_validation_only_technical_margin():
    m=_load()
    validation=[
        m.donor(.40,.10,.20),
        m.donor(.41,.10,.20),
        m.donor(.42,.10,.20),
        m.donor(.43,.10,.20),
    ]
    test=[
        m.donor(.305,.300,.20),
        m.donor(.40,.10,.20),
        m.donor(.41,.10,.20),
        m.donor(.42,.10,.20),
    ]
    assert test[0]["candidate_r2"]-test[0]["technical_r2"] < m.TECH_CLOSE_MARGIN
    assert m._test_metric_set_confirmed(validation,test)


def test_projector_is_sign_invariant_and_rank_fixed():
    m=_load()
    rng=np.random.default_rng(44)
    z=rng.normal(size=(500,4))
    p=z.copy()
    a=m.target_projector(z,p,2)
    assert a["qualified"]
    b=m.target_projector(z,-p,2)
    assert b["qualified"]
    assert np.allclose(a["projector"],b["projector"],atol=1e-10)


def test_singular_value_boundary_tie_fails_closed():
    m=_load()
    eye=np.eye(4)
    r=m.target_projector(eye,eye,2,tie_tol=1e-12)
    assert r["qualified"] is False
    assert r["reason"]=="SINGULAR_VALUE_TIE_AT_SELECTION_BOUNDARY"


def test_decision_state_forbids_private_label_from_nonrecoverability():
    import json
    p=json.loads((ROOT/"results/v64/V65_PRIVILEGED_RECOVERABILITY_DECISION_STATE_V1.json").read_text())
    assert p["classifications"]["PRIVILEGED_PRIVATE"]=="NOT_ASSIGNABLE_BY_THIS_EXPERIMENT"
    assert p["governance"]["execution_authorized"] is False
    assert p["validation_rule"]["aggregate_and_incremental_shell_must_both_pass"] is True
    assert p["test_rule"]["aggregate_and_all_shells_through_selected_rank_must_pass"] is True
