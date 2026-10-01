#!/usr/bin/env python3
"""Synthetic optimizer/EMA qualification for the nested RNA + multimodal student family.

This is SOFTWARE MECHANICS ONLY. It uses the FULL104-shaped synthetic fixture and tests:
- nonzero gradients for active shared/private heads;
- actual optimizer updates and decreasing losses;
- EMA target update semantics;
- private loss applies only where ATAC is measured;
- no RNA-private head exists;
- held-out donor behavior remains finite and directionally correct.

No real biological data are read. This does not authorize JEPA or multimodal training.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
FIXTURE=HERE/"full104_like_nested_student_teacher_synthetic_integration_v1.py"

SEED=6510
STEPS=120
LR=0.20
EMA=0.99


def _load_fixture_module():
    spec=importlib.util.spec_from_file_location("full104_fixture",FIXTURE)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load FULL104-like synthetic fixture")
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _add_bias(X):
    return np.column_stack([np.ones(len(X)),np.asarray(X,float)])


def _loss_grad(X,Y,W):
    pred=X@W
    err=pred-Y
    loss=float(np.square(err).mean())
    grad=(2.0/err.size)*(X.T@err)
    return loss,grad,pred


def _r2(Y,P):
    Y=np.asarray(Y,float);P=np.asarray(P,float)
    den=np.square(Y-Y.mean(0,keepdims=True)).sum()
    return float(1.0-np.square(Y-P).sum()/den)


def run_smoke():
    fm=_load_fixture_module()
    x=fm.build_fixture()
    tr=x["train"]; va=x["val"]; paired=x["paired"]
    trp=tr & paired

    Xr=_add_bias(x["Xr"])
    Xm=_add_bias(np.column_stack([x["Xr"],x["Xa"]]))

    rng=np.random.default_rng(SEED)
    Wr=rng.normal(scale=.01,size=(Xr.shape[1],fm.K_SHARED))
    Wms=rng.normal(scale=.01,size=(Xm.shape[1],fm.K_SHARED))
    Wmp=rng.normal(scale=.01,size=(Xm.shape[1],fm.K_PRIVATE))
    Wema=Wr.copy()
    Wr_initial=Wr.copy()

    # Negative control: unpaired private targets must be completely irrelevant.
    private_loss0,private_grad0,_=_loss_grad(Xm[trp],x["Zp"][trp],Wmp)
    z_alt=x["Zp"].copy()
    z_alt[tr & ~paired] += 1e6
    private_loss1,private_grad1,_=_loss_grad(Xm[trp],z_alt[trp],Wmp)

    first=None
    trace=[]
    for step in range(STEPS):
        lrna,grna,_=_loss_grad(Xr[tr],x["Zs"][tr],Wr)
        lms,gms,_=_loss_grad(Xm[trp],x["Zs"][trp],Wms)
        lmp,gmp,_=_loss_grad(Xm[trp],x["Zp"][trp],Wmp)
        if step==0:
            first={
                "rna_shared_loss":lrna,
                "multimodal_shared_loss":lms,
                "multimodal_private_loss":lmp,
                "rna_shared_grad_l2":float(np.linalg.norm(grna)),
                "multimodal_shared_grad_l2":float(np.linalg.norm(gms)),
                "multimodal_private_grad_l2":float(np.linalg.norm(gmp)),
            }

        Wr_new=Wr-LR*grna
        Wms=Wms-LR*gms
        Wmp=Wmp-LR*gmp

        # EMA target follows only the universal RNA online student.
        Wema=EMA*Wema+(1.0-EMA)*Wr_new
        Wr=Wr_new

        if step in {0,1,2,9,29,59,119}:
            trace.append({
                "step":step+1,
                "rna_shared_loss":lrna,
                "multimodal_shared_loss":lms,
                "multimodal_private_loss":lmp,
                "online_ema_gap_l2":float(np.linalg.norm(Wr-Wema)),
            })

    final={
        "rna_shared_loss":_loss_grad(Xr[tr],x["Zs"][tr],Wr)[0],
        "multimodal_shared_loss":_loss_grad(Xm[trp],x["Zs"][trp],Wms)[0],
        "multimodal_private_loss":_loss_grad(Xm[trp],x["Zp"][trp],Wmp)[0],
    }
    validation={
        "rna_shared_r2":_r2(x["Zs"][va],Xr[va]@Wr),
        "multimodal_shared_r2":_r2(x["Zs"][va],Xm[va]@Wms),
        "multimodal_private_r2":_r2(x["Zp"][va],Xm[va]@Wmp),
    }

    mask_invariance={
        "unpaired_target_perturbation_loss_abs_diff":float(abs(private_loss1-private_loss0)),
        "unpaired_target_perturbation_grad_max_abs_diff":
            float(np.max(np.abs(private_grad1-private_grad0))),
    }
    ema_metrics={
        "updates":STEPS,
        "decay":EMA,
        "ema_to_current_online_l2":float(np.linalg.norm(Wema-Wr)),
        "initial_online_to_current_online_l2":float(np.linalg.norm(Wr_initial-Wr)),
        "ema_is_exact_online_copy":bool(np.array_equal(Wema,Wr)),
    }

    gates={
        "active_gradients_nonzero":bool(
            first["rna_shared_grad_l2"]>0
            and first["multimodal_shared_grad_l2"]>0
            and first["multimodal_private_grad_l2"]>0),
        "rna_loss_decreased":bool(final["rna_shared_loss"]<0.5*first["rna_shared_loss"]),
        "multimodal_shared_loss_decreased":bool(
            final["multimodal_shared_loss"]<0.5*first["multimodal_shared_loss"]),
        "multimodal_private_loss_decreased":bool(
            final["multimodal_private_loss"]<0.5*first["multimodal_private_loss"]),
        "unpaired_private_targets_have_zero_effect":bool(
            mask_invariance["unpaired_target_perturbation_loss_abs_diff"]==0.0
            and mask_invariance["unpaired_target_perturbation_grad_max_abs_diff"]==0.0),
        "ema_is_lagged_not_frozen":bool(
            ema_metrics["ema_to_current_online_l2"]>0
            and ema_metrics["ema_to_current_online_l2"]
                < ema_metrics["initial_online_to_current_online_l2"]),
        "validation_outputs_finite":bool(all(np.isfinite(list(validation.values())))),
        "validation_shared_positive":bool(
            validation["rna_shared_r2"]>0.2 and validation["multimodal_shared_r2"]>0.2),
        "validation_private_multimodal_positive":bool(
            validation["multimodal_private_r2"]>0.5),
    }

    return {
        "schema":"V65_NESTED_STUDENT_TEACHER_SYNTHETIC_TRAINING_MECHANICS_V1",
        "status":"SYNTHETIC_SOFTWARE_MECHANICS_ONLY",
        "optimizer":{
            "type":"full_batch_gradient_descent",
            "steps":STEPS,
            "learning_rate":LR,
        },
        "ema":{
            "target":"UNIVERSAL_RNA_STUDENT_PARAMETERS_ONLY",
            **ema_metrics,
        },
        "private_loss_scope":"PAIRED_TRAIN_ROWS_ONLY",
        "rna_private_head_present":False,
        "first_step":first,
        "final_train":final,
        "validation":validation,
        "mask_negative_control":mask_invariance,
        "trace":trace,
        "gates":gates,
        "pass":bool(all(gates.values())),
        "interpretation":{
            "qualified":"optimizer/gradient/EMA/missing-modality mechanics on controlled synthetic data",
            "not_qualified":"real biological target, production loss weights, architecture size, real shared rank, or training authority",
        },
        "governance":{
            "real_data_used":False,
            "real_training_authorized":False,
            "multimodal_training_authorized":False,
            "jepa_training":"OFF",
            "stage4":"NOT_AUTHORIZED",
        }
    }


def main():
    out=run_smoke()
    print(json.dumps(out,indent=2,sort_keys=True))
    return 0 if out["pass"] else 1


if __name__=="__main__":
    raise SystemExit(main())
