#!/usr/bin/env python3
"""Hardened entrypoint for the frozen TD corrected Sample-A materializer.

This wrapper does not authorize value reads. It reuses the frozen V1 implementation but replaces
both its runtime authorization loader and its physical row-value decoder before invoking V1 main().
A future owner authorization must use the V2 schema/token and bind the hardened G6/G7 entrypoints;
the historical V1 token is deliberately rejected here.
"""
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path


_V1_PATH = Path(__file__).resolve().with_name("materialize_td_relational_corrected_sampleA.py")
_spec = importlib.util.spec_from_file_location("td_corrected_materializer_v1", _V1_PATH)
_v1 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_v1)

VALUE_AUTH_SCHEMA = "JEPA_TD_RELATIONAL_VALUE_READ_AUTHORIZATION_V2"
VALUE_AUTHORIZATION = "AUTHORIZE_EXACT_TD_SAMPLE_A_9216_CORRECTED_VALUE_MATERIALIZATION_V2_ONLY"
VALUE_SCOPE = (
    "TRAIN-only historical A_NATURAL_MIXTURE 25000 cells; exact frozen 9216 TD56-TD59 addresses; "
    "HVS/SEA corrected physical-ID reads; NPH52 historical clean-path pass-through; hardened G6/G7 integrity checks only; "
    "no corrected TD56/TD57B/TD57C/TD59 biological replay, target selection, TD60, model fitting, EMA, training, "
    "TEST, DEV/SEALED, pathology, or external biology"
)
REQUIRED_G6_ENTRYPOINT = "scripts/v5/materialize_td_relational_corrected_sampleA_v2.py"
REQUIRED_G7_ENTRYPOINT = "scripts/v5/audit_td_relational_g7_s174_overlap.py"

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
load_preflight_pass = _v1.load_preflight_pass
assert_empty_output = _v1.assert_empty_output
h5_strings = _v1.h5_strings
identifier_map = _v1.identifier_map
load_inputs = _v1.load_inputs
sha256_file = _v1.sha256_file


def load_value_authority(path: Path) -> dict:
    rec = json.loads(Path(path).read_text(encoding="utf-8"))
    if rec.get("schema") != VALUE_AUTH_SCHEMA:
        raise RuntimeError("V2 value authorization schema mismatch")
    if rec.get("authorization") != VALUE_AUTHORIZATION:
        raise RuntimeError("V2 value authorization token mismatch")
    if rec.get("scope") != VALUE_SCOPE:
        raise RuntimeError("V2 value authorization scope mismatch")
    if rec.get("g6_entrypoint") != REQUIRED_G6_ENTRYPOINT or rec.get("g7_entrypoint") != REQUIRED_G7_ENTRYPOINT:
        raise RuntimeError("V2 value authorization entrypoint binding mismatch")
    if rec.get("training_authorized") is not False:
        raise RuntimeError("V2 value authorization must explicitly keep training OFF")
    if rec.get("biological_replay_authorized") is not False:
        raise RuntimeError("V2 value authorization must explicitly keep biological replay OFF")
    return rec


def raw_integer(v0) -> int:
    """Decode one physical raw-count value without silently rounding transformed/fractional data."""
    x = float(v0)
    if not math.isfinite(x) or x < 0.0:
        raise RuntimeError(f"negative or non-finite raw count: {x!r}")
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
    # Patch the historical implementation in-memory so its internal authorization and every HVS/SEA
    # row decode use the hardened V2 rules. V1 remains preserved only as implementation lineage.
    _v1.load_value_authority = load_value_authority
    _v1.corrected_row = corrected_row
    return _v1.main()


if __name__ == "__main__":
    raise SystemExit(main())
