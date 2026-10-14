from __future__ import annotations

import importlib
import importlib.util
import inspect
import json
from pathlib import Path

import numpy as np
import pytest


CONTRACT_PATH = Path("results/v80/sparse_positive/V80_SPARSE_POSITIVE_QUALIFICATION_CONTRACT_V1.json")
FAMILIES = (
    "SP00_BALANCED_ESTIMABLE",
    "SP01_ULTRASPARSE_ESTIMABLE",
    "SP02_DONOR_IMBALANCED_ESTIMABLE",
    "SP03_SOURCE_SHIFT_ESTIMABLE",
    "SP04_SUPPORT_THINNED_ESTIMABLE",
    "SP05_NO_POSITIVE_SUPPORT_NOT_ESTIMABLE",
    "SP06_RANK_DEFICIENT_NOT_ESTIMABLE",
    "SP07_NEW_DONOR_ESTIMABLE",
)
FAILED_V79_IDS = (
    "09bbe252aeb91c12eb996fbd60e5a420237ba4f317255278cdc6e4bfacf9daa6",
    "6ca5f0876ccdac9c86bf5b2f07a4413fdd9f8b824ec8ad45ae84090d657e2f43",
    "ede8a3a369d69133a85fa4a35a3bd24ca87e4a6c680599b671b9693efe7104a5",
)


def _benchmark():
    spec = importlib.util.find_spec("scripts.v80.v80_sparse_positive_benchmark")
    assert spec is not None, "benchmark module must be implemented after RED"
    return importlib.import_module("scripts.v80.v80_sparse_positive_benchmark")


def _adjudicator():
    spec = importlib.util.find_spec("scripts.v80.v80_sparse_positive_adjudicator")
    assert spec is not None, "adjudicator module must be implemented after RED"
    return importlib.import_module("scripts.v80.v80_sparse_positive_adjudicator")


def _finalizer():
    spec = importlib.util.find_spec("scripts.v80.finalize_v80_sparse_positive_package")
    assert spec is not None, "finalizer module must be implemented after RED"
    return importlib.import_module("scripts.v80.finalize_v80_sparse_positive_package")


def test_contract_is_exact_and_authority_off():
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert tuple(contract["challenge_families"]) == FAMILIES
    assert contract["seed_root"] == 41000000
    assert contract["fit_statuses"] == ["COMPLETE", "NOT_ESTIMABLE", "NUMERICAL_FAILURE"]
    assert contract["v79_immutable_binding"]["historical_result"] == "NOT_QUALIFIED"
    assert not any(contract["authority"].values())


def test_generator_source_does_not_contain_historical_failed_fit_ids():
    B = _benchmark()
    source = inspect.getsource(B)
    for fit_id in FAILED_V79_IDS:
        assert fit_id not in source


def test_world_generation_is_deterministic_and_uses_exact_family_set():
    B = _benchmark()
    a = B.build_sparse_positive_worlds(seed_root=41000000)
    b = B.build_sparse_positive_worlds(seed_root=41000000)
    assert tuple(w.family for w in a) == FAMILIES
    assert B.benchmark_identity(a) == B.benchmark_identity(b)
    assert len({w.opaque_id for w in a}) == len(FAMILIES)


def test_fit_transport_is_opaque_and_controller_free():
    B = _benchmark()
    worlds = B.build_sparse_positive_worlds(seed_root=41000000)
    fit = B.serialize_fit_transport(worlds)
    B.validate_fit_transport(fit)
    raw = json.dumps(fit, sort_keys=True)
    for family in FAMILIES:
        assert family not in raw
    for forbidden in (
        "estimability_truth",
        "latent_detection_intercept",
        "latent_positive_location",
        "challenge_family",
        "controller_truth",
    ):
        assert forbidden not in raw
    for fit_id in FAILED_V79_IDS:
        assert fit_id not in raw


def test_sp05_is_nonestimable_by_zero_positive_support_not_numerical_bad_luck():
    B = _benchmark()
    worlds = {w.family: w for w in B.build_sparse_positive_worlds(seed_root=41000000)}
    w = worlds["SP05_NO_POSITIVE_SUPPORT_NOT_ESTIMABLE"]
    assert w.estimability_truth == "NOT_ESTIMABLE_BY_CONSTRUCTION"
    measured = np.asarray(w.support, dtype=bool)
    detected = np.asarray(w.detected, dtype=bool)
    assert int((measured & detected).sum()) == 0


def test_sp06_is_nonestimable_by_exact_rank_deficiency():
    B = _benchmark()
    worlds = {w.family: w for w in B.build_sparse_positive_worlds(seed_root=41000000)}
    w = worlds["SP06_RANK_DEFICIENT_NOT_ESTIMABLE"]
    assert w.estimability_truth == "NOT_ESTIMABLE_BY_CONSTRUCTION"
    x = np.asarray(w.design_matrix, dtype=float)
    measured_rows = np.asarray(w.support[:, 0], dtype=bool)
    assert np.linalg.matrix_rank(x[measured_rows]) < x.shape[1]


@pytest.mark.parametrize("family", [f for f in FAMILIES if "NOT_ESTIMABLE" not in f])
def test_estimable_worlds_have_positive_support_and_full_rank(family):
    B = _benchmark()
    worlds = {w.family: w for w in B.build_sparse_positive_worlds(seed_root=41000000)}
    w = worlds[family]
    assert w.estimability_truth == "ESTIMABLE"
    x = np.asarray(w.design_matrix, dtype=float)
    measured_rows = np.asarray(w.support[:, 0], dtype=bool)
    assert np.linalg.matrix_rank(x[measured_rows]) == x.shape[1]
    assert int((w.support & w.detected).sum()) > 0
    donors_with_positive = np.unique(w.donor_id[(w.support & w.detected).any(axis=1)])
    assert len(donors_with_positive) >= 4


def test_train_and_test_splits_are_donor_disjoint():
    B = _benchmark()
    for w in B.build_sparse_positive_worlds(seed_root=41000000):
        train = set(np.asarray(w.donor_id)[np.asarray(w.split) == "train"].tolist())
        test = set(np.asarray(w.donor_id)[np.asarray(w.split) == "test"].tolist())
        assert train
        assert test
        assert train.isdisjoint(test)


def test_unsupported_poison_values_do_not_change_serialized_fit_payload():
    B = _benchmark()
    worlds = list(B.build_sparse_positive_worlds(seed_root=41000000))
    original = B.serialize_fit_transport(worlds)
    target = worlds[4]
    poisoned = B.with_unsupported_poison(target, poison=9.9e29)
    worlds[4] = poisoned
    changed = B.serialize_fit_transport(worlds)
    assert original == changed


def _controller_payload(B):
    return B.serialize_controller_transport(B.build_sparse_positive_worlds(seed_root=41000000))


def test_adjudicator_accepts_complete_only_for_estimable_fits():
    B = _benchmark()
    A = _adjudicator()
    controller = _controller_payload(B)
    estimable = next(x for x in controller["fits"] if x["estimability_truth"] == "ESTIMABLE")
    result = A.adjudicate_sparse_positive(
        {"fits": [estimable]},
        [{
            "opaque_fit_id": estimable["opaque_fit_id"],
            "status": "COMPLETE",
            "finite": True,
            "detection_intercept_abs_error": 0.1,
            "positive_location_abs_error": 0.1,
            "donor_effect_rank_correlation": 0.7,
            "heldout_detection_logloss_delta": 0.0,
            "heldout_positive_logdensity_delta": 0.0,
        }],
    )
    assert result["status"] == "PASS"


def test_adjudicator_rejects_false_abstention_on_estimable_fit():
    B = _benchmark()
    A = _adjudicator()
    estimable = next(x for x in _controller_payload(B)["fits"] if x["estimability_truth"] == "ESTIMABLE")
    out = A.adjudicate_sparse_positive(
        {"fits": [estimable]},
        [{"opaque_fit_id": estimable["opaque_fit_id"], "status": "NOT_ESTIMABLE"}],
    )
    assert out["status"] == "FAIL"
    assert out["failures"][0]["reason"] == "FALSE_ABSTENTION"


def test_adjudicator_requires_not_estimable_for_constructed_nonestimability():
    B = _benchmark()
    A = _adjudicator()
    ne = next(x for x in _controller_payload(B)["fits"] if x["estimability_truth"] == "NOT_ESTIMABLE_BY_CONSTRUCTION")
    pass_out = A.adjudicate_sparse_positive(
        {"fits": [ne]},
        [{"opaque_fit_id": ne["opaque_fit_id"], "status": "NOT_ESTIMABLE"}],
    )
    assert pass_out["status"] == "PASS"
    false_certainty = A.adjudicate_sparse_positive(
        {"fits": [ne]},
        [{"opaque_fit_id": ne["opaque_fit_id"], "status": "COMPLETE", "finite": True}],
    )
    assert false_certainty["status"] == "FAIL"
    assert false_certainty["failures"][0]["reason"] == "FALSE_CERTAINTY"


def test_numerical_failure_is_always_hard_fail_even_for_nonestimable_truth():
    B = _benchmark()
    A = _adjudicator()
    ne = next(x for x in _controller_payload(B)["fits"] if x["estimability_truth"] == "NOT_ESTIMABLE_BY_CONSTRUCTION")
    out = A.adjudicate_sparse_positive(
        {"fits": [ne]},
        [{"opaque_fit_id": ne["opaque_fit_id"], "status": "NUMERICAL_FAILURE"}],
    )
    assert out["status"] == "FAIL"
    assert out["failures"][0]["reason"] == "NUMERICAL_FAILURE"


def test_recovery_threshold_failure_cannot_be_rescued_by_other_fits():
    B = _benchmark()
    A = _adjudicator()
    estimable = [x for x in _controller_payload(B)["fits"] if x["estimability_truth"] == "ESTIMABLE"][:2]
    records = []
    for i, fit in enumerate(estimable):
        records.append({
            "opaque_fit_id": fit["opaque_fit_id"],
            "status": "COMPLETE",
            "finite": True,
            "detection_intercept_abs_error": 0.1 if i == 0 else 0.8,
            "positive_location_abs_error": 0.1,
            "donor_effect_rank_correlation": 0.7,
            "heldout_detection_logloss_delta": 0.0,
            "heldout_positive_logdensity_delta": 0.0,
        })
    out = A.adjudicate_sparse_positive({"fits": estimable}, records)
    assert out["status"] == "FAIL"
    assert any(f["reason"] == "RECOVERY_GATE" for f in out["failures"])


def test_finalizer_binds_exact_v79_history_and_keeps_authority_off(tmp_path):
    B = _benchmark()
    F = _finalizer()
    worlds = B.build_sparse_positive_worlds(seed_root=41000000)
    receipt = F.build_package_receipt(worlds=worlds, repo_root=Path.cwd(), contract_path=CONTRACT_PATH)
    assert receipt["v79_immutable_binding"]["world_set_digest"] == "40458efea66e62f3f39cb773641d29c24b80505529baa65bdab31d3975a2a286"
    assert receipt["v79_immutable_binding"]["final_receipt_sha256"] == "ef10852e534fe8a83c3aebd832ad3a531d755d06185464441494712818e8abfd"
    assert receipt["fit_transport_sha256"] != receipt["controller_transport_sha256"]
    assert not any(receipt["authority"].values())
    path = tmp_path / "receipt.json"
    F.write_transport_once(path, receipt)
    with pytest.raises(ValueError, match="exists"):
        F.write_transport_once(path, receipt)


def test_finalizer_refuses_v79_binding_drift(tmp_path):
    B = _benchmark()
    F = _finalizer()
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    contract["v79_immutable_binding"]["historical_result"] = "PASS"
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(contract), encoding="utf-8")
    with pytest.raises(ValueError, match="V79|binding|historical"):
        F.build_package_receipt(
            worlds=B.build_sparse_positive_worlds(seed_root=41000000),
            repo_root=Path.cwd(),
            contract_path=bad,
        )
