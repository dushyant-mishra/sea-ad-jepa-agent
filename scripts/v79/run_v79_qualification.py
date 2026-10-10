import sys, json, time, numpy as np
sys.path.insert(0, "D:/jepa_wt_v79_bayes_20261009/scripts/v79")
import v79_firewall as FW, v79_data as DA, v79_models as M, v79_simulate as SIM
import jax.numpy as jnp
d = FW.load_cell_design("D:/Jepa project/data/cache/s174_rebuilt_real_train_v1", "D:/jepa_wt_v79_bayes_20261009/results/v78/V78_S174_SHARD_OPERATOR_BRIDGE_V1.json")
di = DA.design_indices(d); des = M.design_arrays(di)
lik = sys.argv[1]
sim = SIM.simulate(di, SIM.SCENARIOS["S1_present"], 10, lik, seed=1)
r = M.run_nuts(dict(design=des, y=jnp.asarray(sim["y"]), likelihood=lik), n_chains=4, warmup=1000, draws=1000, seed=5)
flat = M.flatten_chains(r["samples"]); fr = M.realized_fractions(flat, des, lik)
sites = ["m_donor","m_op","m_dk","s_donor","s_op","s_dk","mu","b_depth"] + (["m_res"] if lik=="gaussian" else [])
conv = M.convergence(r["samples"], sites)
out = dict(lik=lik, seconds=r["seconds"], divergences=r["divergences"], mean_steps=r["mean_steps"], conv=conv,
           recovery={x: dict(cov90=float(np.mean((sim["truth_frac"][x] >= np.quantile(fr[x][1], .05, 0)) & (sim["truth_frac"][x] <= np.quantile(fr[x][1], .95, 0)))),
                             est_median=float(np.median(np.median(fr[x][1], 0))), truth_median=float(np.median(sim["truth_frac"][x])))
                     for x in ("cls","src","op","donor","dk","res")})
print(json.dumps(out, indent=1), flush=True)
