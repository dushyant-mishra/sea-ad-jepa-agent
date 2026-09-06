#!/usr/bin/env python3
"""Corrective variants of the historical `run_update`, derived from its own source.

The variants are produced by textual substitution on `inspect.getsource` of the
canonical function and executed in the canonical module's namespace. Nothing is
retyped, so every line except the substituted one is byte-identical to the
historical implementation and no transcription error is possible.

Two variants:

`backward_autocast_disabled`
    Wraps only the `.backward()` call in `torch.autocast(enabled=False)`.
    Forward/backward interleaving, view order, teacher reuse, masks, scaler,
    loss division, checkpointing and RNG progression are all untouched, so
    ambient autocast state during backward is genuinely the only changed factor.

`production_safe`
    The structure PyTorch's AMP example recommends: the forward and loss stay
    under autocast, the backward is issued after leaving the region, and
    view-by-view accumulation is preserved rather than collecting four graphs.
"""

from __future__ import annotations

import inspect
from typing import Any, Callable

BACKWARD_CALL = "scaler.scale(scaled_loss).backward()"


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


def build_variant(phase_e: Any, mode: str) -> Callable[..., Any]:
    """Return a variant of `phase_e.run_update` differing in one declared way."""
    canonical = phase_e.run_update
    source, backward_line = _source_and_line(canonical)
    indent = _indent_of(backward_line)

    if mode == "historical":
        return canonical

    if mode == "backward_autocast_disabled":
        replacement = (
            indent + "with torch.autocast(device_type=device.type, enabled=False):\n"
            + indent + "    " + BACKWARD_CALL
        )
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
        # Declare the accumulator before the microbatch loop and drain it after
        # the autocast block closes, immediately before the existing unscale.
        anchor = "    optimizer.zero_grad(set_to_none=True)"
        if variant.count(anchor) != 1:
            raise RuntimeError("could not locate zero_grad anchor")
        variant = variant.replace(
            anchor, anchor + "\n    _deferred_backwards: list = []", 1
        )
        drain_anchor = "    scaler.unscale_(optimizer)"
        if variant.count(drain_anchor) != 1:
            raise RuntimeError("could not locate unscale anchor")
        variant = variant.replace(
            drain_anchor,
            "    for _deferred in _deferred_backwards:\n"
            "        scaler.scale(_deferred).backward()\n"
            + drain_anchor,
            1,
        )

    namespace = phase_e.__dict__
    exec(compile(variant, "<c2_corrective_" + mode + ">", "exec"), namespace)
    built = namespace[name]
    built.__c2_variant_source__ = variant
    return built


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
