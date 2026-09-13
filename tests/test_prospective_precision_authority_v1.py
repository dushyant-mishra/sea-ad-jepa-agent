import hashlib
import json
from pathlib import Path

import pytest

from sea_ad_jepa.v5.prospective_precision_authority_v1 import (
    PrecisionAuthorityStop,
    canonical_precision_authority_bytes,
    derive_hoeffding_fixed_n,
    validate_precision_authority_v1,
)

FROZEN_AUTHORITY_SHA256 = "cc4ac4d5116fa81990f1c3bd0497fc578eda86bb2d7d3cd2747abcf7ffcf9428"
FROZEN_AUTHORITY_PATH = Path(__file__).resolve().parents[1] / "docs" / "agent" / "V5_PROSPECTIVE_DIMENSION_PRECISION_AUTHORITY_V1.json"


def authority():
    quantities = []
    for qid, lo, hi, tol, kind in [
        ("shared_matched_null_exceedance", 0.0, 1.0, 0.025, "null"),
        ("shared_subspace_stability", 0.0, 1.0, 0.05, "donor"),
        ("shared_held_donor_cross_view_predictability", -1.0, 1.0, 0.05, "donor"),
        ("shared_independent_view_agreement", 0.0, 1.0, 0.05, "donor"),
        ("shared_measurement_shortcut_increment", -1.0, 1.0, 0.05, "donor"),
        ("private_held_donor_increment", -1.0, 1.0, 0.05, "donor"),
        ("private_held_operator_increment", -1.0, 1.0, 0.05, "operator"),
        ("private_measurement_shortcut_increment", -1.0, 1.0, 0.05, "donor"),
        ("private_same_cell_technical_intervention_stability", 0.0, 1.0, 0.05, "donor"),
        ("observation_held_operator_reconstruction", 0.0, 1.0, 0.05, "operator"),
    ]:
        alpha = 0.005
        quantities.append({
            "quantity_id": qid,
            "resampling_kind": kind,
            "lower_bound": lo,
            "upper_bound": hi,
            "absolute_precision_tolerance": tol,
            "risk_allocation": alpha,
            "replicates": derive_hoeffding_fixed_n(hi - lo, tol, alpha),
        })
    return {
        "schema": "JEPA_V5_PROSPECTIVE_DIMENSION_PRECISION_AUTHORITY_V1",
        "status": "FROZEN_BEFORE_DIMENSION_OUTCOME_ACCESS",
        "method": "HOEFFDING_FIXED_N_V1",
        "familywise_precision_risk": 0.05,
        "risk_allocation_method": "BONFERRONI_EQUAL_10",
        "decision_metric_population": "UNCONDITIONAL_OVER_DECLARED_EVALUATION_POPULATION",
        "estimator_failure_policy": "FAILURE_COUNTS_AS_NONQUALIFYING_AND_IS_REPORTED_SEPARATELY",
        "survivor_only_intervals_forbidden": True,
        "precision_is_not_effect_criterion": True,
        "post_outcome_replication_tuning_forbidden": True,
        "gate_ablation_required": True,
        "redundancy_identity_check_required": True,
        "rng_replay_policy": "SHA256_PARENT_QUANTITY_REPLICATE_INDEX_V1",
        "outcomes_inspected_before_freeze": False,
        "checkpoint_outcomes_used": False,
        "pathology_used": False,
        "protected_data_used": False,
        "training_authorized": False,
        "dimension_outcomes_used": False,
        "full104_parent_bindings": {
            "block_manifest_sha256": "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29",
            "materialization_contract_sha256": "612b45742ad80498cbe2f061a75af08c0a10692dc731e0ac8e649417b7e62f17",
            "materialization_audit_sha256": "9fa0ede3135a606bb1fe4cd4cc11881c439b7726b6dec62147c1892967eba7cf",
            "selection_sha256": "edec0fe29d1425ecbe9fa889a610c4ce18621ae060c8144866315db57c3fc62b",
            "selection_manifest_sha256": "3db3614bf544b183143f39b27bad516b3a7a75284df4b2410d9f3e99f0b0842e",
            "metadata_sqlite_sha256": "a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913",
        },
        "dimension_interface_sha256": "dcc8c95ef8ed4b8106ee3b8f1536aa6fac6b338cafd3057b9f567a5336c673df",
        "code_lineage_base_commit_sha": "9001b0cc7bb9b2b548adef86bb3b423e80668b35",
        "quantities": quantities,
    }


def test_hoeffding_fixed_n_is_derived_not_inherited():
    assert derive_hoeffding_fixed_n(1.0, 0.025, 0.005) == 4794
    assert derive_hoeffding_fixed_n(1.0, 0.05, 0.005) == 1199
    assert derive_hoeffding_fixed_n(2.0, 0.05, 0.005) == 4794
    assert derive_hoeffding_fixed_n(1.0, 0.025, 0.005) not in {256, 999, 1000}


def test_frozen_authority_passes_and_reports_execution_counts():
    out = validate_precision_authority_v1(authority())
    assert out["terminal"] == "PASS_V5_PROSPECTIVE_PRECISION_AUTHORITY_V1"
    assert out["full_refit_null_replicates"] == 4794
    assert out["donor_resamples"] == 4794
    assert out["operator_resamples"] == 4794
    assert out["quantity_count"] == 10


def test_frozen_file_is_exact_canonical_authority():
    raw = FROZEN_AUTHORITY_PATH.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == FROZEN_AUTHORITY_SHA256
    obj = json.loads(raw)
    assert raw == canonical_precision_authority_bytes(obj)
    out = validate_precision_authority_v1(obj)
    assert out["terminal"] == "PASS_V5_PROSPECTIVE_PRECISION_AUTHORITY_V1"


def test_hand_entered_historical_count_cannot_masquerade_as_precision_derived():
    x = authority()
    x["quantities"][0]["replicates"] = 999
    with pytest.raises(PrecisionAuthorityStop, match="REPLICATE_COUNT_MISMATCH"):
        validate_precision_authority_v1(x)


def test_familywise_risk_allocation_must_close_exactly():
    x = authority()
    x["quantities"][0]["risk_allocation"] = 0.004
    with pytest.raises(PrecisionAuthorityStop, match="RISK_ALLOCATION_MISMATCH"):
        validate_precision_authority_v1(x)


def test_duplicate_quantity_id_fails_closed():
    x = authority()
    x["quantities"][1]["quantity_id"] = x["quantities"][0]["quantity_id"]
    with pytest.raises(PrecisionAuthorityStop, match="DUPLICATE_QUANTITY"):
        validate_precision_authority_v1(x)


@pytest.mark.parametrize(
    "field",
    ["outcomes_inspected_before_freeze", "checkpoint_outcomes_used", "pathology_used", "protected_data_used", "dimension_outcomes_used"],
)
def test_any_pre_freeze_outcome_or_protected_access_fails(field):
    x = authority()
    x[field] = True
    with pytest.raises(PrecisionAuthorityStop, match="PRE_FREEZE_ACCESS"):
        validate_precision_authority_v1(x)


def test_conditional_or_survivor_only_semantics_fail():
    x = authority()
    x["decision_metric_population"] = "CONDITIONAL_ON_ESTIMATOR_SUCCESS"
    with pytest.raises(PrecisionAuthorityStop, match="UNCONDITIONAL"):
        validate_precision_authority_v1(x)

    y = authority()
    y["survivor_only_intervals_forbidden"] = False
    with pytest.raises(PrecisionAuthorityStop, match="SURVIVOR_ONLY"):
        validate_precision_authority_v1(y)


def test_precision_cannot_be_relabelled_as_effect_threshold():
    x = authority()
    x["precision_is_not_effect_criterion"] = False
    with pytest.raises(PrecisionAuthorityStop, match="PRECISION_EFFECT_CONFLATION"):
        validate_precision_authority_v1(x)


def test_parent_bindings_are_mandatory():
    x = authority()
    del x["full104_parent_bindings"]["metadata_sqlite_sha256"]
    with pytest.raises(PrecisionAuthorityStop, match="PARENT_BINDINGS_INCOMPLETE"):
        validate_precision_authority_v1(x)


def test_canonical_bytes_are_order_stable():
    x = authority()
    a = canonical_precision_authority_bytes(x)
    shuffled = json.loads(json.dumps(x))
    shuffled = dict(reversed(list(shuffled.items())))
    b = canonical_precision_authority_bytes(shuffled)
    assert a == b
    assert a.endswith(b"\n")
