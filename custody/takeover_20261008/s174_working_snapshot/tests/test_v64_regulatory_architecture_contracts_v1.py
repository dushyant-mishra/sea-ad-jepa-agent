from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_regulatory_ledger_preserves_evidence_family_estimator_and_missingness():
    p = json.loads(
        (ROOT / "results/v64/V64_REGULATORY_EVIDENCE_LEDGER_SCHEMA_V1.json").read_text()
    )
    fields = set(p["evidence_record_fields"])
    assert {"measurement_source", "evidence_family", "estimator"}.issubset(fields)
    assert set(p["support_state_enum"]) == {
        "MEASURED_AND_SUPPORTS",
        "MEASURED_AND_DOES_NOT_SUPPORT",
        "NOT_MEASURED",
        "UNRESOLVED",
    }
    assert "NOT_MEASURED_TO_ZERO" in p["forbidden_collapses"]
    assert "ESTIMATOR_COUNT_TO_EVIDENCE_FAMILY_COUNT" in p["forbidden_collapses"]
    assert "RESOURCE_COUNT_TO_INDEPENDENCE_COUNT" in p["forbidden_collapses"]
    assert "PUBLIC_DOWNLOAD_TO_OPEN_LICENSE" in p["forbidden_collapses"]


def test_regulatory_ledger_carries_recoverability_and_provenance():
    p = json.loads(
        (ROOT / "results/v64/V64_REGULATORY_EVIDENCE_LEDGER_SCHEMA_V1.json").read_text()
    )
    assert "rna_recoverability_class" in p["recoverability_fields"]
    assert "artifact_sha256" in p["provenance_fields"]
    assert "access_status" in p["provenance_fields"]
    assert "license_terms_status" in p["provenance_fields"]
    assert "TERMS_UNKNOWN" in p["license_terms_status_enum"]


def test_heldout_family_contract_forbids_same_measurement_estimator_double_count():
    t = (
        ROOT / "docs/agent/V64_HELDOUT_EVIDENCE_FAMILY_VALIDATION_CONTRACT_20260930.md"
    ).read_text()
    assert "SCARlink and SCENT" in t
    assert "one paired-observational measurement family" in t
    assert "A new estimator on the same measurements is not a held-out evidence family" in t
    assert "Morabito remains protected" in t


def test_smoke_receipt_is_explicitly_nonbiological_and_training_off():
    p = json.loads(
        (ROOT / "results/v64/V64_PRIVILEGED_INFORMATION_ARCHITECTURE_SMOKE_RECEIPT_V1.json").read_text()
    )
    assert p["status"] == "SYNTHETIC_SOFTWARE_SMOKE_PASS__NOT_BIOLOGICAL_EVIDENCE"
    assert p["results"]["shared_mean_r2"] > 0.98
    assert p["results"]["private_mean_r2"] < 0.05
    assert p["results"]["forced_full_state_mean_r2"] < p["results"]["shared_mean_r2"] - 0.20
    assert p["rotation_aware_smoke"]["minimum_principal_angle_cosine"] > 0.99
    assert p["governance"]["training"] == "OFF"


def test_all_new_architecture_contracts_remain_non_authorizing():
    rec = json.loads(
        (ROOT / "results/v64/V64_PRIVILEGED_STATE_RECOVERABILITY_CONTRACT_V1.json").read_text()
    )
    ledger = json.loads(
        (ROOT / "results/v64/V64_REGULATORY_EVIDENCE_LEDGER_SCHEMA_V1.json").read_text()
    )
    audit = json.loads(
        (ROOT / "results/v64/V64_PRIVILEGED_INFORMATION_RUNTIME_AUDIT_V1.json").read_text()
    )
    for obj in (rec, ledger, audit):
        assert obj["governance"]["training"] == "OFF"
        assert obj["governance"]["phaseB"] == "STOPPED"
        assert obj["governance"]["stage4"] in {"NOT_AUTHORIZED", "NOT_AUTHORISED"}
