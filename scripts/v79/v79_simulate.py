#!/usr/bin/env python3
"""Planted-truth worlds on the real corrected-TRAIN design (identity-free: only the grouping structure of
cells into classes, sources, operators, donors and donor-classes, plus centred log depth, is reused).

Each scenario fixes the population sd of every component; per-gene sds are drawn log-normally around
them, effects are drawn from those sds, and responses from the Gaussian or Bernoulli likelihood. The
returned truth holds the realized per-gene variance fractions, so recovery is judged on the same
definition the models report.
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


def simulate(design: dict, scenario: dict, n_genes: int, likelihood: str, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    n = design["n"]
    levels = {"cls": design["n_cls"], "src": design["n_src"], "op": design["n_op"], "donor": design["n_donor"],
              "dk": design["n_dk"]}
    mu = rng.normal(0.0, 1.0, n_genes) + (-1.0 if likelihood == "bernoulli" else 1.0)
    b = rng.normal(0.8 if likelihood == "bernoulli" else 0.0, 0.2, n_genes)
    eta = mu[None, :] + b[None, :] * design["log_lib_centered"][:, None]
    realized = {}
    for x in COMPONENTS:
        sd_pop = scenario[x]
        if sd_pop == 0:
            realized[x] = np.zeros(n_genes)
            continue
        sd = sd_pop * np.exp(rng.normal(0.0, GENE_SD_SPREAD, n_genes))
        eff = rng.normal(0.0, 1.0, (levels[x], n_genes)) * sd[None, :]
        per_cell = eff[design[x]]
        eta = eta + per_cell
        realized[x] = per_cell.var(0)
    if likelihood == "gaussian":
        sd_res = scenario["res"] * np.exp(rng.normal(0.0, GENE_SD_SPREAD, n_genes))
        y = eta + rng.normal(0.0, 1.0, eta.shape) * sd_res[None, :]
        realized["res"] = sd_res ** 2
    else:
        y = (rng.random(eta.shape) < 1.0 / (1.0 + np.exp(-eta))).astype(np.float32)
        realized["res"] = np.full(n_genes, np.pi ** 2 / 3)
    tot = sum(realized[k] for k in realized)
    return dict(y=y.astype(np.float32), truth_var=realized, truth_frac={k: v / tot for k, v in realized.items()})
