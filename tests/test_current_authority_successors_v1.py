import hashlib
import pytest

from sea_ad_jepa.v5.biological_specificity_authority_v1 import BiologicalSpecificityAuthorityV1
from sea_ad_jepa.v5.q_safety_authority_v1 import QSafetyAuthorityV1
from sea_ad_jepa.v5.critical_test_execution_authority_v2 import (
    CriticalTestExecutionAuthorityV2,
    CriticalTestExecutionReceiptV1,
)
from sea_ad_jepa.v5.current_authority_roots_v3 import CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V3

H = hashlib.sha256(b"x").hexdigest()


def test_roots_include_specificity_qsafety_and_execution():
    assert "biological_specificity_authority_sha256" in CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V3
    assert "q_safety_authority_sha256" in CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V3
    assert "critical_test_execution_authority_sha256" in CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS_V3


def test_biological_specificity_fail_closed():
    a = BiologicalSpecificityAuthorityV1("bio", H, H, H, H, "qualified_nuisance_class_only", True, True)
    a.validate()
    assert len(a.canonical_digest()) == 64

    with pytest.raises(ValueError):
        BiologicalSpecificityAuthorityV1("bio", H, H, H, H, "scope", False, True).validate()

    with pytest.raises(ValueError):
        BiologicalSpecificityAuthorityV1("bio", H, H, H, H, "scope", True, False).validate()


def test_q_safety_only_allows_known_paths_and_blind_teacher():
    q = QSafetyAuthorityV1("q", "q_excluded_total__q_token_dropped", H, H, True, True, True)
    q.validate()
    assert len(q.canonical_digest()) == 64

    with pytest.raises(ValueError):
        QSafetyAuthorityV1("q", "naive_full_total__q_token_dropped", H, H, True, True, True).validate()

    with pytest.raises(ValueError):
        QSafetyAuthorityV1("q", "fixed_reference__q_token_dropped", H, H, False, True, True).validate()


def _receipt(test_id="t1", source=H, exit_code=0, passed=True):
    return CriticalTestExecutionReceiptV1(
        test_id=test_id,
        provider_id="github-actions",
        provider_run_id="123",
        provider_run_locator="repo/actions/runs/123",
        test_source_sha256=source,
        command_sha256=H,
        stdout_sha256=H,
        stderr_sha256=H,
        artifact_manifest_sha256=H,
        provider_attestation_sha256=H,
        exit_code=exit_code,
        passed=passed,
    )


def test_critical_execution_requires_receipts_not_status_strings():
    a = CriticalTestExecutionAuthorityV2("crit", ["t1"], H, {"t1": _receipt()})
    a.validate()
    assert len(a.canonical_digest()) == 64

    with pytest.raises(ValueError):
        CriticalTestExecutionAuthorityV2("crit", ["t1"], H, {"t1": "EXECUTED_PASS"}).validate()

    with pytest.raises(ValueError):
        CriticalTestExecutionAuthorityV2("crit", ["t1"], H, {"t1": _receipt(exit_code=1)}).validate()

    other = hashlib.sha256(b"other").hexdigest()
    with pytest.raises(ValueError):
        CriticalTestExecutionAuthorityV2("crit", ["t1"], H, {"t1": _receipt(source=other)}).validate()
