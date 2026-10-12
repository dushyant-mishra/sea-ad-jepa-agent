from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/"scripts"/"v79"
sys.path.insert(0,str(HERE))
import run_v79_v2_core_qualification as Q  # noqa: E402

_spec=importlib.util.spec_from_file_location("v79_qrunner_fixture",ROOT/"tests/v79/test_v79_v2_core_qualification_runner.py")
_fx=importlib.util.module_from_spec(_spec); assert _spec.loader is not None; _spec.loader.exec_module(_fx)


def _calibration():
    return [{"bin_index":i,"lower":i/10,"upper":(i+1)/10,"n":1 if i==5 else 0,
             "mean_predicted":0.5 if i==5 else None,"observed_rate":1.0 if i==5 else None} for i in range(10)]


def _heldout(part:str):
    if part=="detection":
        same={"schema":"V79_V2_CORE_DETECTION_HELDOUT_V1","replicate_mode":"same_donor","posterior_draws":200,
              "gauss_hermite_nodes":None,"n_measured":1,"mean_log_loss":0.693,"predicted_prevalence":0.5,
              "observed_prevalence":1.0,"calibration_bins":_calibration()}
        new=dict(same); new["replicate_mode"]="new_donor"; new["gauss_hermite_nodes"]=40
    else:
        same={"schema":"V79_V2_CORE_POSITIVE_HELDOUT_V1","replicate_mode":"same_donor","posterior_draws":200,
              "gauss_hermite_nodes":None,"n_positive":1,"mean_lpd":-0.919}
        new=dict(same); new["replicate_mode"]="new_donor"; new["gauss_hermite_nodes"]=40
    return {"same_donor":same,"new_donor":new}


def test_checkpoint_refuses_missing_heldout_predictive_summary(tmp_path):
    item=_fx._queue()[0]; out=tmp_path/"r"; out.mkdir(); r=_fx._receipt(item); r.pop("heldout_predictive")
    _fx._write_receipt(out/f"fit_{item['fit_id']}.json",r)
    with pytest.raises(Q.QualificationRunRefused):
        Q._validate_existing_receipt(out/f"fit_{item['fit_id']}.json",item,expected_code_sha=_fx.CODE,expected_seed=_fx.SEED)


def test_checkpoint_accepts_exact_truth_blind_heldout_schema(tmp_path):
    item=_fx._queue()[0]; out=tmp_path/"r"; out.mkdir(); r=_fx._receipt(item); r["heldout_predictive"]=_heldout(item["part"])
    _fx._write_receipt(out/f"fit_{item['fit_id']}.json",r)
    got=Q._validate_existing_receipt(out/f"fit_{item['fit_id']}.json",item,expected_code_sha=_fx.CODE,expected_seed=_fx.SEED)
    assert got["heldout_predictive"]["new_donor"]["gauss_hermite_nodes"]==40


def test_checkpoint_refuses_wrong_heldout_mode_or_gh_nodes(tmp_path):
    item=_fx._queue()[0]; out=tmp_path/"r"; out.mkdir(); r=_fx._receipt(item); r["heldout_predictive"]=_heldout(item["part"])
    r["heldout_predictive"]["new_donor"]["gauss_hermite_nodes"]=20
    _fx._write_receipt(out/f"fit_{item['fit_id']}.json",r)
    with pytest.raises(Q.QualificationRunRefused):
        Q._validate_existing_receipt(out/f"fit_{item['fit_id']}.json",item,expected_code_sha=_fx.CODE,expected_seed=_fx.SEED)
