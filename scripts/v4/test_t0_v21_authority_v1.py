import copy
import hashlib
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t0_v21_authority_v1 as a

H = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64
E = "e" * 64
F = "f" * 64
ZERO = "0" * 64
ONE = "1" * 64
TWO = "2" * 64
THREE = "3" * 64
FOUR = "4" * 64
FIVE = "5" * 64
SIX = "6" * 64
SEVEN = "7" * 64


def authority():
    return {
        "expression_root_digest": H,
        "donor_role_ledger_digest": B,
        "donor_order_digest": C,
        "molecular_address_digest": D,
        "transformation_digest": E,
        "nuisance_spec_digest": F,
        "estimator_id": "S2@v21",
        "target_code_sha": ZERO,
        "contract_sha": ONE,
    }


def old_crossfit():
    ids = tuple(f"D{i:02d}" for i in range(28))
    scores = np.arange(28, dtype=float) / 10.0
    folds = []
    for i in range(28):
        folds.append({"held_out_index": i, "n_train": 27,
                      "train_indices": tuple(j for j in range(28) if j != i),
                      "out_of_fold_prediction": float(scores[i]),
                      "fold_ridge_exponent": -4.0})
    return {"kind": "t0_v21_cross_fit_artifact_v1", "n_donors": 28,
            "donor_ids": ids, "y": np.linspace(0, 1, 28),
            "age": np.linspace(55, 90, 28), "sex": np.tile([0., 1.], 14),
            "oof_scores": scores, "folds": folds, "artifact_digest": "legacy"}


def fold_prov(cf):
    ids = tuple(cf["donor_ids"])
    out = []
    for i, d in enumerate(ids):
        out.append({"held_out_donor_id": d,
                    "train_donor_ids": tuple(x for x in ids if x != d),
                    "training_data_digest": hashlib.sha256(f"data-{i}".encode()).hexdigest(),
                    "ridge_trace_digest": hashlib.sha256(f"ridge-{i}".encode()).hexdigest(),
                    "fitted_target_digest": hashlib.sha256(f"fit-{i}".encode()).hexdigest(),
                    "prediction": float(cf["oof_scores"][i])})
    return out


def sealed():
    cf = old_crossfit()
    return a.seal_authoritative_crossfit(cross_fit_artifact=cf,
                                         source_authority=authority(),
                                         fold_provenance=fold_prov(cf))


def validated():
    art = sealed()
    return art, a.validate_authoritative_crossfit(art, expected_source_authority=authority())


def design_receipt():
    return a.seal_confirmation_design_receipt(
        age=np.linspace(55, 90, 12), sex=np.tile([0., 1.], 6),
        source_role="discovery_only_design_envelope",
        source_digest=THREE, contract_sha=ONE)


def permutation_receipt(v):
    return a.seal_nested_permutation_evidence(
        authoritative_crossfit_digest=v["artifact_digest"],
        source_authority_digest=v["source_authority_digest"],
        nested_pipeline_code_sha=ZERO, contract_sha=ONE,
        n_permutations=9999, seed=7, p_upper=0.02, null_digest=H)


def geometry_receipt(v, design):
    return a.seal_predictor_geometry_transport_receipt(
        authoritative_crossfit_digest=v["artifact_digest"],
        source_authority_digest=v["source_authority_digest"],
        confirmation_design_receipt_digest=design["receipt_digest"],
        contract_sha=ONE,
        transport_mode="actual_discovery_residualized_score_geometry",
        residualized_predictor_geometry_digest=FOUR,
        calibration_design_digest=FIVE,
        assumption_statement_digest=SIX)


def calibration_receipt(v, perm, design, geom, *, power=.90, se=.02, surrogate=False,
                        consumes_geometry=True, clears=True):
    lower = max(0.0, power - 1.96 * se)
    return a.seal_power_calibration_receipt(
        authoritative_crossfit_digest=v["artifact_digest"],
        source_authority_digest=v["source_authority_digest"],
        nested_permutation_evidence_digest=perm["evidence_digest"],
        confirmation_design_receipt_digest=design["receipt_digest"],
        predictor_geometry_transport_digest=geom["receipt_digest"],
        calibration_code_sha=SEVEN, contract_sha=ONE,
        n_simulations=2000, n_permutations=9999, seed=9,
        power=power, monte_carlo_standard_error=se, power_lower_95=lower,
        clears_gate=clears, consumes_predictor_geometry=consumes_geometry,
        uses_iid_normal_surrogate=surrogate,
        effect_estimand="geometry_bound_crossfit_effect_v1")


def test_self_consistent_but_wrong_external_authority_fails():
    art = sealed()
    expected = authority(); expected["expression_root_digest"] = TWO
    with pytest.raises(RuntimeError, match="expression_root_digest"):
        a.validate_authoritative_crossfit(art, expected_source_authority=expected)


def test_fold_training_data_digest_is_bound():
    art = sealed()
    art = copy.deepcopy(art)
    art["fold_provenance"][0]["training_data_digest"] = TWO
    with pytest.raises(RuntimeError, match="digest does not recompute"):
        a.validate_authoritative_crossfit(art, expected_source_authority=authority())


def test_illegal_train_donor_set_cannot_be_sealed():
    cf = old_crossfit(); fp = fold_prov(cf)
    fp[0]["train_donor_ids"] = fp[0]["train_donor_ids"][:-1] + ("D00",)
    with pytest.raises(RuntimeError, match="exact 27-donor complement"):
        a.seal_authoritative_crossfit(cross_fit_artifact=cf,
                                      source_authority=authority(), fold_provenance=fp)


def test_self_consistent_forged_crossfit_still_revalidates_structure():
    art = sealed()
    forged = copy.deepcopy(art)
    forged["cross_fit_artifact"]["sex"] = [1.0] * 28  # invalid but self-consistent bytes
    body = {k: forged[k] for k in forged if k != "artifact_digest"}
    forged["artifact_digest"] = a.canonical_digest(body, domain="T0_V21_AUTHORITATIVE_CROSSFIT_V1")
    with pytest.raises(RuntimeError, match="complete binary"):
        a.validate_authoritative_crossfit(forged, expected_source_authority=authority())


def test_self_consistent_forged_score_fold_mismatch_is_refused():
    art = sealed()
    forged = copy.deepcopy(art)
    forged["cross_fit_artifact"]["folds"][3]["out_of_fold_prediction"] += 10.0
    body = {k: forged[k] for k in forged if k != "artifact_digest"}
    forged["artifact_digest"] = a.canonical_digest(body, domain="T0_V21_AUTHORITATIVE_CROSSFIT_V1")
    with pytest.raises(RuntimeError, match="score vector"):
        a.validate_authoritative_crossfit(forged, expected_source_authority=authority())


def test_prediction_mismatch_cannot_be_sealed():
    cf = old_crossfit(); fp = fold_prov(cf); fp[4]["prediction"] += 1
    with pytest.raises(RuntimeError, match="prediction mismatch"):
        a.seal_authoritative_crossfit(cross_fit_artifact=cf,
                                      source_authority=authority(), fold_provenance=fp)


def test_protected_and_unapproved_confirmation_design_sources_are_forbidden():
    with pytest.raises(RuntimeError, match="protected role"):
        a.seal_confirmation_design_receipt(age=np.linspace(55, 90, 12),
                                           sex=np.tile([0., 1.], 6),
                                           source_role="reader_validation",
                                           source_digest=H, contract_sha=ONE)
    with pytest.raises(RuntimeError, match="not an approved"):
        a.seal_confirmation_design_receipt(age=np.linspace(55, 90, 12),
                                           sex=np.tile([0., 1.], 6),
                                           source_role="hand_made_representative_design",
                                           source_digest=H, contract_sha=ONE)


def test_confirmation_design_must_match_external_expected_receipt():
    receipt = design_receipt()
    with pytest.raises(RuntimeError, match="externally expected"):
        a.validate_confirmation_design_receipt(
            receipt, expected_contract_sha=ONE, expected_receipt_digest=H)
    assert a.validate_confirmation_design_receipt(
        receipt, expected_contract_sha=ONE,
        expected_receipt_digest=receipt["receipt_digest"])["verified"]


def test_nested_permutation_evidence_must_match_artifact_and_reject():
    art, v = validated()
    ev = permutation_receipt(v)
    assert a.validate_nested_permutation_evidence(
        ev, artifact_digest=v["artifact_digest"],
        source_authority_digest=v["source_authority_digest"],
        expected_pipeline_code_sha=ZERO, expected_contract_sha=ONE)["verified"]
    ev2 = a.seal_nested_permutation_evidence(
        authoritative_crossfit_digest=v["artifact_digest"],
        source_authority_digest=v["source_authority_digest"],
        nested_pipeline_code_sha=ZERO, contract_sha=ONE,
        n_permutations=9999, seed=7, p_upper=0.20, null_digest=H)
    with pytest.raises(RuntimeError, match="does not reject"):
        a.validate_nested_permutation_evidence(
            ev2, artifact_digest=v["artifact_digest"],
            source_authority_digest=v["source_authority_digest"],
            expected_pipeline_code_sha=ZERO, expected_contract_sha=ONE)


def test_frozen_B_is_enforced():
    with pytest.raises(RuntimeError, match="B=9999"):
        a.seal_nested_permutation_evidence(
            authoritative_crossfit_digest=H, source_authority_digest=B,
            nested_pipeline_code_sha=ZERO, contract_sha=ONE,
            n_permutations=99, seed=1, p_upper=.01, null_digest=C)


def test_iid_normal_surrogate_geometry_is_not_decision_capable():
    art, v = validated(); design = design_receipt()
    with pytest.raises(RuntimeError, match="not decision-capable"):
        a.seal_predictor_geometry_transport_receipt(
            authoritative_crossfit_digest=v["artifact_digest"],
            source_authority_digest=v["source_authority_digest"],
            confirmation_design_receipt_digest=design["receipt_digest"],
            contract_sha=ONE,
            transport_mode="iid_normal_surrogate",
            residualized_predictor_geometry_digest=FOUR,
            calibration_design_digest=FIVE,
            assumption_statement_digest=SIX)


def test_power_calibration_refuses_surrogate_or_missing_geometry_consumption():
    art, v = validated(); design = design_receipt(); perm = permutation_receipt(v)
    geom = geometry_receipt(v, design)
    with pytest.raises(RuntimeError, match="iid-normal surrogate"):
        calibration_receipt(v, perm, design, geom, surrogate=True)
    with pytest.raises(RuntimeError, match="consume predictor-geometry"):
        calibration_receipt(v, perm, design, geom, consumes_geometry=False)


def test_power_calibration_gate_uses_lower_monte_carlo_limit():
    art, v = validated(); design = design_receipt(); perm = permutation_receipt(v)
    geom = geometry_receipt(v, design)
    with pytest.raises(RuntimeError, match="lower Monte Carlo"):
        calibration_receipt(v, perm, design, geom, power=.801, se=.05, clears=True)


def test_decision_capable_gate_is_fully_receipt_bound_and_does_not_call_legacy_power_gate():
    art, v = validated(); design = design_receipt(); perm = permutation_receipt(v)
    geom = geometry_receipt(v, design)
    cal = calibration_receipt(v, perm, design, geom)
    result = a.decision_capable_power_gate(
        artifact=art, expected_source_authority=authority(),
        permutation_evidence=perm, expected_nested_pipeline_code_sha=ZERO,
        confirmation_design_receipt=design,
        expected_confirmation_design_receipt_digest=design["receipt_digest"],
        predictor_geometry_transport_receipt=geom,
        power_calibration_receipt=cal,
        expected_calibration_code_sha=SEVEN)
    assert result["clears_gate"] is True
    assert result["production_authority"]["predictor_geometry"]["verified"]
    assert result["production_authority"]["calibration"]["verified"]

    wrong_design = dict(design)
    wrong_design["receipt_digest"] = H
    with pytest.raises(RuntimeError, match="receipt digest"):
        a.decision_capable_power_gate(
            artifact=art, expected_source_authority=authority(),
            permutation_evidence=perm, expected_nested_pipeline_code_sha=ZERO,
            confirmation_design_receipt=wrong_design,
            expected_confirmation_design_receipt_digest=design["receipt_digest"],
            predictor_geometry_transport_receipt=geom,
            power_calibration_receipt=cal,
            expected_calibration_code_sha=SEVEN)
