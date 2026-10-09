from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "v77" / "run_v78_signed_detection_marginal_tournament.py"
E2_RECEIPT = ROOT / "results" / "v77" / "V77_CLASS_PROPAGATION_TOURNAMENT_V1.json"


def _load_runner():
    assert RUNNER.exists(), "missing V78 runner required by frozen implementation plan"
    spec = importlib.util.spec_from_file_location("v78_tournament", RUNNER)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def test_f0_f1_surface_is_frozen_and_e4_fails_closed():
    R = _load_runner()
    assert R.ARMS == ("F0", "F1", "F2", "F3")
    assert R.DEFAULT_SEED == 7302
    assert R.DEFAULT_MEASUREMENT_SEED == 7302
    assert R.CLASS_PROGRAM_SCALE == 0.55
    assert R.arm_config("F0")["background"] == "v1"
    assert R.arm_config("F1")["background"] == "v2"
    for key in ("truth_arm", "class_scale", "seed", "measurement_seed"):
        assert R.arm_config("F0")[key] == R.arm_config("F1")[key]
    with pytest.raises(PermissionError):
        R.validate_arm("E4")


def test_f0_binds_exact_committed_e2_reference():
    R = _load_runner()
    rec = R.load_e2_reference(E2_RECEIPT)
    assert rec["seed"] == 7302
    assert rec["cells"] == 2500
    assert rec["class_authority_sha256"] == "a4f5e325a54014d87d6380f81ce48922a6558f05ffafdaf7c59c1dc3ae705014"
    assert rec["evaluation_universe"]["sha256"] == "e950e967dd593b253837017f8bda5c5a683d975074728f4b8fe20c27272b9763"
    assert R.extract_e2_score(rec) == rec["results"]["E2"]["score"]


def test_f0_reference_missing_or_mismatched_fails_closed(tmp_path):
    R = _load_runner()
    with pytest.raises(FileNotFoundError):
        R.load_e2_reference(tmp_path / "missing.json")
    bad = json.loads(E2_RECEIPT.read_text())
    bad["seed"] = 7303
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(bad))
    with pytest.raises(RuntimeError):
        R.load_e2_reference(p)


def test_f1_inherits_background_v2_constants():
    R = _load_runner()
    cfg = R.background_v2_contract()
    assert cfg == {
        "broad": {"n": 8, "frac": 0.62, "scale": 0.85},
        "mid": {"n": 40, "frac": 0.12, "scale": 0.55},
        "narrow": {"n": 220, "frac": 0.012, "scale": 0.45},
        "paralog": {"group_frac": 0.22, "group_size": 6, "jitter": 0.12, "scale": 0.70},
    }


def test_2k_operator_support_is_preserved():
    R = _load_runner()
    rec = R.operator_support_2k()
    assert rec["n_cells"] == 2000
    assert rec["n_operators"] == 42
    assert rec["operators_present"] == 42
    assert rec["minimum_operator_count"] >= 1
