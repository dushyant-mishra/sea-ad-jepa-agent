import hashlib
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "v5" / "audit_td_relational_replay_mapping_preflight.py"


def load_module():
    spec = importlib.util.spec_from_file_location("td_mapping_preflight", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_identifier_join_maps_by_id_not_position():
    m = load_module()
    # Physical order is deliberately different from canonical address order.
    var_ids = ["ENSG_C", "ENSG_A", "ENSG_B"]
    id_to_address = {"ENSG_A": 10, "ENSG_B": 20, "ENSG_C": 30}
    col_to_address, excluded = m.identifier_map(var_ids, id_to_address, set())
    assert col_to_address == {0: 30, 1: 10, 2: 20}
    assert excluded == {}


def test_ledger_collision_is_excluded_never_replaced():
    m = load_module()
    var_ids = ["ENSG_A", "ENSG_B"]
    id_to_address = {"ENSG_A": 10, "ENSG_B": 20}
    col_to_address, excluded = m.identifier_map(var_ids, id_to_address, {"ENSG_B"})
    assert col_to_address == {0: 10}
    assert excluded == {1: "LEDGER_COLLISION"}
    cov = m.replay_address_coverage(var_ids, id_to_address, {"ENSG_B"}, {10, 20})
    assert cov["resolved"] == 1
    assert cov["missing"] == [20]


def test_join_collision_fails_closed():
    m = load_module()
    var_ids = ["ENSG_A", "ENSG_A_ALIAS"]
    id_to_address = {"ENSG_A": 10, "ENSG_A_ALIAS": 10}
    col_to_address, excluded = m.identifier_map(var_ids, id_to_address, set())
    assert col_to_address == {}
    assert excluded == {0: "JOIN_COLLISION", 1: "JOIN_COLLISION"}
    cov = m.replay_address_coverage(var_ids, id_to_address, set(), {10})
    assert cov["resolved"] == 0
    assert cov["missing"] == [10]


def test_unrelated_unmapped_feature_does_not_replace_required_gene():
    m = load_module()
    var_ids = ["ENSG_A", "UNKNOWN"]
    id_to_address = {"ENSG_A": 10}
    cov = m.replay_address_coverage(var_ids, id_to_address, set(), {10})
    assert cov["resolved"] == 1
    assert cov["missing"] == []
    assert cov["excluded_columns"] == {"UNMAPPED": 1}


def test_source_file_must_match_frozen_size_and_sha(tmp_path):
    m = load_module()
    p = tmp_path / "source.h5ad"
    p.write_bytes(b"exact-source-bytes")
    rec = {"bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
    assert m.verify_source_file(p, rec) == rec["sha256"]
    p.write_bytes(b"changed-source--")  # same intent: byte drift must not be accepted
    try:
        m.verify_source_file(p, rec)
    except RuntimeError as e:
        assert "source" in str(e).lower() and ("size" in str(e).lower() or "sha" in str(e).lower())
    else:
        raise AssertionError("source-byte drift must fail closed")
