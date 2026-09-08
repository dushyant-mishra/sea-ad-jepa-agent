"""Per-tensor movement adjudication for the healthy-teacher qualification.

The frozen healthy-teacher base explicitly forbids promoting the prototype's
arbitrary 2x-decay margin.  This adjudicator instead constructs the exact
decoupled-weight-decay counterfactual in parameter dtype by replaying AdamW's
multiplicative decay operation for the proved number of optimizer steps.

A zero-baseline tensor passes only with finite nonzero absolute movement.  A
nonzero-baseline tensor passes only when its per-tensor absolute movement is
strictly greater than the exact repeated AdamW decay-only movement.  This is the
literal frozen-base "exceed decay-only behavior" rule without the prototype's
arbitrary 2x multiplier.  No pooled statistic can rescue a failed tensor.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping, Sequence

import torch


def source_sha256() -> str:
    """SHA-256 of the exact adjudicator source bytes currently executing."""
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def decay_only_counterfactual(
    baseline: torch.Tensor,
    *,
    learning_rate: float,
    weight_decay: float,
    valid_steps: int,
) -> torch.Tensor:
    if valid_steps < 0:
        raise ValueError("valid_steps must be non-negative")
    if learning_rate < 0.0 or weight_decay < 0.0:
        raise ValueError("learning_rate and weight_decay must be non-negative")
    if not bool(torch.isfinite(baseline).all()):
        raise RuntimeError("nonfinite baseline tensor")
    out = baseline.detach().clone()
    factor = 1.0 - float(learning_rate) * float(weight_decay)
    if not 0.0 <= factor <= 1.0:
        raise ValueError("invalid AdamW decay factor")
    with torch.no_grad():
        for _ in range(int(valid_steps)):
            out.mul_(factor)
    return out


def adjudicate_tensor(
    baseline: torch.Tensor,
    observed: torch.Tensor,
    *,
    learning_rate: float,
    weight_decay: float,
    valid_steps: int,
) -> dict[str, Any]:
    if baseline.shape != observed.shape or baseline.dtype != observed.dtype:
        raise RuntimeError("baseline/observed tensor structure mismatch")
    if not bool(torch.isfinite(observed).all()):
        return {
            "passed": False,
            "status": "NONFINITE_OBSERVED",
            "absolute_movement": float("nan"),
            "decay_residual_norm": float("nan"),
        }
    expected = decay_only_counterfactual(
        baseline,
        learning_rate=learning_rate,
        weight_decay=weight_decay,
        valid_steps=valid_steps,
    )
    residual = observed.detach() - expected
    absolute = observed.detach() - baseline.detach()
    zero_baseline = not bool((baseline.detach() != 0).any())
    # Norms are accumulated in float64 so the comparison itself does not
    # manufacture a small-gradient floor through fp16/fp32 squaring underflow.
    absolute_norm = float(absolute.double().norm())
    decay_only_norm = float((expected - baseline.detach()).double().norm())
    residual_norm = float(residual.double().norm())
    if zero_baseline:
        passed = absolute_norm > 0.0
        status = "ZERO_BASELINE_MOVED" if passed else "ZERO_BASELINE_UNMOVED"
    else:
        passed = absolute_norm > decay_only_norm
        status = "EXCEEDS_DECAY_ONLY" if passed else "NOT_ABOVE_DECAY_ONLY"
    return {
        "passed": passed,
        "status": status,
        "baseline_norm": float(baseline.detach().double().norm()),
        "absolute_movement": absolute_norm,
        "decay_only_movement": decay_only_norm,
        "decay_residual_norm": residual_norm,
        "zero_baseline": zero_baseline,
        "valid_steps": int(valid_steps),
    }


def adjudicate_module(
    module: torch.nn.Module,
    baseline: Mapping[str, torch.Tensor],
    *,
    names: Sequence[str],
    learning_rate: float,
    weight_decay: float,
    valid_steps: int,
) -> dict[str, Any]:
    current = dict(module.named_parameters())
    missing = sorted((set(names) - set(current)) | (set(names) - set(baseline)))
    if missing:
        raise RuntimeError("movement registry missing tensors: " + ", ".join(missing[:8]))
    rows: dict[str, dict[str, Any]] = {}
    failed: list[str] = []
    for name in names:
        row = adjudicate_tensor(
            baseline[name],
            current[name].detach(),
            learning_rate=learning_rate,
            weight_decay=weight_decay,
            valid_steps=valid_steps,
        )
        rows[name] = row
        if not row["passed"]:
            failed.append(name)
    return {
        "schema": "teacher-student-movement-v1",
        "rows": rows,
        "failed": failed,
        "passed": not failed,
        "terminal": (
            "PASS_PER_TENSOR_MOVEMENT_EXCEEDS_DECAY"
            if not failed
            else "STOP_PER_TENSOR_MOVEMENT_NOT_ABOVE_DECAY"
        ),
        "criterion": "zero baseline: absolute movement > 0; nonzero baseline: absolute movement norm > exact repeated AdamW decay-only movement norm",
        "pooled_rescue_allowed": False,
        "arbitrary_magnitude_multiplier": None,
    }


def enforce_module_movement(*args: Any, **kwargs: Any) -> dict[str, Any]:
    report = adjudicate_module(*args, **kwargs)
    if not report["passed"]:
        raise RuntimeError(
            "per-tensor movement gate rejected: " + ", ".join(report["failed"][:8])
        )
    return report
