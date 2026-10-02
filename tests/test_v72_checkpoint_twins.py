import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/v64/build_v72_checkpoint_twins.py"


def load():
    spec = importlib.util.spec_from_file_location("v72_checkpoints", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fixture(tmp_path):
    root = tmp_path / "checkpoint_challenge"
    load().build(root, seed=7212, n=360)
    return root


def test_checkpoint_twins_cover_required_cases(tmp_path):
    root = fixture(tmp_path)
    results = load().audit(root)
    assert set(results) == {
        "HEALTHY",
        "COLLAPSED",
        "SOURCE_SHORTCUT",
        "DONOR_SHORTCUT",
        "PRIVATE_STATE_LEAK",
        "OVERCONFIDENT_UNRECOVERABLE",
        "CORRUPT_MANIFEST_AXIS",
    }


def test_collapsed_checkpoint_is_behaviorally_collapsed(tmp_path):
    results = load().audit(fixture(tmp_path))
    assert results["COLLAPSED"]["status"] == "AUDITED"
    assert results["COLLAPSED"]["variance"] < 1e-10


def test_source_shortcut_exposes_source_signal(tmp_path):
    results = load().audit(fixture(tmp_path))
    assert results["SOURCE_SHORTCUT"]["source_corr_max"] > 0.95


def test_donor_shortcut_exposes_donor_signal(tmp_path):
    results = load().audit(fixture(tmp_path))
    assert results["DONOR_SHORTCUT"]["donor_corr_max"] > 0.95


def test_private_state_leak_exposes_private_signal(tmp_path):
    results = load().audit(fixture(tmp_path))
    assert results["PRIVATE_STATE_LEAK"]["private_corr_max"] > 0.95


def test_overconfident_unrecoverable_case_has_near_zero_uncertainty(tmp_path):
    results = load().audit(fixture(tmp_path))
    assert results["OVERCONFIDENT_UNRECOVERABLE"]["mean_uncertainty"] < 1e-4
    assert results["OVERCONFIDENT_UNRECOVERABLE"]["private_corr_max"] > 0.1


def test_corrupt_checkpoint_fails_manifest_or_axis(tmp_path):
    results = load().audit(fixture(tmp_path))
    assert results["CORRUPT_MANIFEST_AXIS"]["status"] == "FAIL__MANIFEST_OR_AXIS"


def test_healthy_is_not_collapsed_and_does_not_directly_encode_source(tmp_path):
    results = load().audit(fixture(tmp_path))
    h = results["HEALTHY"]
    assert h["variance"] > 0.1
    assert h["source_corr_max"] < 0.5
