from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/v64/nested_rna_multimodal_student_synthetic_smoke_v1.py"


def _load():
    spec=importlib.util.spec_from_file_location("mm",SCRIPT)
    assert spec and spec.loader
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def test_nested_multimodal_synthetic_smoke_passes():
    out=_load().run_smoke()
    assert out["real_biology_used"] is False
    assert out["training_authorized"] is False
    assert out["pass"] is True


def test_multimodal_recovers_private_while_rna_does_not():
    out=_load().run_smoke()
    m=out["metrics"]
    assert m["multimodal_private_r2"]>0.95
    assert m["rna_private_r2"]<0.05


def test_shared_geometry_is_rotation_invariant():
    out=_load().run_smoke()
    m=out["metrics"]
    assert abs(
        m["rotated_multimodal_shared_geometry_corr"]-
        m["unrotated_multimodal_shared_geometry_corr"]
    )<1e-12


def test_missing_private_state_is_masked_not_observed_zero():
    out=_load().run_smoke()
    assert out["missing_private_is_nan"] is True
