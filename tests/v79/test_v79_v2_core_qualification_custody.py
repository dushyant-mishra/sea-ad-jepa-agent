from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "scripts" / "v79"
sys.path.insert(0, str(HERE))

import v79_v2_core_qualification_custody as C  # noqa: E402
import v79_v2_core_qualification_plan as Q  # noqa: E402


def _ledger():
    return [{"fit_id": f"{i:064x}", "primary_seed": i, "escalation_seed": i + 100000} for i in range(C.EXPECTED_FITS)]


def _auth(ledger):
    return {
        "schema": "V79_V2_CORE_QUALIFICATION_EXECUTION_AUTHORIZATION_V1",
        "qualification_campaign_authorized": True,
        "benchmark_controller_pass": True,
        "contract_sha256": C.SOURCE_CONTRACT_SHA256,
        "blinded_index_sha256": C.QUALIFICATION_INDEX_SHA256,
        "fit_seed_ledger": ledger,
        "scoring_authorized": False,
        "training_authorized": False,
    }


def test_authorization_view_is_identity_blind_and_exact_seed_bound():
    ledger = _ledger()
    a = C.sanitize_execution_authorization(_auth(ledger), expected_seed_ledger=ledger)
    assert a["schema"] == "V79_V2_CORE_QUALIFICATION_EXECUTION_AUTHORIZATION_V1"
    assert len(a["fit_seed_ledger"]) == C.EXPECTED_FITS
    assert all(set(x) == {"fit_id", "primary_seed", "escalation_seed"} for x in a["fit_seed_ledger"])
    raw = json.dumps(a)
    for forbidden in ("Q00", "Q11", "world_name", "world_index", "controller_truth", "operator", "matrix"):
        assert forbidden not in raw


def test_authorization_refuses_seed_ledger_difference():
    ledger = _ledger()
    bad = list(ledger); bad[0] = dict(bad[0]); bad[0]["escalation_seed"] += 1
    with pytest.raises(C.QualificationCustodyRefused):
        C.sanitize_execution_authorization(_auth(bad), expected_seed_ledger=ledger)


def test_authorization_refuses_later_gate_permissions():
    ledger = _ledger()
    a = _auth(ledger); a["scoring_authorized"] = True
    with pytest.raises(C.QualificationCustodyRefused):
        C.sanitize_execution_authorization(a, expected_seed_ledger=ledger)


def test_fit_only_queue_derives_44_genes_without_world_labels():
    fit_view = {"resources": {"estimate": {"n_fits": 1056}}}
    index = {"world_count": 12, "worlds": [
        {"opaque_world_id": f"{i:012x}", "manifest_sha256": f"{i+1:064x}"} for i in range(12)
    ]}
    q = Q.build_qualification_queue(fit_view, index)
    assert len(q) == 1056
    assert max(x["gene_index"] for x in q) == 43
    raw = json.dumps(q)
    assert "world_name" not in raw and "world_index" not in raw and "Q00" not in raw and "Q11" not in raw
