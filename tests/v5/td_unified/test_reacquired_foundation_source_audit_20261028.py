"""No-promotion and arithmetic guards for the reacquired source audit receipt."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
J = ROOT / "results/target_discovery/unified_qualification_v1/JEPA_REACQUIRED_FOUNDATION_SOURCE_AUDIT_20261028.json"
C = ROOT / "results/target_discovery/unified_qualification_v1/JEPA_REACQUIRED_FOUNDATION_50K_OPERATOR_RESIDUALS_20261028.csv"


def test_receipt_sums_and_no_promotion():
    d = json.loads(J.read_text(encoding="utf-8"))
    by = d["expression_sample"]["residual_by_source"]
    assert sum(x["cells"] for x in by.values()) == 50000
    assert sum(x["physical_total"] for x in by.values()) == d["expression_sample"]["residual_overall"]["physical_total"]
    assert sum(x["mapped_total"] for x in by.values()) == d["expression_sample"]["residual_overall"]["mapped_total"]
    assert sum(x["residual_total"] for x in by.values()) == d["expression_sample"]["residual_overall"]["residual_total"]
    assert d["custody"]["bundle_manifest_rows_verified_exact_sha"] == 97
    assert d["expression_sample"]["integer_recovery"]["values_error_gt_1e_6"] == 0
    assert d["training_authorized"] is False
    assert d["project_stop"].endswith("STAGE4_NOT_AUTHORIZED")


def test_operator_csv_closes_to_source_totals():
    d = json.loads(J.read_text(encoding="utf-8"))
    rows = list(csv.DictReader(C.read_text(encoding="utf-8").splitlines()))
    assert len(rows) == 42
    for source, expected in d["expression_sample"]["residual_by_source"].items():
        rr = [r for r in rows if r["source"] == source]
        assert sum(int(r["cells"]) for r in rr) == expected["cells"]
        assert sum(int(r["physical_total"]) for r in rr) == expected["physical_total"]
        assert sum(int(r["mapped_total"]) for r in rr) == expected["mapped_total"]
        assert sum(int(r["residual_total"]) for r in rr) == expected["residual_total"]


def test_missing_nph_shards_are_recorded_not_silently_repaired():
    d = json.loads(J.read_text(encoding="utf-8"))
    x = d["expression_sample"]["expression_audit_shard_ledger"]
    assert x["missing_operator_indices"] == [35, 36, 37, 38, 39, 40, 41]
    assert x["omitted_cells"] == 5221
    assert x["omitted_nnz"] == 20448144

def test_alias_reacquisition_contract_is_minimal_hash_bound_and_fail_closed():
    d = json.loads(J.read_text(encoding="utf-8"))
    r = d["minimal_alias_reacquisition"]
    assert r["original_large_nph_qs_required"] is False
    assert len(r["nph_compact_feature_caches"]) == 7
    assert all(len(x["sha256"]) == 64 for x in r["nph_compact_feature_caches"])
    preferred = {x["path"]: x for x in r["preferred_exact_bytes"]}
    assert preferred[
        "results/v4/stage81a2r_unresolved_identity_reclassification_candidate.csv.gz"
    ]["sha256"] == "ebd216a1a2a46ffec64cd170f3752f822620efff7945e6d9bc8758f19e0947e6"
    final = preferred[
        "results/v4/stage81a2r_authoritative_source_mapping_decisions_candidate.csv.gz"
    ]
    assert final["accept_unhashed_by_filename"] is False
    assert r["adjudication_rule"]["query_key"] == "MOLECULAR_ADDRESS_ID"
    assert r["adjudication_rule"]["symbol_only_clearance_allowed"] is False
    assert r["adjudication_rule"]["unresolved_behavior"].startswith("FAIL_CLOSED")

