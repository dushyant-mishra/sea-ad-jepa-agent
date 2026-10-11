import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "v5_anticheat" / "validate_full104_dimension_metric_receipt_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("full104_dimension_metric_receipt_v1", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def good_receipt():
    sha = "a" * 64
    precision = "b" * 64
    rows = []
    for rank in range(1, 5):
        rows.append({
            "rank": rank,
            "replicates": 1234,
            "physical_binding_sha256": sha,
            "precision_authority_sha256": precision,
            "full_stream": True,
            "fixture": False,
            "matched_null_full_refit": True,
            "held_donor": True,
            "held_operator": True,
        })
    return {
        "schema": "V5_FULL104_DIMENSION_METRIC_RECEIPT_V1",
        "physical_binding_terminal": "PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE",
        "physical_binding_sha256": sha,
        "precision_authority_sha256": precision,
        "precision_replicates": 1234,
        "rank_rows": rows,
        "training_authorized": False,
        "test_fixture_mode": False,
        "synthetic_data_used": False,
    }


def test_good_metric_receipt_passes_but_never_authorizes_training():
    m = load_module()
    out = m.validate_metric_receipt(good_receipt())
    assert out["lawful"] is True
    assert out["terminal"] == "PASS_FULL104_DIMENSION_METRIC_RECEIPT_MECHANICS__NO_DIMENSION_AUTHORITY"
    assert out["training_authorized"] is False
    assert out["dimension_selected"] is False


def test_receipt_rejects_fixture_or_synthetic_metrics():
    m = load_module()
    for key in ("test_fixture_mode", "synthetic_data_used"):
        rec = good_receipt(); rec[key] = True
        out = m.validate_metric_receipt(rec)
        assert out["lawful"] is False


def test_receipt_rejects_nonconsecutive_rank_sweep():
    m = load_module(); rec = good_receipt(); rec["rank_rows"][2]["rank"] = 5
    assert m.validate_metric_receipt(rec)["lawful"] is False


def test_receipt_rejects_arbitrary_replicate_count():
    m = load_module(); rec = good_receipt(); rec["rank_rows"][1]["replicates"] = 999
    out = m.validate_metric_receipt(rec)
    assert out["lawful"] is False
    assert "replicate" in out["reason"]


def test_receipt_rejects_mismatched_parent_hashes():
    m = load_module(); rec = good_receipt(); rec["rank_rows"][0]["physical_binding_sha256"] = "c" * 64
    assert m.validate_metric_receipt(rec)["lawful"] is False
    rec = good_receipt(); rec["rank_rows"][0]["precision_authority_sha256"] = "c" * 64
    assert m.validate_metric_receipt(rec)["lawful"] is False


def test_receipt_requires_full_refit_null_and_both_holdout_axes():
    m = load_module()
    for key in ("matched_null_full_refit", "held_donor", "held_operator", "full_stream"):
        rec = good_receipt(); rec["rank_rows"][0][key] = False
        assert m.validate_metric_receipt(rec)["lawful"] is False


def test_receipt_cannot_self_authorize_training():
    m = load_module(); rec = good_receipt(); rec["training_authorized"] = True
    assert m.validate_metric_receipt(rec)["lawful"] is False
