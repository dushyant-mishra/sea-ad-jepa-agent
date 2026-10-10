import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "v5" / "materialize_td_relational_corrected_sampleA_v2.py"


def load_module():
    spec = importlib.util.spec_from_file_location("td_corrected_materializer_v2", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(m)
    return m


def valid_auth(m):
    return {
        "schema": m.VALUE_AUTH_SCHEMA,
        "authorization": m.VALUE_AUTHORIZATION,
        "scope": m.VALUE_SCOPE,
        "g6_entrypoint": m.REQUIRED_G6_ENTRYPOINT,
        "g7_entrypoint": m.REQUIRED_G7_ENTRYPOINT,
        "training_authorized": False,
        "biological_replay_authorized": False,
    }


def test_value_authority_requires_exact_v2_scope_and_entrypoints(tmp_path):
    m = load_module()
    p = tmp_path / "auth.json"
    p.write_text(json.dumps(valid_auth(m)) + "\n")
    rec = m.load_value_authority(p)
    assert rec["authorization"] == m.VALUE_AUTHORIZATION
    assert rec["g6_entrypoint"] == m.REQUIRED_G6_ENTRYPOINT


def test_value_authority_rejects_old_v1_schema_token(tmp_path):
    m = load_module()
    p = tmp_path / "auth.json"
    p.write_text(json.dumps({
        "schema": "JEPA_TD_RELATIONAL_VALUE_READ_AUTHORIZATION_V1",
        "authorization": "AUTHORIZE_EXACT_TD_SAMPLE_A_9216_CORRECTED_VALUE_MATERIALIZATION_ONLY",
        "scope": m.VALUE_SCOPE,
        "training_authorized": False,
    }) + "\n")
    try:
        m.load_value_authority(p)
    except RuntimeError as e:
        assert "schema" in str(e).lower() or "authorization" in str(e).lower()
    else:
        raise AssertionError("historical V1 authorization must not authorize hardened V2 execution")


def test_value_authority_rejects_wrong_scope_or_entrypoint(tmp_path):
    m = load_module()
    p = tmp_path / "auth.json"
    rec = valid_auth(m)
    rec["scope"] = "broader-than-frozen"
    p.write_text(json.dumps(rec) + "\n")
    try:
        m.load_value_authority(p)
    except RuntimeError as e:
        assert "scope" in str(e).lower()
    else:
        raise AssertionError("wrong scope must fail closed")

    rec = valid_auth(m)
    rec["g6_entrypoint"] = "scripts/v5/materialize_td_relational_corrected_sampleA.py"
    p.write_text(json.dumps(rec) + "\n")
    try:
        m.load_value_authority(p)
    except RuntimeError as e:
        assert "entrypoint" in str(e).lower()
    else:
        raise AssertionError("historical V1 entrypoint must fail closed")


def test_preflight_requires_exact_pass(tmp_path):
    m = load_module()
    p = tmp_path / "PREFLIGHT_RESULT.json"
    p.write_text(json.dumps({"status": "PASS_TD_RELATIONAL_PREFLIGHT_DRIVER_VALUE_BLIND"}) + "\n")
    assert m.load_preflight_pass(p)["status"].startswith("PASS")
    p.write_text(json.dumps({"status": "FAIL"}) + "\n")
    try:
        m.load_preflight_pass(p)
    except RuntimeError as e:
        assert "preflight" in str(e).lower()
    else:
        raise AssertionError("failed preflight must block values")


def test_raw_library_total_is_before_mapping_filter():
    m = load_module()
    indices = [0, 1, 2, 3]
    values = [5, 7, 11, 13]
    col_to_address = {0: 100, 2: 200}
    row, total = m.corrected_row(indices, values, col_to_address, {100, 200})
    assert total == 36
    assert row == {100: 5, 200: 11}


def test_corrected_row_keeps_only_frozen_replay_addresses():
    m = load_module()
    row, total = m.corrected_row([0, 1], [3, 4], {0: 100, 1: 999}, {100})
    assert total == 7
    assert row == {100: 3}


def test_corrected_row_rejects_fractional_and_nonfinite_values_in_raw_count_slot():
    m = load_module()
    for bad in (1.25, float("nan"), float("inf"), -1):
        try:
            m.corrected_row([0], [bad], {0: 100}, {100})
        except RuntimeError:
            pass
        else:
            raise AssertionError(f"invalid raw-count value must fail closed: {bad!r}")


def test_output_namespace_refuses_overwrite(tmp_path):
    m = load_module()
    out = tmp_path / "cache"
    out.mkdir()
    (out / "MANIFEST.json").write_text("{}\n")
    try:
        m.assert_empty_output(out)
    except RuntimeError as e:
        assert "overwrite" in str(e).lower() or "not empty" in str(e).lower()
    else:
        raise AssertionError("materializer must never overwrite")
