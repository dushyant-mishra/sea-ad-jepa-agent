from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def _load():
    p=ROOT/"scripts/v64/privileged_recoverability_permutation_geometry_smoke_v1.py"
    spec=importlib.util.spec_from_file_location("v65_geom",p)
    assert spec and spec.loader
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def test_permutation_geometry_synthetic_smoke_passes():
    out=_load().run_smoke()
    assert out["real_biology_used"] is False
    assert out["good"]["pairing_pass"] is True
    assert out["good"]["geometry_pass"] is True
    assert out["broken"]["geometry_pass"] is False
    assert out["deterministic"] is True
    assert out["canonical_equals_principal_angles"] is True
    assert out["pass_"] is True

def test_seed_rule_is_stable_and_donor_specific():
    m=_load()
    assert m.donor_seed("D1")==m.donor_seed("D1")
    assert m.donor_seed("D1")!=m.donor_seed("D2")

def test_contract_uses_relational_geometry_not_duplicate_principal_angle_gate():
    t=(ROOT/"docs/agent/V65_PRIVILEGED_RECOVERABILITY_PRECISION_DECISION_CONTRACT_20260930.md").read_text()
    assert "relational-geometry correlation" in t
    assert "double-count one mathematical quantity" in t
    assert "Principal-angle values may still be reported as a diagnostic" in t
