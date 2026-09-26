#!/usr/bin/env python3
"""Non-authorizing, synthetic-only query-local teacher-target design preflight.
No project production code/data, protected outcomes, or optimizer/training authorization.
"""
import json
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score

rng = np.random.default_rng(20260926)
# 1. Counterfactual query-leak tests: identical non-query raw counts, changed query count.
raw_a = np.array([10., 20., 50., 12.])
raw_b = np.array([100., 20., 50., 12.])
q = 0
full_norm = lambda x: np.log1p(10000 * x / x.sum())
nonquery = np.array([1, 2, 3])
legacy_delta = float(np.max(np.abs(full_norm(raw_a)[nonquery] - full_norm(raw_b)[nonquery])))
strict_norm = lambda x: np.log1p(10000 * x[nonquery] / x[nonquery].sum())
strict_delta = float(np.max(np.abs(strict_norm(raw_a) - strict_norm(raw_b))))
# Global derived from a full-count vector remains a scalar-leak risk even if scalar token withheld.
global_from_full = lambda x: np.array([np.log1p(x.sum()), np.log1p(x[0] + 0.25*x[1])])
global_from_safe = lambda x: np.array([np.log1p(x[nonquery].sum()), np.log1p(x[1] + 0.25*x[2])])
global_leak = float(np.max(np.abs(global_from_full(raw_a) - global_from_full(raw_b))))
global_safe_delta = float(np.max(np.abs(global_from_safe(raw_a) - global_from_safe(raw_b))))
assert legacy_delta > 0.1 and strict_delta == 0.0
assert global_leak > 0.1 and global_safe_delta == 0.0

# 2. Paired conditional-information test: target is a held-out gene module-derived
#    latent state, queried scalar excluded from teacher and student. All synthetic.
#    Repeated donor offsets and technical effects, split donors before fitting.
n_donors, per_donor, n_prog = 12, 40, 2
n = n_donors * per_donor
donor = np.repeat(np.arange(n_donors), per_donor)
latent = rng.normal(size=(n, n_prog)) + rng.normal(scale=.55, size=(n_donors, n_prog))[donor]
technical = rng.normal(size=(n_donors, 1))[donor] + rng.normal(scale=.5, size=(n, 1))
# Independent 4-gene context and 4-gene target panels in each gene program.
ctx = np.hstack([latent[:, [j]] + rng.normal(scale=.58, size=(n, 4)) + .15*technical for j in range(n_prog)])
tgt = np.hstack([latent[:, [j]] + rng.normal(scale=.58, size=(n, 4)) + .15*technical for j in range(n_prog)])
# Hidden query counts are generated but never supplied to either view.
queried_raw = np.maximum(0, np.round(np.exp(latent + rng.normal(scale=.3, size=(n, 2)))))
# Two query identities ask for distinct program-local state; teacher averages a disjoint module.
# Query-specific negative-control weights are fixed from generating equation, not tuned on test donors.
train = donor < 8
test = ~train
scores = []
for query in range(n_prog):
    y = tgt[:, 4*query:4*query+4].mean(axis=1)
    x_ctx = ctx
    x_tech = technical
    # For the identity-only control, query identity is constant within this per-query fit.
    # Match targets by donor to destroy cell-specific context yet retain donor composition.
    model = Ridge(alpha=10).fit(x_ctx[train],y[train]); pred=model.predict(x_ctx[test]); r2=float(r2_score(y[test],pred))
    null_model = Ridge(alpha=10).fit(x_tech[train],y[train]); nr2=float(r2_score(y[test],null_model.predict(x_tech[test])))
    # No remaining RNA: predicting the training mean for this query.
    identity_r2=float(r2_score(y[test],np.full(test.sum(),y[train].mean())))
    # Deliberately break matching of student/teacher within each donor, preserving donor structure.
    y_shuf=y.copy()
    for d in range(n_donors):
        ii=np.where(donor==d)[0]
        y_shuf[ii]=y_shuf[rng.permutation(ii)]
    shuffled=Ridge(alpha=10).fit(x_ctx[train],y_shuf[train]); shuffled_r2=float(r2_score(y_shuf[test],shuffled.predict(x_ctx[test])))
    scores.append(dict(query=query,full_remaining_rna_r2=r2,technical_only_r2=nr2,identity_only_r2=identity_r2,within_donor_shuffled_r2=shuffled_r2,heldout_donors=4))
    assert r2 > nr2 + .35 and r2 > identity_r2 + .35 and r2 > shuffled_r2 + .35

# 3. Gradient boundary, independent compact torch positive/adversarial fixtures.
import torch
torch.manual_seed(20260926)
teacher=torch.nn.Linear(8,4,bias=False)
student=torch.nn.Linear(8,4,bias=False)
predictor=torch.nn.Linear(4,4,bias=False)
x=torch.randn(16,8)
with torch.no_grad():
    teacher_target=teacher(x).detach()
loss=torch.nn.functional.mse_loss(predictor(student(x)),teacher_target)
loss.backward()
assert teacher.weight.grad is None
assert student.weight.grad is not None and torch.isfinite(student.weight.grad).all() and student.weight.grad.abs().max()>0
assert predictor.weight.grad is not None and predictor.weight.grad.abs().max()>0
# Positive-control planted illicit teacher gradient MUST be detected.
teacher.zero_grad(set_to_none=True)
student.zero_grad(set_to_none=True)
predictor.zero_grad(set_to_none=True)
torch.nn.functional.mse_loss(predictor(student(x)),teacher(x)).backward()
assert teacher.weight.grad is not None and teacher.weight.grad.abs().max()>0

result={
 "scope":"SYNTHETIC_ONLY__NONAUTHORIZING__NO_REAL_JEPA_TRAINING",
 "query_counterfactual": {
    "legacy_full_library_log1p10k_nonquery_max_abs_change":legacy_delta,
    "query_excluded_denominator_nonquery_max_abs_change":strict_delta,
    "full_derived_global_context_max_abs_change":global_leak,
    "query_excluded_global_context_max_abs_change":global_safe_delta,
    "interpretation":"Existing full-library normalization and full-expression-derived global context are NOT automatically query-counterfactual invariant. No production routing changed."},
 "heldout_donor_synthetic_conditional_state_test":scores,
 "teacher_stopgrad_positive_control":True,
 "planted_teacher_gradient_detected":True,
 "assertions_passed":True,
 "limits":["Generated program loadings provide an oracle not available for real RNA", "Disjoint gene views alone cannot prove biological semantics", "No real dataset, no genuine EMA training or source authority closure", "No numerical full104 gate or mask policy selected"]
}
with open('/mnt/data/teacher_target_preflight_v1_results.json','w') as f: json.dump(result,f,indent=2)
print(json.dumps(result,indent=2))