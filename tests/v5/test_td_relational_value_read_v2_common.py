import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "v5" / "td_relational_value_read_v2_common.py"


def load_module():
    spec = importlib.util.spec_from_file_location("td_v2_common", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    return path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def valid_mapping(m):
    return {
        "schema": m.MAPPING_SCHEMA,
        "status": m.MAPPING_PASS,
        "sample_A_contract": {
            "label": "A_NATURAL_MIXTURE",
            "cells": 25000,
            "source_counts": {"HVS": 1129, "NPH52": 1310, "SEA_AD": 22561},
            "h5_matrices": 34,
        },
        "substrate_custody_contract": {
            "frozen_h5_matrices": 35,
            "all_frozen_h5_bytes_must_authenticate": True,
        },
        "checks": {key: True for key in m.REQUIRED_MAPPING_CHECKS},
        "training_authorized": False,
        "real_value_replay_authorized_by_this_receipt": False,
    }


def valid_preflight(m, mapping: dict):
    return {
        "schema": m.PREFLIGHT_SCHEMA,
        "status": m.DRIVER_PASS,
        "inputs": dict(m.EXPECTED_INPUT_HASHES),
        "mapping_receipt_schema": mapping["schema"],
        "mapping_checks": mapping["checks"],
        "real_value_replay_authorized": False,
        "training_authorized": False,
    }


def fake_code_identity(m, g6_path, g7_path):
    return {
        "implementation_commit_sha": "a" * 40,
        "common_script_sha256": m.canonical_text_sha256(Path(m.__file__)),
        "g6_script_sha256": m.canonical_text_sha256(g6_path),
        "g7_script_sha256": m.canonical_text_sha256(g7_path),
        "common_entrypoint": m.COMMON_ENTRYPOINT,
        "g6_entrypoint": m.G6_ENTRYPOINT,
        "g7_entrypoint": m.G7_ENTRYPOINT,
    }


def valid_auth(m, preflight_path, mapping_path, g6_path, g7_path):
    identity = m.code_identity(g6_path, g7_path)
    return {
        "schema": m.VALUE_AUTH_SCHEMA,
        "authorization": m.VALUE_AUTHORIZATION,
        "scope": m.VALUE_SCOPE,
        "preflight_result_sha256": sha(preflight_path),
        "mapping_receipt_sha256": sha(mapping_path),
        **identity,
        "training_authorized": False,
        "biological_replay_authorized": False,
        "target_selection_authorized": False,
        "td60_authorized": False,
    }


def make_bound_files(tmp_path, m):
    mapping_path = write_json(tmp_path / "mapping.json", valid_mapping(m))
    preflight_path = write_json(tmp_path / "preflight.json", valid_preflight(m, json.loads(mapping_path.read_text())))
    g6_path = tmp_path / "g6.py"
    g7_path = tmp_path / "g7.py"
    g6_path.write_text("# g6\n", encoding="utf-8")
    g7_path.write_text("# g7\n", encoding="utf-8")
    m.code_identity = lambda left, right: fake_code_identity(m, left, right)
    auth_path = write_json(tmp_path / "auth.json", valid_auth(m, preflight_path, mapping_path, g6_path, g7_path))
    return preflight_path, mapping_path, g6_path, g7_path, auth_path


def test_bare_pass_only_preflight_is_rejected(tmp_path):
    m = load_module()
    p = write_json(tmp_path / "preflight.json", {"status": m.DRIVER_PASS})
    mp = write_json(tmp_path / "mapping.json", valid_mapping(m))
    try:
        m.load_bound_preflight(p, mp, expected_preflight_sha=sha(p), expected_mapping_sha=sha(mp))
    except RuntimeError as e:
        assert "schema" in str(e).lower() or "inputs" in str(e).lower()
    else:
        raise AssertionError("bare PASS-only preflight must be rejected")


def test_real_mapping_and_driver_terminals_are_distinct():
    m = load_module()
    assert m.MAPPING_PASS == "PASS_TD_RELATIONAL_MAPPING_PREFLIGHT_VALUE_BLIND"
    assert m.DRIVER_PASS == "PASS_TD_RELATIONAL_PREFLIGHT_DRIVER_VALUE_BLIND"
    assert m.MAPPING_PASS != m.DRIVER_PASS


def test_old_v2_preflight_schema_is_rejected(tmp_path):
    m = load_module()
    mapping = valid_mapping(m)
    mp = write_json(tmp_path / "mapping.json", mapping)
    preflight = valid_preflight(m, mapping)
    preflight["schema"] = "JEPA_TD_RELATIONAL_PREFLIGHT_DRIVER_RECEIPT_V2"
    p = write_json(tmp_path / "preflight.json", preflight)
    try:
        m.load_bound_preflight(p, mp, expected_preflight_sha=sha(p), expected_mapping_sha=sha(mp))
    except RuntimeError as e:
        assert "preflight schema" in str(e).lower()
    else:
        raise AssertionError("V2 preflight receipt must be rejected")


def test_missing_required_mapping_check_is_rejected(tmp_path):
    m = load_module()
    mapping = valid_mapping(m)
    mapping["checks"]["all_35_h5_source_sha256_verified"] = False
    mp = write_json(tmp_path / "mapping.json", mapping)
    p = write_json(tmp_path / "preflight.json", valid_preflight(m, mapping))
    try:
        m.load_bound_preflight(p, mp, expected_preflight_sha=sha(p), expected_mapping_sha=sha(mp))
    except RuntimeError as e:
        assert "mapping check" in str(e).lower()
    else:
        raise AssertionError("false required V3 mapping check must be rejected")


def test_mapping_sample_contract_must_be_34_and_35(tmp_path):
    m = load_module()
    mapping = valid_mapping(m)
    mapping["sample_A_contract"]["h5_matrices"] = 35
    mp = write_json(tmp_path / "mapping.json", mapping)
    p = write_json(tmp_path / "preflight.json", valid_preflight(m, mapping))
    try:
        m.load_bound_preflight(p, mp, expected_preflight_sha=sha(p), expected_mapping_sha=sha(mp))
    except RuntimeError as e:
        assert "sample-a" in str(e).lower()
    else:
        raise AssertionError("Sample-A mapping contract must stay 34 while substrate custody stays 35")


def test_changed_preflight_bytes_break_authorization_binding(tmp_path):
    m = load_module()
    p, mp, g6, g7, auth = make_bound_files(tmp_path, m)
    rec = json.loads(auth.read_text())
    p.write_text(p.read_text() + " ", encoding="utf-8")
    try:
        m.load_runtime_authorization(auth, preflight_path=p, mapping_path=mp, g6_path=g6, g7_path=g7)
    except RuntimeError as e:
        assert "preflight" in str(e).lower() and "sha" in str(e).lower()
    else:
        raise AssertionError("byte-changed preflight must invalidate runtime authorization")
    assert rec["preflight_result_sha256"] != sha(p)


def test_old_v1_authorization_schema_and_token_are_rejected(tmp_path):
    m = load_module()
    p, mp, g6, g7, auth = make_bound_files(tmp_path, m)
    rec = json.loads(auth.read_text())
    rec["schema"] = "JEPA_TD_RELATIONAL_VALUE_READ_AUTHORIZATION_V1"
    rec["authorization"] = "AUTHORIZE_EXACT_TD_SAMPLE_A_9216_CORRECTED_VALUE_MATERIALIZATION_ONLY"
    write_json(auth, rec)
    try:
        m.load_runtime_authorization(auth, preflight_path=p, mapping_path=mp, g6_path=g6, g7_path=g7)
    except RuntimeError as e:
        assert "schema" in str(e).lower() or "token" in str(e).lower()
    else:
        raise AssertionError("historical V1 authority must be rejected")


def test_wrong_g6_or_g7_code_sha_is_rejected(tmp_path):
    m = load_module()
    p, mp, g6, g7, auth = make_bound_files(tmp_path, m)
    g6.write_text("# changed g6 same authority stale\n", encoding="utf-8")
    try:
        m.load_runtime_authorization(auth, preflight_path=p, mapping_path=mp, g6_path=g6, g7_path=g7)
    except RuntimeError as e:
        assert "g6" in str(e).lower() and "sha" in str(e).lower()
    else:
        raise AssertionError("changed G6 code must invalidate authority")


def test_shared_common_module_and_commit_are_bound(tmp_path):
    m = load_module()
    p, mp, g6, g7, auth = make_bound_files(tmp_path, m)
    rec = json.loads(auth.read_text())
    rec["common_script_sha256"] = "0" * 64
    write_json(auth, rec)
    try:
        m.load_runtime_authorization(auth, preflight_path=p, mapping_path=mp, g6_path=g6, g7_path=g7)
    except RuntimeError as e:
        assert "common" in str(e).lower() and "sha" in str(e).lower()
    else:
        raise AssertionError("changed shared custody module identity must invalidate authority")

    rec = valid_auth(m, p, mp, g6, g7)
    rec["implementation_commit_sha"] = "b" * 40
    write_json(auth, rec)
    try:
        m.load_runtime_authorization(auth, preflight_path=p, mapping_path=mp, g6_path=g6, g7_path=g7)
    except RuntimeError as e:
        assert "commit" in str(e).lower()
    else:
        raise AssertionError("wrong implementation commit must invalidate authority")


def test_code_identity_is_lf_crlf_stable(tmp_path):
    m = load_module()
    lf = tmp_path / "lf.py"
    crlf = tmp_path / "crlf.py"
    lf.write_bytes(b"x = 1\ny = 2\n")
    crlf.write_bytes(b"x = 1\r\ny = 2\r\n")
    assert m.canonical_text_sha256(lf) == m.canonical_text_sha256(crlf)
    assert m.sha256_file(lf) != m.sha256_file(crlf)


def test_wrong_entrypoint_or_true_authority_boolean_is_rejected(tmp_path):
    m = load_module()
    p, mp, g6, g7, auth = make_bound_files(tmp_path, m)
    rec = json.loads(auth.read_text())
    rec["g7_entrypoint"] = "scripts/v5/wrong.py"
    write_json(auth, rec)
    try:
        m.load_runtime_authorization(auth, preflight_path=p, mapping_path=mp, g6_path=g6, g7_path=g7)
    except RuntimeError as e:
        assert "entrypoint" in str(e).lower()
    else:
        raise AssertionError("wrong entrypoint must be rejected")

    rec = valid_auth(m, p, mp, g6, g7)
    rec["biological_replay_authorized"] = True
    write_json(auth, rec)
    try:
        m.load_runtime_authorization(auth, preflight_path=p, mapping_path=mp, g6_path=g6, g7_path=g7)
    except RuntimeError as e:
        assert "biological" in str(e).lower()
    else:
        raise AssertionError("biological replay authority must remain false")


def test_same_size_byte_change_is_rejected(tmp_path):
    m = load_module()
    p = tmp_path / "source.h5ad"
    p.write_bytes(b"abcdef")
    rec = {"bytes": 6, "sha256": hashlib.sha256(b"abcdef").hexdigest()}
    assert m.verify_source_file(p, rec) == rec["sha256"]
    p.write_bytes(b"abcdeg")
    try:
        m.verify_source_file(p, rec)
    except RuntimeError as e:
        assert "sha" in str(e).lower()
    else:
        raise AssertionError("same-size source byte change must fail")


def test_strict_raw_integer_rejects_fractional_nonfinite_and_negative():
    m = load_module()
    assert m.strict_raw_integer(0) == 0
    assert m.strict_raw_integer(3.0) == 3
    for bad in (1.5, float("nan"), float("inf"), -1):
        try:
            m.strict_raw_integer(bad)
        except RuntimeError:
            pass
        else:
            raise AssertionError(f"raw value must be rejected: {bad!r}")
