"""Fail-closed tests for the physical committed-data 33-target comparison."""
import copy
import math
import sys
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"analysis/therapeutic_perturbation_etl/scripts"))
import build_gse178317_support_qualified_comparison_v2 as mod

BASE=ROOT/"analysis/therapeutic_perturbation_etl"
COMPARISON=BASE/"outputs/gse178317/gse178317_vs_crisprbrain_engagement_v1.csv"
SUPPORT=BASE/"evidence/gse178317_recovery/gse178317_guide_assignment_receipt_v2_lanegate.json"

def original():
    rows,receipt,comparison_sha,support_sha=mod.load_inputs(COMPARISON,SUPPORT)
    assert comparison_sha==mod.SOURCE_COMPARISON_SHA256
    assert len(support_sha)==64
    return rows,receipt

def test_actual_committed_support_qualified_calculation_and_scope(tmp_path):
    rows,receipt=original()
    qualified,result=mod.calculate(rows,receipt)
    assert len(qualified)==33
    assert result["excluded_nonqualified_targets"]==["AARS","LSM6"]
    assert result["direction_agreement"]=={"both_negative":33,"denominator":33}
    assert result["spearman_rho"]==pytest.approx(0.7473262032085561,abs=1e-12)
    assert result["pearson_r"]==pytest.approx(0.6397544786275293,abs=1e-12)
    assert result["magnitude_ratio_of_medians"]==pytest.approx(2.9323062487961007,abs=1e-12)
    assert result["reference_significant_fdr_lt_0_05"]==17
    assert result["reference_nonsignificant_fdr_ge_0_05"]==16
    assert result["independent_validation"] is False
    assert result["biological_uncertainty_estimable"] is False
    assert result["prospective_confirmation_eligible"] is False
    assert result["jepa_prediction_used"] is False
    out=tmp_path/"new-v2"
    saved=mod.run(COMPARISON,SUPPORT,out)
    assert saved["provenance"]["output_csv_sha256"]==mod.digest(
        (out/"gse178317_support_qualified_reference_comparison_v2.csv").read_bytes())
    with pytest.raises(mod.QualificationError,match="occupied"):
        mod.run(COMPARISON,SUPPORT,out)

def test_historical_comparison_source_tampering_rejected(tmp_path):
    path=tmp_path/"comparison.csv"
    path.write_bytes(COMPARISON.read_bytes()+b"\n")
    with pytest.raises(mod.QualificationError,match="SHA256"):
        mod.load_inputs(path,SUPPORT)

def test_support_receipt_tampering_rejected_before_calculation(tmp_path):
    path=tmp_path/"support.json"
    path.write_bytes(SUPPORT.read_bytes()+b"\n")
    with pytest.raises(mod.QualificationError,match="Git blob"):
        mod.load_inputs(COMPARISON,path)

def test_duplicate_and_unrecognized_targets_fail():
    rows,receipt=original()
    duplicate=copy.deepcopy(rows)
    duplicate[0]["target_gene"]=duplicate[1]["target_gene"]
    with pytest.raises(mod.QualificationError,match="duplicate"):
        mod.calculate(duplicate,receipt)
    unknown=copy.deepcopy(rows)
    unknown[0]["target_gene"]="UNDECLARED_TARGET"
    with pytest.raises(mod.QualificationError,match="unknown"):
        mod.calculate(unknown,receipt)

def test_wrong_support_flag_and_changed_global_support_fail():
    rows,receipt=original()
    forged=copy.deepcopy(receipt)
    forged["verdict_basis"]["target_lane_support"]["AARS"]["lane_support_sufficient"]=True
    with pytest.raises(mod.QualificationError,match="support flag"):
        mod.calculate(rows,forged)
    forged=copy.deepcopy(receipt)
    forged["verdict_basis"]["usable_targets"]=38
    with pytest.raises(mod.QualificationError,match="global support"):
        mod.calculate(rows,forged)

def test_mismatched_lane_cell_and_ntc_support_fail():
    rows,receipt=original()
    forged=copy.deepcopy(receipt)
    forged["verdict_basis"]["target_lane_support"]["CDK8"]["paired_lanes"]=["L3","L4"]
    with pytest.raises(mod.QualificationError,match="paired lane"):
        mod.calculate(rows,forged)
    forged=copy.deepcopy(receipt)
    forged["verdict_basis"]["target_lane_support"]["CDK8"]["cells_by_lane"]["L3"]+=1
    with pytest.raises(mod.QualificationError,match="census mismatch"):
        mod.calculate(rows,forged)
    forged=copy.deepcopy(receipt)
    forged["verdict_basis"]["ntc_cells_by_lane"]["L1"]=0
    with pytest.raises(mod.QualificationError,match="NTC"):
        mod.calculate(rows,forged)

def test_ref_nonfinite_or_changed_ncell_refused():
    rows,receipt=original()
    forged=copy.deepcopy(rows)
    forged[0]["ref_log2fc"]=str(math.inf)
    with pytest.raises(mod.QualificationError,match="nonfinite"):
        mod.calculate(forged,receipt)
    forged=copy.deepcopy(rows)
    forged[0]["n_cells"]=str(int(forged[0]["n_cells"])+1)
    with pytest.raises(mod.QualificationError,match="contradicts"):
        mod.calculate(forged,receipt)

def test_prospective_or_reference_authority_forgery_refused():
    rows,receipt=original()
    forged=copy.deepcopy(receipt)
    forged["prospective_confirmation_eligible"]=True
    with pytest.raises(mod.QualificationError,match="qualification scope"):
        mod.calculate(rows,forged)
    forged=copy.deepcopy(receipt)
    forged["verdict"]="PASS_INDEPENDENT_CONFIRMATION"
    with pytest.raises(mod.QualificationError,match="qualification scope"):
        mod.calculate(rows,forged)
