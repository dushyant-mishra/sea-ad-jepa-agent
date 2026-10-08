import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "v5" / "materialize_td_relational_corrected_sampleA.py"


def load_module():
    spec = importlib.util.spec_from_file_location("td_corrected_materializer", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(m)
    return m


def test_value_authority_requires_exact_scope(tmp_path):
    m = load_module()
    p = tmp_path / "auth.json"
    p.write_text(json.dumps({
        "schema": m.VALUE_AUTH_SCHEMA,
        "authorization": m.VALUE_AUTHORIZATION,
        "scope": m.VALUE_SCOPE,
        "training_authorized": False,
    }) + "\n")
    rec = m.load_value_authority(p)
    assert rec["authorization"] == m.VALUE_AUTHORIZATION


def test_value_authority_rejects_wrong_scope(tmp_path):
    m = load_module()
    p = tmp_path / "auth.json"
    p.write_text(json.dumps({
        "schema": m.VALUE_AUTH_SCHEMA,
        "authorization": m.VALUE_AUTHORIZATION,
        "scope": "broader-than-frozen",
        "training_authorized": False,
    }) + "\n")
    try:
        m.load_value_authority(p)
    except RuntimeError as e:
        assert "scope" in str(e).lower()
    else:
        raise AssertionError("wrong scope must fail closed")


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
    col_to_address = {0: 100, 2: 200}  # columns 1 and 3 are excluded/unmapped
    row, total = m.corrected_row(indices, values, col_to_address, {100, 200})
    assert total == 36
    assert row == {100: 5, 200: 11}


def test_corrected_row_keeps_only_frozen_replay_addresses():
    m = load_module()
    row, total = m.corrected_row([0, 1], [3, 4], {0: 100, 1: 999}, {100})
    assert total == 7
    assert row == {100: 3}


def test_g7_exact_overlap_passes_only_zero_mismatch():
    m = load_module()
    current = {100: 3, 200: 5}
    s174 = {100: 3, 200: 5, 999: 8}
    rec = m.g7_compare_rows(current, s174, {100, 200})
    assert rec == {"checked": 2, "mismatches": 0}


def test_g7_counts_missing_as_zero_and_fails_difference():
    m = load_module()
    rec = m.g7_compare_rows({100: 3}, {100: 3, 200: 7}, {100, 200})
    assert rec == {"checked": 2, "mismatches": 1}


def test_g1b_freeze_shard_hashes_must_match(tmp_path):
    m = load_module()
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "abc.counts.npz").write_bytes(b"counts")
    (cache / "abc.meta.npz").write_bytes(b"meta")
    freeze = {
        "rebuilt_cache": {"shards": {
            "abc": {
                "counts": m.sha256_file(cache / "abc.counts.npz"),
                "meta": m.sha256_file(cache / "abc.meta.npz"),
            }
        }}
    }
    assert m.verify_s174_cache_hashes(cache, freeze) == 1
    (cache / "abc.counts.npz").write_bytes(b"changed")
    try:
        m.verify_s174_cache_hashes(cache, freeze)
    except RuntimeError as e:
        assert "s174" in str(e).lower() or "hash" in str(e).lower()
    else:
        raise AssertionError("changed G1b-authorized cache must fail closed")


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
