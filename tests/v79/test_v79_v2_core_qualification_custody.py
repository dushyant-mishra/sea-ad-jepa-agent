from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "scripts" / "v79"
sys.path.insert(0, str(HERE))

import v79_v2_core_qualification_custody as C  # noqa: E402


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
    ledger = [{"fit_id": f"{i:064x}", "primary_seed": i} for i in range(C.EXPECTED_FITS)]
    a = C.sanitize_execution_authorization(_auth(ledger), expected_seed_ledger=ledger)
    assert a["schema"] == "V79_V2_CORE_QUALIFICATION_EXECUTION_AUTHORIZATION_V1"
    assert len(a["fit_seed_ledger"]) == C.EXPECTED_FITS
    raw = json.dumps(a)
    for forbidden in ("Q00", "Q11", "world_name", "world_index", "controller_truth", "operator", "matrix"):
        assert forbidden not in raw


def test_authorization_refuses_seed_ledger_difference():
    ledger = [{"fit_id": f"{i:064x}", "primary_seed": i} for i in range(C.EXPECTED_FITS)]
    bad = list(ledger); bad[0] = dict(bad[0]); bad[0]["primary_seed"] += 1
    with pytest.raises(C.QualificationCustodyRefused):
        C.sanitize_execution_authorization(_auth(bad), expected_seed_ledger=ledger)


def test_authorization_refuses_later_gate_permissions():
    ledger = [{"fit_id": f"{i:064x}", "primary_seed": i} for i in range(C.EXPECTED_FITS)]
    a = _auth(ledger); a["scoring_authorized"] = True
    with pytest.raises(C.QualificationCustodyRefused):
        C.sanitize_execution_authorization(a, expected_seed_ledger=ledger)
