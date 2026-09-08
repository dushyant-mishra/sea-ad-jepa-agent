from __future__ import annotations
from dataclasses import dataclass
from numbers import Integral
import hashlib
import torch

_MASK32 = 0xFFFFFFFF
_M0 = 0xD2511F53
_M1 = 0xCD9E8D57
_W0 = 0x9E3779B9
_W1 = 0xBB67AE85
_DOMAIN = b"SEA_AD_JEPA_V5_KEYED_DROPOUT_PHILOX4X32_10_V1\0"


def _int(value: object, name: str, minimum: int = 0, maximum: int = 0x7FFFFFFFFFFFFFFF) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise ValueError(f"{name} must be an exact integer")
    out = int(value)
    if out < minimum or out > maximum:
        raise ValueError(f"{name} must be in [{minimum},{maximum}]")
    return out


def _mulhilo32(a: torch.Tensor, b: int) -> tuple[torch.Tensor, torch.Tensor]:
    """Exact uint32 multiply high/low using signed-int64-safe 16-bit limbs."""
    x = a.to(torch.int64) & _MASK32
    y = int(b) & _MASK32
    a0 = x & 0xFFFF
    a1 = x >> 16
    b0 = y & 0xFFFF
    b1 = y >> 16
    p0 = a0 * b0
    mid = a0 * b1 + a1 * b0
    p3 = a1 * b1
    temp = p0 + ((mid & 0xFFFF) << 16)
    lo = temp & _MASK32
    carry = temp >> 32
    hi = (p3 + (mid >> 16) + carry) & _MASK32
    return hi, lo


def _site_key(*, training_seed: int, update_index: int, view_index: int, site_id: int) -> tuple[int, int]:
    vals = (
        _int(training_seed, "training_seed", 0, 0xFFFFFFFFFFFFFFFF),
        _int(update_index, "update_index", 0, 0xFFFFFFFFFFFFFFFF),
        _int(view_index, "view_index", 0, 0xFFFFFFFF),
        _int(site_id, "site_id", 0, 0xFFFFFFFF),
    )
    raw = bytearray(_DOMAIN)
    raw.extend(vals[0].to_bytes(8, "little"))
    raw.extend(vals[1].to_bytes(8, "little"))
    raw.extend(vals[2].to_bytes(4, "little"))
    raw.extend(vals[3].to_bytes(4, "little"))
    digest = hashlib.sha256(bytes(raw)).digest()
    return int.from_bytes(digest[:4], "little"), int.from_bytes(digest[4:8], "little")


def _philox4x32_10(
    c0: torch.Tensor,
    c1: torch.Tensor,
    c2: torch.Tensor,
    c3: torch.Tensor,
    k0: int,
    k1: int,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    c0 = c0.to(torch.int64) & _MASK32
    c1 = c1.to(torch.int64) & _MASK32
    c2 = c2.to(torch.int64) & _MASK32
    c3 = c3.to(torch.int64) & _MASK32
    key0 = int(k0) & _MASK32
    key1 = int(k1) & _MASK32
    for round_index in range(10):
        hi0, lo0 = _mulhilo32(c0, _M0)
        hi1, lo1 = _mulhilo32(c2, _M1)
        c0 = (hi1 ^ c1 ^ key0) & _MASK32
        c1 = lo1
        c2 = (hi0 ^ c3 ^ key1) & _MASK32
        c3 = lo0
        if round_index != 9:
            key0 = (key0 + _W0) & _MASK32
            key1 = (key1 + _W1) & _MASK32
    return c0, c1, c2, c3


def philox4x32_10_scalar(
    counter: tuple[int, int, int, int], key: tuple[int, int]
) -> tuple[int, int, int, int]:
    """Small exact scalar helper used for Random123 known-answer verification."""
    c = [
        torch.tensor([_int(v, f"counter[{i}]", 0, _MASK32)], dtype=torch.int64)
        for i, v in enumerate(counter)
    ]
    out = _philox4x32_10(
        c[0], c[1], c[2], c[3],
        _int(key[0], "key[0]", 0, _MASK32),
        _int(key[1], "key[1]", 0, _MASK32),
    )
    return tuple(int(x.item()) for x in out)  # type: ignore[return-value]


@dataclass(frozen=True)
class KeyedDropoutSpec:
    dropout_numerator: int = 1
    dropout_denominator: int = 10

    def validate(self) -> None:
        num = _int(self.dropout_numerator, "dropout_numerator", 0, 1_000_000)
        den = _int(self.dropout_denominator, "dropout_denominator", 1, 1_000_000)
        if num >= den:
            raise ValueError("dropout probability must be in [0,1)")


def scientific_counter_words(
    cell_key: int, canonical_token_id: int, feature_index: int
) -> tuple[int, int, int, int]:
    """Collision-free scientific address over the supported identity domain.

    Counter allocation:
      [stable_cell_key_low32, stable_cell_key_high32, token_id_plus_1, feature]
    """
    cell = _int(cell_key, "cell_key", 0, 0x7FFFFFFFFFFFFFFF)
    token = _int(canonical_token_id, "canonical_token_id", -1, _MASK32 - 1)
    feature = _int(feature_index, "feature_index", 0, _MASK32)
    return cell & _MASK32, (cell >> 32) & _MASK32, token + 1, feature


def keyed_dropout_mask(
    canonical_token_ids: torch.Tensor,
    cell_keys: torch.Tensor,
    *,
    width: int,
    training_seed: int,
    update_index: int,
    view_index: int,
    site_id: int,
    spec: KeyedDropoutSpec = KeyedDropoutSpec(),
) -> torch.Tensor:
    """Stateless packing-invariant dropout over scientific identity.

    The 128-bit Philox counter is [cell stable_key low32, cell stable_key high32,
    canonical token id + 1, feature]. Tensor position, packed position,
    microbatch ordinal, and device do not enter the scientific random address.

    This remains a V5 candidate primitive, not V4 replay/training authority.
    """
    spec.validate()
    if canonical_token_ids.ndim != 2 or canonical_token_ids.dtype not in (torch.int32, torch.int64):
        raise ValueError("canonical_token_ids must be integer [batch,tokens]")
    if cell_keys.ndim != 1 or len(cell_keys) != len(canonical_token_ids) or cell_keys.dtype not in (torch.int32, torch.int64):
        raise ValueError("cell_keys must be one integer per row")
    if bool((canonical_token_ids < -1).any()) or bool((canonical_token_ids > (_MASK32 - 1)).any()):
        raise ValueError("token IDs outside supported range")
    if bool((cell_keys < 0).any()):
        raise ValueError("cell_keys must be nonnegative")
    width = _int(width, "width", 1, 1_000_000)
    k0, k1 = _site_key(
        training_seed=training_seed,
        update_index=update_index,
        view_index=view_index,
        site_id=site_id,
    )
    device = canonical_token_ids.device
    batch, tokens = canonical_token_ids.shape
    cells = cell_keys.to(device=device, dtype=torch.int64)
    c0 = (cells & _MASK32)[:, None, None].expand(batch, tokens, width)
    c1 = ((cells >> 32) & _MASK32)[:, None, None].expand(batch, tokens, width)
    c2 = (canonical_token_ids.to(device=device, dtype=torch.int64) + 1)[:, :, None].expand(batch, tokens, width)
    c3 = torch.arange(width, device=device, dtype=torch.int64)[None, None, :].expand(batch, tokens, width)
    word, _, _, _ = _philox4x32_10(c0, c1, c2, c3, k0, k1)
    keep_num = spec.dropout_denominator - spec.dropout_numerator
    threshold = ((1 << 32) * keep_num) // spec.dropout_denominator
    return word < threshold


def keyed_dropout(
    x: torch.Tensor,
    mask: torch.Tensor,
    spec: KeyedDropoutSpec = KeyedDropoutSpec(),
) -> torch.Tensor:
    spec.validate()
    if mask.shape != x.shape or mask.dtype is not torch.bool:
        raise ValueError("mask must be boolean and match x shape")
    keep_num = spec.dropout_denominator - spec.dropout_numerator
    if keep_num <= 0:
        raise ValueError("zero keep probability is forbidden")
    return x * mask.to(x.dtype) * (spec.dropout_denominator / keep_num)
