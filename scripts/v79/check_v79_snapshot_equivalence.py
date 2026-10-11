"""Prove that recovery fits from earlier snapshots compute exactly what snapshot ad5bbd17 computes for their family:
identical simulated world bytes and identical model potential and gradient at the same point (same sites)."""
import importlib.util
import json
import sys

import numpy as np

PAIRS = {"gaussian": "11d95649", "bernoulli": "aa00a5ac", "lognormal": "33ce9fee"}
NEW = "ad5bbd17"


def load(snap, name):
    spec = importlib.util.spec_from_file_location(f"{name}_{snap}", f"D:/v79_runs/{snap}/scripts/v79/{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[f"{name}_{snap}"] = mod
    spec.loader.exec_module(mod)
    return mod


def main():
    sys.path.insert(0, f"D:/v79_runs/{NEW}/scripts/v79")
    import jax
    import jax.numpy as jnp
    from numpyro.infer.util import initialize_model
    import v79_data as DA
    import v79_firewall as FW
    di = DA.design_indices(FW.load_cell_design("D:/Jepa project/data/cache/s174_rebuilt_real_train_v1",
                                               f"D:/v79_runs/{NEW}/results/v78/V78_S174_SHARD_OPERATOR_BRIDGE_V1.json"))
    out = {}
    for lik, old in PAIRS.items():
        res = {}
        for snap in (old, NEW):
            sys.path.insert(0, f"D:/v79_runs/{snap}/scripts/v79")
            M, SIM = load(snap, "v79_models"), load(snap, "v79_simulate")
            sim = SIM.simulate(di, SIM.SCENARIOS["S1_present"], 20, lik, seed=1_000_000)
            kw = dict(design=M.design_arrays(di), y=jnp.asarray(sim["y"]),
                      likelihood="gaussian" if lik == "lognormal" else lik)
            if lik == "lognormal":
                kw["mask"] = jnp.asarray(sim["mask"])
            info = initialize_model(jax.random.PRNGKey(3), M.vc_model, model_kwargs=kw)
            z = info.param_info.z
            g = jax.grad(info.potential_fn)(z)
            res[snap] = dict(y=np.asarray(sim["y"]).tobytes(), sites=sorted(z), pot=float(info.potential_fn(z)),
                             grad={k: np.asarray(v) for k, v in g.items()})
            sys.path.pop(0)
        a, b = res[old], res[NEW]
        out[lik] = dict(old=old, new=NEW, world_identical=a["y"] == b["y"], sites_identical=a["sites"] == b["sites"],
                        potential_identical=a["pot"] == b["pot"],
                        gradient_identical=all(np.array_equal(a["grad"][k], b["grad"][k]) for k in a["grad"]))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
