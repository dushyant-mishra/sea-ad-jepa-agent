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
            "oof_scores": scores, "folds": folds,
            "fold_ridge_exponents": tuple(f["fold_ridge_exponent"] for f in folds),
            "fold_ridge_exponents_recorded": True,
            "fold_ridge_exponents_vary": False,
            "artifact_digest": "legacy"}


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
        effect_estimand="whole_pipeline_permutation_standardized_effect_v1")


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


def test_declared_ridge_metadata_must_match_fold_records():
    cf = old_crossfit()
    cf["fold_ridge_exponents_recorded"] = False
    with pytest.raises(RuntimeError, match="fold_ridge_exponents_recorded"):
        a.seal_authoritative_crossfit(cross_fit_artifact=cf,
                                      source_authority=authority(),
                                      fold_provenance=fold_prov(cf))

    cf = old_crossfit()
    cf["fold_ridge_exponents"] = tuple([None] * 28)
    with pytest.raises(RuntimeError, match="fold_ridge_exponents"):
        a.seal_authoritative_crossfit(cross_fit_artifact=cf,
                                      source_authority=authority(),
                                      fold_provenance=fold_prov(cf))


def test_prediction_mismatch_cannot_be_sealed():
    cf = old_crossfit(); fp = fold_prov(cf)
    fp[0]["prediction"] += 1.0
    with pytest.raises(RuntimeError, match="fold predictions"):
        a.seal_authoritative_crossfit(cross_fit_artifact=cf,
                                      source_authority=authority(), fold_provenance=fp)


def test_nested_permutation_evidence_requires_full_behavioral_authority():
    art, v = validated()
    ev = permutation_receipt(v)
    bad = dict(ev); bad["shuffled_full_residualized_refit"] = False
    body = {k: bad[k] for k in bad if k != "evidence_digest"}
    bad["null_digest"] = a.canonical_digest(
        {"permutation_scope": "at8_across_donors", "donor_ordering": "frozen",
         "observation_table_row_order": "frozen", "nuisance_design_rebuilt_each_shuffle": True,
         "standardization_recomputed_each_shuffle": True,
          "complete_fit_repeated_each_shuffle": True,
          "nuisance_signature_included_each_shuffle": True,
          "preserves_nans": True, "preserves_iteration_cap_stopping": True,
          "shuffled_full_residualized_refit": False,
          "shuffled_noise_sampling": True, "permutations": 9999},
        domain="T0_V21_NESTED_PERMUTATION_NULL_V1")
    bad["evidence_digest"] = a.canonical_digest({k: bad[k] for k in bad if k != "evidence_digest"},
                                                domain="T0_V21_NESTED_PERMUTATION_EVIDENCE_V1")
    with pytest.raises(RuntimeError, match="shuffled complete residualized refit"):
        a.validate_nested_permutation_evidence(bad, artifact_digest=v["artifact_digest"],
                                                 source_authority_digest=v["source_authority_digest"],
                                                expected_pipeline_code_sha=ZERO, expected_contract_sha=ONE,
                                                expected_evidence_digest=bad["evidence_digest"])


def test_confirmation_design_receipt_rejects_protected_source():
    bad = design_receipt()
    bad = a.seal_confirmation_design_receipt(age=np.linspace(55,90,12), sex=np.tile([0.,1.],6),
                                               source_role="reader_validation", source_digest=THREE, contract_sha=ONE)
    with pytest.raises(RuntimeError, match="protected source"):
        a.validate_confirmation_design_receipt(bad, expected_contract_sha=ONE,
                                               expected_receipt_digest=bad["receipt_digest"])


def test_confirmation_design_receipt_requires_external_digest():
    r = design_receipt()
    with pytest.raises(RuntimeError, match="externally expected"):
        a.validate_confirmation_design_receipt(r, expected_contract_sha=ONE,
                                               expected_receipt_digest=H)


def test_predictor_geometry_receipt_rejects_iid_normal_surrogate():
    art, v = validated(); design = design_receipt()
    with pytest.raises(RuntimeError, match="forbidden"):
        a.seal_predictor_geometry_transport_receipt(
            authoritative_crossfit_digest=v["artifact_digest"],
            source_authority_digest=v["source_authority_digest"],
            confirmation_design_receipt_digest=design["receipt_digest"],
            contract_sha=ONE, transport_mode="iid_normal_surrogate",
            residualized_predictor_geometry_digest=FOUR,
            calibration_design_digest=FIVE, assumption_statement_digest=SIX)


def test_power_calibration_receipt_rejects_iid_surrogate_and_missing_geometry():
    art, v = validated(); design = design_receipt(); perm = permutation_receipt(v)
    geom = geometry_receipt(v, design)
    with pytest.raises(RuntimeError, match="iid-normal surrogate"):
        calibration_receipt(v, perm, design, geom, surrogate=True)
    with pytest.raises(RuntimeError, match="consume predictor geometry"):
        calibration_receipt(v, perm, design, geom, consumes_geometry=False)


def test_power_calibration_lower_bound_must_clear_gate():
    art, v = validated(); design = design_receipt(); perm = permutation_receipt(v)
    geom = geometry_receipt(v, design)
    with pytest.raises(RuntimeError, match="lower Monte Carlo"):
        calibration_receipt(v, perm, design, geom, power=.801, se=.05, clears=True)



def test_power_calibration_effect_estimand_is_enumerated_and_not_hc3_transport():
    art, v = validated(); design = design_receipt(); perm = permutation_receipt(v)
    geom = geometry_receipt(v, design)
    with pytest.raises(RuntimeError, match="effect_estimand"):
        a.seal_power_calibration_receipt(
            authoritative_crossfit_digest=v["artifact_digest"],
            source_authority_digest=v["source_authority_digest"],
            nested_permutation_evidence_digest=perm["evidence_digest"],
            confirmation_design_receipt_digest=design["receipt_digest"],
            predictor_geometry_transport_digest=geom["receipt_digest"],
            calibration_code_sha=SEVEN, contract_sha=ONE,
            n_simulations=2000, n_permutations=9999, seed=9,
            power=.90, monte_carlo_standard_error=.02,
            power_lower_95=max(0.0, .90 - 1.96 * .02),
            clears_gate=True, consumes_predictor_geometry=True,
            uses_iid_normal_surrogate=False,
            effect_estimand="assembled_hc3_t_over_sqrt_n")


def test_self_certified_nested_permutation_evidence_needs_external_receipt_digest():
    art, v = validated()
    ev = permutation_receipt(v)
    with pytest.raises(RuntimeError, match="externally expected"):
        a.validate_nested_permutation_evidence(
            ev, artifact_digest=v["artifact_digest"],
            source_authority_digest=v["source_authority_digest"],
            expected_pipeline_code_sha=ZERO, expected_contract_sha=ONE,
            expected_evidence_digest=H)


def test_self_certified_geometry_and_calibration_need_external_receipt_digests():
    art, v = validated(); design = design_receipt(); perm = permutation_receipt(v)
    geom = geometry_receipt(v, design); cal = calibration_receipt(v, perm, design, geom)
    with pytest.raises(RuntimeError, match="externally expected"):
        a.validate_predictor_geometry_transport_receipt(
            geom, artifact_digest=v["artifact_digest"],
            source_authority_digest=v["source_authority_digest"],
            confirmation_design_receipt_digest=design["receipt_digest"],
            expected_contract_sha=ONE, expected_receipt_digest=H)
    with pytest.raises(RuntimeError, match="externally expected"):
        a.validate_power_calibration_receipt(
            cal, artifact_digest=v["artifact_digest"],
            source_authority_digest=v["source_authority_digest"],
            nested_permutation_evidence_digest=perm["evidence_digest"],
            confirmation_design_receipt_digest=design["receipt_digest"],
            predictor_geometry_transport_digest=geom["receipt_digest"],
            expected_calibration_code_sha=SEVEN, expected_contract_sha=ONE,
            expected_calibration_receipt_digest=H)


def test_decision_gate_refuses_self_minted_permutation_geometry_or_calibration_receipts():
    art, v = validated(); design = design_receipt(); perm = permutation_receipt(v)
    geom = geometry_receipt(v, design); cal = calibration_receipt(v, perm, design, geom)
    with pytest.raises(RuntimeError, match="nested-permutation evidence"):
        a.decision_capable_power_gate(
            artifact=art, expected_source_authority=authority(),
            permutation_evidence=perm, expected_nested_pipeline_code_sha=ZERO,
            expected_nested_permutation_evidence_digest=H,
            confirmation_design_receipt=design,
            expected_confirmation_design_receipt_digest=design["receipt_digest"],
            predictor_geometry_transport_receipt=geom,
            expected_predictor_geometry_transport_digest=geom["receipt_digest"],
            power_calibration_receipt=cal,
            expected_power_calibration_receipt_digest=cal["receipt_digest"],
            expected_calibration_code_sha=SEVEN)
    with pytest.raises(RuntimeError, match="predictor-geometry transport"):
        a.decision_capable_power_gate(
            artifact=art, expected_source_authority=authority(),
            permutation_evidence=perm, expected_nested_pipeline_code_sha=ZERO,
            expected_nested_permutation_evidence_digest=perm["evidence_digest"],
            confirmation_design_receipt=design,
            expected_confirmation_design_receipt_digest=design["receipt_digest"],
            predictor_geometry_transport_receipt=geom,
            expected_predictor_geometry_transport_digest=H,
            power_calibration_receipt=cal,
            expected_power_calibration_receipt_digest=cal["receipt_digest"],
            expected_calibration_code_sha=SEVEN)
    with pytest.raises(RuntimeError, match="power calibration receipt"):
        a.decision_capable_power_gate(
            artifact=art, expected_source_authority=authority(),
            permutation_evidence=perm, expected_nested_pipeline_code_sha=ZERO,
            expected_nested_permutation_evidence_digest=perm["evidence_digest"],
            confirmation_design_receipt=design,
            expected_confirmation_design_receipt_digest=design["receipt_digest"],
            predictor_geometry_transport_receipt=geom,
            expected_predictor_geometry_transport_digest=geom["receipt_digest"],
            power_calibration_receipt=cal,
            expected_power_calibration_receipt_digest=H,
            expected_calibration_code_sha=SEVEN)

def test_decision_capable_gate_is_fully_receipt_bound_and_does_not_call_legacy_power_gate():
    art, v = validated(); design = design_receipt(); perm = permutation_receipt(v)
    geom = geometry_receipt(v, design)
    cal = calibration_receipt(v, perm, design, geom)
    result = a.decision_capable_power_gate(
        artifact=art, expected_source_authority=authority(),
        permutation_evidence=perm, expected_nested_pipeline_code_sha=ZERO,
        expected_nested_permutation_evidence_digest=perm["evidence_digest"],
        confirmation_design_receipt=design,
        expected_confirmation_design_receipt_digest=design["receipt_digest"],
        predictor_geometry_transport_receipt=geom,
        expected_predictor_geometry_transport_digest=geom["receipt_digest"],
        power_calibration_receipt=cal,
        expected_power_calibration_receipt_digest=cal["receipt_digest"],
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
            expected_nested_permutation_evidence_digest=perm["evidence_digest"],
            confirmation_design_receipt=wrong_design,
            expected_confirmation_design_receipt_digest=design["receipt_digest"],
            predictor_geometry_transport_receipt=geom,
            expected_predictor_geometry_transport_digest=geom["receipt_digest"],
            power_calibration_receipt=cal,
            expected_power_calibration_receipt_digest=cal["receipt_digest"],
            expected_calibration_code_sha=SEVEN)
