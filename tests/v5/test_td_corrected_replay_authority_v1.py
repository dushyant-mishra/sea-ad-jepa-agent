import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

from td_corrected_replay_authority_v1 import (  # noqa: E402
    AuthorityError,
    assert_fresh_namespace,
    begin_attempt,
    bind_replay_authority,
)


def _auth(kind: str, namespace: Path):
    return {
        "schema": f"JEPA_TD_CORRECTED_REPLAY_{kind.upper()}_AUTHORITY_V1",
        "authority_id": f"replay-{kind}-001",
        "scope": "TD_CORRECTED_REPLAY_EXECUTE_ONCE",
        "implementation_commit": "abc123",
        "contract_sha256": "1" * 64,
        "qualification_receipt_sha256": "2" * 64,
        "namespace": str(namespace),
        "replay_execution_authorized": True,
        "g6_execution_authorized": False,
        "g7_execution_authorized": False,
        "target_selection_authorized": False,
        "td60_authorized": False,
        "stage4_authorized": False,
        "training_authorized": False,
    }


def test_bind_exact_replay_only_authority_and_begin_once(tmp_path):
    ns = tmp_path / "replay_ns"
    bound = bind_replay_authority(
        contract_sha256="1" * 64,
        qualification_receipt_sha256="2" * 64,
        implementation_commit="abc123",
        namespace=ns,
        owner_authority=_auth("owner", ns),
        runtime_authority=_auth("runtime", ns),
        operational_authority=_auth("operational", ns),
    )
    assert bound.namespace == ns
    marker = begin_attempt(bound, ns)
    assert marker.name == "TD_CORRECTED_REPLAY_EXECUTION_START.json"
    payload = json.loads(marker.read_text())
    assert payload["spent_authority"] is True
    assert payload["authority_ids"] == ["replay-owner-001", "replay-runtime-001", "replay-operational-001"]
    with pytest.raises(AuthorityError, match="namespace"):
        begin_attempt(bound, ns)


def test_reject_wrong_scope_binding_or_forbidden_flags(tmp_path):
    ns = tmp_path / "replay_ns"
    owner, runtime, operational = (_auth(k, ns) for k in ("owner", "runtime", "operational"))
    owner["scope"] = "TD_G7_EXECUTE_ONCE"
    with pytest.raises(AuthorityError, match="scope"):
        bind_replay_authority("1" * 64, "2" * 64, "abc123", ns, owner, runtime, operational)
    owner = _auth("owner", ns)
    owner["training_authorized"] = True
    with pytest.raises(AuthorityError, match="training_authorized"):
        bind_replay_authority("1" * 64, "2" * 64, "abc123", ns, owner, runtime, operational)
    owner = _auth("owner", ns)
    runtime["qualification_receipt_sha256"] = "3" * 64
    with pytest.raises(AuthorityError, match="qualification_receipt_sha256"):
        bind_replay_authority("1" * 64, "2" * 64, "abc123", ns, owner, runtime, operational)


def test_reject_reused_predecessor_or_duplicate_authority_ids(tmp_path):
    ns = tmp_path / "replay_ns"
    owner, runtime, operational = (_auth(k, ns) for k in ("owner", "runtime", "operational"))
    operational["authority_id"] = "G7_RUNTIME_AUTHORITY"
    with pytest.raises(AuthorityError, match="predecessor authority"):
        bind_replay_authority("1" * 64, "2" * 64, "abc123", ns, owner, runtime, operational)
    operational = _auth("operational", ns)
    operational["authority_id"] = owner["authority_id"]
    with pytest.raises(AuthorityError, match="distinct"):
        bind_replay_authority("1" * 64, "2" * 64, "abc123", ns, owner, runtime, operational)


def test_namespace_must_be_fresh(tmp_path):
    ns = tmp_path / "replay_ns"
    assert_fresh_namespace(ns)
    ns.mkdir()
    with pytest.raises(AuthorityError, match="namespace"):
        assert_fresh_namespace(ns)
