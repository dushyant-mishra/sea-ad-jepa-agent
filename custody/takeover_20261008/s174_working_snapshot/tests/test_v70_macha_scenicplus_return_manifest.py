import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"scripts/v64/validate_macha_scenicplus_return_manifest_v1.py"

def mod():
    s=importlib.util.spec_from_file_location("m",P); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def good():
    h="a"*64
    return {
      "schema":"X","date":"2026-10-01","producer_agent":"Macha","source_accession":"GSE214979",
      "acquisition":{
        "matrix":{"filename":"m.h5","bytes":1,"sha256":"1"*64,"recovery_url":"u"},
        "metadata":{"filename":"m.csv.gz","bytes":1,"sha256":"2"*64,"recovery_url":"u"},
        "fragments":{"filename":"f.tsv.gz","bytes":1,"sha256":"3"*64,"recovery_url":"u"},
        "genome_build":"hg38"},
      "development_population":{"celltype_field":"predicted.id","celltype_value":"Microglia","donor_field":"id",
        "all_microglia_n":3000,"development_microglia_n":2400,
        "prospective_overlap_exclusions":["1224","1230","1238"],
        "diagnosis_pathology_used_for_network_construction":False},
      "route_a":{"network_version":"A1","definition_source":"submitted_peaks","network_manifest_sha256":"4"*64,
        "program_table_path":"a","program_table_sha256":"5"*64,"donor_stability_receipt":"a","control_receipts":[],"status":"FROZEN"},
      "route_b":{"network_version":"B1","definition_source":"fragment_consensus","network_manifest_sha256":"6"*64,
        "program_table_path":"b","program_table_sha256":"7"*64,"donor_stability_receipt":"b","control_receipts":[],"status":"FROZEN"},
      "motif_resources":{"version":"v10"},
      "controls":{"tf_label_permutation":"x","annotation_supply":"x","matched_region_gene_permutation":"x",
        "structural_distinctness":"x","donor_fingerprint":"x","route_sensitivity":"x"},
      "frozen_programs":{"path":"p"},
      "crosswalks":{"contains_biological_effect_statistics":False},
      "environment":{"python":"3.x"},
      "governance":{"stage4_correspondence_opened":False,"morabito_biological_outcome_opened":False,
        "recoverability_test_opened":False,"training_started":False}
    }

def test_good_manifest_passes():
    assert mod().validate(good())==[]

def test_fragments_sha_required():
    x=good(); x["acquisition"]["fragments"].pop("sha256")
    assert any("MISSING_ACQUISITION:fragments:sha256" in e for e in mod().validate(x))

def test_pathology_network_selection_rejected():
    x=good(); x["development_population"]["diagnosis_pathology_used_for_network_construction"]=True
    assert "DIAGNOSIS_PATHOLOGY_MUST_NOT_DEFINE_NETWORK" in mod().validate(x)

def test_overlap_exclusion_contract_enforced():
    x=good(); x["development_population"]["prospective_overlap_exclusions"]=["1224"]
    assert "REQUIRED_PROSPECTIVE_OVERLAP_EXCLUSIONS_MISSING" in mod().validate(x)

def test_route_versions_and_tables_must_be_distinct():
    x=good(); x["route_b"]["network_version"]=x["route_a"]["network_version"]; x["route_b"]["program_table_sha256"]=x["route_a"]["program_table_sha256"]
    e=mod().validate(x)
    assert "ROUTE_VERSIONS_MUST_DIFFER" in e
    assert "ROUTE_PROGRAM_TABLES_MUST_BE_DISTINCT" in e

def test_protected_outcome_governance_enforced():
    x=good(); x["governance"]["stage4_correspondence_opened"]=True
    assert "GOVERNANCE_VIOLATION:stage4_correspondence_opened" in mod().validate(x)

def test_crosswalk_biological_effect_forbidden():
    x=good(); x["crosswalks"]["contains_biological_effect_statistics"]=True
    assert "CROSSWALKS_MUST_BE_STRUCTURAL_ONLY" in mod().validate(x)
