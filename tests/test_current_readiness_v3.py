"""V3 registry and versioned readiness overlay; historical receipts immutable."""
from __future__ import annotations

import copy
import csv
import importlib.util
import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "analysis/therapeutic_perturbation_etl"
S = BASE / "scripts/publish_current_readiness_v3.py"
spec = importlib.util.spec_from_file_location("ready_v3", S)
import sys
sys.path.insert(0, str(S.parent))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def sandbox(tmp_path):
    """Copy only the 9 small source files needed for a completely isolated test."""
    d = tmp_path / "analysis"
    for rel in [mod.V2, mod.V3, mod.INV, mod.CROSS, mod.MATRIX, *mod.RECEIPTS.values()]:
        src = BASE / rel
        dest = d / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
    return d


def test_real_committed_v3_all_four_receipts_green():
    x = mod.verified_inputs(BASE)
    assert x["v3_sha256"] != x["v2_sha256"]
    assert len(x["receipt_sha256"]) == 4
    assert x["assertions"]["GSE335887"]["outcome_exposure"] == "UNOPENED_RESERVED"


def test_historical_v2_fails_exactly_six_stale_assertions():
    checker = __import__("audit_receipt_readiness_consistency_v1")
    registry = mod.load(BASE / mod.V2)
    evidence = {k: mod.load(BASE / v) for k, v in mod.RECEIPTS.items()}
    errors = checker.check(registry, evidence)
    assert set(errors) == {
        "GSE301119_STATUS_MUST_BE_IMPLEMENTATION_REPRODUCED_NOT_INDEPENDENT",
        "GSE254205_STATUS_STALE_OR_OVERCLAIMED",
        "GSE178317_STATUS_STALE_OR_OVERCLAIMED",
        "GSE311359_V2_REBUILD_STATUS_STALE",
        "GSE311359_BIOLOGICAL_SCOPE_STATUS_STALE",
        "GSE311359_INDEPENDENCE_OVERCLAIMED_OR_STALE",
    }


def test_overlay_csv_and_receipt_published_without_physical_recompute(tmp_path):
    d = sandbox(tmp_path)
    out = tmp_path / "current_v3"
    mod.publish(d, out)
    a = json.loads((out / "CURRENT_READINESS_OVERLAY_RECEIPT_V3.json").read_text())
    with (out / "CURRENT_CURATOR_ASSERTIONS_V3.csv").open(newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 9
    assert a["computed_matrix_rederived"] is False
    assert a["curator_assertions_v3_csv_sha256"] == mod.sha256(
        out / "CURRENT_CURATOR_ASSERTIONS_V3.csv")
    assert a["historical_cross_study_v2_computed_matrix_sha256"] == mod.sha256(d / mod.MATRIX)
    assert a["protected_outcome_opened"] is False
    assert a["training_authorized"] is False
    assert a["therapeutic_ranking"] is False
    assert (BASE / mod.MATRIX).read_bytes() == (d / mod.MATRIX).read_bytes()


def test_no_overwrite_after_first_publication(tmp_path):
    d = sandbox(tmp_path)
    out = tmp_path / "published"
    mod.publish(d, out)
    before = (out / "CURRENT_READINESS_OVERLAY_RECEIPT_V3.json").read_bytes()
    with pytest.raises(ValueError, match="STOP_OUTPUT_EXISTS"):
        mod.publish(d, out)
    assert (out / "CURRENT_READINESS_OVERLAY_RECEIPT_V3.json").read_bytes() == before


def test_cannot_promote_implementation_to_independent(tmp_path):
    d = sandbox(tmp_path)
    p = d / mod.V3
    a = mod.load(p)
    a["assertions"]["GSE301119"]["independent_reproduction"] = "INDEPENDENT_REPRODUCED"
    p.write_text(json.dumps(a))
    with pytest.raises(ValueError, match="STOP_UNEXPECTED_V3_STATUS"):
        mod.verified_inputs(d)


def test_protected_exposure_cannot_change(tmp_path):
    d = sandbox(tmp_path)
    p = d / mod.V3
    a = mod.load(p)
    a["assertions"]["GSE335887"]["outcome_exposure"] = "INSPECTED_DEVELOPMENT"
    p.write_text(json.dumps(a))
    with pytest.raises(ValueError, match="STOP_PROTECTED_OR_BIOLOGICAL_SCOPE_CHANGED"):
        mod.verified_inputs(d)


def test_unrelated_biological_status_cannot_change(tmp_path):
    d = sandbox(tmp_path)
    p = d / mod.V3
    a = mod.load(p)
    a["assertions"]["GSE240609"]["biological_estimability"] = "CLONE_LEVEL_ESTIMABLE"
    p.write_text(json.dumps(a))
    with pytest.raises(ValueError, match="STOP_UNEXPECTED_V3_STATUS"):
        mod.verified_inputs(d)


def test_old_registry_digest_mismatch_stops(tmp_path):
    d = sandbox(tmp_path)
    p = d / mod.V2
    p.write_bytes(p.read_bytes() + b" ")
    with pytest.raises(ValueError, match="STOP_HISTORICAL_V2_REGISTRY_DIGEST_DRIFT"):
        mod.verified_inputs(d)


def test_receipt_blob_substitution_stops(tmp_path):
    d = sandbox(tmp_path)
    p = d / mod.RECEIPTS["GSE301119"]
    a = mod.load(p)
    a["synthetic_sign_checks"]["planted_signs"]["gFLAT"] = 0.0
    p.write_text(json.dumps(a))
    with pytest.raises(ValueError, match="STOP_UNBOUND_V3_RECEIPT"):
        mod.verified_inputs(d)


def test_cross_study_computed_matrix_changed_stops(tmp_path):
    d = sandbox(tmp_path)
    p = d / mod.MATRIX
    p.write_bytes(p.read_bytes() + b"\nFAKE")
    with pytest.raises(ValueError, match="STOP_HISTORICAL_COMPUTED_MATRIX_DRIFT"):
        mod.verified_inputs(d)


def test_historical_inventory_embedded_registry_tamper_stops(tmp_path):
    d = sandbox(tmp_path)
    p = d / mod.INV
    a = mod.load(p)
    a["curator_assertions"]["entries"]["GSE175721"]["etl_status"] = "PASS"
    p.write_text(json.dumps(a))
    with pytest.raises(ValueError, match="STOP_HISTORICAL_INVENTORY_ASSERTIONS_CHANGED"):
        mod.verified_inputs(d)


def test_missing_physical_receipt_refuses_publication(tmp_path):
    d = sandbox(tmp_path)
    (d / mod.RECEIPTS["GSE311359"]).unlink()
    out = tmp_path / "would_be_v3"
    with pytest.raises(ValueError, match="MISSING_EVIDENCE"):
        mod.publish(d, out)
    assert not out.exists()


def test_v3_gse301119_estimand_hold_explicit():
    a = mod.load(BASE / mod.V3)["assertions"]["GSE301119"]
    assert a["scientific_estimand_status"].startswith("HOLD_")
    assert a["independent_reproduction"] == "IMPLEMENTATION_REPRODUCED"


def test_v3_does_not_claim_full_precision():
    a = mod.load(BASE / mod.V3)["assertions"]["GSE254205"]
    assert a["independent_reproduction"] == "IMPLEMENTATION_REPRODUCED_TO_STORED_PRECISION"
    assert a["outcome_exposure"] == "INSPECTED_DEVELOPMENT_BULK_THREE_CONTRASTS_ONLY"
