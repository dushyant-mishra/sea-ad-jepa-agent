#!/usr/bin/env python3
"""Are two V79 snapshots computationally identical for recovery? Checked on EVERY world path, not S1 alone
(controller ruling 2026-10-11): for each likelihood family and each of S0-S5, the simulated world bytes, the fitted
design (the S2 class permutation), the components fitted (S5 drops donor and donor-class), the resolved sampler
centring, the sampled sites, and the potential and gradient at the same point. Each snapshot runs in its own
process, so no module cache or global JAX setting leaks between them. CPU only.

Usage: check_v79_snapshot_equivalence.py <snapshot dir A> <snapshot dir B> [likelihoods ...] > certificate.json
       check_v79_snapshot_equivalence.py --dump <snapshot dir> <out.npz> <likelihoods ...>   (internal)
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

LIKS = ("gaussian", "bernoulli", "ztnb", "lognormal")


def dump(snap: Path, out: Path, liks) -> None:
    sys.path.insert(0, str(snap / "scripts" / "v79"))
    import jax
    import jax.numpy as jnp
    from numpyro.infer.util import initialize_model
    import run_v79_recovery as RR
    import v79_data as DA
    import v79_firewall as FW
    import v79_models as M
    import v79_simulate as SIM
    di = DA.design_indices(FW.load_cell_design(DA.local_path("D:/Jepa project/data/cache/s174_rebuilt_real_train_v1"),
                                               DA.local_path(snap / "results/v78/V78_S174_SHARD_OPERATOR_BRIDGE_V1.json")))
    arrays, meta = {}, {}
    for lik in liks:
        lik_model = "gaussian" if lik == "lognormal" else lik
        for name, (scen, mod) in RR.FITS.items():
            off = {"gaussian": 0, "bernoulli": 500, "ztnb": 700, "lognormal": 900}[lik]
            sim = SIM.simulate(di, SIM.SCENARIOS[scen], 6, lik, seed=1_000_000 + list(SIM.SCENARIOS).index(scen) + off)
            fdi = RR.permuted_design(di, 20261009 + 7) if mod == "permute_class" else di
            comps = tuple(c for c in M.COMPONENTS if not (mod == "drop_donor" and c in ("donor", "dk")))
            des = M.design_arrays(fdi)
            kw = dict(design=des, y=jnp.asarray(sim["y"]), likelihood=lik_model, components=comps)
            if lik == "ztnb":
                kw.update(mask=jnp.asarray(sim["mask"]), offset=jnp.asarray(sim["offset"]))
            if lik == "lognormal":
                kw.update(mask=jnp.asarray(sim["mask"]))
            key = M.centring_key(lik_model, kw.get("mask"))
            info = initialize_model(jax.random.PRNGKey(3), M.vc_model, model_kwargs=kw)
            z = info.param_info.z
            g = jax.grad(info.potential_fn)(z)
            tag = f"{lik}|{name}"
            meta[tag] = dict(world_sha=hashlib.sha256(np.asarray(sim["y"]).tobytes()).hexdigest(),
                             design_sha=hashlib.sha256(np.asarray(fdi["cls"]).tobytes()
                                                       + np.asarray(fdi["dk"]).tobytes()).hexdigest(),
                             components=list(comps), centring=M.CENTRING[key], sites=sorted(z),
                             potential=float(info.potential_fn(z)))
            for k, v in g.items():
                arrays[f"{tag}|{k}"] = np.asarray(v)
    np.savez(out, **arrays)
    out.with_suffix(".json").write_text(json.dumps(meta), encoding="utf-8")


def main() -> None:
    if sys.argv[1] == "--dump":
        dump(Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4:] or LIKS)
        return
    a, b = Path(sys.argv[1]), Path(sys.argv[2])
    liks = sys.argv[3:] or LIKS
    outs = []
    for snap in (a, b):
        o = Path(f"equiv_dump_{snap.name}.npz").resolve()
        subprocess.run([sys.executable, __file__, "--dump", str(snap), str(o), *liks], check=True)
        outs.append(o)
    ma = json.loads(outs[0].with_suffix(".json").read_text(encoding="utf-8"))
    mb = json.loads(outs[1].with_suffix(".json").read_text(encoding="utf-8"))
    ga, gb = np.load(outs[0]), np.load(outs[1])
    res = {}
    for tag in ma:
        x, y = ma[tag], mb.get(tag)
        if y is None:
            res[tag] = dict(identical=False, reason="missing in B")
            continue
        grads = [k for k in ga.files if k.startswith(tag + "|")]
        checks = dict(world=x["world_sha"] == y["world_sha"], design=x["design_sha"] == y["design_sha"],
                      components=x["components"] == y["components"], centring=x["centring"] == y["centring"],
                      sites=x["sites"] == y["sites"], potential=x["potential"] == y["potential"],
                      gradient=all(k in gb.files and np.array_equal(ga[k], gb[k]) for k in grads))
        res[tag] = dict(identical=all(checks.values()), **checks)
    print(json.dumps(dict(schema="V79_SNAPSHOT_EQUIVALENCE_V2", a=a.name, b=b.name, likelihoods=list(liks),
                          worlds_checked=len(res), all_identical=all(v["identical"] for v in res.values()),
                          per_world=res), indent=1))


if __name__ == "__main__":
    main()
