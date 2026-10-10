"""The planted-truth simulator scores truth on the model's own decomposition: re-expressed effects rebuild the
same linear predictor, class and source sum to zero over levels, operator and donor sum to zero within each
source, donor-class within each class, and fractions sum to one. Pure numpy, no real data."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))
import v79_simulate as SIM  # noqa: E402


def toy_design(seed=0):
    rng = np.random.default_rng(seed)
    n_src, ops_per_src, donors_per_src, n_cls = 3, 4, 6, 3
    rows = []
    for s in range(n_src):
        for o in range(ops_per_src):
            for d in range(donors_per_src):
                for _ in range(rng.integers(2, 5)):
                    rows.append((s, s * ops_per_src + o, s * donors_per_src + d, int(rng.integers(n_cls))))
    src, op, donor, cls = (np.array(c) for c in zip(*rows))
    keys = sorted(set(zip(donor.tolist(), cls.tolist())))
    lut = {k: i for i, k in enumerate(keys)}
    dk = np.array([lut[(a, b)] for a, b in zip(donor.tolist(), cls.tolist())])
    lib = rng.normal(0, 0.3, len(src))
    return dict(n=len(src), cls=cls, src=src, op=op, donor=donor, dk=dk, n_cls=n_cls, n_src=n_src,
                n_op=n_src * ops_per_src, n_donor=n_src * donors_per_src, n_dk=len(keys),
                log_lib_centered=lib - lib.mean())


@pytest.mark.parametrize("likelihood", ["gaussian", "bernoulli"])
def test_reexpressed_effects_rebuild_the_same_predictor(likelihood):
    d = toy_design()
    sim = SIM.simulate(d, SIM.SCENARIOS["S1_present"], 5, likelihood, seed=3, return_parts=True)
    rebuilt = sim["mu"][None] + sim["b"][None] * d["log_lib_centered"][:, None]
    for x in SIM.COMPONENTS:
        rebuilt = rebuilt + sim["model_eff"][x][d[x]]
    # the level means removed from cls and src belong to the intercept: compare up to a per-gene constant
    diff = sim["eta"] - rebuilt
    assert np.allclose(diff - diff.mean(0, keepdims=True), 0.0, atol=1e-10)


def test_constraints_match_the_model_parameterization():
    d = toy_design(1)
    eff = SIM.simulate(d, SIM.SCENARIOS["S1_present"], 4, "gaussian", seed=5, return_parts=True)["model_eff"]
    assert np.allclose(eff["cls"].mean(0), 0) and np.allclose(eff["src"].mean(0), 0)
    for child, par in (("op", "src"), ("donor", "src"), ("dk", "cls")):
        par_of = np.zeros(eff[child].shape[0], dtype=int)
        par_of[d[child]] = d[par]
        for p in np.unique(par_of):
            assert np.allclose(eff[child][par_of == p].mean(0), 0.0, atol=1e-12)


def test_fractions_sum_to_one_and_absent_components_are_zero_where_they_must_be():
    d = toy_design(2)
    sim = SIM.simulate(d, SIM.SCENARIOS["S4_operator_only_no_class"], 6, "gaussian", seed=9)
    total = sum(sim["truth_frac"].values())
    assert np.allclose(total, 1.0)
    for x in ("donor", "dk", "cls"):
        assert np.allclose(sim["truth_var"][x], 0.0)
    assert np.all(sim["truth_var"]["op"] > 0)
