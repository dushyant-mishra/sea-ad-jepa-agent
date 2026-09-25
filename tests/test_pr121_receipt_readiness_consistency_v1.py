"""Adversarial, zero-skip validation of PR121 receipt/readiness consistency.

The committed historical V2 is EXPECTED TO FAIL. A positive fixture has only
its four affected statuses corrected; receipts and sealed boundaries stay fixed.
No heavyweight experiment or reserved outcome is opened.
"""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "analysis/therapeutic_perturbation_etl"
PATH = SRC / "scripts/audit_receipt_readiness_consistency_v1.py"
spec = importlib.util.spec_from_file_location("readiness_check", PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def inputs():
    registry = mod.load(SRC / mod.REGISTRY)
    receipts = {key: mod.load(SRC / val) for key, val in mod.RECEIPTS.items()}
    return registry, receipts


def corrected_fixture():
    registry, receipts = inputs()
    registry = copy.deepcopy(registry)
    a = registry["assertions"]
    a["GSE301119"]["independent_reproduction"] = "IMPLEMENTATION_REPRODUCED"
    a["GSE254205"]["independent_reproduction"] = "IMPLEMENTATION_REPRODUCED_TO_STORED_PRECISION"
    a["GSE178317"]["independent_reproduction"] = "IMPLEMENTATION_REPRODUCED_TO_STORED_PRECISION"
    a["GSE311359"]["etl_status"] = "PASS_DEVELOPMENT_ETL_ID_KEYED"
    a["GSE311359"]["biological_estimability"] = "SEQUENCE_IDENTITY_UNPROVEN_CIS_CAUSALITY_UNPROVEN"
    a["GSE311359"]["independent_reproduction"] = "ID_KEYED_V1_NONBIN1_PARITY_ONLY"
    return registry, receipts


def test_positive_control_corrected_fixture_passes():
    registry, receipts = corrected_fixture()
    assert mod.check(registry, receipts) == []


def test_real_v2_currently_fails_for_expected_stale_claims():
    registry, receipts = inputs()
    errors = set(mod.check(registry, receipts))
    assert errors == {
        "GSE301119_STATUS_MUST_BE_IMPLEMENTATION_REPRODUCED_NOT_INDEPENDENT",
        "GSE254205_STATUS_STALE_OR_OVERCLAIMED",
        "GSE178317_STATUS_STALE_OR_OVERCLAIMED",
        "GSE311359_V2_REBUILD_STATUS_STALE",
        "GSE311359_BIOLOGICAL_SCOPE_STATUS_STALE",
        "GSE311359_INDEPENDENCE_OVERCLAIMED_OR_STALE",
    }


def test_false_independence_promotion_rejected():
    registry, receipts = corrected_fixture()
    registry["assertions"]["GSE301119"]["independent_reproduction"] = "INDEPENDENT_REPRODUCED"
    assert any("GSE301119_STATUS_" in x for x in mod.check(registry, receipts))


def test_numerical_receipt_tamper_rejected():
    registry, receipts = corrected_fixture()
    receipts["GSE301119"]["modalities"]["CRISPRi"]["per_donor_max_abs_delta"]["D1"] = 2e-8
    assert "GSE301119_UNQUALIFIED_RECEIPT_CRISPRi" in mod.check(registry, receipts)


def test_swapped_sign_control_missing_rejected():
    registry, receipts = corrected_fixture()
    receipts["GSE301119"]["synthetic_sign_checks"]["swapped_numerator_denominator_negates_ok"] = False
    assert "GSE301119_SIGN_CONTROLS_NOT_DEMONSTRATED" in mod.check(registry, receipts)


def test_rounding_is_not_full_precision():
    registry, receipts = corrected_fixture()
    receipts["GSE254205"]["declared_tolerance_met_at_full_precision"] = True
    assert "GSE254205_RECEIPT_NOT_STORED_PRECISION_REPRODUCED" in mod.check(registry, receipts)


def test_bin1_phantom_reappearance_rejected():
    registry, receipts = corrected_fixture()
    receipts["GSE311359"]["phantom_units_detected"] = 14
    assert "GSE311359_RECEIPT_NOT_ID_KEYED_QUALIFIED" in mod.check(registry, receipts)


def test_preserve_reserved_and_author_stop():
    registry, receipts = corrected_fixture()
    registry["assertions"]["GSE335887"]["outcome_exposure"] = "INSPECTED_DEVELOPMENT"
    registry["assertions"]["GSE175721"]["etl_status"] = "PASS_DEVELOPMENT_ETL"
    errors = mod.check(registry, receipts)
    assert "GSE335887_PROTECTED_EXPOSURE_PROMOTED" in errors
    assert "GSE175721_AUTHOR_SOURCE_STOP_REMOVED" in errors


def test_missing_receipt_fail_closed():
    registry, receipts = corrected_fixture()
    receipts.pop("GSE178317")
    assert "MISSING_REQUIRED_RECEIPT" in mod.check(registry, receipts)


def test_cli_exit_codes_and_no_rewrite(tmp_path):
    registry, receipts = corrected_fixture()
    for study, rel in mod.RECEIPTS.items():
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(json.dumps(receipts[study]), encoding="utf-8")
    rp = tmp_path / mod.REGISTRY
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(json.dumps(registry), encoding="utf-8")
    old = rp.read_bytes()
    assert mod.main(["--root", str(tmp_path)]) == 0
    assert rp.read_bytes() == old
    registry["assertions"]["GSE311359"]["etl_status"] = "STOP_PENDING_PHYSICAL_V2_REBUILD"
    rp.write_text(json.dumps(registry), encoding="utf-8")
    assert mod.main(["--root", str(tmp_path)]) == 1
