#!/usr/bin/env python3
"""Does JAX's default float32 matmul precision on this GPU (TF32 on Ampere) change the model's log density?

Computes the potential and its gradient at the same point three ways in one process: GPU at default matmul
precision, GPU at 'highest' (true float32), and CPU. Run inside the WSL GPU environment from a snapshot.
Usage: check_v79_gpu_precision.py <likelihood> <scenario> <seed>
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import jax  # noqa: E402
import jax.numpy as jnp  # noqa: E402
from numpyro.infer.util import initialize_model  # noqa: E402
import v79_data as DA  # noqa: E402
import v79_firewall as FW  # noqa: E402
import v79_models as M  # noqa: E402
import v79_simulate as SIM  # noqa: E402

lik, scen, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
di = DA.design_indices(FW.load_cell_design(DA.local_path("D:/Jepa project/data/cache/s174_rebuilt_real_train_v1"),
                                           DA.local_path(HERE.parents[1] / "results/v78/V78_S174_SHARD_OPERATOR_BRIDGE_V1.json")))
des = M.design_arrays(di)
sim = SIM.simulate(di, SIM.SCENARIOS[scen], 20, lik, seed=seed)
kw = dict(design=des, y=jnp.asarray(sim["y"]), likelihood=lik)
if lik == "ztnb":
    kw.update(mask=jnp.asarray(sim["mask"]), offset=jnp.asarray(sim["offset"]))
info = initialize_model(jax.random.PRNGKey(3), M.vc_model, model_kwargs=kw)
z = info.param_info.z
out = {}
for name, dev, prec in (("gpu_default", jax.devices("gpu")[0], None), ("gpu_highest", jax.devices("gpu")[0], "highest"),
                        ("cpu", jax.devices("cpu")[0], None)):
    put = lambda tree: jax.tree_util.tree_map(lambda v: jax.device_put(v, dev) if hasattr(v, "shape") else v, tree)  # noqa: E731
    zd, kwd = put(z), put(kw)                         # arrays only; the likelihood name stays a string
    info_d = initialize_model(jax.random.PRNGKey(3), M.vc_model, model_kwargs=kwd)
    if prec:
        with jax.default_matmul_precision(prec):
            pot = float(jax.jit(info_d.potential_fn)(zd)); g = jax.jit(jax.grad(info_d.potential_fn))(zd)
    else:
        pot = float(jax.jit(info_d.potential_fn)(zd)); g = jax.jit(jax.grad(info_d.potential_fn))(zd)
    out[name] = dict(potential=pot, grad={k: np.asarray(v, dtype=np.float64) for k, v in g.items()})
res = {}
for name in ("gpu_default", "gpu_highest"):
    a, b = out[name], out["cpu"]
    gd = max(float(np.max(np.abs(a["grad"][k] - b["grad"][k])) / (np.max(np.abs(b["grad"][k])) + 1e-30)) for k in b["grad"])
    res[name] = dict(potential=a["potential"], cpu_potential=b["potential"],
                     abs_potential_diff=abs(a["potential"] - b["potential"]), max_rel_grad_diff=gd)
print(json.dumps(dict(likelihood=lik, scenario=scen, jax=jax.__version__, devices=[str(d) for d in jax.devices()],
                      comparison=res), indent=1), flush=True)
