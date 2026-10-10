import sys, json, time, numpy as np
sys.path.insert(0, "D:/jepa_wt_v79_bayes_20261009/scripts/v79")
import v79_firewall as FW, v79_data as DA, v79_models as M, v79_simulate as SIM
import jax.numpy as jnp
# usage: run_v79_qualification.py <gaussian|bernoulli|ztnb|lognormal> [target_accept]; S1 world, 10 genes, contract schedule
# lognormal: the Phase C log-normal family (Gaussian on log count minus offset over detected cells) fitted to the
# ztnb world; its fractions are compared with the ztnb truth only descriptively (different family, no coverage rule)
d = FW.load_cell_design("D:/Jepa project/data/cache/s174_rebuilt_real_train_v1", "D:/jepa_wt_v79_bayes_20261009/results/v78/V78_S174_SHARD_OPERATOR_BRIDGE_V1.json")
di = DA.design_indices(d); des = M.design_arrays(di)
lik = sys.argv[1]
ta = float(sys.argv[2]) if len(sys.argv) > 2 else 0.9
sim = SIM.simulate(di, SIM.SCENARIOS["S1_present"], 10, "ztnb" if lik == "lognormal" else lik, seed=1)
kw = dict(design=des, y=jnp.asarray(sim["y"]), likelihood=lik)
if lik == "ztnb":
    kw.update(mask=jnp.asarray(sim["mask"]), offset=jnp.asarray(sim["offset"]))
if lik == "lognormal":
    ylog = np.where(sim["mask"], np.log(np.maximum(sim["y"], 1.0)) - sim["offset"][:, None], 0.0).astype(np.float32)
    kw = dict(design=des, y=jnp.asarray(ylog), likelihood="gaussian", mask=jnp.asarray(sim["mask"]))
    lik_fit = "gaussian"
else:
    lik_fit = lik
r = M.run_nuts(kw, n_chains=4, warmup=1000, draws=1000, seed=5, target_accept=ta)
flat = M.flatten_chains(r["samples"])
fr = M.realized_fractions(flat, des, lik_fit, mask=sim.get("mask"), typical_offset=sim.get("typical_offset"))
sites = ["m_donor","m_op","m_dk","s_donor","s_op","s_dk","mu","b_depth"] + (["m_res"] if lik_fit=="gaussian" else []) + (["m_phi","s_phi","logphi"] if lik=="ztnb" else [])
conv = M.convergence(r["samples"], sites)
out = dict(lik=lik, centring=M.CENTRING[M.centring_key(lik_fit, kw.get("mask"))], target_accept=ta, seconds=r["seconds"], divergences=r["divergences"], mean_steps=r["mean_steps"], conv=conv,
           recovery={x: dict(cov90=float(np.mean((sim["truth_frac"][x] >= np.quantile(fr[x][1], .05, 0)) & (sim["truth_frac"][x] <= np.quantile(fr[x][1], .95, 0)))),
                             est_median=float(np.median(np.median(fr[x][1], 0))), truth_median=float(np.median(sim["truth_frac"][x])))
                     for x in ("cls","src","op","donor","dk","res")})
if lik == "ztnb":
    lp = np.median(np.asarray(flat["logphi"]), 0)
    out["logphi_recovery"] = dict(est=[float(v) for v in lp], truth=[float(v) for v in sim["truth_logphi"]])
print(json.dumps(out, indent=1), flush=True)
