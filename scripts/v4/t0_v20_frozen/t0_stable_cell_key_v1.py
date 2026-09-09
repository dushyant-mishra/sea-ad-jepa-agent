from __future__ import annotations
import hashlib
import math
from numbers import Integral
from typing import Any

MAX_I63 = (1 << 63) - 1
MATRIX_ID = "sea_ad_mtg_rna_final_2026"
OPERATOR_INDEX = 31
SOURCE = "SEA_AD"
PARTITION = "reader_fit"
NATIVE_CLASS = "Immune"


def stable_key_from_parts(matrix_id: str, local_row: int, cell_id: str) -> int:
    if not isinstance(matrix_id, str) or not matrix_id:
        raise ValueError("matrix_id must be a nonempty string")
    if isinstance(local_row, bool) or not isinstance(local_row, int) or local_row < 0:
        raise ValueError("local_row must be a nonnegative integer")
    if not isinstance(cell_id, str) or not cell_id:
        raise ValueError("cell_id must be a nonempty string")
    payload = f"{matrix_id}|{local_row}|{cell_id}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") & MAX_I63


def parse_stable_key_exact(value: Any) -> int:
    if isinstance(value, bool):
        raise ValueError("stable_key cannot be boolean")
    if isinstance(value, Integral):
        out = int(value)
    elif isinstance(value, str):
        s = value.strip()
        if not s or not s.isdecimal():
            raise ValueError("stable_key string must be unsigned decimal")
        out = int(s, 10)
    else:
        # Never accept float, including integral-looking float, because 63-bit keys
        # exceed the exact integer range of float64.
        raise ValueError("stable_key must be int or decimal string; floats are forbidden")
    if not (0 <= out <= MAX_I63):
        raise ValueError("stable_key out of signed-63-bit range")
    return out
