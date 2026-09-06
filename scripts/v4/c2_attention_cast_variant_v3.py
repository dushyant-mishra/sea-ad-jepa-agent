#!/usr/bin/env python3
"""The decisive cast-position variant for C2.

`KernelLinearAttention.forward` ends:

    return self.output(output.to(tokens.dtype)), denominator.amin()

so the attention result is cast fp32 to fp16 *before* the output projection.
`self.output` therefore takes its gradient on the fp16 side of the cast, while
every upstream tensor -- the einsums, q/k/v, the q/k/v projections and
`attention_norm` -- must send its gradient back *through* the cast.

The variant changes exactly one thing: it applies the output projection in fp32
and casts to the residual-stream dtype *after* the projection.

    historical:        fp32 attention -> cast to fp16 -> output projection
    after_projection:  fp32 attention -> output projection -> cast to fp16

Nothing else differs. The q/k/v projections still run under the outer autocast
in fp16 in both variants, so a second precision boundary at `projected_q.float()`
remains in both and is not confounded with the one under test.

This patches the class method in place under a context manager. It never edits
the canonical source.
"""

from __future__ import annotations

import torch
import torch.nn.functional as F


def _forward_after_projection(self, tokens: torch.Tensor, valid_mask: torch.Tensor):
    """Canonical forward with the output cast moved after the output projection."""
    if (
        tokens.ndim != 3
        or valid_mask.shape != tokens.shape[:2]
        or valid_mask.dtype is not torch.bool
    ):
        raise ValueError(
            "tokens and valid_mask must be [batch,tokens,width] and boolean [batch,tokens]"
        )
    batch, count, _ = tokens.shape
    shape = (batch, count, self.heads, self.head_dim)
    projected_q = self.query(tokens).reshape(shape)
    projected_k = self.key(tokens).reshape(shape)
    projected_v = self.value(tokens).reshape(shape)
    with torch.autocast(device_type=tokens.device.type, enabled=False):
        q = (F.elu(projected_q.float()) + 1.0).transpose(1, 2)
        k = (F.elu(projected_k.float()) + 1.0).transpose(1, 2)
        v = projected_v.float().transpose(1, 2)
        valid = valid_mask[:, None, :, None]
        k = k * valid
        v = v * valid
        kv = torch.einsum("bhnd,bhne->bhde", k, v)
        ksum = k.sum(dim=2)
        denominator = torch.einsum("bhnd,bhd->bhn", q, ksum).clamp_min(self.eps)
        numerator = torch.einsum("bhnd,bhde->bhne", q, kv)
        output = (numerator / denominator[..., None]).transpose(1, 2).reshape(
            batch, count, self.width
        )
        # THE SINGLE CHANGE: project in fp32, then cast for the residual stream.
        projected = self.output(output)
    return projected.to(tokens.dtype), denominator.amin()


class attention_cast_variant:
    """Swap `KernelLinearAttention.forward` for the duration of a block."""

    def __init__(self, attention_class: type, mode: str) -> None:
        if mode not in ("historical", "after_projection"):
            raise ValueError("unknown attention cast mode: " + mode)
        self.attention_class = attention_class
        self.mode = mode
        self.original = attention_class.forward

    def __enter__(self) -> "attention_cast_variant":
        if self.mode == "after_projection":
            self.attention_class.forward = _forward_after_projection
        return self

    def __exit__(self, *exc: object) -> None:
        self.attention_class.forward = self.original
