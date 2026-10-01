from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def _load():
    p=ROOT/"scripts/v64/privileged_recoverability_geometry_gate_v2.py"
    spec=importlib.util.spec_from_file_location("v65_geom_gate",p)
    assert spec and spec.loader
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_permutation_seed_and_sequence_are_deterministic():
    m=_load()
    assert m.DEFAULT_PERMUTATIONS==10_000
    a=m.permutation_seed_uint64("DONOR_X")
    b=m.permutation_seed_uint64("DONOR_X")
    assert a==b
    p1=m.permutation_indices("DONOR_X",12,25)
    p2=m.permutation_indices("DONOR_X",12,25)
    assert np.array_equal(p1,p2)
    assert all(np.array_equal(np.sort(p),np.arange(12)) for p in p1)


def test_strong_shared_geometry_passes_permutation_gate():
    m=_load()
    rng=np.random.default_rng(99)
    z=rng.normal(size=(36,3))
    pred=z + .06*rng.normal(size=z.shape)
    out=m.donor_geometry_gate(z,pred,"SYNTH_D1",n_perm=250)
    assert out["canonical"]["observed"]>out["canonical"]["null_q99_higher"]
    assert out["relational_geometry"]["observed"]>out["relational_geometry"]["null_q99_higher"]
    assert out["pass"] is True


def test_pairing_disruption_removes_geometry_support():
    m=_load()
    rng=np.random.default_rng(101)
    z=rng.normal(size=(36,3))
    pred=z + .05*rng.normal(size=z.shape)
    pred=pred[rng.permutation(len(pred))]
    out=m.donor_geometry_gate(z,pred,"SYNTH_D2",n_perm=250)
    assert out["pass"] is False


def test_observed_must_be_strictly_greater_than_higher_quantile():
    m=_load()
    x=np.array([0.1,0.2,0.3,0.4,0.5])
    assert m._higher_quantile(x,0.8)==0.5
    # equality to the threshold would fail under the contract's strict '>'.
    assert not (0.5 > m._higher_quantile(x,0.8))


def test_rank_deficiency_fails_closed():
    m=_load()
    x=np.arange(30,dtype=float)[:,None]
    z=np.column_stack([x,x])  # rank 1 for requested k=2
    try:
        m.donor_geometry_gate(z,z,"SYNTH_D3",n_perm=20)
    except ValueError as e:
        assert "rank-deficient" in str(e)
    else:
        raise AssertionError("rank-deficient projected state did not fail closed")


def test_canonical_and_principal_angle_alias_redundancy_is_independently_audited():
    audit=(ROOT/"scripts/v64/audit_recoverability_geometry_gate_redundancy_v1.py").read_text()
    assert "same singular values" in audit
    state=__import__("json").loads(
        (ROOT/"results/v64/V65_PRIVILEGED_RECOVERABILITY_DECISION_STATE_V2.json").read_text()
    )
    assert state["geometry_gate"]["G1"]["principal_angle_cosines"]=="REPORTABLE_ALIAS_NOT_INDEPENDENT_GATE"
    assert state["geometry_gate"]["G2"]["metric"].startswith("PEARSON_CORRELATION")
