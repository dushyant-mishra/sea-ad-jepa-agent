from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

import td_v79_c6_synthetic_extension_v1 as C6X  # noqa: E402

REGISTRY = ROOT / "results" / "target_discovery" / "synthetic_crosswalk" / "TD_V79_C6_SYNTHETIC_EXTENSION_V1.json"


def registry():
    return C6X.load_registry(REGISTRY)


def test_registry_exact_candidate_contract_and_no_authority():
    reg = registry()
    C6X.validate_registry(reg)
    assert reg["candidate_id"] == "C6_SHARED_QUERY_COMPOSITE"
    assert reg["synthetic_contract_sha256"] == C6X.EXPECTED_CONTRACT_SHA256
    assert all(v is False for v in reg["authority"].values())


def test_c6_increment_truth_is_mandatory_not_estimable():
    reg = registry()
    claim = next(x for x in reg["claims"] if x["claim"] == "C6_INCREMENT_OVER_C1_C3_BIOLOGICAL_TRUTH")
    assert claim["evidence_class"] == "NOT_ESTIMABLE"
    assert claim["worlds"] == []
    assert claim["required_truth_fields"] == []


def test_decisive_claims_have_explicit_truth_and_known_worlds():
    reg = registry()
    for claim in reg["claims"]:
        if claim["evidence_class"].startswith("DECISIVE"):
            assert claim["worlds"]
            assert claim["required_truth_fields"]
            assert set(claim["worlds"]) <= set(C6X.EXACT_WORLDS)


def _receipt(decisive_status="PASS"):
    reg = registry()
    results = []
    for claim in reg["claims"]:
        status = "NOT_ESTIMABLE" if claim["evidence_class"] == "NOT_ESTIMABLE" else decisive_status
        evidence = [] if status == "NOT_ESTIMABLE" else [
            {"world": w, "truth_manifest_sha256": "a" * 64, "result_sha256": "b" * 64}
            for w in claim["worlds"]
        ]
        results.append({
            "claim": claim["claim"],
            "evidence_class": claim["evidence_class"],
            "status": status,
            "world_evidence": evidence,
        })
    return {
        "schema": C6X.RECEIPT_SCHEMA,
        "candidate_id": "C6_SHARED_QUERY_COMPOSITE",
        "registry_sha256": C6X.canonical_sha256(reg),
        "synthetic_contract_sha256": C6X.EXPECTED_CONTRACT_SHA256,
        "claim_results": results,
        "authority": {k: False for k in C6X.AUTHORITY_KEYS},
    }


def test_receipt_requires_complete_exact_c6_claim_set():
    reg = registry()
    rec = _receipt()
    C6X.validate_receipt(rec, reg)
    bad = copy.deepcopy(rec)
    bad["claim_results"].pop()
    with pytest.raises(C6X.C6SyntheticExtensionError):
        C6X.validate_receipt(bad, reg)


def test_receipt_cannot_copy_wrong_candidate_or_wrong_contract():
    reg = registry()
    bad = _receipt()
    bad["candidate_id"] = "C1_SHARED_EMERGENT"
    with pytest.raises(C6X.C6SyntheticExtensionError):
        C6X.validate_receipt(bad, reg)
    bad = _receipt()
    bad["synthetic_contract_sha256"] = "c" * 64
    with pytest.raises(C6X.C6SyntheticExtensionError):
        C6X.validate_receipt(bad, reg)


def test_decisive_result_requires_exact_world_evidence_and_not_estimable_forbids_fake_evidence():
    reg = registry()
    bad = _receipt()
    first = next(x for x in bad["claim_results"] if x["evidence_class"].startswith("DECISIVE"))
    first["world_evidence"].pop()
    with pytest.raises(C6X.C6SyntheticExtensionError):
        C6X.validate_receipt(bad, reg)

    bad = _receipt()
    ne = next(x for x in bad["claim_results"] if x["status"] == "NOT_ESTIMABLE")
    ne["world_evidence"] = [{"world": "Q00_BASELINE", "truth_manifest_sha256": "a" * 64, "result_sha256": "b" * 64}]
    with pytest.raises(C6X.C6SyntheticExtensionError):
        C6X.validate_receipt(bad, reg)


def test_real_fail_or_not_estimable_cannot_be_rescued_and_decisive_fail_can_eliminate_real_pass():
    reg = registry()
    good = _receipt("PASS")
    assert C6X.combine("FAIL", good, reg) == "ELIMINATED_REAL_FAIL"
    assert C6X.combine("NOT_ESTIMABLE", good, reg) == "UNRESOLVED_REAL_NOT_ESTIMABLE"

    failed = _receipt("PASS")
    decisive = next(x for x in failed["claim_results"] if x["evidence_class"].startswith("DECISIVE"))
    decisive["status"] = "FAIL"
    assert C6X.combine("PASS", failed, reg) == "ELIMINATED_SYNTHETIC_FALSIFIER"
    assert C6X.combine("PASS", good, reg) == "ELIGIBLE_PENDING_TARGET_SELECTION"


def test_diagnostic_fail_does_not_eliminate_c6():
    reg = registry()
    rec = _receipt("PASS")
    diag = next(x for x in rec["claim_results"] if x["evidence_class"] == "DIAGNOSTIC")
    diag["status"] = "FAIL"
    assert C6X.combine("PASS", rec, reg) == "ELIGIBLE_PENDING_TARGET_SELECTION"
