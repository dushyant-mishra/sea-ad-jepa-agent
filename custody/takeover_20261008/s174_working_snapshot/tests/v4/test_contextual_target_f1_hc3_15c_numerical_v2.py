from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[2]


def load(relative: str, name: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ill_conditioned_fixture():
    rng = np.random.default_rng(15002)
    n, p = 104, 16
    q, _ = np.linalg.qr(rng.normal(size=(n, p)))
    v, _ = np.linalg.qr(rng.normal(size=(p, p)))
    singular = np.geomspace(1.0, 1.0 / 5_871_549.064470025, p)
    x = q @ np.diag(singular) @ v.T
    x[:, 0] = 1.0
    x[:, 1:] -= x[:, 1:].mean(axis=0)
    y = 0.31 + rng.normal(0.0, 0.04, n)
    return x, y


def test_qr_and_independent_svd_agree_under_frozen_tolerances():
    qr = load("scripts/v4/contextual_target_f1_hc3_stable_qr_v2.py", "qr_v2")
    svd = load("scripts/v4/validate_contextual_target_f1_hc3_svd_v2.py", "svd_v2")
    x, y = ill_conditioned_fixture()
    a = qr.hc3_intercept_qr(y, x, expected_rank=16, expected_df=88)
    b = svd.hc3_intercept_svd(y, x, expected_rank=16, expected_df=88)
    tol = 100 * np.finfo(np.float64).eps * np.linalg.cond(x) * max(1.0, np.max(np.abs(y)))
    assert a["estimable"] is b["estimable"] is True
    assert a["gate"] is b["gate"]
    assert np.max(np.abs(np.asarray(a["leverage"]) - np.asarray(b["leverage"]))) <= 2.3092638912203256e-12
    for key in ("beta0", "se", "lower", "upper"):
        assert abs(a[key] - b[key]) <= tol


@pytest.mark.parametrize("kind", ["nonfinite", "rank", "df", "zero_se"])
def test_stable_qr_fails_closed(kind):
    qr = load("scripts/v4/contextual_target_f1_hc3_stable_qr_v2.py", f"qr_{kind}")
    x, y = ill_conditioned_fixture()
    expected_rank, expected_df = 16, 88
    if kind == "nonfinite":
        y[0] = np.nan
    elif kind == "rank":
        x[:, -1] = x[:, -2]
    elif kind == "df":
        expected_df = 87
    else:
        y[:] = 0.25
    result = qr.hc3_intercept_qr(y, x, expected_rank=expected_rank, expected_df=expected_df)
    assert result["estimable"] is False
    assert result["gate"] is False


def test_additive_replacement_changes_only_hc3_report_and_gate():
    adapter = load("scripts/v4/contextual_target_f1_hc3_15c_adapter_v2.py", "adapter_v2")
    x, y = ill_conditioned_fixture()
    legacy = {
        "qualified": False,
        "gates": {"legal_provenance": True, "hc3_nuisance_positive": False, "other": True},
        "reports": {"nuisance": {"legacy": True}, "other": {"kept": True}},
        "claim_scope": "frozen",
    }
    repaired = adapter.replace_hc3_only(legacy, y, x, expected_rank=16, expected_df=88)
    assert repaired["gates"]["legal_provenance"] is True
    assert repaired["gates"]["other"] is True
    assert repaired["reports"]["other"] == {"kept": True}
    assert repaired["reports"]["nuisance"].get("legacy") is None
    assert list(repaired["gates"]).count("hc3_nuisance_positive") == 1
    assert repaired["qualified"] is all(repaired["gates"].values())


def test_constant_shift_moves_lower_without_changing_standard_error():
    qr = load("scripts/v4/contextual_target_f1_hc3_stable_qr_v2.py", "qr_shift")
    x, y = ill_conditioned_fixture()
    base = qr.hc3_intercept_qr(y, x, expected_rank=16, expected_df=88)
    shifted = qr.hc3_intercept_qr(y + 0.125, x, expected_rank=16, expected_df=88)
    assert abs(shifted["se"] - base["se"]) <= 1e-12
    assert abs((shifted["lower"] - base["lower"]) - 0.125) <= 1e-12


def test_independent_validator_does_not_import_production_qr():
    text = (ROOT / "scripts/v4/validate_contextual_target_f1_hc3_svd_v2.py").read_text(encoding="utf-8")
    assert "contextual_target_f1_hc3_stable_qr_v2" not in text
    assert "np.linalg.qr" not in text


def test_production_qr_has_no_normal_equations_or_fallback():
    text = (ROOT / "scripts/v4/contextual_target_f1_hc3_stable_qr_v2.py").read_text(encoding="utf-8")
    forbidden = (".T @ x", ".T@x", "np.linalg.inv", "np.linalg.pinv", "ridge")
    assert not any(token in text for token in forbidden)


def canonical_authority_root():
    root = Path("D:/Jepa project")
    if not (root / "outputs/contextual_teacher_target_v1_f1_hc3_nuisance_design_freeze_20260902").is_dir():
        pytest.skip("local frozen authority is not installed")
    return root


def test_frozen_effective_design_binding_is_exact():
    adapter = load("scripts/v4/contextual_target_f1_hc3_15c_adapter_v2.py", "adapter_binding")
    schema, raw, effective = adapter.load_frozen_effective_design(canonical_authority_root())
    assert schema["selected_triple"] == [5, 0, 4]
    assert raw.shape == effective.shape == (104, 16)
    assert adapter.array_sha256(effective) == "37653ed4a21f513a7389630bffa7447f9022323e8240bb80f53394138f1917eb"


def test_full_synthetic_wrapper_preserves_non_hc3_gates():
    adapter = load("scripts/v4/contextual_target_f1_hc3_15c_adapter_v2.py", "adapter_full")
    authority = canonical_authority_root()
    baseline = __import__("json").loads(
        (authority / "outputs/contextual_teacher_target_v1_f1_hc3_15c_decision_integration_20260902/F1_15C_SYNTHETIC_BASELINE.json").read_text()
    )
    repaired = adapter.qualify_synthetic(baseline["payload"], authority_root=authority, repo_root=ROOT)
    for key, value in baseline["decision"]["gates"].items():
        if key != "hc3_nuisance_positive":
            assert repaired["gates"][key] is value
    assert repaired["qualified"] is True
    assert repaired["real_reader_forward_authority"] is None


def test_candidate_design_mutations_are_rejected():
    adapter = load("scripts/v4/contextual_target_f1_hc3_15c_adapter_v2.py", "adapter_mutation")
    authority = canonical_authority_root()
    directory = authority / "outputs/contextual_teacher_target_v1_f1_hc3_nuisance_design_freeze_20260902"
    schema = (directory / "F1_HC3_SELECTED_DONOR_DESIGN_SCHEMA.json").read_bytes()
    design = bytearray((directory / "F1_HC3_SELECTED_DONOR_DESIGN_F64LE.bin").read_bytes())
    adapter.verify_candidate_selected_design(schema, bytes(design))
    design[17] ^= 1
    with pytest.raises(ValueError, match="SELECTED_DESIGN_MISMATCH"):
        adapter.verify_candidate_selected_design(schema, bytes(design))


def test_synthetic_runner_emits_required_conclusion_artifacts():
    import shutil
    import tempfile

    runner = load("scripts/v4/run_contextual_target_f1_hc3_15c_numerical_v2.py", "runner_v2")
    scratch_root = ROOT / ".tmp"
    scratch_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="f1_15c_runner_", dir=scratch_root) as temporary:
        output = Path(temporary)
        freeze = ROOT / "outputs/contextual_teacher_target_v1_f1_hc3_15c_numerical_robustness_repair_20260902"
        for name in (
            "F1_HC3_15C_NUMERICAL_ROBUSTNESS_REPAIR_CONTRACT.md",
            "F1_HC3_15C_NUMERICAL_TOLERANCE_AUTHORITY.json",
            "F1_HC3_15C_PREIMPLEMENTATION_FREEZE.json",
        ):
            shutil.copy2(freeze / name, output / name)
        runner.run(output, authority_root=canonical_authority_root(), repo_root=ROOT)
        required = {
            "F1_HC3_15C_EFFECTIVE_DESIGN_BINDING.json",
            "F1_HC3_15C_NEAR_BOUNDARY_FIXTURE_BINDING.json",
            "F1_HC3_15C_STABLE_QR_RESULTS.json",
            "F1_HC3_15C_INDEPENDENT_SVD_VALIDATION.json",
            "F1_HC3_15C_NUMERICAL_COMPARISON.json",
            "F1_HC3_15C_ADVERSARIAL_REGRESSION.json",
            "F1_HC3_15C_REPAIR_FIREWALL_AUDIT.json",
        }
        assert required <= {path.name for path in output.iterdir()}
        comparison = __import__("json").loads((output / "F1_HC3_15C_NUMERICAL_COMPARISON.json").read_text())
        assert comparison["status"] == "PASS_F1_HC3_15C_NUMERICAL_COMPARISON"
        assert comparison["near_boundary"]["positive"]["qr_gate"] is True
        assert comparison["near_boundary"]["negative"]["qr_gate"] is False
