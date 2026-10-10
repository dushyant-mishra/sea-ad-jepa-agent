#!/usr/bin/env python3
"""V79 computational feasibility benchmark (contract deliverable 8). Simulated data on the real design only.

Measures, with JAX work blocked before every clock read:
  - potential and gradient cost per call for 10, 30 and 60 genes, both likelihoods;
  - one full-schedule fit (contract chains, warm-up and draws) at --fit-genes genes per likelihood: wall time,
    mean NUTS steps, divergences and worst R-hat/ESS.
Then applies the contract's frozen rules: the gene count is the largest multiple of 10 (at most 60) whose
projected full-fit time is within 2 hours (projection: measured full fit x gradient-cost ratio, which assumes
steps per iteration do not grow with genes; the record states this assumption); held-out-donor folds are 5 if
one fit takes at most 30 minutes, otherwise 2. The Pyro attempt that was abandoned is recorded as evidence.
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import v79_data as DA  # noqa: E402
import v79_firewall as FW  # noqa: E402
import v79_models as M  # noqa: E402
import v79_simulate as SIM  # noqa: E402

ROOT = HERE.parents[1]
CACHE = "D:/Jepa project/data/cache/s174_rebuilt_real_train_v1"
BRIDGE = ROOT / "results/v78/V78_S174_SHARD_OPERATOR_BRIDGE_V1.json"
PYRO_EVIDENCE = dict(framework="Pyro 1.9.1 on PyTorch 2.7.0+cu128 (env sea-ad-jepa-v3, RTX 3080)",
                     outcome="abandoned: a 10-gene Gaussian fit with 150 warm-up and 50 draws did not finish within "
                             "about 27 minutes; per-step Python overhead with deep NUTS trees",
                     note="recorded from the self-audit log; not re-run")


def grad_timing(des, n_genes: int, likelihood: str, reps: int = 30) -> dict:
    import jax
    import jax.numpy as jnp
    from numpyro.infer.util import initialize_model
    sim = SIM.simulate(dict(_DI), SIM.SCENARIOS["S1_present"], n_genes, likelihood, seed=11)
    info = initialize_model(jax.random.PRNGKey(0), M.vc_model,
                            model_kwargs=dict(design=des, y=jnp.asarray(sim["y"]), likelihood=likelihood))
    f, g, z = jax.jit(info.potential_fn), jax.jit(jax.grad(info.potential_fn)), info.param_info.z
    jax.block_until_ready(f(z))
    jax.block_until_ready(g(z))
    out = {}
    for name, fn in (("potential_ms", f), ("gradient_ms", g)):
        t = time.time()
        for _ in range(reps):
            jax.block_until_ready(fn(z))
        out[name] = (time.time() - t) / reps * 1000
    out["n_params"] = int(sum(int(np.prod(v.shape)) for v in z.values()))
    return out


def full_fit(des, n_genes: int, likelihood: str, chains: int, warmup: int, draws: int, seed: int) -> dict:
    import jax.numpy as jnp
    sim = SIM.simulate(dict(_DI), SIM.SCENARIOS["S1_present"], n_genes, likelihood, seed=seed)
    r = M.run_nuts(dict(design=des, y=jnp.asarray(sim["y"]), likelihood=likelihood),
                   n_chains=chains, warmup=warmup, draws=draws, seed=seed)
    sites = ["mu", "b_depth", "m_op", "m_donor", "m_dk", "s_op", "s_donor", "s_dk"] + \
            (["m_res", "s_res"] if likelihood == "gaussian" else [])
    conv = M.convergence(r["samples"], sites)
    return dict(seconds=r["seconds"], mean_steps=r["mean_steps"], divergences=r["divergences"],
                worst_rhat=max(v["max_rhat"] for v in conv.values()),
                worst_ess=min(min(v["min_ess_bulk"], v["min_ess_tail"]) for v in conv.values()))


def main() -> None:
    global _DI
    ap = argparse.ArgumentParser()
    ap.add_argument("--fit-genes", type=int, default=10)
    ap.add_argument("--chains", type=int, default=4)
    ap.add_argument("--warmup", type=int, default=1000)
    ap.add_argument("--draws", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=20261009)
    ap.add_argument("--qualification", nargs="*", default=None,
                    help="likelihood=path pairs of committed qualification records (contract settings, same model "
                         "code) whose full-fit wall times are used instead of refitting")
    ap.add_argument("--out", default=str(ROOT / "results/v79/V79_COMPUTE_BENCHMARK_V1.json"))
    a = ap.parse_args()
    import jax
    _DI = DA.design_indices(FW.load_cell_design(DA.local_path(CACHE), DA.local_path(BRIDGE)))
    des = M.design_arrays(_DI)
    grads = {lik: {g: grad_timing(des, g, lik) for g in (10, 30, 60)} for lik in ("gaussian", "bernoulli")}
    if a.qualification:
        fits = {}
        for pair in a.qualification:
            lik, path = pair.split("=", 1)
            q = json.loads(Path(path).read_text(encoding="utf-8"))
            fits[lik] = dict(seconds=q["seconds"], mean_steps=q["mean_steps"], divergences=q["divergences"],
                             worst_rhat=max(v["max_rhat"] for v in q["conv"].values()),
                             worst_ess=min(min(v["min_ess_bulk"], v["min_ess_tail"]) for v in q["conv"].values()),
                             source=str(path))
    else:
        fits = {lik: full_fit(des, a.fit_genes, lik, a.chains, a.warmup, a.draws, a.seed)
                for lik in ("gaussian", "bernoulli")}
    proj = {}
    for lik in fits:
        base = grads[lik][a.fit_genes]["gradient_ms"]
        proj[lik] = {g: fits[lik]["seconds"] * grads[lik][g]["gradient_ms"] / base for g in (10, 30, 60)}
    worst = {g: max(proj[lik][g] for lik in proj) for g in (10, 30, 60)}
    feasible = [g for g in (10, 30, 60) if worst[g] <= 7200]
    # the rule is a multiple of 10 up to 60; interpolate linearly between measured points
    candidates = [g for g in range(10, 70, 10) if np.interp(g, [10, 30, 60], [worst[10], worst[30], worst[60]]) <= 7200]
    n_genes = max(candidates) if candidates else None
    fit_s = float(np.interp(n_genes, [10, 30, 60], [worst[10], worst[30], worst[60]])) if n_genes else None
    rec = dict(
        schema="V79_COMPUTE_BENCHMARK_V1", data="simulated responses on the real corrected-TRAIN design; no expression read",
        environment=dict(python=sys.version.split()[0], platform=platform.platform(), jax=jax.__version__,
                         devices=[str(x) for x in jax.devices()]),
        pyro_attempt=PYRO_EVIDENCE, gradient_timing=grads, full_fit=dict(genes=a.fit_genes, settings=vars(a), fits=fits),
        projection=dict(seconds_by_genes=proj, worst_by_genes=worst,
                        assumption="steps per iteration do not grow with the gene count; checked at the first real fit"),
        rules_applied=dict(gene_count=n_genes, projected_fit_seconds=fit_s, measured_feasible_points=feasible,
                           held_out_folds=(5 if fit_s is not None and fit_s <= 1800 else 2)))
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline=chr(10)) as fh:
        fh.write(json.dumps(rec, indent=1) + chr(10))
    print(json.dumps(rec["rules_applied"]), json.dumps({k: round(v["seconds"]) for k, v in fits.items()}))


_DI: dict = {}

if __name__ == "__main__":
    main()
