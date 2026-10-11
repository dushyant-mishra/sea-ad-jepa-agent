"""Contract for comparing historical V3 replay with mask-corrected V4 replay."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))
import compare_v79_s174_masked_replay as C  # noqa: E402


def _gene(g, det=(.50,.45,.42,.40,.39), pos=(-1.0,-.9,-.8,-.79,-.80), op_rule=None):
    models = ["depth_linear","depth_quad","depth_class","depth_class_source","depth_class_source_operator"]
    d = {m:{"mean_logloss":x} for m,x in zip(models,det)}
    p = {m:{"mean_lpd":x} for m,x in zip(models,pos)}
    sens_d = {"0.25":{"mean_logloss":det[-1]},"1.0":{"mean_logloss":det[-1]},"4.0":{"mean_logloss":det[-1]}}
    sens_p = {"0.25":{"mean_lpd":pos[-1]},"1.0":{"mean_lpd":pos[-1]},"4.0":{"mean_lpd":pos[-1]}}
    return ({"gene_position":g,"models":d,"operator_penalty_sensitivity":sens_d},
            {"gene_position":g,"models":p,"operator_penalty_sensitivity":sens_p})


def _replay(masked=False):
    gd0,gp0=_gene(3); gd1,gp1=_gene(7,det=(.52,.50,.48,.47,.46),pos=(-1.1,-1.0,-.95,-.94,-.96))
    return {
        "schema":"V79_S174_STRUCTURE_REPLAY_DEVELOPMENT_V4_MASKED" if masked else "V79_S174_STRUCTURE_REPLAY_DEVELOPMENT_V3",
        "cache_sha256":"cache",
        "panel_positions_internal":[3,7],
        "support_panel_positions_internal":[3],
        "folds":3,"seed":20261011,"permutations":99,
        "operator_increment_robustness":{
            "detection":{"ruling":"PRIOR_SENSITIVE__UNRESOLVED","by_lambda":{}},
            "positive_lognormal":{"ruling":"NOT_SUPPORTED","by_lambda":{}}},
        "random_effect_support":{
            "detection":{"donor":{"supported_genes":1,"eligible_genes":1},"operator":{"supported_genes":1,"eligible_genes":1},"donor_class_increment":{"supported_genes":0,"eligible_genes":1}},
            "positive":{"donor":{"supported_genes":1,"eligible_genes":1},"operator":{"supported_genes":0,"eligible_genes":1},"donor_class_increment":{"supported_genes":0,"eligible_genes":1}}},
        "per_gene_detection":[gd0,gd1],"per_gene_positive":[gp0,gp1],
        "structural_support":({"n_unmeasured_entries":11,"unmeasured_fraction":.02,"affected_cache_genes":1} if masked else None),
    }


def test_comparison_reports_a_to_h_and_mask_delta():
    out=C.compare_replays(_replay(False),_replay(True))
    assert out["panel_identity"] == "MATCH"
    assert out["A_quadratic_depth"]["detection"]["masked_median_increment"] > 0
    assert out["B_broad_class"]["positive"]["masked_median_increment"] > 0
    assert out["C_source"]["detection"]["masked_median_increment"] > 0
    assert out["D_operator"]["detection_ruling_masked"] == "PRIOR_SENSITIVE__UNRESOLVED"
    assert out["E_donor"]["detection"]["masked_supported_genes"] == 1
    assert out["F_operator_beyond_donor"]["detection"]["masked_supported_genes"] == 1
    assert out["G_donor_class"]["detection"]["masked_supported_genes"] == 0
    assert out["H_lognormal"]["masked_positive_genes_evaluable"] == 2
    assert out["structural_support"]["n_unmeasured_entries"] == 11
    assert out["controller_ruling"] == "NOT_AUTOMATED__CONTROLLER_REVIEW_REQUIRED"


def test_comparison_fails_closed_on_panel_or_frozen_setting_mismatch():
    old=_replay(False); new=_replay(True); new["panel_positions_internal"]=[3,8]
    with pytest.raises(SystemExit): C.compare_replays(old,new)
    new=_replay(True); new["seed"]=17
    with pytest.raises(SystemExit): C.compare_replays(old,new)


def test_cli_writes_machine_readable_comparison(tmp_path):
    oldp=tmp_path/"old.json"; newp=tmp_path/"new.json"; outp=tmp_path/"cmp.json"
    oldp.write_text(json.dumps(_replay(False))); newp.write_text(json.dumps(_replay(True)))
    C.main([str(oldp),str(newp),str(outp)])
    out=json.loads(outp.read_text())
    assert out["schema"] == "V79_S174_V3_VS_V4_MASKED_COMPARISON_V1"
    assert out["controller_ruling"].startswith("NOT_AUTOMATED")
