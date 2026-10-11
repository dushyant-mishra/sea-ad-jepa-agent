"""Synthetic fixtures for the TD V2 G6/G7 runtime-authorization gate (synthetic owner decision included).

Every file built here is synthetic and lives under pytest's tmp_path. Nothing here creates, reads or stands in for a
real owner decision, a real runtime value authorization or the real PR #259 receipts; the gate's pinned PR #259 SHAs
are pointed at the synthetic receipts with monkeypatch for the duration of one test only.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
COMMON = ROOT / "scripts" / "v5" / "td_relational_value_read_v2_common.py"


def load_common(name: str = "td_v2_common_gate_fixture"):
    spec = importlib.util.spec_from_file_location(name, COMMON)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path: Path, payload: dict, **dump_kwargs) -> Path:
    dump_kwargs.setdefault("sort_keys", True)
    Path(path).write_bytes((json.dumps(payload, **dump_kwargs) + "\n").encode("utf-8"))
    return Path(path)


def valid_mapping(m) -> dict:
    return {
        "schema": m.MAPPING_SCHEMA,
        "status": m.MAPPING_PASS,
        "sample_A_contract": {
            "label": "A_NATURAL_MIXTURE",
            "cells": 25000,
            "source_counts": {"HVS": 1129, "NPH52": 1310, "SEA_AD": 22561},
            "h5_matrices": 34,
        },
        "substrate_custody_contract": {"frozen_h5_matrices": 35, "all_frozen_h5_bytes_must_authenticate": True},
        "checks": {key: True for key in m.REQUIRED_MAPPING_CHECKS},
        "training_authorized": False,
        "real_value_replay_authorized_by_this_receipt": False,
    }


def valid_preflight(m, mapping: dict) -> dict:
    return {
        "schema": m.PREFLIGHT_SCHEMA,
        "status": m.DRIVER_PASS,
        "inputs": dict(m.EXPECTED_INPUT_HASHES),
        "mapping_receipt_schema": mapping["schema"],
        "mapping_checks": mapping["checks"],
        "real_value_replay_authorized": False,
        "training_authorized": False,
    }


def fake_code_identity(m, g6_path, g7_path, commit: str = "a" * 40) -> dict:
    return {
        "implementation_commit_sha": commit,
        "common_script_sha256": m.canonical_text_sha256(Path(m.__file__)),
        "g6_script_sha256": m.canonical_text_sha256(g6_path),
        "g7_script_sha256": m.canonical_text_sha256(g7_path),
        "common_entrypoint": m.COMMON_ENTRYPOINT,
        "g6_entrypoint": m.G6_ENTRYPOINT,
        "g7_entrypoint": m.G7_ENTRYPOINT,
    }


OWNER_DECISION_FLAGS = ("biological_replay_authorized", "target_selection_authorized", "td60_authorized",
                        "training_authorized")


def synthetic_owner_decision(m, commit: str = "a" * 40) -> dict:
    """A SYNTHETIC owner-decision record for tests; it names the gate's (monkeypatched) PR #259 pins."""
    return {
        "schema": "JEPA_TD_RELATIONAL_G6_G7_OWNER_DECISION_V1",
        "decision": "AUTHORIZE_G6_G7_INTEGRITY_ONLY",
        "authorized_pr259_preflight_driver_sha256": m.PR259_DRIVER_SHA256,
        "authorized_pr259_mapping_receipt_sha256": m.PR259_MAPPING_SHA256,
        "qualified_implementation_commit_sha": commit,
        **{flag: False for flag in OWNER_DECISION_FLAGS},
        "synthetic_test_fixture_not_an_owner_decision": True,
    }


def authorization_record(m, b, **overrides) -> dict:
    """Synthetic runtime authorization; an override of None removes that key."""
    rec = {
        "schema": m.VALUE_AUTH_SCHEMA,
        "authorization": m.VALUE_AUTHORIZATION,
        "scope": m.VALUE_SCOPE,
        "owner_decision_sha256": sha(b.owner_decision),
        "preflight_result_sha256": sha(b.preflight),
        "mapping_receipt_sha256": sha(b.mapping),
        "replay_manifest_sha256": sha(b.replay_manifest),
        **m.code_identity(b.g6, b.g7),
        "training_authorized": False,
        "biological_replay_authorized": False,
        "target_selection_authorized": False,
        "td60_authorized": False,
    }
    rec.update(overrides)
    return {k: v for k, v in rec.items() if v is not None}


def rewrite_authorization(m, b, **overrides) -> Path:
    """(Re)build the synthetic runtime authorization around whatever bytes the bound files hold right now."""
    return write_json(b.auth, authorization_record(m, b, **overrides))


def build_gate(tmp_path: Path, m, monkeypatch) -> SimpleNamespace:
    """Synthetic receipts, replay manifest, code files and authorization, with the gate's PR #259 pins pointed at the
    synthetic receipt bytes (monkeypatch; restored after the test)."""
    tmp_path = Path(tmp_path)
    b = SimpleNamespace(
        mapping=tmp_path / "mapping.json",
        preflight=tmp_path / "preflight.json",
        replay_manifest=tmp_path / "replay_manifest.csv",
        g6=tmp_path / "g6.py",
        g7=tmp_path / "g7.py",
        auth=tmp_path / "auth.json",
        owner_decision=tmp_path / "owner_decision.json",
    )
    b.replay_manifest.write_bytes(b"molecular_address_index,gene\n3,G3\n5,G5\n8,G8\n")
    monkeypatch.setitem(m.EXPECTED_INPUT_HASHES, "replay_manifest_sha256", sha(b.replay_manifest))
    write_json(b.mapping, valid_mapping(m))
    write_json(b.preflight, valid_preflight(m, json.loads(b.mapping.read_text(encoding="utf-8"))))
    b.g6.write_text("# g6\n", encoding="utf-8")
    b.g7.write_text("# g7\n", encoding="utf-8")
    monkeypatch.setattr(m, "code_identity", lambda left, right: fake_code_identity(m, left, right))
    monkeypatch.setattr(m, "PR259_DRIVER_SHA256", sha(b.preflight), raising=False)
    monkeypatch.setattr(m, "PR259_MAPPING_SHA256", sha(b.mapping), raising=False)
    write_json(b.owner_decision, synthetic_owner_decision(m))
    rewrite_authorization(m, b)
    return b


def call_gate(m, b, **overrides):
    kwargs = dict(preflight_path=b.preflight, mapping_path=b.mapping, replay_manifest_path=b.replay_manifest,
                  g6_path=b.g6, g7_path=b.g7, owner_decision_path=b.owner_decision)
    kwargs.update(overrides)
    return m.load_runtime_authorization(b.auth, **kwargs)
