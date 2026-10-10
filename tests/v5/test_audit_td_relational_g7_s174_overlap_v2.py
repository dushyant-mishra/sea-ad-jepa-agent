import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "v5" / "audit_td_relational_g7_s174_overlap_v2.py"


def load_module():
    spec = importlib.util.spec_from_file_location("td_g7_v2", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_overlap_status_is_pass_only_for_real_exact_overlap():
    m = load_module()
    assert m.overlap_status(3, 0) == "PASS_TD_G7_S174_EXACT_OVERLAP"
    assert m.overlap_status(3, 1) == "STOP_TD_G7_S174_CROSSCHECK_MISMATCH"
    assert m.overlap_status(0, 0) == "NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP"
    assert m.exit_code_for_status("PASS_TD_G7_S174_EXACT_OVERLAP") == 0
    assert m.exit_code_for_status("STOP_TD_G7_S174_CROSSCHECK_MISMATCH") != 0
    assert m.exit_code_for_status("NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP") != 0


def test_g1b_result_requires_pass_all_requirements_and_exact_freeze_sha():
    m = load_module()
    result = {
        "schema": "S174_REBUILD_G1B_RESULT_V1",
        "freeze": {"path": m.G1B_FREEZE_REPO_PATH, "sha256": m.G1B_FREEZE_SHA256},
        "requirements": {f"R{i}": True for i in range(1, 8)},
        "G1b_pass": True,
    }
    m.validate_g1b_result(result)

    bad = json.loads(json.dumps(result))
    bad["G1b_pass"] = False
    try:
        m.validate_g1b_result(bad)
    except RuntimeError as e:
        assert "pass" in str(e).lower()
    else:
        raise AssertionError("G1b result without PASS must be rejected")

    bad = json.loads(json.dumps(result))
    bad["requirements"]["R4"] = False
    try:
        m.validate_g1b_result(bad)
    except RuntimeError as e:
        assert "requirement" in str(e).lower()
    else:
        raise AssertionError("failed G1b requirement must be rejected")

    bad = json.loads(json.dumps(result))
    bad["freeze"]["sha256"] = "0" * 64
    try:
        m.validate_g1b_result(bad)
    except RuntimeError as e:
        assert "freeze" in str(e).lower()
    else:
        raise AssertionError("G1b result bound to wrong freeze must be rejected")


def test_s174_payload_requires_full_41238_geometry_and_integer_data():
    m = load_module()
    m.validate_s174_payload(
        np.asarray([1, 2, 3], dtype=np.int64),
        np.asarray([0, 1, 2], dtype=np.int64),
        np.asarray([0, 3], dtype=np.int64),
        (1, 41_238),
    )
    for bad_shape in ((1, 14_417), (1, 41_237)):
        try:
            m.validate_s174_payload(
                np.asarray([1], dtype=np.int64),
                np.asarray([0], dtype=np.int64),
                np.asarray([0, 1], dtype=np.int64),
                bad_shape,
            )
        except RuntimeError as e:
            assert "41238" in str(e).replace(",", "") or "geometry" in str(e).lower()
        else:
            raise AssertionError("S174 wrong column geometry must fail")

    for bad in (1.5, float("nan"), float("inf"), -1.0):
        try:
            m.validate_s174_payload(
                np.asarray([bad]),
                np.asarray([0], dtype=np.int64),
                np.asarray([0, 1], dtype=np.int64),
                (1, 41_238),
            )
        except RuntimeError:
            pass
        else:
            raise AssertionError(f"S174 invalid raw value must fail: {bad!r}")


def test_sparse_reference_row_uses_strict_integer_semantics():
    m = load_module()

    class Row:
        indices = np.asarray([10, 20], dtype=np.int64)
        data = np.asarray([2.0, 3.0], dtype=np.float64)

    class X:
        def getrow(self, _):
            return Row()

    assert m.sparse_row_dict(X(), 0, {10, 30}) == {10: 2}

    Row.data = np.asarray([2.5, 3.0], dtype=np.float64)
    try:
        m.sparse_row_dict(X(), 0, {10, 20})
    except RuntimeError:
        pass
    else:
        raise AssertionError("fractional S174 row value must fail")


def test_compare_rows_checks_all_replay_addresses_including_implicit_zeros():
    m = load_module()
    got = m.compare_rows({10: 2}, {10: 2}, {10, 20, 30})
    assert got == {"checked": 3, "mismatches": 0}
    got = m.compare_rows({10: 2}, {10: 2, 20: 1}, {10, 20, 30})
    assert got == {"checked": 3, "mismatches": 1}


def test_same_size_changed_physical_source_is_rejected(tmp_path):
    m = load_module()
    p = tmp_path / "source.h5ad"
    p.write_bytes(b"abcdef")
    rec = {"bytes": 6, "sha256": hashlib.sha256(b"abcdef").hexdigest()}
    assert m.common.verify_source_file(p, rec) == rec["sha256"]
    p.write_bytes(b"abcdeg")
    try:
        m.common.verify_source_file(p, rec)
    except RuntimeError:
        pass
    else:
        raise AssertionError("G7 must reject same-size changed H5AD before reread")


def test_g7_requires_same_authority_g6_pass_receipt(tmp_path):
    m = load_module()
    expected_trace = {
        "preflight_result_sha256": "p",
        "mapping_receipt_sha256": "m",
        "authorization_sha256": "a",
        "implementation_commit_sha": "c" * 40,
        "common_script_sha256": "common",
        "g6_script_sha256": "g6",
        "g7_script_sha256": "g7",
        "common_entrypoint": "scripts/v5/td_relational_value_read_v2_common.py",
        "g6_entrypoint": "scripts/v5/materialize_td_relational_corrected_sampleA_v2.py",
        "g7_entrypoint": "scripts/v5/audit_td_relational_g7_s174_overlap_v2.py",
        "authorization_schema": "JEPA_TD_RELATIONAL_VALUE_READ_AUTHORIZATION_V2",
        "authorization_token": "AUTHORIZE_EXACT_TD_SAMPLE_A_9216_CORRECTED_VALUE_MATERIALIZATION_V2_ONLY",
    }
    path = tmp_path / "g6.json"
    receipt = {
        "schema": m.G6_RECEIPT_SCHEMA,
        "status": m.G6_PASS,
        "authority_trace": dict(expected_trace),
        "biological_replay_authorized": False,
        "target_selection_authorized": False,
        "td60_authorized": False,
        "training_authorized": False,
    }
    path.write_text(json.dumps(receipt) + "\n", encoding="utf-8")
    assert m.load_g6_pass_receipt(path, expected_trace)["status"] == m.G6_PASS

    receipt["status"] = "STOP_TD_G6_SOURCE_LIBRARY_MISMATCH"
    path.write_text(json.dumps(receipt) + "\n", encoding="utf-8")
    try:
        m.load_g6_pass_receipt(path, expected_trace)
    except RuntimeError as e:
        assert "g6 pass" in str(e).lower()
    else:
        raise AssertionError("G7 must not run after failed G6")

    receipt["status"] = m.G6_PASS
    receipt["authority_trace"]["g7_script_sha256"] = "different"
    path.write_text(json.dumps(receipt) + "\n", encoding="utf-8")
    try:
        m.load_g6_pass_receipt(path, expected_trace)
    except RuntimeError as e:
        assert "same preflight" in str(e).lower() or "same" in str(e).lower()
    else:
        raise AssertionError("G7 must reject differently bound G6 receipt")


def test_v2_schema_is_distinct_from_historical_v1():
    m = load_module()
    assert m.G7_SCHEMA == "JEPA_TD_RELATIONAL_G7_S174_OVERLAP_V2"
