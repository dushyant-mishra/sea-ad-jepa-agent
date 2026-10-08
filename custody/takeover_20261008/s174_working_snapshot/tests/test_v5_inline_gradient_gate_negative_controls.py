"""Negative controls proving the V5 gradient gate actually stops an update.

WHY THIS EXISTS
    PR #147 reported "protected gradient gate 40/40 affirmative", derived from
    the `gradient_gate` counters in each update report. That statistic is
    VACUOUS. `_gradient_report` raises when any of `missing`, `nonfinite`,
    `exact_zero` or `teacher_gradients` is non-empty, and only reaches its
    `return` on the healthy path — where it returns those four fields as
    hard-coded literal zeros:

        if missing or nonfinite or exact_zero or teacher_grads:
            raise RuntimeError(...)
        return {'missing':0,'nonfinite':0,'exact_zero':0,'teacher_gradients':0, ...}

    So asserting those counters are zero asserts that a function which can only
    return zeros returned zeros. It cannot fail, and a check that cannot fail is
    not evidence.

WHAT IS ACTUALLY EVIDENCE
    (a) that the gate raises on each damaged condition, BEFORE the optimizer
        steps and before the teacher EMA advances -- proved here;
    (b) that 40 consecutive updates completed without raising -- proved by the
        historical run; and
    (c) `max_abs_gradient`, which is a measurement rather than a literal.

Each test damages exactly one thing and asserts the update is refused AND that
no state advanced. The positive control must pass, otherwise the refusals could
be firing for an unrelated reason.
"""

from __future__ import annotations

import copy

import pytest
import torch

from sea_ad_jepa.v4.teacher_student_runtime import sample_uniform_target_blocks
from sea_ad_jepa.v5.inactive_update_reference import (
    build_reference_modules,
    run_inactive_reference_update,
)


def _case():
    torch.manual_seed(707)
    n, vocab = 6, 32
    ops = [0, 1, 0, 1, 1, 0]
    op0 = torch.tensor([0, 1, 3, 5, 7, 9, 12, 15, 18, 21, 25, 29])
    op1 = torch.tensor([0, 1, 2, 3, 4, 5, 7, 8, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31])
    measured = torch.zeros((n, vocab), dtype=torch.bool)
    for row, op in enumerate(ops):
        measured[row, op0 if op == 0 else op1] = True
    expression = torch.randn(n, vocab)
    expression[~measured] = 0
    cells = torch.tensor([70_001, 70_002, 70_003, 70_004, 70_005, 70_006], dtype=torch.int64)
    weights = torch.tensor([.4, 2.0, 1.1, .7, 3.2, .6], dtype=torch.float32)
    views = [sample_uniform_target_blocks(
        measured, production_seed=8813003, cell_indices=cells, sample_pass=0,
        view_index=v, mask_fraction=.40, block_count=4) for v in range(2)]
    return (expression, measured, cells, ops, weights, views,
            {0: len(op0), 1: len(op1)})


def _modules():
    return build_reference_modules(
        vocabulary_size=32, width=16, heads=4, blocks=1, ffn_width=24,
        dropout=.10, learning_rate=3e-4, betas=(.9, .999), eps=1e-8,
        weight_decay=.01, init_seed=8113002)


def _kwargs(data):
    return dict(expression=data[0], measurement_mask=data[1],
                stable_cell_keys=data[2], operator_ids=data[3],
                scientific_cell_weights=data[4], target_block_views=data[5],
                measured_tokens_by_operator=data[6],
                max_teacher_tokens_per_microbatch=40, run_seed=8113002,
                update_index=0, ema_momentum=.99)


def _step(modules):
    """Optimizer step scalar, or 0 before any step."""
    st = modules.optimizer.state_dict()["state"]
    if not st:
        return 0
    return int(next(iter(st.values()))["step"])


def _teacher_snapshot(modules):
    return {k: v.detach().clone() for k, v in modules.teacher.state_dict().items()}


def _teacher_unchanged(modules, snap):
    cur = modules.teacher.state_dict()
    return all(torch.equal(cur[k], v) for k, v in snap.items())


def test_positive_control_healthy_update_is_accepted():
    """Without this, every refusal below could be firing for an unrelated reason."""
    data, modules = _case(), _modules()
    before = _step(modules)
    report = run_inactive_reference_update(modules, **_kwargs(data))
    assert report["optimizer_step_after"] == before + 1
    assert report["gradient_gate"]["max_abs_gradient"] > 0.0


def test_gradient_gate_counters_are_literals_not_measurements():
    """Documents WHY the 40/40 counter statistic was vacuous.

    On the healthy path the four counters are hard-coded zeros, so they carry no
    information. Only `max_abs_gradient` varies. This test exists so the claim in
    the PR #147 correction is checkable rather than asserted.
    """
    data, modules = _case(), _modules()
    gate = run_inactive_reference_update(modules, **_kwargs(data))["gradient_gate"]
    assert gate["missing"] == 0 and gate["nonfinite"] == 0
    assert gate["exact_zero"] == 0 and gate["teacher_gradients"] == 0
    # the only field that is a measurement
    assert isinstance(gate["max_abs_gradient"], float) and gate["max_abs_gradient"] > 0.0


@pytest.mark.parametrize("damage", ["exact_zero", "nonfinite"])
def test_damaged_online_gradient_stops_before_optimizer_and_ema(damage):
    """A dead or non-finite gradient must refuse the update with NOTHING advanced."""
    data, modules = _case(), _modules()
    before_step = _step(modules)
    snap = _teacher_snapshot(modules)

    target = next(p for p in modules.online.parameters() if p.requires_grad)
    if damage == "exact_zero":
        handle = target.register_hook(lambda g: torch.zeros_like(g))
    else:
        handle = target.register_hook(lambda g: g * float("nan"))
    try:
        with pytest.raises(RuntimeError, match="gradient gate failed"):
            run_inactive_reference_update(modules, **_kwargs(data))
    finally:
        handle.remove()

    assert _step(modules) == before_step, "optimizer stepped despite a failed gate"
    assert _teacher_unchanged(modules, snap), "teacher EMA advanced despite a failed gate"


def test_teacher_gradient_presence_stops_the_update():
    """Any gradient on the teacher is a firewall breach and must refuse."""
    data, modules = _case(), _modules()
    before_step = _step(modules)
    snap = _teacher_snapshot(modules)

    tp = next(iter(modules.teacher.parameters()))
    tp.grad = torch.zeros_like(tp)          # planted teacher gradient
    with pytest.raises(RuntimeError, match="gradient gate failed"):
        run_inactive_reference_update(modules, **_kwargs(data))

    assert _step(modules) == before_step
    assert _teacher_unchanged(modules, snap)


def test_refused_update_leaves_optimizer_able_to_run_afterwards():
    """A refusal must be a clean stop, not a corrupted optimizer."""
    data, modules = _case(), _modules()
    target = next(p for p in modules.online.parameters() if p.requires_grad)
    handle = target.register_hook(lambda g: torch.zeros_like(g))
    with pytest.raises(RuntimeError):
        run_inactive_reference_update(modules, **_kwargs(data))
    handle.remove()

    before = _step(modules)
    report = run_inactive_reference_update(modules, **_kwargs(data))
    assert report["optimizer_step_after"] == before + 1
