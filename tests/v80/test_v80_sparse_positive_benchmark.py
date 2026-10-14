from __future__ import annotations

import importlib
import importlib.util
import inspect
import json
from pathlib import Path
import tempfile

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
    assert importlib.util.find_spec("scripts.v80.v80_sparse_positive_benchmark") is not None
    return importlib.import_module("scripts.v80.v80_sparse_positive_benchmark")


def _adjudicator():
    assert importlib.util.find_spec("scripts.v80.v80_sparse_positive_adjudicator") is not None
    return importlib.import_module("scripts.v80.v80_sparse_positive_adjudicator")


def _finalizer():
    assert importlib.util.find_spec("scripts.v80.finalize_v80_sparse_positive_package") is not None
    return importlib.import_module("scripts.v80.finalize_v80_sparse_positive_package")


def _payloads(B):
    worlds = B.build_sparse_positive_worlds(seed_root=41000000)
    return worlds, B.serialize_fit_transport(worlds), B.serialize_controller_transport(worlds)


def _oracle_record(world, gene, fit_id):
    return {
        "opaque_fit_id": fit_id,
        "status": "COMPLETE",
        "detection_fixed_effect_estimates": [
            float(world.latent_detection_intercept[gene]),
            *[float(x) for x in world.detection_fixed_effect_tail],
        ],
        "positive_location_estimate": float(world.latent_positive_location[gene]),
        "detection_donor_effect_estimates": world.latent_detection_donor_effect.tolist(),
        "positive_donor_effect_estimates": world.latent_positive_donor_effect.tolist(),
        "detection_probability": world.latent_detection_probability[:, gene].tolist(),
        "positive_mu": world.latent_positive_mu[:, gene].tolist(),
        "positive_sigma": float(world.positive_sigma),
    }


def test_contract_exact_estimand_v79_binding_and_authority_off():
    c = json.loads(CONTRACT_PATH.read_text())
    assert tuple(c["challenge_families"]) == FAMILIES
    assert c["requested_estimand"]["scope"] == "PER_GENE_FULL_TWO_PART_MODEL"
    assert c["requested_estimand"]["complete_requires_all_requested_components_estimable"] is True
    assert c["v79_immutable_binding"]["historical_result"] == "NOT_QUALIFIED"
    assert not any(c["authority"].values())


def test_generator_source_has_no_historical_failed_fit_ids():
    source = inspect.getsource(_benchmark())
    assert all(fit_id not in source for fit_id in FAILED_V79_IDS)


def test_deterministic_exact_families_and_opaque_fit_transport():
    B = _benchmark()
    a = B.build_sparse_positive_worlds(seed_root=41000000)
    b = B.build_sparse_positive_worlds(seed_root=41000000)
    assert tuple(w.family for w in a) == FAMILIES
    assert B.benchmark_identity(a) == B.benchmark_identity(b)
    fit = B.serialize_fit_transport(a)
    B.validate_fit_transport(fit)
    raw = json.dumps(fit, sort_keys=True)
    assert all(f not in raw for f in FAMILIES)
    assert all(x not in raw for x in FAILED_V79_IDS)
    assert "estimability_truth" not in raw
    assert "latent_detection_probability" not in raw


def test_heldout_outcomes_are_absent_fit_side_and_present_controller_side():
    B = _benchmark()
    worlds, fit, controller = _payloads(B)
    for fit_world in fit["worlds"]:
        split = np.asarray(fit_world["split"])
        test = split == "test"
        assert not np.asarray(fit_world["outcome_observed"], dtype=bool)[test].any()
        assert not np.asarray(fit_world["detected"], dtype=bool)[test].any()
        assert np.all(np.asarray(fit_world["positive_value"], dtype=float)[test] == 0.0)
    estimable_truth = next(x for x in controller["fits"] if x["estimability_truth"] == "ESTIMABLE")
    assert len(estimable_truth["observed_detected"]) == len(worlds[0].donor_id)
    assert len(estimable_truth["observed_positive_value"]) == len(worlds[0].donor_id)


def test_sp05_and_sp06_are_nonestimable_for_declared_mathematical_reasons():
    B = _benchmark()
    worlds = {w.family: w for w in B.build_sparse_positive_worlds(seed_root=41000000)}
    sp05 = worlds["SP05_NO_POSITIVE_SUPPORT_NOT_ESTIMABLE"]
    assert sp05.estimability_truth == B.NOT_ESTIMABLE
    assert sp05.nonestimability_reason == "NO_MEASURED_POSITIVE_OBSERVATIONS_FOR_POSITIVE_COMPONENT"
    assert not (sp05.support & sp05.detected).any()
    sp06 = worlds["SP06_RANK_DEFICIENT_NOT_ESTIMABLE"]
    assert sp06.estimability_truth == B.NOT_ESTIMABLE
    assert sp06.nonestimability_reason == "DETECTION_DESIGN_EXACT_RANK_DEFICIENCY_CELL_CLASS_EQUALS_SOURCE"
    assert np.linalg.matrix_rank(sp06.design_matrix[sp06.support[:, 0]]) < sp06.design_matrix.shape[1]


@pytest.mark.parametrize("family", [f for f in FAMILIES if "NOT_ESTIMABLE" not in f])
def test_estimable_worlds_are_full_rank_and_have_per_gene_train_test_positives(family):
    B = _benchmark()
    w = {x.family: x for x in B.build_sparse_positive_worlds(seed_root=41000000)}[family]
    assert w.estimability_truth == B.ESTIMABLE
    assert np.linalg.matrix_rank(w.design_matrix[w.support[:, 0]]) == w.design_matrix.shape[1]
    for gene in range(w.detected.shape[1]):
        positive = w.support[:, gene] & w.detected[:, gene]
        donors = np.unique(w.donor_id[positive])
        assert len(donors) >= 4
        assert np.any(positive & (w.split == "train"))
        assert np.any(positive & (w.split == "test"))


def test_donor_splits_disjoint_and_unsupported_poison_invariant():
    B = _benchmark()
    worlds = list(B.build_sparse_positive_worlds(seed_root=41000000))
    for w in worlds:
        train = set(w.donor_id[w.split == "train"].tolist())
        test = set(w.donor_id[w.split == "test"].tolist())
        assert train and test and train.isdisjoint(test)
    original = B.serialize_fit_transport(worlds)
    worlds[4] = B.with_unsupported_poison(worlds[4], poison=9.9e29)
    assert B.serialize_fit_transport(worlds) == original


def test_controller_computes_metrics_and_rejects_estimator_self_scoring():
    B = _benchmark(); A = _adjudicator()
    worlds, fit, controller = _payloads(B)
    world_by_id = {w.opaque_id: w for w in worlds}
    truths = [x for x in controller["fits"] if x["estimability_truth"] == B.ESTIMABLE]
    records = [
        _oracle_record(world_by_id[t["opaque_world_id"]], int(t["gene_index"]), t["opaque_fit_id"])
        for t in truths
    ]
    out = A.adjudicate_sparse_positive({"fits": truths}, fit, records)
    assert out["status"] == "PASS", out["failures"]
    assert out["metrics_computed_by_controller"] is True
    assert out["heldout_outcomes_opened_controller_side_only"] is True
    bad = dict(records[0]); bad["detection_intercept_abs_error"] = 0.0
    with pytest.raises(ValueError, match="self-report"):
        A.adjudicate_sparse_positive({"fits": [truths[0]]}, fit, [bad])


def test_status_semantics_false_abstention_false_certainty_and_numerical_failure():
    B = _benchmark(); A = _adjudicator()
    _, fit, controller = _payloads(B)
    est = next(x for x in controller["fits"] if x["estimability_truth"] == B.ESTIMABLE)
    ne = next(x for x in controller["fits"] if x["estimability_truth"] == B.NOT_ESTIMABLE)
    out = A.adjudicate_sparse_positive({"fits": [est]}, fit, [{"opaque_fit_id": est["opaque_fit_id"], "status": "NOT_ESTIMABLE"}])
    assert out["failures"][0]["reason"] == "FALSE_ABSTENTION"
    out = A.adjudicate_sparse_positive({"fits": [ne]}, fit, [{"opaque_fit_id": ne["opaque_fit_id"], "status": "COMPLETE", "detection_fixed_effect_estimates": [0,0,0,0], "positive_location_estimate": 0, "detection_donor_effect_estimates": [0]*24, "positive_donor_effect_estimates": [0]*24, "detection_probability": [0.5]*1920, "positive_mu": [0]*1920, "positive_sigma": 1}])
    assert out["failures"][0]["reason"] == "FALSE_CERTAINTY"
    out = A.adjudicate_sparse_positive({"fits": [ne]}, fit, [{"opaque_fit_id": ne["opaque_fit_id"], "status": "NUMERICAL_FAILURE"}])
    assert out["failures"][0]["reason"] == "NUMERICAL_FAILURE"
    out = A.adjudicate_sparse_positive({"fits": [ne]}, fit, [{"opaque_fit_id": ne["opaque_fit_id"], "status": "NOT_ESTIMABLE"}])
    assert out["status"] == "PASS"


def test_finalizer_binds_v79_and_refuses_drift(tmp_path):
    B = _benchmark(); F = _finalizer()
    worlds = B.build_sparse_positive_worlds(seed_root=41000000)
    receipt = F.build_package_receipt(worlds=worlds, repo_root=Path.cwd(), contract_path=CONTRACT_PATH)
    assert receipt["v79_immutable_binding"]["world_set_digest"] == "40458efea66e62f3f39cb773641d29c24b80505529baa65bdab31d3975a2a286"
    assert receipt["v79_immutable_binding"]["final_receipt_sha256"] == "ef10852e534fe8a83c3aebd832ad3a531d755d06185464441494712818e8abfd"
    assert receipt["fit_transport_sha256"] != receipt["controller_transport_sha256"]
    assert not any(receipt["authority"].values())
    target = tmp_path / "receipt.json"; F.write_transport_once(target, receipt)
    with pytest.raises(ValueError, match="exists"):
        F.write_transport_once(target, receipt)
    c = json.loads(CONTRACT_PATH.read_text()); c["v79_immutable_binding"]["historical_result"] = "PASS"
    with tempfile.TemporaryDirectory(dir=Path.cwd()) as td:
        bad = Path(td) / "bad.json"; bad.write_text(json.dumps(c))
        with pytest.raises(ValueError, match="V79|binding|historical"):
            F.build_package_receipt(worlds=worlds, repo_root=Path.cwd(), contract_path=bad)
