import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"results/v64/V70_GSE214979_FULL104_STRUCTURAL_CROSSWALK_V1.json"

def load(): return json.loads(P.read_text())

def test_exact_identity_counts_are_frozen():
    x=load()["exact_identity"]
    assert x["matched_addresses"]==35704
    assert x["unmatched_gse_gene_ids"]==897
    assert x["full104_addresses_not_exactly_covered"]==5534
    assert x["matched_identity_class_counts"]=={"current_exact":35445,"legacy_exact":259}

def test_exact_identity_arithmetic_reconciles():
    x=load(); e=x["exact_identity"]; s=x["sources"]
    assert e["matched_addresses"]+e["unmatched_gse_gene_ids"]==s["gse214979"]["genes"]
    assert e["matched_addresses"]+e["full104_addresses_not_exactly_covered"]==s["full104"]["canonical_addresses"]

def test_full104_support_reference_counts_match_authority():
    m=load()["measurement_support"]
    assert m["HVS"]["full104_any_measured_addresses"]==18736
    assert m["NPH52"]["full104_any_measured_addresses"]==35098
    assert m["NPH52"]["full104_all_operators_measured_addresses"]==29136
    assert m["SEA_AD"]["full104_any_measured_addresses"]==35076
    assert m["all_three_source_families"]["full104_measured_by_all_three"]==17346
    assert m["all_42_operators"]["full104_measured_by_all_42"]==17186

def test_gse_covers_nearly_all_common_full104_addresses():
    m=load()["measurement_support"]
    assert m["all_three_source_families"]["gse_exact_matched"]==17345
    assert m["all_42_operators"]["gse_exact_matched"]==17185
    assert m["all_three_source_families"]["coverage_fraction"]>0.9999
    assert m["all_42_operators"]["coverage_fraction"]>0.9999

def test_source_specific_measured_overlap_is_exact():
    m=load()["measurement_support"]
    assert m["HVS"]["gse_exact_matched_any_measured"]==17948
    assert m["NPH52"]["gse_exact_matched_any_measured"]==30203
    assert m["NPH52"]["gse_exact_matched_all_operators_measured"]==27015
    assert m["SEA_AD"]["gse_exact_matched_any_measured"]==35008

def test_provenance_is_explicitly_not_measurement_support():
    x=load()["provenance_vs_measurement_warning"]
    assert "provenance, not measurement support" in x["rule"]

def test_no_biological_claim_or_governance_change():
    x=load()
    assert x["status"].endswith("NO_BIOLOGICAL_EFFECT")
    assert x["governance"]["stage4"]=="NOT_AUTHORIZED"
    assert x["governance"]["correspondence"]=="UNOPENED"
    assert x["governance"]["Morabito"]=="PROTECTED"
