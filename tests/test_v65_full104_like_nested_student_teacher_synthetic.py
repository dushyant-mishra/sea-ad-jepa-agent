from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/v64/full104_like_nested_student_teacher_synthetic_integration_v1.py"

def _load():
    spec=importlib.util.spec_from_file_location("smoke",SCRIPT)
    assert spec and spec.loader
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def test_full104_like_nested_integration_passes():
    out=_load().run_smoke()
    assert out["pass"] is True
    assert out["governance"]["real_data_used"] is False

def test_rna_recovers_shared_but_not_private():
    m=_load().run_smoke()["metrics"]
    assert m["rna_shared_r2"]>m["technical_shared_r2"]+0.15
    assert m["rna_private_r2"]<0.10

def test_multimodal_adds_private_information():
    m=_load().run_smoke()["metrics"]
    assert m["multimodal_private_r2"]>0.60
    assert m["multimodal_shared_r2"]>=m["rna_shared_r2"]-0.03

def test_fixture_matches_project_scale_structure_not_cell_count():
    f=_load().run_smoke()["fixture"]
    assert f["donors"]==104
    assert f["operators"]==42
    assert f["sources"]==3
    assert f["train_donors"]+f["validation_donors"]+f["test_donors"]==104
