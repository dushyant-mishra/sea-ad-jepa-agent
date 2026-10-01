from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    path = ROOT / "scripts/v64/privileged_information_architecture_smoke_v1.py"
    spec = importlib.util.spec_from_file_location("v64_privileged_smoke", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_privileged_information_smoke_producer_passes_deterministically():
    mod = _load()
    out = mod.run_smoke()
    assert out["schema"] == "V64_PRIVILEGED_INFORMATION_ARCHITECTURE_SMOKE_V1"
    assert out["status"] == "SYNTHETIC_SOFTWARE_SMOKE_ONLY"
    assert out["pass"] is True
    assert out["training_authorized"] is False
    assert out["main"]["shared_mean_r2"] > 0.98
    assert out["main"]["private_mean_r2"] < 0.05
    assert out["main"]["forced_full_state_mean_r2"] < out["main"]["shared_mean_r2"] - 0.20
    assert out["rotation_aware"]["minimum_principal_angle_cosine"] > 0.99


def test_privileged_information_smoke_is_exactly_replayable():
    mod = _load()
    assert mod.run_smoke() == mod.run_smoke()


def test_mean_multivariate_r2_rejects_misaligned_shapes():
    mod = _load()
    import numpy as np
    a = np.zeros((4, 2))
    b = np.zeros((4, 3))
    try:
        mod.mean_multivariate_r2(a, b)
    except ValueError:
        pass
    else:
        raise AssertionError("misaligned smoke targets must fail closed")
