#!/usr/bin/env python3
"""V79 Phase C: positive magnitude conditional on detection (contract BAYESIAN_SYNTHETIC_GEOMETRY_CONTRACT_V1).

Candidate families (contract): log-normal on log count and zero-truncated negative binomial, both with the
log-depth offset log(cached-address library) and the same components and depth covariate as Phases A and B, on
the same frozen gene sample. Only each gene's detected cells enter; the detected pattern is held fixed.

  fold    --family F --fold f   fit F on the donors outside fold f (source-stratified donor folds, frozen seed,
                                number of folds from the benchmark); for every held-out positive observation the
                                pointwise log predictive probability on the count scale (v79_phase_c) with new
                                donor and donor-class effects drawn from the fitted spreads (v79_ppc), plus
                                held-out posterior predictive coverage of the positive-count statistics
  choose                        the frozen rule: higher mean held-out lpd per positive observation wins
  full    --family F            fit the chosen family on every cell; realized variance fractions over detected cells

The family choice is refused unless every fold of both families is diagnosed. `full` refuses a family other
than the recorded winner. Outputs are INTERNAL (results/v79/internal/phase_c/); genes are positions in the frozen
sample. Gated like every real-data runner (custody, recovery, benchmark) and additionally on the zero-truncated
NB recovery suite, since that likelihood is new in Phase C.
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
import v79_phase_c as PC  # noqa: E402
import v79_ppc as PPC  # noqa: E402

ROOT = HERE.parents[1]
CACHE = "D:/Jepa project/data/cache/s174_rebuilt_real_train_v1"
BRIDGE = ROOT / "results/v78/V78_S174_SHARD_OPERATOR_BRIDGE_V1.json"
CONTRACT = ROOT / "docs/agent/BAYESIAN_SYNTHETIC_GEOMETRY_CONTRACT_V1.json"
ZTNB_RECOVERY = ROOT / "results/v79/V79_SIMULATION_RECOVERY_ztnb.json"
OUT = ROOT / "results/v79/internal/phase_c"
N_PRED_DRAWS = 1000
SEED_OFFSET = {"full": 4, "ztnb": 40, "lognormal": 50}     # added to the contract seed base (fold added too)


def gate() -> dict:
    import run_v79_inference as INF
    pre = INF.preconditions()
    if not ZTNB_RECOVERY.exists():
        raise SystemExit("refusing Phase C: missing zero-truncated NB recovery record")
    crit = json.loads(ZTNB_RECOVERY.read_text(encoding="utf-8")).get("criteria") or {}
    if not crit or not all(v["pass_"] for v in crit.values()):
        raise SystemExit("refusing Phase C: zero-truncated NB recovery criteria do not all pass")
    pre["ztnb_recovery_sha256"] = INF.sha_file(ZTNB_RECOVERY)
    return pre


def load(pre: dict) -> dict:
    d = FW.load_cell_design(DA.local_path(CACHE), DA.local_path(BRIDGE))
    di = DA.design_indices(d)
    X = DA.load_counts(DA.local_path(CACHE), DA.local_path(BRIDGE))
    genes = DA.stratified_gene_sample(X, pre["gene_count"])
    counts = X[:, genes].toarray().astype(np.float64)
    if not np.array_equal(counts, np.round(counts)) or counts.min() < 0:
        raise SystemExit("STOP: sampled counts are not non-negative integers; the negative binomial is undefined")
    lib = np.asarray(X.sum(1)).ravel().astype(np.float64)
    return dict(di=di, genes=genes, counts=counts, mask=counts > 0, offset=np.log(lib))


def model_kwargs(family: str, des: dict, data: dict, rows) -> dict:
    import jax.numpy as jnp
    c, m, o = data["counts"][rows], data["mask"][rows], data["offset"][rows]
    if family == "ztnb":
        return dict(design=des, y=jnp.asarray(c.astype(np.float32)), likelihood="ztnb", mask=jnp.asarray(m),
                    offset=jnp.asarray(o.astype(np.float32)))
    ylog = np.where(m, np.log(np.maximum(c, 1.0)) - o[:, None], 0.0)
    return dict(design=des, y=jnp.asarray(ylog.astype(np.float32)), likelihood="gaussian", mask=jnp.asarray(m))


def diagnose(samples, family: str) -> dict:
    import run_v79_inference as INF
    import v79_models as M
    lik = "gaussian" if family == "lognormal" else "ztnb"
    diag = INF.diagnose(samples, lik, M.COMPONENTS)
    if family == "ztnb":
        conv = M.convergence(samples, ["m_phi", "s_phi", "logphi"])
        diag["per_site"].update(conv)
        diag["worst_rhat"] = max(diag["worst_rhat"], max(v["max_rhat"] for v in conv.values()))
        diag["worst_ess"] = min(diag["worst_ess"], min(min(v["min_ess_bulk"], v["min_ess_tail"]) for v in conv.values()))
    return diag


def fit(kw: dict, family: str, seed: int, a) -> dict:
    import run_v79_inference as INF
    import v79_models as M
    attempts, run = [], None
    for ta in INF.RETRY_ACCEPT:
        run = M.run_nuts(kw, n_chains=a.chains, warmup=a.warmup, draws=a.draws, seed=seed, target_accept=ta)
        dg = diagnose(run["samples"], family)
        ok = sum(run["divergences"]) == 0 and dg["worst_rhat"] <= INF.RHAT_MAX and dg["worst_ess"] >= INF.ESS_MIN
        attempts.append(dict(target_accept=ta, seconds=run["seconds"], divergences=run["divergences"],
                             mean_steps=run["mean_steps"], worst_rhat=dg["worst_rhat"], worst_ess=dg["worst_ess"],
                             diagnosed=bool(ok)))
        if sum(run["divergences"]) == 0:
            break
    return dict(run=run, attempts=attempts, diagnosed=attempts[-1]["diagnosed"],
                centring=M.CENTRING[M.centring_key(kw["likelihood"], kw.get("mask"))])


def env() -> dict:
    import jax
    return dict(python=sys.version.split()[0], platform=platform.platform(), jax=jax.__version__)


def write(path: Path, rec: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline=chr(10)) as fh:
        fh.write(json.dumps(PPC._jsonable(rec)) + chr(10))


def fold(a) -> None:
    import v79_models as M
    pre = gate()
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    base = contract["inference"]["seed_base"]
    data = load(pre)
    di = data["di"]
    folds = PPC.donor_folds(di, pre["held_out_folds"], base)
    train_di, tr, te, tm = PPC.split_design(di, folds[a.fold])
    des = M.design_arrays(train_di)
    seed = base + SEED_OFFSET[a.family] + a.fold
    t0 = time.time()
    res = fit(model_kwargs(a.family, des, data, tr), a.family, seed, a)
    flat = M.flatten_chains(res["run"]["samples"])
    sel = PPC.thin_indices(flat["mu"].shape[0], N_PRED_DRAWS)
    y, w, off = data["counts"][te], data["mask"][te], data["offset"][te]
    oi, og = np.nonzero(w)                                  # held-out positive observations, row-major order
    yv = y[oi, og]
    acc = np.full(len(yv), -np.inf)
    obs_stats = PPC.positive_statistics(y, w, tm)
    reps = []
    par = "logphi" if a.family == "ztnb" else "logsd_res"
    for i in sel.tolist():
        rng = np.random.default_rng([base, a.fold, i])
        sub = {k: v[i:i + 1] for k, v in flat.items()}
        eta = PPC.heldout_eta(sub, des, tm, tm["depth"], rng, 1, M.COMPONENTS, True)[0][0]
        m = eta[oi, og] + off[oi]
        p = np.exp(np.asarray(flat[par][i], dtype=np.float64))[og]
        lp = PC.ztnb_logpmf(yv, np.exp(m), p) if a.family == "ztnb" else PC.lognormal_count_logpmf(yv, m, p)
        acc = np.logaddexp(acc, lp)
        draw = {par: np.asarray(flat[par][i])}
        rep = PPC.replicate_positive(a.family, eta, off, draw, rng) * w
        reps.append(PPC.positive_statistics(rep, w, tm))
    pointwise = acc - np.log(len(sel))
    cov = PPC.coverage(obs_stats, reps)
    rec = dict(schema="V79_PHASE_C_FOLD_INTERNAL_V1", status="INTERNAL__NOT_SYNTHETIC_CONSUMABLE",
               family=a.family, fold=a.fold, k=pre["held_out_folds"], fold_seed=base, nuts_seed=seed,
               preconditions=pre, settings=dict(chains=a.chains, warmup=a.warmup, draws=a.draws,
                                                n_pred_draws=int(len(sel))),
               centring=res["centring"], attempts=res["attempts"], diagnosed=res["diagnosed"],
               n_train_cells=int(len(tr)), n_test_cells=int(len(te)), n_positive_observations=int(len(yv)),
               observation_donor_code=tm["donor_original_code"][tm["donor"][oi]],
               observation_gene_position=og, pointwise_lpd=pointwise, mean_lpd=float(pointwise.mean()),
               coverage=cov, environment=env(), wall_seconds=time.time() - t0, lane=FW.LANE_TERMINAL)
    write(OUT / f"fold_{a.family}_{a.fold}.json", rec)
    print(a.family, "fold", a.fold, "diagnosed", res["diagnosed"], "mean lpd", round(rec["mean_lpd"], 4))


def choose(a) -> None:
    recs = {}
    for p in sorted(OUT.glob("fold_*_*.json")):
        r = json.loads(p.read_text(encoding="utf-8"))
        recs[(r["family"], r["fold"])] = r
    ks = {r["k"] for r in recs.values()}
    if len(ks) != 1:
        raise SystemExit(f"fold records disagree on k: {ks}")
    k = ks.pop()
    missing = [(f, i) for f in PC.FAMILIES for i in range(k) if (f, i) not in recs]
    if missing:
        raise SystemExit(f"missing fold records: {missing}")
    undiagnosed = [key for key, r in recs.items() if not r["diagnosed"]]
    lpd, donors = {f: [] for f in PC.FAMILIES}, []
    for i in range(k):
        z, g = recs[("ztnb", i)], recs[("lognormal", i)]
        if z["observation_donor_code"] != g["observation_donor_code"] or \
                z["observation_gene_position"] != g["observation_gene_position"]:
            raise SystemExit(f"fold {i}: the two families were scored on different observations")
        for f in PC.FAMILIES:
            lpd[f].extend(recs[(f, i)]["pointwise_lpd"])
        donors.extend(z["observation_donor_code"])
    result = None if undiagnosed else PC.compare(lpd, donors)
    rec = dict(schema="V79_PHASE_C_FAMILY_CHOICE_INTERNAL_V1", status="INTERNAL__NOT_SYNTHETIC_CONSUMABLE", k=k,
               undiagnosed_folds=[list(x) for x in undiagnosed],
               decision=("REFUSED: not every fold is diagnosed; no family is chosen" if undiagnosed else
                         f"{result['winner']} (frozen rule)"),
               comparison=result,
               per_fold_mean_lpd={f"{f}_{i}": recs[(f, i)]["mean_lpd"] for f in PC.FAMILIES for i in range(k)},
               fold_record_files=sorted(p.name for p in OUT.glob("fold_*_*.json")), lane=FW.LANE_TERMINAL)
    write(OUT / "V79_PHASE_C_FAMILY_CHOICE_INTERNAL_V1.json", rec)
    print(rec["decision"])


def full(a) -> None:
    import v79_models as M
    choice = json.loads((OUT / "V79_PHASE_C_FAMILY_CHOICE_INTERNAL_V1.json").read_text(encoding="utf-8"))
    if a.family == "auto" and choice["comparison"] is not None:
        a.family = choice["comparison"]["winner"]
    if choice["comparison"] is None or choice["comparison"]["winner"] != a.family:
        raise SystemExit(f"refusing: {a.family} is not the recorded winner ({choice['decision']})")
    pre = gate()
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    data = load(pre)
    des = M.design_arrays(data["di"])
    seed = contract["inference"]["seed_base"] + SEED_OFFSET["full"]
    t0 = time.time()
    rows = np.arange(data["di"]["n"])
    res = fit(model_kwargs(a.family, des, data, rows), a.family, seed, a)
    w = data["mask"]
    typical = (data["offset"][:, None] * w).sum(0) / np.maximum(w.sum(0), 1)
    lik = "ztnb" if a.family == "ztnb" else "gaussian"
    import run_v79_inference as INF
    frac = INF.summarize(res["run"], des, lik, mask=w, typical_offset=typical if lik == "ztnb" else None)
    hyper = INF.hyperparameters(res["run"])
    rec = dict(schema="V79_PHASE_C_INTERNAL_V1", status="INTERNAL__NOT_SYNTHETIC_CONSUMABLE", family=a.family,
               residual_convention=("Nakagawa, Johnson & Schielzeth 2017 log-normal approximation ln(1 + 1/lambda + "
                                    "1/phi) for the NB2 parent (a convention for the truncated model)"
                                    if lik == "ztnb" else "Gaussian residual variance on log count"),
               family_choice_sha256=__import__("hashlib").sha256(
                   (OUT / "V79_PHASE_C_FAMILY_CHOICE_INTERNAL_V1.json").read_bytes()).hexdigest(),
               preconditions=pre, seed=seed, centring=res["centring"], attempts=res["attempts"],
               diagnosed=res["diagnosed"],
               interpretation=("estimates may be read" if res["diagnosed"] else
                               "NOT_DIAGNOSED: estimates are recorded but must not be interpreted"),
               detected_share_per_gene=w.mean(0), fractions=frac, hyperparameters=hyper,
               gene_sample=dict(n=int(len(data["genes"])), seed=DA.GENE_SAMPLE_SEED,
                                internal_address_indices=data["genes"]),
               environment=env(), wall_seconds=time.time() - t0, lane=FW.LANE_TERMINAL)
    write(OUT / "V79_PHASE_C_INTERNAL_V1.json", rec)
    print("phase C", a.family, "diagnosed", res["diagnosed"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["fold", "choose", "full"])
    ap.add_argument("--family", choices=list(PC.FAMILIES) + ["auto"], help="auto (full only): the recorded winner")
    ap.add_argument("--fold", type=int, default=0)
    ap.add_argument("--chains", type=int, default=4)
    ap.add_argument("--warmup", type=int, default=1000)
    ap.add_argument("--draws", type=int, default=1000)
    a = ap.parse_args()
    if a.mode in ("fold", "full") and not a.family:
        raise SystemExit("--family is required")
    if a.mode == "fold" and a.family == "auto":
        raise SystemExit("--family auto is only for full")
    {"fold": fold, "choose": choose, "full": full}[a.mode](a)


if __name__ == "__main__":
    main()
