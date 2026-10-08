#!/usr/bin/env python3
"""Corrective variants of the historical `run_update`, derived from its own source.

The variants are produced by textual substitution on `inspect.getsource` of the
canonical function and executed in the canonical module's namespace. Nothing is
retyped, so every line except the substituted one is byte-identical to the
historical implementation and no transcription error is possible.

Modes:

`historical`
    The canonical function, unmodified.

`backward_autocast_disabled`
    Wraps only the `.backward()` call in `torch.autocast(enabled=False)`.
    Forward/backward interleaving, view order, teacher reuse, masks, scaler,
    loss division, checkpointing and RNG progression are all untouched, so
    ambient autocast state during backward is genuinely the only changed factor.
    This is the correction that passed independent verification.

`production_safe`
    SUPERSEDED_DO_NOT_RUN. Accumulates every scaled loss and drains the
    backwards after the autocast block, holding 64 live graphs at 128/8, which
    exhausts memory. Never executed. The minimal `backward_autocast_disabled`
    correction has already passed the exact real geometry and independent
    verification and is the preferred repair.

`successor`
    The adopted training path: the `backward_autocast_disabled` correction plus
    mandatory gradient-gate and frozen-registry enforcement, inserted after
    `scaler.unscale_(optimizer)` and before `scaler.step(optimizer)`.

`gated_historical`
    Negative control for the adoption regression: the gate in the same position
    but with the historical backward left inside autocast. Must STOP before the
    optimizer steps.
"""

from __future__ import annotations

import inspect
from typing import Any, Callable

BACKWARD_CALL = "scaler.scale(scaled_loss).backward()"
UNSCALE_ANCHOR = "    scaler.unscale_(optimizer)"

# Enforced after unscale and before the optimizer step. Earlier would read
# scaled gradients; later would let a dead step land before the check.
GATE_LINES = (
    "    _mandatory_gate.enforce_registry(online)",
    "    _mandatory_gate.enforce(online)",
)

GATED_MODES = ("successor", "gated_historical")


def _indent_of(line: str) -> str:
    return line[: len(line) - len(line.lstrip())]


def _source_and_line(canonical: Callable[..., Any]) -> tuple[str, str]:
    source = inspect.getsource(canonical)
    matches = [line for line in source.splitlines() if BACKWARD_CALL in line]
    if len(matches) != 1:
        raise RuntimeError(
            "expected exactly one backward call in run_update, found %d" % len(matches)
        )
    return source, matches[0]


def _autocast_disabled_replacement(indent: str) -> str:
    return "\n".join(
        (
            indent + "with torch.autocast(device_type=device.type, enabled=False):",
            indent + "    " + BACKWARD_CALL,
        )
    )


def _install(phase_e: Any, variant: str, name: str, mode: str) -> Callable[..., Any]:
    namespace = phase_e.__dict__
    if mode in GATED_MODES:
        from scripts.v4 import c2_mandatory_gradient_gate_v1 as gate_module

        namespace["_mandatory_gate"] = gate_module
    exec(compile(variant, "<c2_corrective_" + mode + ">", "exec"), namespace)
    built = namespace[name]
    built.__c2_variant_source__ = variant
    return built


def build_variant(phase_e: Any, mode: str) -> Callable[..., Any]:
    """Return a variant of `phase_e.run_update` differing in one declared way."""
    canonical = phase_e.run_update
    source, backward_line = _source_and_line(canonical)
    indent = _indent_of(backward_line)

    if mode == "historical":
        return canonical

    if mode in GATED_MODES:
        if source.count(UNSCALE_ANCHOR) != 1:
            raise RuntimeError("could not locate the unscale anchor")
        variant = source.replace(
            UNSCALE_ANCHOR, "\n".join((UNSCALE_ANCHOR,) + GATE_LINES), 1
        )
        if mode == "successor":
            variant = variant.replace(
                backward_line, _autocast_disabled_replacement(indent)
            )
        name = "run_update_" + mode
        variant = variant.replace("def run_update(", "def " + name + "(", 1)
        return _install(phase_e, variant, name, mode)

    if mode == "backward_autocast_disabled":
        replacement = _autocast_disabled_replacement(indent)
        name = "run_update_backward_autocast_disabled"
    elif mode == "production_safe":
        # Defer the backward until the autocast region has been left, but keep
        # one backward per view in the original order rather than accumulating
        # four graphs and backwarding them together.
        replacement = indent + "_deferred_backwards.append(scaled_loss)"
        name = "run_update_production_safe"
    else:
        raise ValueError("unknown corrective mode: " + mode)

    variant = source.replace(backward_line, replacement)
    variant = variant.replace("def run_update(", "def " + name + "(", 1)

    if mode == "production_safe":
        anchor = "    optimizer.zero_grad(set_to_none=True)"
        if variant.count(anchor) != 1:
            raise RuntimeError("could not locate zero_grad anchor")
        variant = variant.replace(
            anchor, anchor + "\n    _deferred_backwards: list = []", 1
        )
        if variant.count(UNSCALE_ANCHOR) != 1:
            raise RuntimeError("could not locate unscale anchor")
        variant = variant.replace(
            UNSCALE_ANCHOR,
            "    for _deferred in _deferred_backwards:\n"
            "        scaler.scale(_deferred).backward()\n" + UNSCALE_ANCHOR,
            1,
        )

    return _install(phase_e, variant, name, mode)


def variant_diff(phase_e: Any, mode: str) -> str:
    """The exact textual difference from canonical, for the artifact record."""
    if mode == "historical":
        return "(no change)"
    import difflib

    canonical = inspect.getsource(phase_e.run_update).splitlines()
    built = build_variant(phase_e, mode).__c2_variant_source__.splitlines()
    return "\n".join(
        line for line in difflib.unified_diff(
            canonical, built, "canonical_run_update", "variant_" + mode, lineterm="", n=2
        )
    )
