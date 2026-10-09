"""Tests for the control sensitivity ledger, including its own meta-control.

The ledger exists to prove other controls can fail. So it must itself be shown
to fail: `test_ledger_detects_a_vacuous_control` plants a control that never
fires and requires the ledger to name it VACUOUS_DID_NOT_FIRE. Without that
test the ledger would be exactly the thing it was built to catch.

The real gradient-gate legs run against the actual V5 harness, not a mock.
"""

from __future__ import annotations

import pytest
import torch

from sea_ad_jepa.v4.teacher_student_runtime import sample_uniform_target_blocks
from sea_ad_jepa.v5.inactive_update_reference import (
    build_reference_modules, run_inactive_reference_update)
from sea_ad_jepa.v5.control_sensitivity_ledger_v1 import (
    ControlSensitivityLedger, DegenerateConfiguration, LegResult, run_leg,
    classify, require_distinct_arms, require_comparator_capacity,
    require_effect_resolvable,
    FIRED, QUIET, REFUSED_DEGENERATE,
    SENSITIVE, VACUOUS_DID_NOT_FIRE, FALSE_POSITIVE_ON_HEALTHY,
    SCORED_A_DEGENERATE_CONFIG, INCOMPLETE_LEGS)


# --------------------------------------------------------------------------
# meta-controls: the ledger must itself be falsifiable
# --------------------------------------------------------------------------
def test_ledger_detects_a_vacuous_control():
    """THE load-bearing test: a control that never fires must be NAMED."""
    healthy = run_leg(lambda: False, "healthy")
    planted = run_leg(lambda: False, "planted")          # should have fired
    degen = run_leg(lambda: (_ for _ in ()).throw(
        DegenerateConfiguration("x")), "degenerate")
    assert classify(healthy, planted, degen) == VACUOUS_DID_NOT_FIRE


def test_ledger_detects_a_false_positive_control():
    healthy = run_leg(lambda: True, "healthy")           # fired when it should not
    planted = run_leg(lambda: True, "planted")
    degen = run_leg(lambda: (_ for _ in ()).throw(
        DegenerateConfiguration("x")), "degenerate")
    assert classify(healthy, planted, degen) == FALSE_POSITIVE_ON_HEALTHY


def test_ledger_detects_scoring_of_a_degenerate_configuration():
    """Stage73's defect: identical arms produced a clean-looking number."""
    healthy = run_leg(lambda: False, "healthy")
    planted = run_leg(lambda: True, "planted")
    degen = run_leg(lambda: False, "degenerate")         # scored instead of refusing
    assert classify(healthy, planted, degen) == SCORED_A_DEGENERATE_CONFIG


def test_missing_degenerate_leg_is_not_a_pass():
    healthy = run_leg(lambda: False, "healthy")
    planted = run_leg(lambda: True, "planted")
    assert classify(healthy, planted, None) == INCOMPLETE_LEGS


def test_fully_sensitive_control_is_recognised():
    healthy = run_leg(lambda: False, "healthy")
    planted = run_leg(lambda: True, "planted")
    degen = run_leg(lambda: (_ for _ in ()).throw(
        DegenerateConfiguration("identical arms")), "degenerate")
    assert classify(healthy, planted, degen) == SENSITIVE


def test_empty_ledger_refuses_to_summarise():
    with pytest.raises(ValueError):
        ControlSensitivityLedger().summary()


def test_duplicate_control_id_rejected():
    led = ControlSensitivityLedger()
    good = dict(healthy=run_leg(lambda: False, "healthy"),
                planted=run_leg(lambda: True, "planted"),
                degenerate=run_leg(lambda: (_ for _ in ()).throw(
                    DegenerateConfiguration("d")), "degenerate"),
                source="t")
    led.record("c1", **good)
    with pytest.raises(ValueError):
        led.record("c1", **good)


# --------------------------------------------------------------------------
# degeneracy detectors, each anchored to the real defect it encodes
# --------------------------------------------------------------------------
def test_identical_arms_refused_stage73_defect():
    """Stage73: context / gene-label-permuted / target-shuffled were identical."""
    arm = [0.3236108129998988] * 8
    with pytest.raises(DegenerateConfiguration, match="byte-identical"):
        require_distinct_arms(arm, list(arm), label="stage73")


def test_same_object_arms_refused():
    arm = [1.0, 2.0]
    with pytest.raises(DegenerateConfiguration, match="same object"):
        require_distinct_arms(arm, arm, label="x")


def test_genuinely_distinct_arms_are_scoreable():
    require_distinct_arms([0.3236108129998988], [0.3322895616077756], label="stage73r")


def test_under_capacity_comparator_refused_lane_a_defect():
    with pytest.raises(DegenerateConfiguration, match="capacity"):
        require_comparator_capacity(4, 32, label="global_context_only")


def test_matched_capacity_comparator_is_scoreable():
    require_comparator_capacity(32, 32, label="exchange_query")


def test_interval_spanning_zero_refuses_a_direction_claim():
    """Stage73R: delta -0.008366, CI [-0.019597, +0.000169] includes zero."""
    with pytest.raises(DegenerateConfiguration, match="includes zero"):
        require_effect_resolvable(-0.01959704363673176, 0.00016928217069961393,
                                  label="context_vs_target_shuffled")


def test_interval_excluding_zero_is_resolvable():
    """Stage73R context vs no_graph: [0.001367, 0.022093] excludes zero."""
    require_effect_resolvable(0.0013672167662245327, 0.022092538220107316,
                              label="context_vs_no_graph")


# --------------------------------------------------------------------------
# the real gradient gate, exercised against the actual harness
# --------------------------------------------------------------------------
def _case():
    torch.manual_seed(707)
    n, vocab = 6, 32
    ops = [0, 1, 0, 1, 1, 0]
    op0 = torch.tensor([0, 1, 3, 5, 7, 9, 12, 15, 18, 21, 25, 29])
    op1 = torch.tensor([0, 1, 2, 3, 4, 5, 7, 8, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31])
    measured = torch.zeros((n, vocab), dtype=torch.bool)
    for row, op in enumerate(ops):
        measured[row, op0 if op == 0 else op1] = True
    expr = torch.randn(n, vocab)
    expr[~measured] = 0
    cells = torch.tensor([70_001, 70_002, 70_003, 70_004, 70_005, 70_006], dtype=torch.int64)
    w = torch.tensor([.4, 2.0, 1.1, .7, 3.2, .6], dtype=torch.float32)
    views = [sample_uniform_target_blocks(
        measured, production_seed=8813003, cell_indices=cells, sample_pass=0,
        view_index=v, mask_fraction=.40, block_count=4) for v in range(2)]
    return dict(expression=expr, measurement_mask=measured, stable_cell_keys=cells,
                operator_ids=ops, scientific_cell_weights=w, target_block_views=views,
                measured_tokens_by_operator={0: len(op0), 1: len(op1)},
                max_teacher_tokens_per_microbatch=40, run_seed=8113002,
                update_index=0, ema_momentum=.99)


def _modules():
    return build_reference_modules(
        vocabulary_size=32, width=16, heads=4, blocks=1, ffn_width=24, dropout=.10,
        learning_rate=3e-4, betas=(.9, .999), eps=1e-8, weight_decay=.01,
        init_seed=8113002)


def _gate_fires(damage: str | None) -> bool:
    """True iff the harness REFUSES the update. Real harness, not a mock."""
    mods, kw = _modules(), _case()
    handle = None
    if damage == "zero":
        p = next(x for x in mods.online.parameters() if x.requires_grad)
        handle = p.register_hook(lambda g: torch.zeros_like(g))
    elif damage == "nonfinite":
        p = next(x for x in mods.online.parameters() if x.requires_grad)
        handle = p.register_hook(lambda g: g * float("nan"))
    elif damage == "teacher":
        tp = next(iter(mods.teacher.parameters()))
        tp.grad = torch.zeros_like(tp)
    try:
        run_inactive_reference_update(mods, **kw)
        return False
    except RuntimeError:
        return True
    finally:
        if handle is not None:
            handle.remove()


@pytest.mark.parametrize("damage", ["zero", "nonfinite", "teacher"])
def test_gradient_gate_is_sensitive_on_the_real_harness(damage):
    led = ControlSensitivityLedger()
    verdict = led.record(
        f"inline_gradient_gate::{damage}",
        healthy=run_leg(lambda: _gate_fires(None), "healthy"),
        planted=run_leg(lambda: _gate_fires(damage), "planted"),
        degenerate=run_leg(
            lambda: require_comparator_capacity(0, 1, label="no-parameter model"),
            "degenerate"),
        source="src/sea_ad_jepa/v5/inactive_update_reference.py::_gradient_report",
        notes="counters are literals on the healthy path; firing behaviour is the real evidence")
    assert verdict == SENSITIVE, led.entries


def test_ledger_summary_is_digest_bound_and_non_authorizing():
    led = ControlSensitivityLedger()
    led.record("c",
               healthy=run_leg(lambda: False, "healthy"),
               planted=run_leg(lambda: True, "planted"),
               degenerate=run_leg(lambda: (_ for _ in ()).throw(
                   DegenerateConfiguration("d")), "degenerate"),
               source="t")
    s = led.summary()
    assert s["all_sensitive"] is True
    assert s["training_authorized"] is False
    assert len(s["ledger_digest"]) == 64
