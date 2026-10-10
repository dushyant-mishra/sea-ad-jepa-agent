#!/usr/bin/env python3
"""Planted-truth worlds on the real corrected-TRAIN design (identity-free: only the grouping structure of
cells into classes, sources, operators, donors and donor-classes, plus centred log depth, is reused).

Each scenario fixes the population sd of every component; per-gene sds are drawn log-normally around
them, effects are drawn from those sds, and responses from the Gaussian or Bernoulli likelihood.

Truth is scored on the model's own decomposition: operator and donor effects are split into their
within-source deviation and the source mean of their levels (credited to source), donor-class effects into
their within-class deviation and the class mean (credited to class), and class and source effects are taken
as deviations from their level mean. The planted linear predictor is unchanged; only its bookkeeping matches
the estimand, so recovery is judged on exactly the definition the models report.
"""
from __future__ import annotations

import numpy as np

COMPONENTS = ("cls", "src", "op", "donor", "dk")

SCENARIOS = {
    "S1_present": dict(cls=0.6, src=0.3, op=0.4, donor=0.5, dk=0.3, res=1.0),
    "S0_class_absent": dict(cls=0.0, src=0.3, op=0.4, donor=0.5, dk=0.3, res=1.0),
    "S3_donor_only_no_class": dict(cls=0.0, src=0.0, op=0.0, donor=0.9, dk=0.0, res=1.0),
    "S4_operator_only_no_class": dict(cls=0.0, src=0.0, op=0.9, donor=0.0, dk=0.0, res=1.0),
}
GENE_SD_SPREAD = 0.3


def simulate(design: dict, scenario: dict, n_genes: int, likelihood: str, seed: int, return_parts: bool = False) -> dict:
    rng = np.random.default_rng(seed)
    n = design["n"]
    levels = {"cls": design["n_cls"], "src": design["n_src"], "op": design["n_op"], "donor": design["n_donor"],
              "dk": design["n_dk"]}
    mu = rng.normal(0.0, 1.0, n_genes) + (-1.0 if likelihood == "bernoulli" else 1.0)
    b = rng.normal(0.8 if likelihood == "bernoulli" else 0.0, 0.2, n_genes)
    eta = mu[None, :] + b[None, :] * design["log_lib_centered"][:, None]
    eff = {}
    for x in COMPONENTS:
        sd_pop = scenario[x]
        eff[x] = np.zeros((levels[x], n_genes))
        if sd_pop > 0:
            sd = sd_pop * np.exp(rng.normal(0.0, GENE_SD_SPREAD, n_genes))
            eff[x] = rng.normal(0.0, 1.0, (levels[x], n_genes)) * sd[None, :]
        eta = eta + eff[x][design[x]]
    # re-express the planted effects on the model's parameterization (same eta)
    parent = {"op": "src", "donor": "src", "dk": "cls"}
    model_eff = {x: eff[x].copy() for x in COMPONENTS}
    for child, par in parent.items():
        par_of = np.zeros(levels[child], dtype=np.int64)
        par_of[design[child]] = design[par]
        for p in range(levels[par]):
            sel = par_of == p
            if sel.any():
                m = model_eff[child][sel].mean(0)
                model_eff[child][sel] -= m
                model_eff[par][p] += m
    for x in ("cls", "src"):
        model_eff[x] = model_eff[x] - model_eff[x].mean(0, keepdims=True)
    realized = {x: model_eff[x][design[x]].var(0) for x in COMPONENTS}
    if likelihood == "gaussian":
        sd_res = scenario["res"] * np.exp(rng.normal(0.0, GENE_SD_SPREAD, n_genes))
        y = eta + rng.normal(0.0, 1.0, eta.shape) * sd_res[None, :]
        realized["res"] = sd_res ** 2
    else:
        y = (rng.random(eta.shape) < 1.0 / (1.0 + np.exp(-eta))).astype(np.float32)
        realized["res"] = np.full(n_genes, np.pi ** 2 / 3)
    tot = sum(realized[k] for k in realized)
    out = dict(y=y.astype(np.float32), truth_var=realized, truth_frac={k: v / tot for k, v in realized.items()})
    if return_parts:
        out.update(eta=eta, mu=mu, b=b, model_eff=model_eff)
    return out
