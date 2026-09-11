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
        folds.append({
            "held_out_index": i,
            "n_train": 27,
            "train_indices": tuple(j for j in range(28) if j != i),
            "out_of_fold_prediction": float(scores[i]),
            "fold_ridge_exponent": -4.0,
        })
    return {
        "kind": "t0_v21_cross_fit_artifact_v1",
        "n_donors": 28,
        "donor_ids": ids,
        "y": np.linspace(0, 1, 28),
        "age": np.linspace(55, 90, 28),
        "sex": np.tile([0.0, 1.0], 14),
        "oof_scores": scores,
        "folds": folds,
        "fold_ridge_exponents": tuple(f["fold_ridge_exponent"] for f in folds),
        "fold_ridge_exponents_recorded": True,
        "fold_ridge_exponents_vary": False,
        "artifact_digest": "legacy",
    }


def fold_prov(cf):
    ids = tuple(cf["donor_ids"])
    out = []
    for i, donor in enumerate(ids):
        out.append({
            "held_out_donor_id": donor,
            "train_donor_ids": tuple(x for x in ids if x != donor),
            "training_data_digest": hashlib.sha256(f"data-{i}".encode()).hexdigest(),
            "ridge_trace_digest": hashlib.sha256(f"ridge-{i}".encode()).hexdigest(),
            "fitted_target_digest": hashlib.sha256(f"fit-{i}".encode()).hexdigest(),
            "prediction": float(cf["oof_scores"][i]),
        })
    return out


def sealed():
    cf = old_crossfit()
    return a.seal_authoritative_crossfit(
        cross_fit_artifact=cf,
        source_authority=authority(),
        fold_provenance=fold_prov(cf),
    )


def validated():
    artifact = sealed()
    return artifact, a.validate_authoritative_crossfit(
        artifact, expected_source_authority=authority())


def design_receipt():
    return a.seal_confirmation_design_receipt(
        age=np.linspace(55, 90, 12),
        sex=np.tile([0.0, 1.0], 6),
        source_role="discovery_only_design_envelope",
        source_digest=THREE,
        contract_sha=ONE,
    )


def permutation_receipt(v):
    return a.seal_nested_permutation_evidence(
        authoritative_crossfit_digest=v["artifact_digest"],
        source_authority_digest=v["source_authority_digest"],
        nested_pipeline_code_sha=ZERO,
        contract_sha=ONE,
        n_permutations=9999,
        seed=7,
        p_upper=0.02,
        null_digest=H,
    )


def geometry_receipt(v, design):
    return a.seal_predictor_geometry_transport_receipt(
        authoritative_crossfit_digest=v["artifact_digest"],
        source_authority_digest=v["source_authority_digest"],
        confirmation_design_receipt_digest=design["receipt_digest"],
        contract_sha=ONE,
        transport_mode="actual_discovery_residualized_score_geometry",
        residualized_predictor_geometry_digest=FOUR,
        calibration_design_digest=FIVE,
        assumption_statement_digest=SIX,
    )


def calibration_receipt(v, perm, design, geom, *, effect_estimand="whole_pipeline_permutation_standardized_effect_v1"):
    power = 0.90
    se = 0.02
    lower = max(0.0, power - 1.96 * se)
    return a.seal_power_calibration_receipt(
        authoritative_crossfit_digest=v["artifact_digest"],
        source_authority_digest=v["source_authority_digest"],
        nested_permutation_evidence_digest=perm["evidence_digest"],
        confirmation_design_receipt_digest=design["receipt_digest"],
        predictor_geometry_transport_digest=geom["receipt_digest"],
        calibration_code_sha=SEVEN,
        contract_sha=ONE,
        n_simulations=2000,
        n_permutations=9999,
        seed=9,
        power=power,
        monte_carlo_standard_error=se,
        power_lower_95=lower,
        clears_gate=True,
        consumes_predictor_geometry=True,
        uses_iid_normal_surrogate=False,
        effect_estimand=effect_estimand,
    )


def complete_receipts():
    artifact, v = validated()
    design = design_receipt()
    perm = permutation_receipt(v)
    geom = geometry_receipt(v, design)
    cal = calibration_receipt(v, perm, design, geom)
    return artifact, v, design, perm, geom, cal


def test_restored_surface_and_status_are_explicit():
    for name in (
        "seal_authoritative_crossfit", "seal_nested_permutation_evidence",
        "seal_confirmation_design_receipt", "seal_predictor_geometry_transport_receipt",
        "seal_power_calibration_receipt", "validate_authoritative_crossfit",
        "validate_nested_permutation_evidence", "validate_confirmation_design_receipt",
        "validate_predictor_geometry_transport_receipt", "validate_power_calibration_receipt",
        "decision_capable_power_gate",
    ):
        assert callable(getattr(a, name))
    assert a.EFFECT_TRANSPORT_STATUS == "OPEN"
    assert a.POWER_GATE_PRODUCTION_VERDICT_CAPABILITY == "DISABLED"
    assert a.TRANSPORT_AUTHORIZED_EFFECT_ESTIMANDS == frozenset()


def test_authoritative_crossfit_roundtrip_and_external_authority_binding():
    artifact, v = validated()
    assert v["verified"] is True
    wrong = authority(); wrong["expression_root_digest"] = TWO
    with pytest.raises(RuntimeError, match="expression_root_digest"):
        a.validate_authoritative_crossfit(artifact, expected_source_authority=wrong)


def test_fold_provenance_mutation_and_illegal_train_set_fail():
    artifact = copy.deepcopy(sealed())
    artifact["fold_provenance"][0]["training_data_digest"] = TWO
    with pytest.raises(RuntimeError, match="digest does not recompute"):
        a.validate_authoritative_crossfit(artifact, expected_source_authority=authority())

    cf = old_crossfit(); fp = fold_prov(cf)
    fp[0]["train_donor_ids"] = fp[0]["train_donor_ids"][:-1] + ("D00",)
    with pytest.raises(RuntimeError, match="exact 27-donor complement"):
        a.seal_authoritative_crossfit(
            cross_fit_artifact=cf, source_authority=authority(), fold_provenance=fp)


def test_self_consistent_crossfit_forgery_is_revalidated():
    artifact = copy.deepcopy(sealed())
    artifact["cross_fit_artifact"]["sex"] = [1.0] * 28
    body = {k: artifact[k] for k in artifact if k != "artifact_digest"}
    artifact["artifact_digest"] = a.canonical_digest(
        body, domain="T0_V21_AUTHORITATIVE_CROSSFIT_V1")
    with pytest.raises(RuntimeError, match="complete binary"):
        a.validate_authoritative_crossfit(artifact, expected_source_authority=authority())


def test_ridge_summary_must_match_fold_records():
    cf = old_crossfit()
    cf["fold_ridge_exponents_recorded"] = False
    with pytest.raises(RuntimeError, match="fold_ridge_exponents_recorded"):
        a.seal_authoritative_crossfit(
            cross_fit_artifact=cf, source_authority=authority(), fold_provenance=fold_prov(cf))

    cf = old_crossfit()
    cf["fold_ridge_exponents"] = tuple([None] * 28)
    with pytest.raises(RuntimeError, match="fold_ridge_exponents"):
        a.seal_authoritative_crossfit(
            cross_fit_artifact=cf, source_authority=authority(), fold_provenance=fold_prov(cf))


def test_nested_permutation_seal_derives_and_binds_behavioral_null():
    _, v = validated()
    ev = permutation_receipt(v)
    assert ev["null_digest"] == a.nested_permutation_null_digest()
    assert ev["shuffled_full_residualized_refit"] is True
    out = a.validate_nested_permutation_evidence(
        ev,
        artifact_digest=v["artifact_digest"],
        source_authority_digest=v["source_authority_digest"],
        expected_pipeline_code_sha=ZERO,
        expected_contract_sha=ONE,
        expected_evidence_digest=ev["evidence_digest"],
    )
    assert out["verified"] is True


def test_nested_permutation_behavior_forgery_and_self_certification_fail():
    _, v = validated()
    ev = permutation_receipt(v)
    bad = copy.deepcopy(ev)
    bad["shuffled_full_residualized_refit"] = False
    body = {k: bad[k] for k in bad if k != "evidence_digest"}
    bad["evidence_digest"] = a.canonical_digest(
        body, domain="T0_V21_NESTED_PERMUTATION_EVIDENCE_V1")
    with pytest.raises(RuntimeError, match="shuffled complete residualized refit"):
        a.validate_nested_permutation_evidence(
            bad,
            artifact_digest=v["artifact_digest"],
            source_authority_digest=v["source_authority_digest"],
            expected_pipeline_code_sha=ZERO,
            expected_contract_sha=ONE,
            expected_evidence_digest=bad["evidence_digest"],
        )
    with pytest.raises(RuntimeError, match="externally expected"):
        a.validate_nested_permutation_evidence(
            ev,
            artifact_digest=v["artifact_digest"],
            source_authority_digest=v["source_authority_digest"],
            expected_pipeline_code_sha=ZERO,
            expected_contract_sha=ONE,
            expected_evidence_digest=H,
        )


def test_protected_confirmation_source_fails_at_seal():
    with pytest.raises(RuntimeError, match="protected role"):
        a.seal_confirmation_design_receipt(
            age=np.linspace(55, 90, 12),
            sex=np.tile([0.0, 1.0], 6),
            source_role="reader_validation",
            source_digest=THREE,
            contract_sha=ONE,
        )


def test_geometry_rejects_iid_surrogate_and_external_digest_substitution():
    _, v = validated(); design = design_receipt()
    with pytest.raises(RuntimeError, match="not decision-capable"):
        a.seal_predictor_geometry_transport_receipt(
            authoritative_crossfit_digest=v["artifact_digest"],
            source_authority_digest=v["source_authority_digest"],
            confirmation_design_receipt_digest=design["receipt_digest"],
            contract_sha=ONE,
            transport_mode="iid_normal_surrogate",
            residualized_predictor_geometry_digest=FOUR,
            calibration_design_digest=FIVE,
            assumption_statement_digest=SIX,
        )
    geom = geometry_receipt(v, design)
    with pytest.raises(RuntimeError, match="externally expected"):
        a.validate_predictor_geometry_transport_receipt(
            geom,
            artifact_digest=v["artifact_digest"],
            source_authority_digest=v["source_authority_digest"],
            confirmation_design_receipt_digest=design["receipt_digest"],
            expected_contract_sha=ONE,
            expected_receipt_digest=H,
        )


def test_calibration_rejects_hc3_transport_label_and_external_digest_substitution():
    _, v = validated(); design = design_receipt(); perm = permutation_receipt(v)
    geom = geometry_receipt(v, design)
    with pytest.raises(RuntimeError, match="effect_estimand"):
        calibration_receipt(v, perm, design, geom, effect_estimand="assembled_hc3_t_over_sqrt_n")
    cal = calibration_receipt(v, perm, design, geom)
    with pytest.raises(RuntimeError, match="externally expected"):
        a.validate_power_calibration_receipt(
            cal,
            artifact_digest=v["artifact_digest"],
            source_authority_digest=v["source_authority_digest"],
            nested_permutation_evidence_digest=perm["evidence_digest"],
            confirmation_design_receipt_digest=design["receipt_digest"],
            predictor_geometry_transport_digest=geom["receipt_digest"],
            expected_calibration_code_sha=SEVEN,
            expected_contract_sha=ONE,
            expected_calibration_receipt_digest=H,
        )


def test_decision_gate_checks_external_receipts_before_transport_stop():
    artifact, _, design, perm, geom, cal = complete_receipts()
    with pytest.raises(RuntimeError, match="nested-permutation evidence"):
        a.decision_capable_power_gate(
            artifact=artifact,
            expected_source_authority=authority(),
            permutation_evidence=perm,
            expected_nested_pipeline_code_sha=ZERO,
            expected_nested_permutation_evidence_digest=H,
            confirmation_design_receipt=design,
            expected_confirmation_design_receipt_digest=design["receipt_digest"],
            predictor_geometry_transport_receipt=geom,
            expected_predictor_geometry_transport_digest=geom["receipt_digest"],
            power_calibration_receipt=cal,
            expected_power_calibration_receipt_digest=cal["receipt_digest"],
            expected_calibration_code_sha=SEVEN,
        )


def test_valid_receipts_cannot_produce_production_power_verdict_while_transport_open():
    artifact, _, design, perm, geom, cal = complete_receipts()
    with pytest.raises(RuntimeError, match=a.TRANSPORT_STOP):
        a.decision_capable_power_gate(
            artifact=artifact,
            expected_source_authority=authority(),
            permutation_evidence=perm,
            expected_nested_pipeline_code_sha=ZERO,
            expected_nested_permutation_evidence_digest=perm["evidence_digest"],
            confirmation_design_receipt=design,
            expected_confirmation_design_receipt_digest=design["receipt_digest"],
            predictor_geometry_transport_receipt=geom,
            expected_predictor_geometry_transport_digest=geom["receipt_digest"],
            power_calibration_receipt=cal,
            expected_power_calibration_receipt_digest=cal["receipt_digest"],
            expected_calibration_code_sha=SEVEN,
        )
