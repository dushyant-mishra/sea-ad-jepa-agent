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
    assert out["results"]["lower_rank_failure_blocks_higher_ranks"]==0
    assert out["results"]["technical_shortcut_selected_rank"]==0
    assert out["results"]["validation_failure_locked_rank"]==0
    assert out["results"]["tie_fails_closed"] is True
    assert out["test_values_used_for_rank_selection"] is False
    assert out["privileged_private_assignable"] is False
    assert out["training_authorized"] is False
    assert out["real_paired_outcome_opened"] is False


def test_largest_contiguous_rank_wins_without_skipping_failed_rank():
    m=_load()
    partial,full,lower_fail,_,_,_=m.synthetic_scenarios()
    assert m.validation_rank_eligible(partial[2])
    assert m.validation_rank_eligible(partial[4])
    assert not m.validation_rank_eligible(partial[8])
    assert m.validation_rank_eligible(partial[16])
    assert m.select_validation_rank(partial)==4
    assert m.select_validation_rank(full)==16
    assert m.select_validation_rank(lower_fail)==0


def test_technical_shortcut_is_unqualified_despite_high_r2():
    m=_load()
    _,_,_,shortcuts,_,_=m.synthetic_scenarios()
    assert all(d["candidate_r2"]>0.9 for d in shortcuts[2])
    assert m.select_validation_rank(shortcuts)==0


def test_validation_failure_cannot_be_rescued_by_test():
    m=_load()
    _,_,_,_,weak,spectacular=m.synthetic_scenarios()
    selected=m.select_validation_rank(weak)
    assert selected==0
    assert m.classify(selected,None,spectacular)=="UNQUALIFIED"


def test_test_confirmation_cannot_retune_rank():
    m=_load()
    partial,_,_,_,_,_=m.synthetic_scenarios()
    selected=m.select_validation_rank(partial)
    assert selected==4
    bad_test=[
        m.donor(.12,.05,.08),
        m.donor(.13,.05,.08),
        m.donor(.11,.05,.08),
        m.donor(.12,.05,.08),
    ]
    assert m.classify(selected,partial[selected],bad_test)=="UNQUALIFIED"
    # No alternate-rank search is performed after TEST failure.
    assert selected==2


def test_projector_is_sign_invariant_and_rank_fixed():
    m=_load()
    rng=np.random.default_rng(44)
    z=rng.normal(size=(500,4))
    p=z.copy()
    a=m.target_projector(z,p,2)
    assert a["qualified"]
    # Flip signs of predicted coordinates; target-space projector should span same subspace.
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


def test_materiality_margin_is_median_not_per_donor():
    m=_load()
    # One donor has positive but sub-margin DELTA_R2; median remains well above 0.05.
    donors=[
        m.donor(.22,.10,.20),  # delta 0.02
        m.donor(.40,.10,.20),  # delta 0.20
        m.donor(.42,.10,.20),  # delta 0.22
        m.donor(.41,.10,.20),  # delta 0.21
    ]
    assert all(d["delta_r2"]>0 for d in donors)
    assert np.median([d["delta_r2"] for d in donors])>=m.DELTA_MARGIN
    assert m.validation_rank_eligible(donors)


def test_test_confirmation_does_not_inherit_validation_only_technical_margin():
    m=_load()
    validation=[
        m.donor(.40,.10,.20),
        m.donor(.41,.10,.20),
        m.donor(.42,.10,.20),
        m.donor(.43,.10,.20),
    ]
    # One TEST donor has only 0.005 advantage over technical baseline, but all TEST
    # requirements are met: DELTA_R2 > 0, median delta >= .05, candidate > 0,
    # permutation/geometry pass, and replication fraction passes.
    test=[
        m.donor(.305,.300,.20),
        m.donor(.40,.10,.20),
        m.donor(.41,.10,.20),
        m.donor(.42,.10,.20),
    ]
    assert test[0]["candidate_r2"]-test[0]["technical_r2"] < m.TECH_CLOSE_MARGIN
    assert m.test_confirmed(validation,test)
