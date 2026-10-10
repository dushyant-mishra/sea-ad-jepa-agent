#!/usr/bin/env python3
"""V79 simulation-based recovery: can the variance-component model recover planted structure, and can it fail?

Scenarios and pass rules are the contract's (BAYESIAN_SYNTHETIC_GEOMETRY_CONTRACT_V1, simulation_recovery):
  S1_present         every component planted                       coverage
  S0_class_absent    class variance zero                           no invented class
  S2_class_permuted  S1 data fitted with class labels permuted within source    no invented class
  S3_donor_only      only donor variance planted                   coverage of donor; no invented class
  S4_operator_only   only operator variance planted                coverage of operator; no invented class
  S5_labels_removed  S1 data fitted without donor and donor-class  residual fraction rises above S1's
Worlds use only the real grouping structure (no expression values). Every fit must also meet the contract's
diagnostics; a fit that does not is reported NOT_DIAGNOSED and its criteria are not credited.
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import v79_data as DA  # noqa: E402
import v79_firewall as FW  # noqa: E402
import v79_models as M  # noqa: E402
import v79_simulate as SIM  # noqa: E402

ROOT = HERE.parents[1]
CACHE = "D:/Jepa project/data/cache/s174_rebuilt_real_train_v1"
BRIDGE = ROOT / "results/v78/V78_S174_SHARD_OPERATOR_BRIDGE_V1.json"
RHAT_MAX, ESS_MIN = 1.01, 400
FITS = {  # name: (planted scenario, fit modification)
    "S1_present": ("S1_present", None),
    "S0_class_absent": ("S0_class_absent", None),
    "S2_class_permuted": ("S1_present", "permute_class"),
    "S3_donor_only": ("S3_donor_only_no_class", None),
    "S4_operator_only": ("S4_operator_only_no_class", None),
    "S5_labels_removed": ("S1_present", "drop_donor"),
}


def permuted_design(di: dict, seed: int) -> dict:
    """Class labels permuted among cells within each source (the class structure is destroyed, the rest kept)."""
    rng = np.random.default_rng(seed)
    out = dict(di)
    cls = di["cls"].copy()
    for s in np.unique(di["src"]):
        idx = np.where(di["src"] == s)[0]
        cls[idx] = cls[rng.permutation(idx)]
    out["cls"] = cls
    dk_keys = [f"{a}|{b}" for a, b in zip(di["donor"], cls)]
    out["dk"], levels = DA.encode(dk_keys)
    out["n_dk"] = len(levels)
    return out


def diagnose(run: dict, likelihood: str, components) -> dict:
    sites = ["mu", "b_depth"] + [f"m_{x}" for x in components if x not in M.FIXED] + \
            [f"s_{x}" for x in components if x not in M.FIXED] + [f"logsd_{x}" for x in components if x not in M.FIXED] + \
            [f"theta_{x}" for x in components if x in M.FIXED] + (["m_res", "s_res", "logsd_res"] if likelihood == "gaussian" else [])
    conv = M.convergence(run["samples"], sites)
    worst_rhat = max(v["max_rhat"] for v in conv.values())
    worst_ess = min(min(v["min_ess_bulk"], v["min_ess_tail"]) for v in conv.values())
    ok = worst_rhat <= RHAT_MAX and worst_ess >= ESS_MIN and sum(run["divergences"]) == 0
    return dict(worst_rhat=worst_rhat, worst_ess=worst_ess, divergences=run["divergences"], mean_steps=run["mean_steps"],
                seconds=run["seconds"], diagnosed=ok, per_site=conv)


def fit(name: str, di: dict, likelihood: str, n_genes: int, chains: int, warmup: int, draws: int, seed: int) -> dict:
    scen, mod = FITS[name]
    sim = SIM.simulate(di, SIM.SCENARIOS[scen], n_genes, likelihood, seed=seed)
    fdi = permuted_design(di, seed + 7) if mod == "permute_class" else di
    comps = tuple(c for c in M.COMPONENTS if not (mod == "drop_donor" and c in ("donor", "dk")))
    des = M.design_arrays(fdi)
    import jax.numpy as jnp
    run = M.run_nuts(dict(design=des, y=jnp.asarray(sim["y"]), likelihood=likelihood, components=comps),
                     n_chains=chains, warmup=warmup, draws=draws, seed=seed)
    fr = M.realized_fractions(M.flatten_chains(run["samples"]), des, likelihood, components=comps)
    per = {}
    for x, (_, frac) in fr.items():
        lo, hi = np.quantile(frac, [0.05, 0.95], axis=0)
        truth = sim["truth_frac"].get(x)
        # score a component when the scenario plants it (residual is always planted for the Gaussian); realized
        # truth can be small but nonzero for an absent component under the model's bookkeeping, so it is not used
        planted_sd = SIM.SCENARIOS[scen].get(x, None) if x != "res" else (1.0 if likelihood == "gaussian" else 0.0)
        planted = mod is None and truth is not None and bool(planted_sd and planted_sd > 0)
        per[x] = dict(gene_median=[float(v) for v in np.median(frac, 0)],
                      across_gene_median_q=[float(v) for v in np.quantile(np.median(frac, 1), [0.05, 0.5, 0.95])],
                      truth=[float(v) for v in truth] if truth is not None else None,
                      planted_and_scored=bool(planted),
                      covered=[bool(a) for a in ((truth >= lo) & (truth <= hi))] if planted else None)
    return dict(scenario=scen, modification=mod, components=list(comps), components_result=per,
                diagnostics=diagnose(run, likelihood, comps))


def criteria(res: dict) -> dict:
    out = {}
    s1 = res["S1_present"]["components_result"]
    for name, r in res.items():
        cov = [c for x in r["components_result"].values() if x["planted_and_scored"] for c in x["covered"]]
        if cov:
            n = len(cov)
            bound = stats.binom.ppf(0.01, n, 0.9) / n
            out[f"{name}.coverage"] = dict(observed=float(np.mean(cov)), bound=float(bound), n=n,
                                           pass_=bool(np.mean(cov) >= bound))
    s1_cls_q05 = s1["cls"]["across_gene_median_q"][0]
    for name in ("S0_class_absent", "S2_class_permuted", "S3_donor_only", "S4_operator_only"):
        q95 = res[name]["components_result"]["cls"]["across_gene_median_q"][2]
        out[f"{name}.no_invented_class"] = dict(q95=q95, s1_q05=s1_cls_q05, pass_=bool(q95 < s1_cls_q05))
    out["S5_labels_removed.labels_matter"] = dict(
        s5_res_q05=res["S5_labels_removed"]["components_result"]["res"]["across_gene_median_q"][0],
        s1_res_q95=s1["res"]["across_gene_median_q"][2],
        pass_=bool(res["S5_labels_removed"]["components_result"]["res"]["across_gene_median_q"][0]
                   > s1["res"]["across_gene_median_q"][2]))
    diagnosed = {name: r["diagnostics"]["diagnosed"] for name, r in res.items()}
    out["all_fits_diagnosed"] = dict(per_fit=diagnosed, pass_=all(diagnosed.values()))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--likelihood", choices=["gaussian", "bernoulli"], required=True)
    ap.add_argument("--fits", default=",".join(FITS))
    ap.add_argument("--genes", type=int, default=20)
    ap.add_argument("--chains", type=int, default=4)
    ap.add_argument("--warmup", type=int, default=1000)
    ap.add_argument("--draws", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=20261009)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    d = FW.load_cell_design(DA.local_path(CACHE), DA.local_path(BRIDGE))
    di = DA.design_indices(d)
    res, t0 = {}, time.time()
    for i, name in enumerate(a.fits.split(",")):
        res[name] = fit(name, di, a.likelihood, a.genes, a.chains, a.warmup, a.draws, a.seed + 101 * i)
        print(name, "diagnosed", res[name]["diagnostics"]["diagnosed"], "rhat", round(res[name]["diagnostics"]["worst_rhat"], 3),
              "ess", round(res[name]["diagnostics"]["worst_ess"]), "s", round(res[name]["diagnostics"]["seconds"]), flush=True)
    import jax
    rec = dict(schema="V79_SIMULATION_RECOVERY_V1", likelihood=a.likelihood, settings=vars(a),
               fits=res, criteria=criteria(res) if set(FITS) <= set(res) else None,
               environment=dict(python=sys.version.split()[0], platform=platform.platform(), jax=jax.__version__,
                                devices=[str(x) for x in jax.devices()]),
               wall_seconds=time.time() - t0)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline=chr(10)) as fh:
        fh.write(json.dumps(rec, indent=1) + chr(10))
    if rec["criteria"]:
        print({k: v["pass_"] for k, v in rec["criteria"].items()})


if __name__ == "__main__":
    main()
