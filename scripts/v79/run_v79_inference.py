#!/usr/bin/env python3
"""V79 real corrected-TRAIN inference for phases A, B and B0 (contract BAYESIAN_SYNTHETIC_GEOMETRY_CONTRACT_V1).

  A   Gaussian on log1p(count / cached-address library * 1e4), depth covariate log(source_library) centred
  B   Bernoulli-logit detection (count > 0), same depth covariate
  B0  cell-level Gaussian on log(source_library) and log(detected features over all addresses), no depth covariate

A and B use one frozen, identity-blind gene sample (prevalence deciles, seed from the contract). The contract's
diagnostics and retry rule are applied mechanically: any divergence -> refit at target_accept 0.95, then 0.99;
still failing any criterion -> NOT_DIAGNOSED, and its estimates are not interpreted. Outputs are INTERNAL
(results/v79/internal/): per-gene results are keyed by position in the frozen sample, and the address indices of
that sample stay in the internal record only. Nothing here is synthetic-consumable.

Refuses to run unless the custody receipt passes and the recovery and benchmark records exist and pass.
"""
from __future__ import annotations

import argparse
import hashlib
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

ROOT = HERE.parents[1]
CACHE = "D:/Jepa project/data/cache/s174_rebuilt_real_train_v1"
BRIDGE = ROOT / "results/v78/V78_S174_SHARD_OPERATOR_BRIDGE_V1.json"
CUSTODY = ROOT / "results/v79/V79_CORRECTED_TRAIN_CUSTODY_RECEIPT_V1.json"
CONTRACT = ROOT / "docs/agent/BAYESIAN_SYNTHETIC_GEOMETRY_CONTRACT_V1.json"
BENCHMARK = ROOT / "results/v79/V79_COMPUTE_BENCHMARK_V1.json"
RECOVERY = [ROOT / "results/v79/V79_SIMULATION_RECOVERY_gaussian.json",
            ROOT / "results/v79/V79_SIMULATION_RECOVERY_bernoulli.json"]
RHAT_MAX, ESS_MIN = 1.01, 400
RETRY_ACCEPT = (0.9, 0.95, 0.99)


def sha_file(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def preconditions() -> dict:
    """The contract's order: custody, recovery and benchmark must all be in place and passing."""
    fails = []
    cust = json.loads(CUSTODY.read_text(encoding="utf-8"))
    if cust["terminal"] != "PASS_V79_CORRECTED_TRAIN_CUSTODY_AUTHENTICATED":
        fails.append("custody receipt does not pass")
    for r in RECOVERY:
        if not r.exists():
            fails.append(f"missing recovery record {r.name}")
            continue
        crit = json.loads(r.read_text(encoding="utf-8")).get("criteria") or {}
        if not crit or not all(v["pass_"] for v in crit.values()):
            fails.append(f"recovery criteria do not all pass in {r.name}")
    if not BENCHMARK.exists():
        fails.append("missing compute benchmark")
    if fails:
        raise SystemExit("refusing real-data inference: " + "; ".join(fails))
    bench = json.loads(BENCHMARK.read_text(encoding="utf-8"))
    return dict(custody_sha256=sha_file(CUSTODY), contract_sha256=sha_file(CONTRACT),
                benchmark_sha256=sha_file(BENCHMARK), recovery_sha256={r.name: sha_file(r) for r in RECOVERY},
                gene_count=bench["rules_applied"]["gene_count"], held_out_folds=bench["rules_applied"]["held_out_folds"])


def diagnose(samples, likelihood: str, components) -> dict:
    sites = ["mu"] + (["b_depth"] if "b_depth" in samples else []) + \
            [f"{p}_{x}" for x in components if x not in M.FIXED for p in ("m", "s", "logsd")] + \
            [f"theta_{x}" for x in components if x in M.FIXED] + (["m_res", "s_res", "logsd_res"] if likelihood == "gaussian" else [])
    sites = [s for s in sites if s in samples]
    conv = M.convergence(samples, sites)
    return dict(worst_rhat=max(v["max_rhat"] for v in conv.values()),
                worst_ess=min(min(v["min_ess_bulk"], v["min_ess_tail"]) for v in conv.values()), per_site=conv)


def fit_with_retry(design, y, likelihood, seed, chains, warmup, draws, depth=True, mask=None) -> dict:
    import jax.numpy as jnp
    attempts = []
    for ta in RETRY_ACCEPT:
        kw = dict(design=design, y=jnp.asarray(y), likelihood=likelihood, depth=depth)
        if mask is not None:
            kw["mask"] = jnp.asarray(mask)
        run = M.run_nuts(kw, n_chains=chains, warmup=warmup, draws=draws, seed=seed, target_accept=ta)
        diag = diagnose(run["samples"], likelihood, M.COMPONENTS)
        ok = sum(run["divergences"]) == 0 and diag["worst_rhat"] <= RHAT_MAX and diag["worst_ess"] >= ESS_MIN
        attempts.append(dict(target_accept=ta, seconds=run["seconds"], divergences=run["divergences"],
                             mean_steps=run["mean_steps"], worst_rhat=diag["worst_rhat"], worst_ess=diag["worst_ess"],
                             diagnosed=ok))
        if ok or sum(run["divergences"]) == 0:
            break                           # the retry rule escalates only on divergences
    return dict(run=run, attempts=attempts, diagnosed=attempts[-1]["diagnosed"])


def summarize(run, design, likelihood, mask=None, typical_offset=None, components=M.COMPONENTS) -> dict:
    """Per component: the fraction summaries, and the absolute realized variance (per-gene posterior median and
    90% interval), which a generator needs as a magnitude as well as a share."""
    fr = M.realized_fractions(M.flatten_chains(run["samples"]), design, likelihood, components=components, mask=mask,
                              typical_offset=typical_offset)
    out = {}
    for k, (var, frac) in fr.items():
        med = np.median(frac, 1)                                     # across-gene median, per draw
        out[k] = dict(across_gene_median_q=[float(v) for v in np.quantile(med, [0.05, 0.5, 0.95])],
                      per_gene_median=[float(v) for v in np.median(frac, 0)],
                      per_gene_q05=[float(v) for v in np.quantile(frac, 0.05, 0)],
                      per_gene_q95=[float(v) for v in np.quantile(frac, 0.95, 0)],
                      variance_per_gene_median=[float(v) for v in np.median(var, 0)],
                      variance_per_gene_q05=[float(v) for v in np.quantile(var, 0.05, 0)],
                      variance_per_gene_q95=[float(v) for v in np.quantile(var, 0.95, 0)])
    return out


HYPER_SITES = ("m_op", "s_op", "m_donor", "s_donor", "m_dk", "s_dk", "m_res", "s_res", "m_phi", "s_phi")


def hyperparameters(run) -> dict:
    """Posterior 5/50/95% of the population hyperparameters: m_x is the typical per-gene log sd of component x,
    s_x the spread of per-gene log sds across genes. Anonymous by construction (no gene index)."""
    flat = M.flatten_chains(run["samples"])
    return {k: [float(v) for v in np.quantile(np.asarray(flat[k], dtype=np.float64), [0.05, 0.5, 0.95])]
            for k in HYPER_SITES if k in flat}


def phase_response(phase: str, d: dict, X, gene_count: int) -> dict:
    """The response matrix of a phase, built once here for the fit and for the held-out checks."""
    if phase == "B0":
        n_det = np.asarray((X > 0).sum(1)).ravel().astype(np.float64)
        y = np.stack([np.log(np.asarray(d["source_library"], dtype=np.float64)), np.log(np.maximum(n_det, 1))], 1)
        return dict(y=y.astype(np.float32), likelihood="gaussian", depth=False, genes=None,
                    responses=["log_source_library", "log_detected_features"])
    genes = DA.stratified_gene_sample(X, gene_count)
    if phase == "A":
        lib = np.asarray(X.sum(1)).ravel()
        return dict(y=DA.cp10k_log1p(X, genes, lib).astype(np.float32), likelihood="gaussian", depth=True,
                    genes=genes, responses=None)
    return dict(y=(X[:, genes].toarray() > 0).astype(np.float32), likelihood="bernoulli", depth=True, genes=genes,
                responses=None)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=["A", "B", "B0"], required=True)
    ap.add_argument("--chains", type=int, default=4)
    ap.add_argument("--warmup", type=int, default=1000)
    ap.add_argument("--draws", type=int, default=1000)
    ap.add_argument("--out-dir", default=str(ROOT / "results/v79/internal"))
    a = ap.parse_args()
    pre = preconditions()
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    seed = contract["inference"]["seed_base"] + {"A": 1, "B": 2, "B0": 3}[a.phase]
    d = FW.load_cell_design(DA.local_path(CACHE), DA.local_path(BRIDGE))
    di = DA.design_indices(d)
    des = M.design_arrays(di)
    X = DA.load_counts(DA.local_path(CACHE), DA.local_path(BRIDGE))
    t0 = time.time()
    pr = phase_response(a.phase, d, X, pre["gene_count"])
    lik, genes, responses = pr["likelihood"], pr["genes"], pr["responses"]
    res = fit_with_retry(des, pr["y"], lik, seed, a.chains, a.warmup, a.draws, depth=pr["depth"])
    import jax
    rec = dict(
        schema=f"V79_PHASE_{a.phase}_INTERNAL_V1", status="INTERNAL__NOT_SYNTHETIC_CONSUMABLE",
        phase=a.phase, likelihood=lik, preconditions=pre, settings=vars(a), seed=seed,
        diagnosed=res["diagnosed"], attempts=res["attempts"],
        interpretation=("estimates may be read" if res["diagnosed"] else
                        "NOT_DIAGNOSED: estimates are recorded but must not be interpreted"),
        fractions=summarize(res["run"], des, lik), hyperparameters=hyperparameters(res["run"]),
        responses=responses,
        gene_sample=dict(n=None if genes is None else int(len(genes)), seed=DA.GENE_SAMPLE_SEED,
                         internal_address_indices=None if genes is None else [int(g) for g in genes]),
        environment=dict(python=sys.version.split()[0], platform=platform.platform(), jax=jax.__version__),
        wall_seconds=time.time() - t0, lane=FW.LANE_TERMINAL)
    out = Path(a.out_dir) / f"V79_PHASE_{a.phase}_INTERNAL_V1.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline=chr(10)) as fh:
        fh.write(json.dumps(rec, indent=1) + chr(10))
    print(a.phase, "diagnosed", rec["diagnosed"], [(x["target_accept"], round(x["worst_rhat"], 4), round(x["worst_ess"])) for x in res["attempts"]])


if __name__ == "__main__":
    main()
