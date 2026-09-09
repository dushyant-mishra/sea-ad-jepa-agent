"""Vectorized device implementation of the frozen V5 Philox dropout contract.

This module is prospective mechanics only.  It preserves the exact V2 Philox
address allocation while removing the scalar Python loop from mask generation.
It is device-agnostic PyTorch code and can run on CPU or CUDA; CUDA execution is
*not* qualified merely because this module exists.

Full uint64 cell-key coverage is available through explicit low/high uint32 word
tensors.  The convenience ``cell_keys`` path accepts nonnegative signed int64
keys, which covers the current reader-fit stable-key authority.
"""
from __future__ import annotations

import math
from numbers import Integral
import torch

_MASK32 = 0xFFFFFFFF
_M0 = 0xD2511F53
_M1 = 0xCD9E8D57
_W0 = 0x9E3779B9
_W1 = 0xBB67AE85
_TWO32 = 1 << 32


def _bounded_scalar(value: object, name: str, upper: int) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise ValueError(f"{name} must be an exact integer")
    out = int(value)
    if out < 0 or out > upper:
        raise ValueError(f"{name} must lie in [0,{upper}]")
    return out


def dropout_threshold_u32(probability: float) -> int:
    """Return exact integer threshold equivalent to V2 open-unit comparison.

    V2 keeps a word ``w`` iff ``(w + 0.5) / 2**32 >= p``.  Computing the
    threshold once with the exact binary64 ratio avoids device floating-point
    boundary disagreement in the mask decision.
    """
    p = float(probability)
    if not math.isfinite(p) or not 0.0 <= p < 1.0:
        raise ValueError("probability must lie in [0,1)")
    numerator, denominator = p.as_integer_ratio()
    # ceil(p*2**32 - 1/2) exactly in integer arithmetic.
    top = (numerator << 33) - denominator
    bottom = denominator << 1
    threshold = -((-top) // bottom)
    return max(0, min(_TWO32, threshold))


def _validate_u32_words(words: torch.Tensor, name: str) -> None:
    if words.dtype != torch.int64:
        raise ValueError(f"{name} must be int64 uint32 words")
    if bool(((words < 0) | (words > _MASK32)).any()):
        raise ValueError(f"{name} must lie in uint32 range")


def _mul_const_hilo32(constant: int, value: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Exact uint32 scalar×tensor multiply without signed-int64 overflow."""
    constant = _bounded_scalar(constant, "constant", _MASK32)
    a0 = constant & 0xFFFF
    a1 = constant >> 16
    b0 = value & 0xFFFF
    b1 = value >> 16
    p0 = a0 * b0
    cross = a0 * b1 + a1 * b0
    low_full = p0 + ((cross & 0xFFFF) << 16)
    carry = low_full >> 32
    lo = low_full & _MASK32
    hi = (a1 * b1 + (cross >> 16) + carry) & _MASK32
    return hi, lo


def philox4x32_10_words(
    c0: torch.Tensor,
    c1: torch.Tensor,
    c2: torch.Tensor,
    c3: torch.Tensor,
    *,
    key0: int,
    key1: int,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """Vectorized canonical Philox4x32-10 over broadcast-compatible uint32 words."""
    if not (c0.device == c1.device == c2.device == c3.device):
        raise ValueError("counter words must share a device")
    for name, word in (("c0", c0), ("c1", c1), ("c2", c2), ("c3", c3)):
        _validate_u32_words(word, name)
    k0 = _bounded_scalar(key0, "key0", _MASK32)
    k1 = _bounded_scalar(key1, "key1", _MASK32)
    a0, a1, a2, a3 = torch.broadcast_tensors(c0, c1, c2, c3)
    for round_index in range(10):
        hi0, lo0 = _mul_const_hilo32(_M0, a0)
        hi1, lo1 = _mul_const_hilo32(_M1, a2)
        a0, a1, a2, a3 = (
            (hi1 ^ a1 ^ k0) & _MASK32,
            lo1,
            (hi0 ^ a3 ^ k1) & _MASK32,
            lo0,
        )
        if round_index != 9:
            k0 = (k0 + _W0) & _MASK32
            k1 = (k1 + _W1) & _MASK32
    return a0, a1, a2, a3


def _validate_token_keys(token_keys: torch.Tensor) -> None:
    if token_keys.dtype != torch.int64 or token_keys.ndim != 2:
        raise ValueError("token_keys must be int64 [cells,tokens]")
    if bool(((token_keys < -1) | (token_keys > 65_534)).any()):
        raise ValueError("canonical token keys must lie in [-1,65534]")


def keyed_dropout_u32_words_tensor(
    *,
    cell_key_lo: torch.Tensor,
    cell_key_hi: torch.Tensor,
    token_keys: torch.Tensor,
    feature_count: int,
    run_seed: int,
    update_index: int,
    domain_index: int,
    view_index: int,
    layer_index: int,
    site_index: int,
) -> torch.Tensor:
    """Generate V2 Philox first words for a [cells,tokens,features] identity grid."""
    if cell_key_lo.ndim != 1 or cell_key_hi.ndim != 1 or cell_key_lo.shape != cell_key_hi.shape:
        raise ValueError("cell key word tensors must be aligned one-dimensional arrays")
    if token_keys.ndim != 2 or token_keys.shape[0] != cell_key_lo.shape[0]:
        raise ValueError("token_keys must align with cell key rows")
    if not (cell_key_lo.device == cell_key_hi.device == token_keys.device):
        raise ValueError("cell/token key tensors must share a device")
    _validate_u32_words(cell_key_lo, "cell_key_lo")
    _validate_u32_words(cell_key_hi, "cell_key_hi")
    _validate_token_keys(token_keys)
    feature_count = _bounded_scalar(feature_count, "feature_count", 65_536)
    if feature_count < 1:
        raise ValueError("feature_count must be at least one")
    seed = _bounded_scalar(run_seed, "run_seed", _MASK32)
    update = _bounded_scalar(update_index, "update_index", _MASK32)
    domain = _bounded_scalar(domain_index, "domain_index", 0xFF)
    view = _bounded_scalar(view_index, "view_index", 0xFF)
    layer = _bounded_scalar(layer_index, "layer_index", 0xFF)
    site = _bounded_scalar(site_index, "site_index", 0xFF)

    cells, tokens = token_keys.shape
    features = torch.arange(feature_count, dtype=torch.int64, device=token_keys.device)
    c0 = cell_key_lo[:, None, None].expand(cells, tokens, feature_count)
    c1 = cell_key_hi[:, None, None].expand(cells, tokens, feature_count)
    c2 = ((features[None, None, :] << 16) | (token_keys[:, :, None] + 1)).expand(cells, tokens, feature_count)
    c3_value = (domain << 24) | (site << 16) | (layer << 8) | view
    c3 = torch.tensor(c3_value, dtype=torch.int64, device=token_keys.device)
    out0, _, _, _ = philox4x32_10_words(c0, c1, c2, c3, key0=seed, key1=update)
    return out0


def split_signed_cell_keys(cell_keys: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Split current nonnegative signed-int64 stable keys into uint32 words."""
    if cell_keys.dtype != torch.int64 or cell_keys.ndim != 1:
        raise ValueError("cell_keys must be int64 [cells]")
    if bool((cell_keys < 0).any()):
        raise ValueError("signed cell_keys cannot encode uint64 values >= 2**63; use explicit low/high words")
    return cell_keys & _MASK32, (cell_keys >> 32) & _MASK32


def keyed_dropout_u32_tensor(
    *,
    cell_keys: torch.Tensor,
    token_keys: torch.Tensor,
    feature_count: int,
    run_seed: int,
    update_index: int,
    domain_index: int,
    view_index: int,
    layer_index: int,
    site_index: int,
) -> torch.Tensor:
    lo, hi = split_signed_cell_keys(cell_keys)
    return keyed_dropout_u32_words_tensor(
        cell_key_lo=lo,
        cell_key_hi=hi,
        token_keys=token_keys,
        feature_count=feature_count,
        run_seed=run_seed,
        update_index=update_index,
        domain_index=domain_index,
        view_index=view_index,
        layer_index=layer_index,
        site_index=site_index,
    )


def keyed_feature_dropout_device(
    values: torch.Tensor,
    *,
    cell_keys: torch.Tensor,
    token_keys: torch.Tensor,
    probability: float,
    run_seed: int,
    update_index: int,
    domain_index: int,
    view_index: int,
    layer_index: int,
    site_index: int,
    training: bool = True,
) -> torch.Tensor:
    """Vectorized V2 feature dropout for current signed-int64 reader-fit keys."""
    if values.ndim != 3 or not values.is_floating_point() or not bool(torch.isfinite(values).all()):
        raise ValueError("values must be finite floating [cells,tokens,features]")
    if cell_keys.dtype != torch.int64 or cell_keys.ndim != 1 or len(cell_keys) != len(values):
        raise ValueError("cell_keys must be int64 [cells]")
    if token_keys.dtype != torch.int64 or token_keys.shape != values.shape[:2]:
        raise ValueError("token_keys must be int64 [cells,tokens]")
    if not (values.device == cell_keys.device == token_keys.device):
        raise ValueError("values/cell_keys/token_keys must share a device")
    threshold = dropout_threshold_u32(probability)
    p = float(probability)
    if not training or p == 0.0:
        return values
    words = keyed_dropout_u32_tensor(
        cell_keys=cell_keys,
        token_keys=token_keys,
        feature_count=values.shape[2],
        run_seed=run_seed,
        update_index=update_index,
        domain_index=domain_index,
        view_index=view_index,
        layer_index=layer_index,
        site_index=site_index,
    )
    keep = words >= threshold
    return values * keep.to(dtype=values.dtype) / (1.0 - p)
