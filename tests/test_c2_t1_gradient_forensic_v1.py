"""CPU tests for the C2 gradient forensic instrumentation and adjudicator.

These prove the measuring instrument before it is pointed at any real condition:
a dead tensor must be detectable, a pooled statistic must not hide one, and the
adjudicator must refuse to conclude unless exactly one factor explains both
directions.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

from scripts.v4.run_c2_t1_gradient_forensic_v1 import (  # noqa: E402
    adjudicate,
    build_conditions,
    gradient_snapshot,
    live_reference_registry,
    make_blocks,
    mandatory_tensor_registry,
    moment_snapshot,
    movement_snapshot,
    role_of,
)
from sea_ad_jepa.v4.ipb_jepa import IPBEncoder  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads(
    (ROOT / "configs" / "v4" / "c2_t1_gradient_forensic_v1.json").read_text(encoding="utf-8")
)


@pytest.fixture(scope="module")
def encoder() -> IPBEncoder:
    return IPBEncoder(vocabulary_size=64, dropout=0.0)


def test_registry_has_exactly_the_48_contracted_tensors(encoder: IPBEncoder) -> None:
    registry = mandatory_tensor_registry(encoder)
    assert len(registry) == CONFIG["expected_mandatory_tensors"] == 48
    by_role: dict[str, int] = {}
    for item in registry:
        by_role[item["role"]] = by_role.get(item["role"], 0) + 1
    # Six blocks, each contributing weight and bias for four mandatory roles.
    assert by_role == {
        "attention_norm": 12,
        "attention.query": 12,
        "attention.key": 12,
        "attention.value": 12,
    }
    assert all(item["requires_grad"] for item in registry)


def test_live_reference_registry_is_attention_output_only(encoder: IPBEncoder) -> None:
    live = live_reference_registry(encoder)
    assert len(live) == CONFIG["expected_live_reference_tensors"] == 12
    assert {item["role"] for item in live} == {"attention.output"}
    mandatory_names = {item["name"] for item in mandatory_tensor_registry(encoder)}
    assert mandatory_names.isdisjoint({item["name"] for item in live})


def test_role_of_does_not_confuse_ffn_or_final_norm(encoder: IPBEncoder) -> None:
    names = [name for name, _ in encoder.named_parameters()]
    assert role_of("blocks.0.ffn_norm.weight") is None
    assert role_of("final_norm.weight") is None
    assert role_of("blocks.3.attention.query.weight") == "attention.query"
    # ffn_norm must never be counted as attention_norm.
    assert any("ffn_norm" in name for name in names)
    assert all(role_of(name) is None for name in names if "ffn_norm" in name)


class _Tiny(torch.nn.Module):
    """Analytic stand-in with one parameter per mechanical state."""

    def __init__(self) -> None:
        super().__init__()
        self.blocks = torch.nn.ModuleDict(
            {
                "0": torch.nn.ModuleDict(
                    {"attention": torch.nn.ModuleDict({"query": torch.nn.Linear(2, 2)})}
                )
            }
        )


def _tiny_registry() -> tuple[_Tiny, list[dict[str, object]]]:
    model = _Tiny()
    registry = [
        {"name": "blocks.0.attention.query.weight", "role": "attention.query"},
        {"name": "blocks.0.attention.query.bias", "role": "attention.query"},
    ]
    return model, registry


def test_gradient_snapshot_separates_missing_zero_nonfinite_and_live() -> None:
    model, registry = _tiny_registry()
    params = dict(model.named_parameters())

    snapshot = gradient_snapshot(model, registry)
    assert snapshot["dead_count"] == 2
    assert {e["status"] for e in snapshot["entries"].values()} == {"MISSING"}

    params["blocks.0.attention.query.weight"].grad = torch.zeros(2, 2)
    params["blocks.0.attention.query.bias"].grad = torch.tensor([float("nan"), 1.0])
    snapshot = gradient_snapshot(model, registry)
    assert snapshot["entries"]["blocks.0.attention.query.weight"]["status"] == "ZERO"
    assert snapshot["entries"]["blocks.0.attention.query.bias"]["status"] == "NONFINITE"
    assert snapshot["dead_count"] == 2

    params["blocks.0.attention.query.weight"].grad = torch.ones(2, 2)
    params["blocks.0.attention.query.bias"].grad = torch.ones(2)
    snapshot = gradient_snapshot(model, registry)
    assert snapshot["dead_count"] == 0
    assert snapshot["dead_names"] == []


def test_one_dead_tensor_is_not_hidden_by_a_live_neighbour() -> None:
    """The pooling failure that let a mean report health over 48 dead tensors."""
    model, registry = _tiny_registry()
    params = dict(model.named_parameters())
    params["blocks.0.attention.query.weight"].grad = torch.ones(2, 2) * 1e6
    params["blocks.0.attention.query.bias"].grad = torch.zeros(2)
    snapshot = gradient_snapshot(model, registry)
    assert snapshot["dead_count"] == 1
    assert snapshot["dead_names"] == ["blocks.0.attention.query.bias"]


def test_moment_snapshot_requires_both_moments_independently() -> None:
    model, registry = _tiny_registry()
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=0.01)
    params = dict(model.named_parameters())
    for param in params.values():
        param.grad = torch.zeros_like(param)
    optimizer.step()
    snapshot = moment_snapshot(optimizer, model, registry)
    assert snapshot["zero_first_moment"] == 2
    assert snapshot["zero_second_moment"] == 2

    # A nonzero first moment must not conceal a zero second moment.
    state = optimizer.state[params["blocks.0.attention.query.weight"]]
    state["exp_avg"] = torch.ones_like(state["exp_avg"])
    snapshot = moment_snapshot(optimizer, model, registry)
    assert snapshot["zero_first_moment"] == 1
    assert snapshot["zero_second_moment"] == 2


def test_movement_snapshot_reports_per_tensor_and_flags_zero_baseline() -> None:
    model, registry = _tiny_registry()
    params = dict(model.named_parameters())
    with torch.no_grad():
        params["blocks.0.attention.query.weight"].fill_(1.0)
        params["blocks.0.attention.query.bias"].zero_()
    before = {item["name"]: params[item["name"]].detach().float().clone() for item in registry}
    with torch.no_grad():
        params["blocks.0.attention.query.weight"].mul_(1.5)
    snapshot = movement_snapshot(before, model, registry, 1e-4, 0.01, 205)
    weight = snapshot["entries"]["blocks.0.attention.query.weight"]
    bias = snapshot["entries"]["blocks.0.attention.query.bias"]
    assert weight["relative_movement"] == pytest.approx(0.5)
    assert bias["zero_baseline"] is True
    assert bias["relative_movement"] is None
    assert snapshot["decay_only_prediction"] == pytest.approx(2.049791e-04, rel=1e-4)


def test_make_blocks_keeps_one_visible_gene_and_fills_members() -> None:
    generator = torch.Generator().manual_seed(7)
    measurement = torch.ones(3, 64, dtype=torch.bool)
    for mode in ("random40", "measured_complement"):
        blocks = make_blocks(measurement, mode, generator, n_blocks=4, block_size=8)
        assert not blocks.hidden_mask[:, 0].any()
        assert blocks.indices.shape == (3, 4, 8)
        assert blocks.member_mask.all()


def test_build_conditions_expands_every_frozen_factor() -> None:
    conditions = build_conditions(CONFIG)
    expected = (
        set(CONFIG["endpoints"])
        | {f["id"] for f in CONFIG["frozen_factor_order"]}
        | {r["id"] for r in CONFIG["reverse_sufficiency_order"]}
    )
    assert set(conditions) == expected
    # Each forward variant differs from the historical endpoint in exactly one key.
    historical = CONFIG["endpoints"]["HISTORICAL_SCALE"]
    for factor in CONFIG["frozen_factor_order"]:
        differing = {
            key for key in historical if conditions[factor["id"]][key] != historical[key]
        }
        assert differing == set(factor["override"]), factor["id"]


def _result(dead: int, live_ref_dead: int = 0) -> dict[str, object]:
    return {
        "mandatory": {"pre_unscale": {"dead_count": dead, "total": 48}},
        "live_reference": {"pre_unscale": {"dead_count": live_ref_dead}},
    }


def _base_results() -> dict[str, object]:
    return {"HEALTHY_SIMPLIFIED": _result(0), "HISTORICAL_SCALE": _result(48)}


def test_adjudicator_stops_when_an_endpoint_is_not_reproduced() -> None:
    results = _base_results()
    results["HISTORICAL_SCALE"] = _result(12)
    assert adjudicate(CONFIG, results)["terminal"].startswith(
        "STOP_C2_HISTORICAL_ENDPOINT_NOT_REPRODUCED"
    )
    results = _base_results()
    results["HEALTHY_SIMPLIFIED"] = _result(3)
    assert adjudicate(CONFIG, results)["terminal"].startswith(
        "STOP_C2_HEALTHY_ENDPOINT_NOT_REPRODUCED"
    )


def test_adjudicator_stops_when_the_live_reference_is_also_dead() -> None:
    results = _base_results()
    results["HISTORICAL_SCALE"] = _result(48, live_ref_dead=12)
    assert adjudicate(CONFIG, results)["terminal"] == "STOP_C2_LIVE_REFERENCE_NOT_LIVE_AT_HISTORICAL"


def test_adjudicator_refuses_when_no_single_factor_rescues() -> None:
    results = _base_results()
    for factor in CONFIG["frozen_factor_order"]:
        results[factor["id"]] = _result(48)
    verdict = adjudicate(CONFIG, results)
    assert verdict["terminal"] == "STOP_C2_CAUSE_NOT_LOCALIZED_NO_SINGLE_FACTOR_RESCUES"


def test_adjudicator_refuses_when_two_factors_rescue() -> None:
    results = _base_results()
    for index, factor in enumerate(CONFIG["frozen_factor_order"]):
        results[factor["id"]] = _result(0 if index < 2 else 48)
    for factor in CONFIG["reverse_sufficiency_order"]:
        results[factor["id"]] = _result(0)
    verdict = adjudicate(CONFIG, results)
    assert verdict["terminal"] == "STOP_C2_CAUSE_NOT_LOCALIZED"
    assert len(verdict["necessary_and_sufficient_rescuers"]) == 2


def test_adjudicator_localizes_only_on_a_unique_two_way_transition() -> None:
    results = _base_results()
    for index, factor in enumerate(CONFIG["frozen_factor_order"]):
        results[factor["id"]] = _result(0 if index == 0 else 48)
    for index, factor in enumerate(CONFIG["reverse_sufficiency_order"]):
        results[factor["id"]] = _result(48 if index == 0 else 0)
    verdict = adjudicate(CONFIG, results)
    assert verdict["terminal"] == "C2_GRADIENT_SEVERING_CONDITION_LOCALIZED"
    assert verdict["necessary_and_sufficient_rescuers"] == ["F1_LOSS_OPERANDS_FP32"]
    assert verdict["sufficient_inducers"] == ["R1_LOSS_OPERANDS_FP16"]


def test_adjudicator_will_not_localize_on_rescue_without_induction() -> None:
    """A factor that rescues but whose inverse does not induce is not the cause."""
    results = _base_results()
    for index, factor in enumerate(CONFIG["frozen_factor_order"]):
        results[factor["id"]] = _result(0 if index == 0 else 48)
    for factor in CONFIG["reverse_sufficiency_order"]:
        results[factor["id"]] = _result(0)
    assert adjudicate(CONFIG, results)["terminal"] == "STOP_C2_CAUSE_NOT_LOCALIZED"
