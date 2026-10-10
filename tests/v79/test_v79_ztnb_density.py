"""The zero-truncated NB likelihood in v79_models equals NumPyro's NegativeBinomial2 log pmf minus log P(Y > 0),
up to the data-only constant sum(-lgamma(y + 1)) over detected entries: the difference is the same at every
parameter value, so the posterior is unchanged. Needs JAX/NumPyro (skipped in CI)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("numpyro")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))


def test_ztnb_factor_matches_reference_up_to_a_data_constant():
    import jax.numpy as jnp
    import numpyro.distributions as dist
    from jax.scipy.special import gammaln
    from numpyro.handlers import substitute, trace
    import v79_models as M
    rng = np.random.default_rng(0)
    di = dict(cls=np.array([0, 1, 2, 0, 1, 2, 0, 1]), src=np.array([0, 0, 1, 1, 0, 1, 0, 1]),
              op=np.array([0, 1, 2, 3, 0, 2, 1, 3]), donor=np.array([0, 1, 2, 3, 0, 2, 1, 3]),
              dk=np.arange(8), n_cls=3, n_src=2, n_op=4, n_donor=4, n_dk=8, log_lib_centered=rng.normal(0, .3, 8))
    des = M.design_arrays(di)
    y = jnp.asarray(rng.poisson(2.0, (8, 3)).astype(np.float32))
    mask = y > 0
    off = jnp.asarray(rng.normal(np.log(2000), .2, 8).astype(np.float32))
    consts = []
    for seed in range(6):
        tr = trace(__import__("numpyro").handlers.seed(M._vc_model, seed)).get_trace(
            design=des, y=y, likelihood="ztnb", mask=mask, offset=off)
        got = float(tr["y_ztnb"]["fn"].log_prob(0.0) if hasattr(tr["y_ztnb"]["fn"], "log_prob") else 0.0)
        got = float(tr["y_ztnb"]["fn"].log_factor) if hasattr(tr["y_ztnb"]["fn"], "log_factor") else got
        mu, b = tr["mu"]["value"], tr["b_depth"]["value"]
        eta = mu + b * des["depth"][:, None]
        for x in M.COMPONENTS:
            if x in M.FIXED:
                eta = eta + des["onehot"][x] @ tr[f"a_{x}"]["value"]
            else:
                eta = eta + des["proj"][x] @ tr[f"a_{x}"]["value"]
        phi = jnp.exp(tr["logphi"]["value"])
        mean = jnp.exp(eta + off[:, None])
        ref = dist.NegativeBinomial2(mean, phi).log_prob(jnp.where(mask, y, 1.0))
        ref = ref - jnp.log1p(-jnp.exp(phi * (jnp.log(phi) - jnp.log(phi + mean))))
        ref = float(jnp.where(mask, ref, 0.0).sum())
        assert np.isfinite(got), seed                      # stable even where the textbook form overflows
        if np.isfinite(ref):
            consts.append(got - ref)
    expect = float(jnp.where(mask, gammaln(y + 1.0), 0.0).sum())
    assert len(consts) >= 2 and np.allclose(consts, expect, rtol=1e-4, atol=1e-2), (consts, expect)
