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

def test_mechanical_query_observability_uses_scalar_state_not_coarse_measured_boolean():
    d = json.loads(J.read_text(encoding="utf-8"))
    m = d["mechanical_query_observability"]
    p = m["pair_counts"]
    assert p["total"] == 42 * 41238
    assert p["measured_scalar"] + p["measured_collision_unresolved"] + p["structurally_unmeasured"] == p["total"]
    assert m["query_rule"]["eligible_state"] == "MEASURED_SCALAR"
    assert "MEASURED_COLLISION_UNRESOLVED" in m["query_rule"]["refused_states"]
    assert m["query_rule"]["symbol_inference_allowed"] is False
    assert m["query_rule"]["cross_operator_inference_allowed"] is False
    assert m["query_rule"]["source_rights_inferred"] is False
    assert m["address_counts"]["measured_scalar_any_operator"] == 40949
    assert m["address_counts"]["measured_scalar_all_42_operators"] == 17186


def test_mechanical_source_family_coverage_closes_to_scalar_pair_total():
    d = json.loads(J.read_text(encoding="utf-8"))
    m = d["mechanical_query_observability"]
    assert sum(x["scalar_pairs"] for x in m["by_source_family"].values()) == m["pair_counts"]["measured_scalar"]
    assert sum(m["source_family_presence_patterns"].values()) == m["address_counts"]["total"]
    assert sum(x["addresses"] for x in m["by_identity_class"].values()) == m["address_counts"]["total"]


def test_qc_selection_remains_fail_closed():
    d = json.loads(J.read_text(encoding="utf-8"))
    q = d["qc_selection_audit"]
    assert q["status"] == "NOT_RECOVERED__FAIL_CLOSED"
    assert q["explicit_depositor_qc_policy_found"] is False
    assert q["rights_effect"] == "NONE__NO_QUERY_RIGHTS_ISSUED"
    assert "ABSENCE_IN_PACKAGE_DOES_NOT_PROVE_UPSTREAM_QC_ABSENT" in q["inference"]

def test_provenance_reacquisition_does_not_invent_specimen_identity():
    d = json.loads(J.read_text(encoding="utf-8"))
    p = d["provenance_metadata_reacquisition"]
    assert p["HVS"]["matrices_scanned"] == 24
    assert p["SEA_AD"]["matrices_scanned"] == 11
    assert p["SEA_AD"]["sample_id_matrices"] == 10
    assert p["NPH52"]["sample_or_specimen_field_observed"] is False
    policy = p["policy"]
    assert policy["expression_values_required"] is False
    assert policy["pathology_values_required"] is False
    assert policy["matrix_id_may_substitute_for_specimen"] is False
    assert policy["exp_component_name_may_substitute_for_specimen"] is False
    assert policy["source_object_may_substitute_for_specimen"] is False
    assert policy["specimen_identity_status"] == "NOT_QUALIFIED"

