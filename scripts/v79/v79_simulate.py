#!/usr/bin/env python3
"""Planted-truth worlds on the real corrected-TRAIN design (identity-free: only the grouping structure of
cells into classes, sources, operators, donors and donor-classes, plus centred log depth, is reused).

Each scenario fixes the population sd of every component; per-gene sds are drawn log-normally around
them, effects are drawn from those sds, and responses from the Gaussian or Bernoulli likelihood, or (ztnb)
negative-binomial counts with a log-depth offset of which only the positive cells are modelled.

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
ZTNB_LOG_MEAN_COUNT = (-0.5, 1.5)   # log mean count at average depth: about 0.03 to 12 counts, detection 3-90%
ZTNB_LOG_PHI = (np.log(2.0), 0.3)


def simulate(design: dict, scenario: dict, n_genes: int, likelihood: str, seed: int, return_parts: bool = False) -> dict:
    rng = np.random.default_rng(seed)
    n = design["n"]
    levels = {"cls": design["n_cls"], "src": design["n_src"], "op": design["n_op"], "donor": design["n_donor"],
              "dk": design["n_dk"]}
    offset = np.asarray(design["log_lib"], dtype=np.float64) if likelihood == "ztnb" else None
    if likelihood == "ztnb":
        mu = rng.normal(ZTNB_LOG_MEAN_COUNT[0], ZTNB_LOG_MEAN_COUNT[1], n_genes) - offset.mean()
    else:
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
    mu_model = mu.copy()
    for x in ("cls", "src"):
        mu_model = mu_model + model_eff[x].mean(0)
        model_eff[x] = model_eff[x] - model_eff[x].mean(0, keepdims=True)
    if likelihood == "lognormal":
        # Phase C log-normal world: Gaussian log count (minus offset) observed on detected cells only, with
        # detection depending on the linear predictor (not on the noise), so the masked model is the true model
        sd_res = scenario["res"] * np.exp(rng.normal(0.0, GENE_SD_SPREAD, n_genes))
        ylog = eta + rng.normal(0.0, 1.0, eta.shape) * sd_res[None, :]
        a = rng.normal(0.0, 1.5, n_genes)                         # detection rates about 5% to 95%
        p = 1.0 / (1.0 + np.exp(-(a[None, :] + (eta - eta.mean(0, keepdims=True)))))
        mask = rng.random(eta.shape) < p
        nd = np.maximum(mask.sum(0), 1)
        realized = {}
        for x in COMPONENTS:
            e = model_eff[x][design[x]]
            m = (e * mask).sum(0) / nd
            realized[x] = (((e - m) ** 2) * mask).sum(0) / nd
        realized["res"] = sd_res ** 2
        tot = sum(realized[k] for k in realized)
        out = dict(y=np.where(mask, ylog, 0.0).astype(np.float32), mask=mask, truth_var=realized,
                   truth_frac={k: v / tot for k, v in realized.items()})
        if return_parts:
            out.update(eta=eta, mu=mu, mu_model=mu_model, b=b, model_eff=model_eff)
        return out
    if likelihood == "ztnb":
        logphi = rng.normal(ZTNB_LOG_PHI[0], ZTNB_LOG_PHI[1], n_genes)
        phi = np.exp(logphi)
        mean = np.exp(eta + offset[:, None])
        counts = rng.negative_binomial(phi[None, :], phi[None, :] / (phi[None, :] + mean)).astype(np.float64)
        mask = counts > 0
        nd = np.maximum(mask.sum(0), 1)
        realized = {}
        for x in COMPONENTS:                                       # over each gene's detected cells
            e = model_eff[x][design[x]]
            m = (e * mask).sum(0) / nd
            realized[x] = (((e - m) ** 2) * mask).sum(0) / nd
        tot_c = sum(realized.values())
        typical_offset = (offset[:, None] * mask).sum(0) / nd
        lam = np.exp(mu_model + typical_offset + 0.5 * tot_c)
        realized["res"] = np.log1p(1.0 / lam + 1.0 / phi)      # Nakagawa et al. 2017 convention, as the model
        tot = sum(realized[k] for k in realized)
        out = dict(y=counts.astype(np.float32), mask=mask, offset=offset.astype(np.float32),
                   typical_offset=typical_offset, truth_var=realized,
                   truth_frac={k: v / tot for k, v in realized.items()}, truth_logphi=logphi)
        if return_parts:
            out.update(eta=eta, mu=mu, mu_model=mu_model, b=b, model_eff=model_eff)
        return out
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
