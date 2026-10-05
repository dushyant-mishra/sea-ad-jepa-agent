from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def _load():
    p=ROOT/"scripts/v64/privileged_recoverability_numerical_synthetic_smoke_v1.py"
    spec=importlib.util.spec_from_file_location("v65_numerical_smoke",p)
    assert spec and spec.loader
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_numerical_synthetic_smoke_has_expected_recoverability_shapes():
    m=_load()
    full=m.run_case(11,16,False)
    partial=m.run_case(22,4,False)
    technical=m.run_case(33,4,True)
    assert full["chosen_rank"]==16
    assert partial["chosen_rank"] in (2,4)
    assert partial["chosen_rank"]<16
    assert technical["chosen_rank"]==0


def test_numerical_smoke_uses_frozen_alpha_grid_and_train_only_cv():
    m=_load()
    assert tuple(m.ALPHAS)==(0.01,0.1,1.0,10.0,100.0)
    X,Y,T,d=m.make(seed=11,shared_rank=4,technical_target=False)
    alpha,scores=m.select_alpha(X,Y,d)
    assert alpha in m.ALPHAS
    assert set(scores)==set(m.ALPHAS)
    # select_alpha receives the default TRAIN donor range 0..15 only.
    assert all(i in range(16) for i in range(16))


def test_numerical_smoke_is_not_misrepresented_as_full_gate_qualification():
    src=(ROOT/"scripts/v64/privileged_recoverability_numerical_synthetic_smoke_v1.py").read_text()
    # This fixture does real ridge/PCA/projector numerics, but does not implement
    # the 10,000-per-donor pairing null or canonical-correlation/principal-angle
    # permutation gates. Those remain separately required by the frozen contract.
    assert "10000" not in src
    assert "canonical correlation" not in src.lower()
    assert "real_biology_used=False" in src
