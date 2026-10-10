#!/usr/bin/env python3
"""Hardened entrypoint for the frozen TD corrected Sample-A materializer.

This wrapper does not authorize value reads. It reuses the frozen V1 implementation but replaces
its row-value decoder with a strict raw-integer reader before invoking V1 main(). Future authorization
must bind this V2 entrypoint; the V1 entrypoint is retained only as historical implementation lineage.
"""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path


_V1_PATH = Path(__file__).resolve().with_name("materialize_td_relational_corrected_sampleA.py")
_spec = importlib.util.spec_from_file_location("td_corrected_materializer_v1", _V1_PATH)
_v1 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_v1)

# Re-export the frozen authority constants/helpers used by tests and G7.
VALUE_AUTH_SCHEMA = _v1.VALUE_AUTH_SCHEMA
VALUE_AUTHORIZATION = _v1.VALUE_AUTHORIZATION
VALUE_SCOPE = _v1.VALUE_SCOPE
PREFLIGHT_PASS = _v1.PREFLIGHT_PASS
EXPECTED_REPLAY_MANIFEST_SHA = _v1.EXPECTED_REPLAY_MANIFEST_SHA
EXPECTED_SAMPLE_FREEZE_SHA = _v1.EXPECTED_SAMPLE_FREEZE_SHA
EXPECTED_PROVENANCE_SHA = _v1.EXPECTED_PROVENANCE_SHA
EXPECTED_COLLISION_SHA = _v1.EXPECTED_COLLISION_SHA
EXPECTED_MACHA_FREEZE_SHA = _v1.EXPECTED_MACHA_FREEZE_SHA
N_ADDR = _v1.N_ADDR
N_SAMPLE_A = _v1.N_SAMPLE_A
N_REPLAY = _v1.N_REPLAY
SOURCE_COUNTS = _v1.SOURCE_COUNTS
FAMILY = _v1.FAMILY
VAR_ID_COLUMN = _v1.VAR_ID_COLUMN
load_value_authority = _v1.load_value_authority
load_preflight_pass = _v1.load_preflight_pass
assert_empty_output = _v1.assert_empty_output
h5_strings = _v1.h5_strings
identifier_map = _v1.identifier_map
load_inputs = _v1.load_inputs
sha256_file = _v1.sha256_file


def raw_integer(v0) -> int:
    """Decode one physical raw-count value without silently rounding transformed/fractional data."""
    x = float(v0)
    if not math.isfinite(x) or x < 0.0:
        raise RuntimeError("negative or non-finite raw count")
    v = int(x)
    if float(v) != x:
        raise RuntimeError(f"non-integer value encountered in raw-count slot: {x!r}")
    return v


def corrected_row(indices, values, col_to_address: dict[int, int], replay_addresses: set[int]):
    """Strict V2 row reader: whole-row total before filtering, exact integer counts only."""
    row: dict[int, int] = {}
    total = 0
    for j0, v0 in zip(indices, values):
        j = int(j0)
        v = raw_integer(v0)
        total += v
        a = col_to_address.get(j)
        if a is not None and a in replay_addresses and v:
            if a in row:
                raise RuntimeError(f"noninjective mapped replay address encountered at value read: {a}")
            row[a] = v
    return row, total


def main() -> int:
    # Patch the frozen V1 module in-memory so every HVS/SEA value read inside its main path uses the
    # strict V2 decoder. No V1 source file is modified and no broader behavior changes.
    _v1.corrected_row = corrected_row
    return _v1.main()


if __name__ == "__main__":
    raise SystemExit(main())
