from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def _load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    assert spec and spec.loader
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_paired_signal_passes_r2_permutation_gate():
    r2=_load("r2gate","scripts/v64/privileged_recoverability_pairing_r2_gate_v2.py")
    rng=np.random.default_rng(303)
    z=rng.normal(size=(40,3))
    pred=z+.08*rng.normal(size=z.shape)
    out=r2.pairing_r2_gate(z,pred,np.zeros(3),"SYNTH_R2_A",n_perm=250)
    assert out["observed_r2"]>out["null_q99_higher"]
    assert out["pass"] is True


def test_disrupted_pairing_fails_r2_permutation_gate():
    r2=_load("r2gate2","scripts/v64/privileged_recoverability_pairing_r2_gate_v2.py")
    rng=np.random.default_rng(304)
    z=rng.normal(size=(40,3))
    pred=z+.05*rng.normal(size=z.shape)
    pred=pred[rng.permutation(len(pred))]
    out=r2.pairing_r2_gate(z,pred,np.zeros(3),"SYNTH_R2_B",n_perm=250)
    assert out["pass"] is False


def test_r2_and_geometry_reuse_identical_permutation_schedule():
    r2=_load("r2gate3","scripts/v64/privileged_recoverability_pairing_r2_gate_v2.py")
    geom=_load("geomgate3","scripts/v64/privileged_recoverability_geometry_gate_v2.py")
    rng=np.random.default_rng(305)
    z=rng.normal(size=(36,2))
    pred=z+.06*rng.normal(size=z.shape)
    perms=geom.permutation_indices("SYNTH_SHARED_NULL",len(z),200)
    r=r2.pairing_r2_gate(
        z,pred,np.zeros(2),"SYNTH_SHARED_NULL",permutations=perms,n_perm=200
    )
    g=geom.donor_geometry_gate(
        z,pred,"SYNTH_SHARED_NULL",expected_rank=2,permutations=perms,n_perm=200
    )
    assert r["seed_uint64"]==g["seed_uint64"]==geom.permutation_seed_uint64("SYNTH_SHARED_NULL")
    assert r["n_permutations"]==g["n_permutations"]==200
    assert r["pass"] is True and g["pass"] is True


def test_default_real_execution_count_is_10000():
    r2=_load("r2gate4","scripts/v64/privileged_recoverability_pairing_r2_gate_v2.py")
    assert r2.DEFAULT_PERMUTATIONS==10_000
