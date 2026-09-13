from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_METADATA_SHA256 = "a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913"


def _load(name: str, relpath: str):
    path = ROOT / relpath
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_schedule_chain_uses_same_frozen_metadata_authority_as_full104_binder():
    derive = _load(
        "derive_full_population_schedule_optimum_v3",
        "scripts/v5_anticheat/derive_full_population_schedule_optimum_v3.py",
    )
    materialize = _load(
        "materialize_full_population_schedule_v4",
        "scripts/v5_anticheat/materialize_full_population_schedule_v4.py",
    )
    audit = _load(
        "audit_full_population_proposal_weight_restart_v1",
        "scripts/v5_anticheat/audit_full_population_proposal_weight_restart_v1.py",
    )
    binder = _load(
        "bind_full104_expression_blocks_v4",
        "scripts/v5_anticheat/bind_full104_expression_blocks_v4.py",
    )

    assert binder.EXPECTED_METADATA_SQLITE_SHA256 == CANONICAL_METADATA_SHA256
    assert derive.EXPECTED_METADATA_SQLITE_SHA256 == CANONICAL_METADATA_SHA256
    assert materialize.EXPECTED_METADATA_SQLITE_SHA256 == CANONICAL_METADATA_SHA256
    assert audit.EXPECTED_METADATA_SQLITE_SHA256 == CANONICAL_METADATA_SHA256
