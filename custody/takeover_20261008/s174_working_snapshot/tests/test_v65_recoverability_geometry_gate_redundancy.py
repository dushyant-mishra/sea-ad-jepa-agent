from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def _load():
    p=ROOT/"scripts/v64/audit_recoverability_geometry_gate_redundancy_v1.py"
    spec=importlib.util.spec_from_file_location("v65_geom_audit",p)
    assert spec and spec.loader
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_canonical_correlations_equal_principal_angle_cosines():
    out=_load().run_audit()
    assert out["redundancy_confirmed"] is True
    assert out["max_abs_difference"] < 1e-10
    assert out["real_biology_used"] is False
    assert out["execution_authorized"] is False


def test_relational_geometry_is_distinct_and_pairing_sensitive():
    out=_load().run_audit()
    assert -1 <= out["relational_geometry_correlation"] <= 1
    assert -1 <= out["permuted_relational_geometry_correlation"] <= 1
    assert out["relational_geometry_correlation"] > out["permuted_relational_geometry_correlation"]
