from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/"scripts"/"v79"
sys.path.insert(0,str(HERE))
import v79_v2_core_score_descriptive as D  # noqa: E402


def _quantity(labels, truth, mean):
    truth=np.asarray(truth,dtype=float); mean=np.asarray(mean,dtype=float)
    sd=np.ones_like(truth)
    return {"labels":list(labels),"truth":truth.tolist(),"posterior_mean":mean.tolist(),"posterior_sd":sd.tolist(),
            "q005":(mean-2.5).tolist(),"q025":(mean-2).tolist(),"q05":(mean-1).tolist(),"q50":mean.tolist(),
            "q95":(mean+1).tolist(),"q975":(mean+2).tolist(),"q995":(mean+2.5).tolist(),
            "covered90":[True]*len(truth),"covered95":[True]*len(truth),"covered99":[True]*len(truth),
            "standardized_error":(mean-truth).tolist()}


def _row(world,part,gene,*,offset=0.0,donor_truth=None,donor_mean=None,ppc=(0.5,)):
    if donor_truth is None: donor_truth=np.array([-1.,0.,1.])
    if donor_mean is None: donor_mean=np.asarray(donor_truth)+offset
    q={
        "intercept":_quantity(["intercept"],[1.0],[1.0+offset]),
        "depth1":_quantity(["depth1"],[2.0],[2.0+offset]),
        "depth2":_quantity(["depth2"],[0.5],[0.5+offset]),
        "class":_quantity(["helmert_0","helmert_1"],[1.0,-1.0],[1.0+offset,-1.0+offset]),
        "source":_quantity(["helmert_0","helmert_1"],[0.5,-0.5],[0.5+offset,-0.5+offset]),
        "donor_sd":_quantity(["donor_sd"],[1.0],[1.0+offset]),
        "donor_effects":_quantity(["donor_0","donor_1","donor_2"],donor_truth,donor_mean),
    }
    if part=="positive": q["sigma"]=_quantity(["sigma"],[0.5],[0.5+offset])
    return {"fit_id":f"{gene:064x}","world_name":world,"world_index":10 if world.startswith("Q10") else 11 if world.startswith("Q11") else 0,
            "opaque_world_id":"a"*12,"gene_index":gene,"part":part,"final_diagnosis":"COMPLETE","quantities":q,
            "ppc":[{"name":f"s{i}","observed":0.0,"p_value":float(p)} for i,p in enumerate(ppc)]}


def _calibration(predicted=0.2,observed=0.2):
    rows=[]
    for b in range(10):
        rows.append({"bin_index":b,"lower":b/10,"upper":(b+1)/10,"n":0,"mean_predicted":None,"observed_rate":None})
    rows[2]={"bin_index":2,"lower":0.2,"upper":0.3,"n":10,"mean_predicted":predicted,"observed_rate":observed}
    return rows


def _detection_mode(loss,*,mode):
    return {"schema":"V79_V2_CORE_DETECTION_HELDOUT_V1","replicate_mode":mode,"posterior_draws":200,
            "gauss_hermite_nodes":None if mode=="same_donor" else 40,"n_measured":10,"mean_log_loss":loss,
            "predicted_prevalence":0.2,"observed_prevalence":0.2,"calibration_bins":_calibration()}


def test_parameter_recovery_reports_corr_rmse_and_nonzero_sign_agreement():
    rows=[_row("Q00_BASELINE","detection",g,offset=0.1*g) for g in range(4)]
    out=D.parameter_recovery(rows)
    rec=out["groups"]["Q00_BASELINE|detection|class"]
    assert rec["n_scalars"]==8
    assert rec["rmse"]>0
    assert rec["pearson"] is not None
    assert 0.0<=rec["sign_agreement_nonzero_truth"]<=1.0


def test_donor_recovery_reports_per_gene_spearman_slope_shrinkage_and_null_when_undefined():
    good=_row("Q00_BASELINE","detection",0,donor_truth=np.array([-1.,0.,1.]),donor_mean=np.array([-0.5,0.,0.5]))
    bad=_row("Q00_BASELINE","detection",1,donor_truth=np.array([1.,1.,1.]),donor_mean=np.array([0.,0.,0.]))
    out=D.donor_recovery([good,bad])
    a=out["per_gene"][0]; b=out["per_gene"][1]
    assert math.isclose(a["spearman"],1.0) and math.isclose(a["calibration_slope"],2.0) and math.isclose(a["shrinkage_factor"],0.5)
    assert b["spearman"] is None and b["calibration_slope"] is None and b["shrinkage_factor"] is None


def test_detection_and_positive_heldout_aggregate_model_minus_oracle_without_becoming_gates():
    receipts=[
        {"fit_id":"a"*64,"part":"detection","heldout_predictive":{"same_donor":_detection_mode(0.7,mode="same_donor"),"new_donor":_detection_mode(0.8,mode="new_donor")}},
        {"fit_id":"b"*64,"part":"positive","heldout_predictive":{"same_donor":{"mean_lpd":-1.2},"new_donor":{"mean_lpd":-1.4}}},
    ]
    oracle={
        "a"*64:{"planted_prevalence":0.03,"same_donor":{"mean_log_loss":0.5},"new_donor":{"mean_log_loss":0.6}},
        "b"*64:{"same_donor":{"mean_lpd":-1.0},"new_donor":{"mean_lpd":-1.1}},
    }
    d=D.detection_heldout(receipts,oracle); p=D.positive_heldout(receipts,oracle)
    assert math.isclose(d["same_donor"]["mean_model_minus_oracle_log_loss"],0.2)
    assert d["low_prevalence_lt_0_05"]["n_fits"]==1
    assert math.isclose(p["new_donor"]["mean_model_minus_oracle_mean_lpd"],-0.3)


def test_q11_minus_q10_is_exact_gene_part_pairing_and_second_stage_compares_gene_geometry():
    rows=[]
    for g in range(4):
        truth=np.array([-1.,0.,1.])*(g+1)
        rows.append(_row("Q10_S174_DESIGN_IMBALANCE","detection",g,offset=0.0,donor_truth=truth,donor_mean=truth))
        rows.append(_row("Q11_OMITTED_OPERATOR","detection",g,offset=0.2,donor_truth=truth,donor_mean=truth+0.2,ppc=(0.005,0.5)))
    heldout={}
    for row in rows:
        heldout[(row["world_name"],row["part"],row["gene_index"])]=0.5 if row["world_name"].startswith("Q10") else 0.8
    out=D.ppc_q10_q11_second_stage(rows,heldout_model_metric=heldout)
    q=out["q11_minus_q10"]["detection"]
    assert q["paired_genes"]==4
    assert q["mean_abs_standardized_error_delta"]>0
    assert q["ppc_extreme_fraction_delta"]>0
    assert math.isclose(q["heldout_model_metric_delta"],0.3)
    stage=out["second_stage"]["Q10_S174_DESIGN_IMBALANCE|detection"]
    assert stage["n_genes"]==4 and stage["n_common_donors"]==3
    assert stage["gene_correlation_upper_triangle_pearson"] is not None


def test_build_descriptive_metrics_requires_all_five_families_and_is_explicitly_non_gating():
    rows=[_row("Q10_S174_DESIGN_IMBALANCE","detection",g) for g in range(3)]
    rows += [_row("Q11_OMITTED_OPERATOR","detection",g,offset=.1) for g in range(3)]
    receipts=[]; oracle={}; held={}
    for i,row in enumerate(rows):
        fid=f"{100+i:064x}"; row["fit_id"]=fid
        receipts.append({"fit_id":fid,"part":"detection","heldout_predictive":{"same_donor":_detection_mode(0.7,mode="same_donor"),"new_donor":_detection_mode(0.8,mode="new_donor")}})
        oracle[fid]={"planted_prevalence":0.2,"same_donor":{"mean_log_loss":0.5},"new_donor":{"mean_log_loss":0.6}}
        held[(row["world_name"],row["part"],row["gene_index"])]=0.7
    out=D.build_descriptive_metrics(rows,receipts,oracle,heldout_model_metric=held)
    assert out["schema"]=="V79_V2_CORE_DESCRIPTIVE_METRICS_V1" and out["gating"] is False
    assert set(out["families"])=={"parameter_recovery","donor_recovery","detection_heldout","positive_heldout","ppc_q10_q11_second_stage"}
