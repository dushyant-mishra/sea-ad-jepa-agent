#!/usr/bin/env python3
"""V79 hierarchical variance-component models (NumPyro, NUTS).

For gene g and cell c with broad class k, source s, observation operator o, donor d and donor-class j:

    eta[c,g] = mu[g] + a_cls[k,g] + a_src[s,g] + a_op[o,g] + a_don[d,g] + a_dk[j,g] + b[g] * depth[c]

  gaussian   y[c,g] ~ Normal(eta[c,g], sd_res[g])            (Phase A log1p CP10K; Phase C positive log counts)
  bernoulli  y[c,g] ~ Bernoulli(logit = eta[c,g])           (Phase B detection; residual pi^2/3 on the logit scale)
  ztnb       y[c,g] | y > 0 ~ zero-truncated NegBin(mean = exp(eta[c,g] + offset[c]), dispersion phi[g])
             (Phase C positive counts; offset = log library; residual on the log scale ln(1 + 1/mean + 1/phi),
             the distribution-specific variance of Nakagawa, Johnson & Schielzeth 2017)

Class and source have three levels each: they are fixed effects with an exchangeable sum-to-zero N(0, 1.5) prior,
parameterized by K-1 coefficients on an orthonormal sum-to-zero basis, so no direction is left that only the prior
informs (an earlier version sampled K free values and subtracted their mean, leaving such a direction and badly
conditioning NUTS; see the self-audit log).

Operator, donor and donor-class are random effects defined WITHIN their parent group, because every operator and
donor sits inside one source and every donor-class inside one class: the data inform only parent + mean child, so
unconstrained children leave a prior-only ridge. Each is parameterized on a block-orthonormal within-parent
sum-to-zero basis, theta ~ N(0, sd_x[g]), effect = B_x theta. Read as: operator = operator variation within a
source; donor = donor variation within a source; donor-class = donor-specific class deviation within a class;
source = between-source differences; class = between-class differences. Each gene's log sd for a random component
is drawn from a population N(m_x, s_x) shared across genes, so the across-gene distribution is itself estimated. Random effects are centred by default
(effect_centered=1): groups here are data-rich (about 30 cells per donor), where a non-centred form makes deep
NUTS trees. Per-gene log sds are non-centred (few genes inform the population). The centring is a sampler
setting chosen on simulated designs and frozen in the contract, never on real data. Every component's
variance is reported as the realized (finite-population) variance of its effects over the observed cells, so
fractions add up over one fixed set of cells.

Observation operators and sources enter as observation effects; they are never latent biological classes.
Framework: NumPyro NUTS on JAX (chains in parallel on CPU host devices). A first Pyro (PyTorch) port was
abandoned because per-step Python overhead made warmed-up NUTS too slow on this design; its timing is in the
compute benchmark.
"""
from __future__ import annotations

import math
import os
import time

os.environ.setdefault("XLA_FLAGS", "--xla_force_host_platform_device_count=8")
import jax  # noqa: E402
import jax.numpy as jnp  # noqa: E402
import numpy as np  # noqa: E402
import numpyro  # noqa: E402
import numpyro.distributions as dist  # noqa: E402
from numpyro.handlers import reparam  # noqa: E402
from numpyro.infer import MCMC, NUTS  # noqa: E402
from numpyro.infer.reparam import LocScaleReparam  # noqa: E402

COMPONENTS = ("cls", "src", "op", "donor", "dk")
FIXED = ("cls", "src")
FIXED_PRIOR_SD = 1.5
LOGISTIC_RESIDUAL_VAR = math.pi ** 2 / 3


PARENT = {"op": "src", "donor": "src", "dk": "cls"}


def within_parent_basis(child: np.ndarray, parent: np.ndarray, n_child: int) -> np.ndarray:
    """Block-orthonormal basis (n_child x (n_child - n_groups)) of effects summing to zero within each parent."""
    par = np.full(n_child, -1)
    for c, p in zip(child, parent):
        if par[c] not in (-1, p):
            raise ValueError("a child level belongs to two parents")
        par[c] = p
    cols = []
    for p in np.unique(par):
        idx = np.where(par == p)[0]
        if len(idx) < 2:
            continue
        q = sum_to_zero_basis(len(idx))
        block = np.zeros((n_child, len(idx) - 1))
        block[idx] = q
        cols.append(block)
    return np.concatenate(cols, axis=1)


def design_arrays(di: dict) -> dict:
    """Index codes, plus a dense one-hot (cells x levels) per component: effects enter eta by matrix product,
    because on CPU the gradient of an index gather is a slow single-threaded scatter-add (measured 9x the
    forward cost; see the self-audit log)."""
    d = {k: jnp.asarray(di[k], dtype=jnp.int32) for k in COMPONENTS}
    n_lev = {"cls": di["n_cls"], "src": di["n_src"], "op": di["n_op"], "donor": di["n_donor"], "dk": di["n_dk"]}
    d["onehot"] = {k: jnp.asarray(np.eye(n_lev[k], dtype=np.float32)[np.asarray(di[k])]) for k in COMPONENTS}
    d["basis"], d["proj"] = {}, {}
    for x, par in PARENT.items():
        B = within_parent_basis(np.asarray(di[x]), np.asarray(di[par]), n_lev[x])
        d["basis"][x] = B
        d["proj"][x] = jnp.asarray(np.eye(n_lev[x], dtype=np.float64)[np.asarray(di[x])] @ B, dtype=jnp.float32)
    d["depth"] = jnp.asarray(di["log_lib_centered"], dtype=jnp.float32)
    d["levels"] = {"cls": di["n_cls"], "src": di["n_src"], "op": di["n_op"], "donor": di["n_donor"], "dk": di["n_dk"]}
    return d


# Centring per likelihood, chosen on simulated designs (contract: a sampler setting, never chosen on real data).
# Detection: a donor-class level has about 11 binary cells, too little to pin a logit effect or its per-gene sd,
# so both are non-centred (self-audit 16, 22: centred effects failed R-hat; with effects alone non-centred the
# divergences sat at small donor-class sds; experiment E3 with both: 0 divergences, R-hat 1.007, ESS 524).
# Phase C models only detected cells (fewer still per donor-class level) and starts from the same setting.
NC_DK = {"dk": 0.0, "logsd_dk": 0.0}
# Gaussian too: at 20 genes the centred per-gene donor-class log sd failed (R-hat 1.035, ESS 66-113 in recovery
# S0 and S1; self-audit 29); a donor-class level has about 11 cells, so small donor-class sds are weakly pinned.
CENTRING = {"gaussian": dict(NC_DK), "gaussian_masked": dict(NC_DK), "bernoulli": dict(NC_DK), "ztnb": dict(NC_DK)}


def centring_key(likelihood: str, mask) -> str:
    return "gaussian_masked" if likelihood == "gaussian" and mask is not None else likelihood


def vc_model(*args, effect_centered=None, logsd_centered: float = 1.0, **kwargs):
    """Both effects and per-gene log sds are centred by default: each gene's spread is pinned by its own data
    (149 donors, 426 donor-classes, 42 operators), and a non-centred log sd in that regime makes the narrow
    funnel that forces tiny NUTS steps (self-audit entries 3 and 10)."""
    if effect_centered is None:
        effect_centered = CENTRING[centring_key(kwargs.get("likelihood", "gaussian"), kwargs.get("mask"))]

    def config(site):
        name = site["name"]
        if name.endswith("_decentered"):
            return None
        if name.startswith("logsd_"):
            # per-site override, e.g. CENTRING[...]["logsd_dk"] = 0.0 (a per-gene sd weakly pinned by its data)
            c = effect_centered.get(name, logsd_centered) if isinstance(effect_centered, dict) else logsd_centered
            return LocScaleReparam(centered=c) if c != 1.0 else None
        if name.startswith("a_"):
            c = effect_centered.get(name[2:], 1.0) if isinstance(effect_centered, dict) else effect_centered
            if c != 1.0:
                return LocScaleReparam(centered=c)
        return None
    return reparam(_vc_model, config=config)(*args, **kwargs)


def sum_to_zero_basis(k: int) -> np.ndarray:
    """K x (K-1) orthonormal basis of the sum-to-zero subspace."""
    c = np.eye(k) - 1.0 / k
    q, _ = np.linalg.qr(c)
    return q[:, : k - 1]


def _vc_model(design, y, likelihood="gaussian", components=COMPONENTS, mask=None, depth=True, offset=None):
    N, G = y.shape
    if likelihood == "ztnb":
        w = mask if mask is not None else (y > 0)
        lc = jnp.where(w, jnp.log(jnp.clip(y, 1.0)) - offset[:, None], 0.0)
        center = lc.sum(0) / jnp.clip(w.sum(0), 1)
    elif likelihood == "gaussian":
        if mask is not None:
            center = jnp.where(mask, y, 0.0).sum(0) / jnp.clip(mask.sum(0), 1)
        else:
            center = y.mean(0)
    else:
        p = jnp.clip(y.mean(0), 1e-3, 1 - 1e-3)
        center = jnp.log(p) - jnp.log1p(-p)
    with numpyro.plate("genes", G, dim=-1):
        mu = numpyro.sample("mu", dist.Normal(center, 2.5))
        b = numpyro.sample("b_depth", dist.Normal(0.0, 1.0)) if depth else jnp.zeros(G)
    eta = mu + b * design["depth"][:, None]
    for x in components:
        L = design["levels"][x]
        if x in FIXED:
            with numpyro.plate(f"contrasts_{x}", L - 1, dim=-2), numpyro.plate(f"genes_{x}", G, dim=-1):
                theta = numpyro.sample(f"theta_{x}", dist.Normal(0.0, FIXED_PRIOR_SD))
            a = numpyro.deterministic(f"a_{x}", jnp.asarray(sum_to_zero_basis(L), dtype=jnp.float32) @ theta)
            eta = eta + design["onehot"][x] @ a
            continue
        m = numpyro.sample(f"m_{x}", dist.Normal(math.log(0.3), 1.0))
        s = numpyro.sample(f"s_{x}", dist.HalfNormal(0.5))
        with numpyro.plate(f"genes_{x}", G, dim=-1):
            logsd = numpyro.sample(f"logsd_{x}", dist.Normal(m, s))
        P = design["proj"][x]
        with numpyro.plate(f"levels_{x}", P.shape[1], dim=-2), numpyro.plate(f"genes_{x}_l", G, dim=-1):
            th = numpyro.sample(f"a_{x}", dist.Normal(0.0, jnp.exp(logsd)))
        eta = eta + P @ th
    if likelihood == "ztnb":
        m_phi = numpyro.sample("m_phi", dist.Normal(math.log(2.0), 1.5))
        s_phi = numpyro.sample("s_phi", dist.HalfNormal(0.5))
        with numpyro.plate("genes_phi", G, dim=-1):
            logphi = numpyro.sample("logphi", dist.Normal(m_phi, s_phi))
        phi = jnp.exp(logphi)
        log_mean = eta + offset[:, None]
        w = mask if mask is not None else (y > 0)
        yy = jnp.where(w, y, 1.0)
        # NB2 log pmf without the data-only constant -lgamma(y + 1) (posterior unchanged; one lgamma per entry
        # saved), written with softplus so that tiny means stay finite in float32 (self-audit 32):
        #   phi * log(phi / (phi + mean)) = -phi * softplus(d),  y * log(mean / (phi + mean)) = -y * softplus(-d)
        d = log_mean - logphi
        log_p0 = -phi * jax.nn.softplus(d)                              # log P(y = 0) under the parent NB
        lp = (jax.scipy.special.gammaln(yy + phi) - jax.scipy.special.gammaln(phi)
              + log_p0 - yy * jax.nn.softplus(-d))
        lp = lp - jnp.log(-jnp.expm1(log_p0))                           # log P(y > 0), stable as P0 -> 1
        numpyro.factor("y_ztnb", jnp.where(w, lp, 0.0).sum())
        return
    if likelihood == "gaussian":
        m_r = numpyro.sample("m_res", dist.Normal(0.0, 1.5))
        s_r = numpyro.sample("s_res", dist.HalfNormal(0.5))
        with numpyro.plate("genes_res", G, dim=-1):
            logsd_res = numpyro.sample("logsd_res", dist.Normal(m_r, s_r))
        sd_res = jnp.exp(logsd_res)
    with numpyro.plate("cells", N, dim=-2), numpyro.plate("genes_obs", G, dim=-1):
        if likelihood == "gaussian":
            if mask is not None:
                with numpyro.handlers.mask(mask=mask):
                    numpyro.sample("y", dist.Normal(eta, sd_res), obs=y)
            else:
                numpyro.sample("y", dist.Normal(eta, sd_res), obs=y)
        else:
            numpyro.sample("y", dist.Bernoulli(logits=eta), obs=y)


def realized_fractions(samples: dict, design: dict, likelihood: str, components=COMPONENTS, mask=None,
                       typical_offset=None) -> dict:
    """Per draw and gene: realized variance of each component's effects over the observed cells (over the
    detected cells when a mask is given), the residual variance, and their fractions. Computed from level effects
    and per-level cell counts, never by expanding effects to every cell. Returns (variance, fraction) pairs of
    numpy arrays (draws x genes)."""
    out, tot = {}, None
    for x in components:
        eff = np.asarray(samples[f"a_{x}"], dtype=np.float64)
        if x in design.get("basis", {}):                                          # within-parent coefficients
            eff = np.einsum("lk,dkg->dlg", design["basis"][x], eff)
        idx = np.asarray(design[x])
        n_lev = eff.shape[1]
        if mask is None:
            cnt = np.bincount(idx, minlength=n_lev).astype(np.float64)[:, None]   # levels x 1
        else:
            m = np.asarray(mask, dtype=np.float64)                                # cells x genes
            cnt = np.zeros((n_lev, m.shape[1]))
            np.add.at(cnt, idx, m)                                                # levels x genes
        n = cnt.sum(0)                                                            # (1,) or (genes,)
        mean = (eff * cnt[None]).sum(1) / n                                       # draws x genes
        v = (cnt[None] * (eff - mean[:, None, :]) ** 2).sum(1) / n
        out[x] = v
        tot = v if tot is None else tot + v
    if likelihood == "gaussian":
        res = np.exp(np.asarray(samples["logsd_res"], dtype=np.float64)) ** 2
    elif likelihood == "ztnb":
        # Nakagawa, Johnson & Schielzeth (2017) log-normal approximation for the NB2 parent, a CONVENTION for the
        # truncated model: lambda = exp(mu + mean offset over the gene's detected cells + total component variance/2)
        if typical_offset is None:
            raise ValueError("ztnb fractions need typical_offset (per gene: mean log-depth offset over detected cells)")
        lam = np.exp(np.asarray(samples["mu"], dtype=np.float64) + np.asarray(typical_offset)[None, :] + 0.5 * tot)
        phi = np.exp(np.asarray(samples["logphi"], dtype=np.float64))
        res = np.log1p(1.0 / lam + 1.0 / phi)
    else:
        res = np.full_like(tot, LOGISTIC_RESIDUAL_VAR)
    out["res"] = res
    tot = tot + res
    return {k: (v, v / tot) for k, v in out.items()}


def run_nuts(model_kwargs: dict, n_chains: int, warmup: int, draws: int, seed: int, target_accept: float = 0.9,
             max_tree_depth: int = 10) -> dict:
    kernel = NUTS(vc_model, target_accept_prob=target_accept, max_tree_depth=max_tree_depth)
    if jax.default_backend() == "gpu":
        method = "vectorized"                              # one GPU: chains advance together in one program
    else:
        method = "parallel" if n_chains <= jax.local_device_count() else "sequential"
    # V79_PROGRESS=1 streams per-chain progress to stderr (self-audit 31: a timed-out run must leave evidence)
    mcmc = MCMC(kernel, num_warmup=warmup, num_samples=draws, num_chains=n_chains, chain_method=method,
                progress_bar=os.environ.get("V79_PROGRESS") == "1")
    t0 = time.time()
    mcmc.run(jax.random.PRNGKey(seed), extra_fields=("diverging", "num_steps"), **model_kwargs)
    jax.block_until_ready(mcmc.get_samples())        # JAX dispatches asynchronously; time the real work
    secs = time.time() - t0
    extra = mcmc.get_extra_fields(group_by_chain=True)
    return dict(mcmc=mcmc, samples=mcmc.get_samples(group_by_chain=True), seconds=secs,
                divergences=[int(x) for x in np.asarray(extra["diverging"]).sum(1)],
                mean_steps=float(np.asarray(extra["num_steps"]).mean()))


def convergence(grouped: dict, sites) -> dict:
    """Rank-normalized split R-hat and bulk/tail ESS (ArviZ) for the listed sites: worst value per site."""
    import arviz as az
    out = {}
    for k in sites:
        a = np.asarray(grouped[k], dtype=np.float64)
        a = a.reshape(a.shape[0], a.shape[1], -1)
        rh = [float(az.rhat(a[:, :, i])) for i in range(a.shape[2])]
        eb = [float(az.ess(a[:, :, i], method="bulk")) for i in range(a.shape[2])]
        et = [float(az.ess(a[:, :, i], method="tail")) for i in range(a.shape[2])]
        out[k] = dict(max_rhat=max(rh), min_ess_bulk=min(eb), min_ess_tail=min(et))
    return out


def flatten_chains(grouped: dict) -> dict:
    return {k: np.asarray(v).reshape(-1, *np.asarray(v).shape[2:]) for k, v in grouped.items()}
