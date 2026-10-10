import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "v77"))
sys.path.insert(0, str(ROOT / "scripts" / "v79"))


def test_evaluation_universe_loader_authenticates_actual_bytes(monkeypatch, tmp_path):
    import run_v79_detection_localization as D

    seen = {}
    expected = np.array([1, 3, 5], dtype=np.int64)

    def fake_load(path, expected_sha, expected_name):
        seen["path"] = Path(path)
        seen["sha"] = expected_sha
        seen["name"] = expected_name
        return expected.copy()

    monkeypatch.setattr(D.V77, "load_universe", fake_load)
    got = D.load_evaluation_universe(tmp_path / "frozen_evaluation_universe.npz")

    assert np.array_equal(got, expected)
    assert seen["sha"] == D.V78.EXPECTED_EVALUATION_UNIVERSE_SHA256
    assert seen["name"] == D.V77.CORRECTED_UNIVERSE_NAME


def test_evaluation_universe_loader_propagates_hash_failure(monkeypatch, tmp_path):
    import run_v79_detection_localization as D

    def reject(*args, **kwargs):
        raise RuntimeError("evaluation universe sha256 mismatch")

    monkeypatch.setattr(D.V77, "load_universe", reject)
    with pytest.raises(RuntimeError, match="sha256 mismatch"):
        D.load_evaluation_universe(tmp_path / "wrong.npz")
