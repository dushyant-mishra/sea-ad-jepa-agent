"""Per-tensor movement adjudication for the healthy-teacher qualification.

The frozen healthy-teacher base explicitly forbids promoting the prototype's
arbitrary 2x-decay margin.  This adjudicator instead constructs the exact
decoupled-weight-decay counterfactual in parameter dtype by replaying AdamW's
multiplicative decay operation for the proved number of optimizer steps.

A tensor passes only if its observed state is finite and differs elementwise
from that exact decay-only counterfactual.  Thus a pure-decay tensor cannot pass,
zero-baseline tensors require real nonzero movement, and no pooled statistic can
rescue an individually dead tensor.
"""
from __future__ import annotations

import hashlib
from typing import Any, Mapping, Sequence

import torch


def source_sha256() -> str:
    """Stable semantic label helper; package manifests still bind exact source bytes."""
    return hashlib.sha256(b"teacher-student-movement-adjudicator-v1").hexdigest()


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
    differs_from_decay_only = bool((residual != 0).any())
    return {
        "passed": differs_from_decay_only,
        "status": "DEVIATES_FROM_DECAY_ONLY" if differs_from_decay_only else "DECAY_ONLY",
        "baseline_norm": float(baseline.detach().float().norm()),
        "absolute_movement": float(absolute.float().norm()),
        "decay_only_movement": float((expected - baseline.detach()).float().norm()),
        "decay_residual_norm": float(residual.float().norm()),
        "zero_baseline": not bool((baseline.detach() != 0).any()),
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
            "PASS_PER_TENSOR_NON_DECAY_MOVEMENT"
            if not failed
            else "STOP_PER_TENSOR_MOVEMENT_NOT_DISTINGUISHABLE_FROM_DECAY"
        ),
        "criterion": "exact repeated AdamW decay-only counterfactual; elementwise inequality",
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
