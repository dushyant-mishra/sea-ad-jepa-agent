import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CAND=ROOT/"docs"/"agent"/"TEACHER_STUDENT_V5_FULL_POPULATION_HORIZON_CANDIDATE_V3.json"
DERIVE=ROOT/"scripts"/"v5_anticheat"/"derive_full_population_schedule_optimum_v3.py"
MAT=ROOT/"scripts"/"v5_anticheat"/"materialize_full_population_schedule_v4.py"

def test_real_full_reader_candidate_is_bound_and_not_synthetic():
    o=json.loads(CAND.read_text())
    assert o["authenticated_population"]=={
        "metadata_sqlite_sha256":"a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913",
        "partition":"reader_fit","cells":4553407,"unique_stable_keys":4553407,
        "donors":104,"donor_operator_groups":1400,
    }
    assert o["synthetic_data_used_for_authority"] is False
    assert o["pathology_used"] is False
    assert o["checkpoint_outcomes_used"] is False
    assert o["training_authorized"] is False

def test_exact_schedule_boundary_is_pinned():
    o=json.loads(CAND.read_text()); r=o["exact_dataset_result"]
    assert r["total_presentations"]==5267086
    assert r["previous_total_presentations"]==5267085
    assert r["importance_ess_fraction"]>0.5
    assert r["previous_importance_ess_fraction"]<0.5
    assert r["maximum_cell_multiplicity"]==32
    assert r["minimum_group_presentations"]==16
    assert r["importance_weight_ratio"]=={"numerator":58037,"denominator":864,"float":67.17245370370371}

def test_raw_and_domain_bound_ledger_digests_are_not_conflated():
    x=json.loads(CAND.read_text())["canonical_cell_ledger"]
    assert x["raw_sha256"]=="e05f4a524748cf427b1c3e899a5b672641566c772aa91da8a2a56dae2b9a3c97"
    assert x["domain_bound_sha256"]=="23a5c52e2b472604a9e32c71e114b4752094950180c8d155c7ee45dd95ce8c23"
    assert x["raw_sha256"]!=x["domain_bound_sha256"]
    assert x["replayed_byte_identically_twice"] is True

def test_scientific_constraints_are_cli_authorities_not_hidden_current_values():
    derive=DERIVE.read_text()
    materialize=MAT.read_text()
    for flag in ("--expected-cells","--expected-donors","--expected-groups","--group-floor","--cell-cap","--ess-floor-numerator","--ess-floor-denominator","--partition"):
        assert flag in derive
    assert "partition='reader_fit'" not in derive
    assert "partition='reader_fit'" not in materialize
    assert "max(0,16-" not in materialize
    assert "==104" not in derive
    assert "4553407" not in derive
    assert "synthetic_data_used_for_authority" in derive
    assert "synthetic_data_used_for_authority" in materialize
