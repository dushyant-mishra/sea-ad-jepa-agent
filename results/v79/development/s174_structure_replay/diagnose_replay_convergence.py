"""Convergence-only diagnosis of the failed replay (no predictive metric is computed or recorded).

Re-runs, for every replay gene, model and held-out-donor fold, exactly the frozen _logistic_fit optimizer call of
run_v79_s174_structure_replay.py (same design, folds, ridge, L-BFGS-B settings) but records the optimizer status
instead of raising: success flag, iterations, final gradient inf-norm, max |coefficient|, and how many operator
levels in the training fold have zero or all detections for that gene (quasi-separation). Test-fold log loss and
positive-count LPD are deliberately NOT computed, so any repair rule can still be chosen prospectively."""
import json, sys
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts" / "v79"))
import run_v79_s174_structure_replay as R

D = Path(__file__).resolve().parent
data = R.load_compact_cache(D / "V79_ANALYSIS_CACHE_G500.npz", D / "V79_ANALYSIS_CACHE_G500_RECEIPT.json")
panel = R.select_panel_positions(data["prevalence_selected"], 200, R.SEED)
folds = R.donor_folds(data["donor"], data["src"], 3, R.SEED)
rows = []
for g in panel.tolist():
    y = (data["counts_selected"][:, g] > 0).astype(np.float64)
    for model in R.MODELS:
        X = R.design_matrix(data, model)
        for f, test in enumerate(folds):
            tr = ~test
            Xt, yt = X[tr], y[tr]
            def obj(b):
                eta = Xt @ b
                return float(np.logaddexp(0.0, eta).sum() - np.dot(yt, eta) + 0.5 * R.RIDGE * np.dot(b[1:], b[1:]))
            def grad(b):
                gr = Xt.T @ (expit(Xt @ b) - yt); gr[1:] += R.RIDGE * b[1:]; return gr
            res = minimize(obj, np.zeros(X.shape[1]), jac=grad, method="L-BFGS-B", options={"maxiter": 300, "ftol": 1e-10})
            gnorm = float(np.linalg.norm(grad(res.x), ord=np.inf))
            fails = (not res.success) and gnorm > 1e-4
            if fails or model == "depth_class_source_operator":
                ops = data["op"][tr]
                sep = sum(1 for o in np.unique(ops) if yt[ops == o].min() == yt[ops == o].max())
            else:
                sep = None
            rows.append(dict(gene_position=int(g), train_prevalence=float(yt.mean()), model=model, fold=f,
                             success=bool(res.success), would_raise=bool(fails), iterations=int(res.nit),
                             grad_inf_norm=gnorm, max_abs_coef=float(np.abs(res.x).max()),
                             operator_levels_constant_in_train=sep, message=str(res.message)))
fail = [r for r in rows if r["would_raise"]]
by_model = {m: sum(r["would_raise"] for r in rows if r["model"] == m) for m in R.MODELS}
rec = dict(schema="V79_S174_REPLAY_CONVERGENCE_DIAGNOSIS_V1", metrics_computed=False,
           n_fits=len(rows), n_would_raise=len(fail), would_raise_by_model=by_model,
           genes_with_any_failure=sorted({r["gene_position"] for r in fail}),
           failing_fits=fail,
           operator_model_quasi_separation=dict(
               fits=sum(1 for r in rows if r["model"] == "depth_class_source_operator"),
               fits_with_any_constant_operator_level=sum(1 for r in rows if r["model"] == "depth_class_source_operator" and r["operator_levels_constant_in_train"])),
           all_fits=rows)
(D / "V79_S174_REPLAY_CONVERGENCE_DIAGNOSIS.json").write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
print(json.dumps({k: rec[k] for k in ("n_fits", "n_would_raise", "would_raise_by_model", "genes_with_any_failure", "operator_model_quasi_separation")}))
for r in fail[:12]:
    print({k: r[k] for k in ("gene_position", "train_prevalence", "model", "fold", "iterations", "grad_inf_norm", "max_abs_coef", "operator_levels_constant_in_train")})
