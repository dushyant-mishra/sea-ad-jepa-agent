from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def _load():
    p=ROOT/"scripts/v64/privileged_recoverability_shortcut_smoke_v1.py"
    spec=importlib.util.spec_from_file_location("v64_shortcut_smoke",p)
    assert spec and spec.loader
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_shortcut_smoke_distinguishes_predictability_from_baseline_advantage():
    out=_load().run_smoke()
    assert out["pass"] is True
    assert out["biology_factor"]["rna_r2"]>0.90
    assert out["biology_factor"]["technical_baseline_r2"]<0.05
    assert out["technical_shortcut_factor"]["rna_r2"]>0.90
    assert out["technical_shortcut_factor"]["technical_baseline_r2"]>0.90
    assert abs(out["technical_shortcut_factor"]["rna_advantage"])<0.02
    assert out["training_authorized"] is False


def test_shortcut_smoke_replays_exactly():
    m=_load()
    assert m.run_smoke()==m.run_smoke()


def test_contract_requires_locked_teacher_factor_and_shortcut_baselines():
    t=(ROOT/"docs/agent/V64_RECOVERABILITY_SHORTCUT_AND_TEACHER_IMMUTABILITY_CONTRACT_20260930.md").read_text()
    assert "High RNA predictability is necessary but not sufficient" in t
    assert "Teacher/factor immutability" in t
    assert "rotating the factor on TEST" in t
    assert "technical descriptors only" in t
    assert "recoverability may become tautological" in t
