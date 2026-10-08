"""Adversarial tests for the repaired mandatory gradient gate.

The historical gate detected missing and nonfinite gradients but permitted an
exact-zero one, which is why the T1 defect ran 205 updates unnoticed. These tests
attack the repaired gate directly, and the final one replays the preserved K0
historical condition from its own artifact bytes.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.v4.c2_mandatory_gradient_gate_v1 import (
    STATUS_EXACT_ZERO,
    STATUS_LIVE,
    STATUS_MISSING,
    STATUS_NONFINITE,
    classify_norm,
    gate_from_norms,
    gate_module,
    mandatory_names,
)

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "outputs" / "c2_t1_gradient_forensic_20260906" / "v3_exact_path"


def test_exact_zero_gradient_is_rejected() -> None:
    """The defect the historical gate permitted."""
    report = gate_from_norms({"blocks.0.attention.query.weight": 0.0})
    assert not report["passed"]
    assert report["statuses"]["blocks.0.attention.query.weight"] == STATUS_EXACT_ZERO
    assert report["terminal"] == "STOP_MANDATORY_GRADIENT_GATE_REJECTED"


def test_tiny_finite_nonzero_gradient_is_not_confused_with_zero() -> None:
    """No magnitude floor: real but small training signal must survive."""
    for tiny in (1e-30, 5.96e-8, 1e-12, 4.9e-324):
        report = gate_from_norms({"blocks.0.attention.key.bias": tiny})
        assert report["passed"], tiny
        assert report["statuses"]["blocks.0.attention.key.bias"] == STATUS_LIVE


def test_missing_and_nonfinite_still_fail() -> None:
    assert classify_norm(None) == STATUS_MISSING
    assert classify_norm(float("nan")) == STATUS_NONFINITE
    assert classify_norm(float("inf")) == STATUS_NONFINITE
    assert classify_norm(float("-inf")) == STATUS_NONFINITE
    report = gate_from_norms({"a": None, "b": float("nan"), "c": float("inf"), "d": 1.0})
    assert not report["passed"]
    assert report["rejected_names"] == ["a", "b", "c"]
    assert report["counts"][STATUS_LIVE] == 1


def test_one_dead_tensor_is_not_hidden_by_many_live_ones() -> None:
    """The pooling failure that let a mean report health over 48 dead tensors."""
    norms = {"live_%02d" % index: 1e6 for index in range(47)}
    norms["blocks.5.attention.value.weight"] = 0.0
    report = gate_from_norms(norms)
    assert not report["passed"]
    assert report["rejected_names"] == ["blocks.5.attention.value.weight"]
    assert report["rejected_count"] == 1


def test_all_live_passes() -> None:
    report = gate_from_norms({"a": 1.0, "b": 1e-9})
    assert report["passed"]
    assert report["terminal"] == "PASS_MANDATORY_GRADIENT_GATE"


def test_gate_module_reads_live_parameters() -> None:
    torch = pytest.importorskip("torch")

    class Block(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.attention_norm = torch.nn.LayerNorm(2)
            self.attention = torch.nn.ModuleDict({"query": torch.nn.Linear(2, 2)})

    class Model(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.blocks = torch.nn.ModuleList([Block()])

    model = Model()
    names = mandatory_names(model)
    assert set(names) == {
        "blocks.0.attention_norm.weight",
        "blocks.0.attention_norm.bias",
        "blocks.0.attention.query.weight",
        "blocks.0.attention.query.bias",
    }

    # No gradients yet: every protected tensor is MISSING.
    assert gate_module(model)["counts"][STATUS_MISSING] == 4

    params = dict(model.named_parameters())
    for param in params.values():
        param.grad = torch.ones_like(param)
    assert gate_module(model)["passed"]

    # A single exact-zero gradient must reject the whole step.
    params["blocks.0.attention.query.weight"].grad = torch.zeros(2, 2)
    report = gate_module(model)
    assert not report["passed"]
    assert report["rejected_names"] == ["blocks.0.attention.query.weight"]


def _load(name: str) -> dict:
    path = ARTIFACTS / name
    if not path.is_file():
        pytest.skip("preserved C2 artifact not present: " + name)
    return json.loads(path.read_text(encoding="utf-8"))


def test_repaired_gate_catches_the_preserved_k0_historical_condition() -> None:
    """Replay the historical defect from its own preserved bytes."""
    record = _load("C2_V3_K0_HISTORICAL.json")
    entries = record["updates"][0]["mandatory_gradients_post_unscale"]["entries"]
    report = gate_from_norms({name: value["norm"] for name, value in entries.items()})
    assert not report["passed"], "repaired gate must reject the historical condition"
    assert report["rejected_count"] == 48
    assert report["counts"][STATUS_EXACT_ZERO] == 48
    assert report["counts"][STATUS_LIVE] == 0


def test_repaired_gate_passes_the_preserved_k1_corrected_condition() -> None:
    record = _load("C2_V3_K1_BACKWARD_AUTOCAST_DISABLED.json")
    entries = record["updates"][0]["mandatory_gradients_post_unscale"]["entries"]
    report = gate_from_norms({name: value["norm"] for name, value in entries.items()})
    assert report["passed"], "repaired gate must accept the corrected condition"
    assert report["counts"][STATUS_LIVE] == 48


def test_historical_gate_blind_spot_is_real_not_assumed() -> None:
    """The historical gate counted only missing and nonfinite, so K0 passed it."""
    record = _load("C2_V3_K0_HISTORICAL.json")
    entries = record["updates"][0]["mandatory_gradients_post_unscale"]["entries"]
    missing = sum(1 for v in entries.values() if v["status"] == "MISSING")
    nonfinite = sum(1 for v in entries.values() if v["status"] == "NONFINITE")
    zero = sum(1 for v in entries.values() if v["status"] == "ZERO")
    assert missing == 0 and nonfinite == 0, "historical gate saw nothing to reject"
    assert zero == 48, "yet every mandatory tensor was exactly zero"


def test_live_tensor_with_subnormal_element_is_not_called_dead() -> None:
    """A norm squares, so a lone subnormal underflows to a zero norm.

    This is the defect independent verification found: at fp32 the smallest
    subnormal 1.4e-45 squares to 2e-90 and vanishes, so a norm-based test
    reported 48 genuinely nonzero tensors as exact zero and would have rejected
    real training signal. `gate_module` must test emptiness exactly.
    """
    torch = pytest.importorskip("torch")
    from scripts.v4.c2_mandatory_gradient_gate_v1 import classify_tensor, gate_module

    for dtype in (torch.float32, torch.float16):
        subnormal = torch.nextafter(
            torch.tensor(0.0, dtype=dtype), torch.tensor(1.0, dtype=dtype)
        )
        grad = torch.zeros(8, 8, dtype=dtype)
        grad.view(-1)[0] = subnormal
        if dtype is torch.float32:
            # The premise holds for fp32, where the square genuinely underflows.
            # For fp16 torch accumulates the norm in fp32, so it does not.
            assert float(grad.norm()) == 0.0, "premise: the norm underflows to zero"
        assert classify_tensor(grad) == STATUS_LIVE, dtype
        assert classify_tensor(torch.zeros(8, 8, dtype=dtype)) == STATUS_EXACT_ZERO

    class Tiny(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.blocks = torch.nn.ModuleList([torch.nn.Module()])
            self.blocks[0].attention_norm = torch.nn.LayerNorm(4)

    model = Tiny()
    names = ["blocks.0.attention_norm.weight", "blocks.0.attention_norm.bias"]
    params = dict(model.named_parameters())
    for name in names:
        grad = torch.zeros_like(params[name])
        grad.view(-1)[0] = torch.nextafter(
            torch.tensor(0.0), torch.tensor(1.0)
        )
        params[name].grad = grad
    assert gate_module(model, names)["passed"]


def test_nonfinite_is_detected_even_when_other_elements_are_finite() -> None:
    torch = pytest.importorskip("torch")
    from scripts.v4.c2_mandatory_gradient_gate_v1 import classify_tensor

    grad = torch.ones(4, 4)
    grad[2, 2] = float("nan")
    assert classify_tensor(grad) == STATUS_NONFINITE
    grad[2, 2] = float("inf")
    assert classify_tensor(grad) == STATUS_NONFINITE
    assert classify_tensor(None) == STATUS_MISSING


def test_frozen_registry_is_exactly_the_48_expected_identities() -> None:
    """Dynamic discovery alone must not define completeness."""
    from scripts.v4.c2_mandatory_gradient_gate_v1 import (
        EXPECTED_MANDATORY_COUNT, FROZEN_MANDATORY_REGISTRY)

    assert len(FROZEN_MANDATORY_REGISTRY) == EXPECTED_MANDATORY_COUNT == 48
    assert len(set(FROZEN_MANDATORY_REGISTRY)) == 48
    by_role: dict[str, int] = {}
    for name in FROZEN_MANDATORY_REGISTRY:
        role = "attention_norm" if "attention_norm" in name \
            else name.split("attention.")[1].rsplit(".", 1)[0]
        by_role[role] = by_role.get(role, 0) + 1
    assert by_role == {"attention_norm": 12, "query": 12, "key": 12, "value": 12}


def test_registry_validation_catches_a_shrunken_or_renamed_protected_set() -> None:
    torch = pytest.importorskip("torch")
    from scripts.v4.c2_mandatory_gradient_gate_v1 import (
        enforce_registry, validate_registry)

    import sys
    src = str(ROOT / "src")          # the package lives under src/, not the repo root
    if src not in sys.path:
        sys.path.insert(0, src)
    try:
        from sea_ad_jepa.v4.ipb_jepa import IPBEncoder
    except Exception:  # noqa: BLE001
        pytest.skip("production encoder not importable here")

    encoder = IPBEncoder(vocabulary_size=64, width=160, heads=4, blocks=6)
    report = validate_registry(encoder)
    assert report["passed"], report
    assert report["discovered_count"] == 48
    assert report["by_role"] == {
        "attention_norm": 12, "attention.query": 12,
        "attention.key": 12, "attention.value": 12}

    # A model with fewer blocks must be rejected, not silently under-protected.
    shrunken = IPBEncoder(vocabulary_size=64, width=160, heads=4, blocks=5)
    shrunken_report = validate_registry(shrunken)
    assert not shrunken_report["passed"]
    assert shrunken_report["discovered_count"] == 40
    assert len(shrunken_report["missing"]) == 8
    with pytest.raises(RuntimeError):
        enforce_registry(shrunken)
