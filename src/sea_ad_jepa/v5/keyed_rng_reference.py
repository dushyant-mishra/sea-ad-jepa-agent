"""Reference-only Philox4x32-10 keyed RNG contract for V5.

This module is deliberately inactive.  It pins the proposed bit-level random
primitive and scientific-identity addressing needed for packing-invariant
training stochasticity.  It is a small CPU reference, not a production GPU
kernel and not execution authority.
"""
from __future__ import annotations

import hashlib
from numbers import Integral

_MASK32 = 0xFFFFFFFF
_M0 = 0xD2511F53
_M1 = 0xCD9E8D57
_W0 = 0x9E3779B9
_W1 = 0xBB67AE85
_DOMAIN = b"SEA_AD_JEPA_V5_KEYED_DROPOUT_PHILOX4X32_10_V1\0"


def _u32(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise ValueError(f"{name} must be an exact integer")
    out = int(value)
    if out < 0 or out > _MASK32:
        raise ValueError(f"{name} must lie in uint32 range")
    return out


def _u64(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise ValueError(f"{name} must be an exact integer")
    out = int(value)
    if out < 0 or out > 0xFFFFFFFFFFFFFFFF:
        raise ValueError(f"{name} must lie in uint64 range")
    return out


def _mulhilo32(a: int, b: int) -> tuple[int, int]:
    product = (int(a) * int(b)) & 0xFFFFFFFFFFFFFFFF
    return (product >> 32) & _MASK32, product & _MASK32


def philox4x32_10(counter: tuple[int, int, int, int], key: tuple[int, int]) -> tuple[int, int, int, int]:
    """Canonical Random123 Philox4x32 with ten rounds and uint32 wrap."""
    if len(counter) != 4 or len(key) != 2:
        raise ValueError("Philox4x32 requires four counter words and two key words")
    c = [_u32(v, f"counter[{i}]") for i, v in enumerate(counter)]
    k = [_u32(v, f"key[{i}]") for i, v in enumerate(key)]
    for round_index in range(10):
        hi0, lo0 = _mulhilo32(_M0, c[0])
        hi1, lo1 = _mulhilo32(_M1, c[2])
        c = [
            (hi1 ^ c[1] ^ k[0]) & _MASK32,
            lo1,
            (hi0 ^ c[3] ^ k[1]) & _MASK32,
            lo0,
        ]
        if round_index != 9:
            k[0] = (k[0] + _W0) & _MASK32
            k[1] = (k[1] + _W1) & _MASK32
    return tuple(c)  # type: ignore[return-value]


def site_key_words(
    *,
    run_seed: int,
    update_index: int,
    view_index: int,
    layer_index: int,
    site_index: int,
) -> tuple[int, int]:
    """Derive a site key; no tensor position, microbatch ordinal, or device enters."""
    fields = {
        "run_seed": run_seed,
        "update_index": update_index,
        "view_index": view_index,
        "layer_index": layer_index,
        "site_index": site_index,
    }
    encoded = bytearray(_DOMAIN)
    for name, raw in fields.items():
        value = _u32(raw, name)
        encoded.extend(value.to_bytes(4, "little", signed=False))
    digest = hashlib.sha256(bytes(encoded)).digest()
    return (
        int.from_bytes(digest[0:4], "little"),
        int.from_bytes(digest[4:8], "little"),
    )


def dropout_counter_words(*, cell_key: int, canonical_token_key: int, feature_index: int) -> tuple[int, int, int, int]:
    """Map retained scientific identity to one unique Philox counter.

    The 128-bit Philox counter is allocated exactly as:
      [stable_cell_key_low32, stable_cell_key_high32, token_key_plus_1, feature].
    Canonical token key -1 is reserved for the cell token; gene keys are
    0..41,237.  This supports the reader-fit uint64 stable_key authority without
    tensor-position or microbatch identity entering the random address.
    """
    cell = _u64(cell_key, "cell_key")
    if isinstance(canonical_token_key, bool) or not isinstance(canonical_token_key, Integral):
        raise ValueError("canonical_token_key must be an exact integer")
    token = int(canonical_token_key)
    if token < -1 or token >= _MASK32:
        raise ValueError("canonical_token_key outside supported range")
    feature = _u32(feature_index, "feature_index")
    cell_lo = cell & _MASK32
    cell_hi = (cell >> 32) & _MASK32
    return cell_lo, cell_hi, token + 1, feature


def keyed_dropout_u32(
    *,
    run_seed: int,
    update_index: int,
    view_index: int,
    layer_index: int,
    site_index: int,
    cell_key: int,
    canonical_token_key: int,
    feature_index: int,
) -> int:
    key = site_key_words(
        run_seed=run_seed,
        update_index=update_index,
        view_index=view_index,
        layer_index=layer_index,
        site_index=site_index,
    )
    counter = dropout_counter_words(
        cell_key=cell_key,
        canonical_token_key=canonical_token_key,
        feature_index=feature_index,
    )
    return philox4x32_10(counter, key)[0]


def u32_open_unit(value: int) -> float:
    """Deterministic open-interval conversion used by the contract."""
    word = _u32(value, "value")
    return (word + 0.5) / 4294967296.0


def keyed_dropout_keep(**kwargs: int | float) -> bool:
    """Return the V5 contract keep/drop decision for one scientific element."""
    if "probability" not in kwargs:
        raise ValueError("probability is required")
    p = float(kwargs.pop("probability"))
    if not 0.0 <= p < 1.0:
        raise ValueError("probability must lie in [0,1)")
    return u32_open_unit(keyed_dropout_u32(**kwargs)) >= p  # type: ignore[arg-type]
