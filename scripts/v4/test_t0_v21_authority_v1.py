import copy
import hashlib
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import t0_v21_authority_v1 as a
import t0_v21_selection_and_power_v1 as executor

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


def crossfit():
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
    return executor.seal_cross_fit(
        oof_result={"n_donors": 28, "oof_predictions": scores, "folds": folds},
        donor_ids=ids,
        y=np.linspace(0, 1, 28),
        age=np.linspace(55, 90, 28),
        sex=np.tile([0.0, 1.0], 14),
    )


def fold_prov(cf):
    ids = tuple(cf["donor_ids"])
    return [
        {
            "held_out_donor_id": d,
            "train_donor_ids": tuple(x for x in ids if x != d),
            "training_data_digest": hashlib.sha256(f"data-{i}".encode()).hexdigest(),
            "ridge_trace_digest": hashlib.sha256(f"ridge-{i}".encode()).hexdigest(),
            "fitted_target_digest": hashlib.sha256(f"fit-{i}".encode()).hexdigest(),
            "prediction": float(cf["oof_scores"][i]),
        }
        for i, d in enumerate(ids)
    ]


def sealed():
    cf = crossfit()
    return a.seal_authoritative_crossfit(
        cross_fit_artifact=cf,
        source_authority=authority(),
        fold_provenance=fold_prov(cf),
    )


def validated():
    art = sealed()
    return art, a.validate_authoritative_crossfit(
        art, expected_source_authority=authority())


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


def test_authority_surface_and_legacy_implementation_exist():
    assert a.EFFECT_TRANSPORT_STATUS == "OPEN"
    assert callable(a.seal_authoritative_crossfit)
    assert callable(a.validate_authoritative_crossfit)
    assert callable(a.decision_capable_power_gate)


def test_crossfit_is_revalidated_by_executor_and_ridge_metadata_is_bound():
    cf = crossfit()
    bad = copy.deepcopy(cf)
    bad["fold_ridge_exponents_recorded"] = False
    with pytest.raises(RuntimeError, match="declares fold_ridge_exponents_recorded"):
        a.seal_authoritative_crossfit(
            cross_fit_artifact=bad,
            source_authority=authority(),
            fold_provenance=fold_prov(cf),
        )


def test_authoritative_artifact_revalidates_nested_crossfit_after_digest_rewrite():
    art = sealed()
    forged = copy.deepcopy(art)
    forged["cross_fit_artifact"]["fold_ridge_exponents"] = tuple([None] * 28)
    body = {k: forged[k] for k in forged if k != "artifact_digest"}
    forged["artifact_digest"] = a.canonical_digest(
        body, domain="T0_V21_AUTHORITATIVE_CROSSFIT_V1")
    with pytest.raises(RuntimeError, match="fold_ridge_exponents"):
        a.validate_authoritative_crossfit(
            forged, expected_source_authority=authority())


def test_wrong_external_source_authority_fails():
    art = sealed()
    wrong = authority()
    wrong["expression_root_digest"] = TWO
    with pytest.raises(RuntimeError, match="expression_root_digest"):
        a.validate_authoritative_crossfit(
            art, expected_source_authority=wrong)


def test_protected_confirmation_source_remains_forbidden():
    with pytest.raises(RuntimeError, match="protected role"):
        a.seal_confirmation_design_receipt(
            age=np.linspace(55, 90, 12),
            sex=np.tile([0.0, 1.0], 6),
            source_role="reader_validation",
            source_digest=THREE,
            contract_sha=ONE,
        )


def test_nested_permutation_receipt_requires_external_expected_digest():
    _, v = validated()
    ev = permutation_receipt(v)
    with pytest.raises(RuntimeError, match="externally expected"):
        a.validate_nested_permutation_evidence(
            ev,
            artifact_digest=v["artifact_digest"],
            source_authority_digest=v["source_authority_digest"],
            expected_pipeline_code_sha=ZERO,
            expected_contract_sha=ONE,
            expected_evidence_digest=TWO,
        )
    assert a.validate_nested_permutation_evidence(
        ev,
        artifact_digest=v["artifact_digest"],
        source_authority_digest=v["source_authority_digest"],
        expected_pipeline_code_sha=ZERO,
        expected_contract_sha=ONE,
        expected_evidence_digest=ev["evidence_digest"],
    )["verified"]


def test_geometry_receipt_requires_external_expected_digest():
    _, v = validated()
    design = design_receipt()
    geom = geometry_receipt(v, design)
    with pytest.raises(RuntimeError, match="externally expected"):
        a.validate_predictor_geometry_transport_receipt(
            geom,
            artifact_digest=v["artifact_digest"],
            source_authority_digest=v["source_authority_digest"],
            confirmation_design_receipt_digest=design["receipt_digest"],
            expected_contract_sha=ONE,
            expected_receipt_digest=TWO,
        )


def test_unvalidated_effect_estimands_cannot_mint_production_power_receipts():
    for estimand in (
        "assembled_hc3_t_over_sqrt_n",
        "whole_pipeline_permutation_standardized_effect_v1",
        "prospective_conservative_geometry_envelope_effect_v1",
        "observed_null_sd_correction",
    ):
        with pytest.raises(RuntimeError, match="not authority-bound"):
            a.seal_power_calibration_receipt(effect_estimand=estimand)


def test_production_gate_cannot_be_reenabled_by_well_formed_caller_arguments():
    with pytest.raises(
            RuntimeError,
            match="STOP_T0_V21_EFFECT_TRANSPORT_NOT_AUTHORITY_BOUND"):
        a.decision_capable_power_gate(
            artifact={},
            expected_source_authority={},
            permutation_evidence={},
            expected_nested_pipeline_code_sha=ZERO,
            confirmation_design_receipt={},
            expected_confirmation_design_receipt_digest=H,
            predictor_geometry_transport_receipt={},
            power_calibration_receipt={},
            expected_calibration_code_sha=ZERO,
        )
