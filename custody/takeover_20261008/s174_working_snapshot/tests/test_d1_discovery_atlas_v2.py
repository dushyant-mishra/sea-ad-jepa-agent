from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "v4"))

import d1_discovery_atlas_v2 as atlas  # noqa: E402
from d1_real_data_derivation_core_v1 import MEASURED_SCALAR  # noqa: E402


def derivation_fixture(*, D=3, blocks=None):
    if blocks is None:
        blocks = [[0], [1, 2], [3]]
    # Sign of axis 0 is intentionally negative in its largest loading. The
    # object builder must preserve this exact sign rather than QR-flipping it.
    vectors = np.array([
        [-1.0, 0.0, 0.0],
        [ 0.0, 1.0, 0.0],
        [ 0.0, 0.0, 1.0],
        [ 0.0, 0.0, 0.0],
    ])
    return {
        "D": D,
        "eigenvalues": [9.0, 4.0, 4.0, 1.0],
        "eigenvectors_leading": vectors[:, :D].tolist(),
        "degeneracy_blocks": blocks,
        "real_overlap_lower": [0.90, 0.91, 0.95],
        "null_overlap_upper": [0.20, 0.30, 0.40],
    }


def test_discovery_objects_preserve_isolated_axis_sign_and_block_identity() -> None:
    objects = atlas.build_discovery_objects(derivation_fixture())
    assert [o.program_id for o in objects] == [
        "D1OBJ-B0-R1-1", "D1OBJ-B1-R2-3"]
    isolated, block = objects
    assert isolated.object_type == "ISOLATED_AXIS"
    assert isolated.basis[0, 0] == -1.0
    assert isolated.magnitude == pytest.approx(3.0)
    assert block.object_type == "DEGENERATE_SUBSPACE"
    assert block.variance == pytest.approx(8.0)
    assert block.magnitude == pytest.approx(math.sqrt(8.0))
    assert block.stability_margin == pytest.approx(0.95 - 0.40)


def test_D_may_not_cut_through_a_degenerate_block() -> None:
    bad = derivation_fixture(D=2)
    bad["eigenvectors_leading"] = np.asarray(
        derivation_fixture()["eigenvectors_leading"])[:, :2].tolist()
    with pytest.raises(ValueError, match="cuts through block"):
        atlas.build_discovery_objects(bad)


def test_degeneracy_blocks_must_be_ordered_not_merely_a_partition() -> None:
    bad = derivation_fixture(blocks=[[1, 2], [0], [3]])
    with pytest.raises(ValueError, match="ordered"):
        atlas.build_discovery_objects(bad)


def test_isolated_axis_score_uses_preserved_global_sign() -> None:
    obj = atlas.build_discovery_objects(derivation_fixture())[0]
    states = np.array([[2.0, 0, 0, 0], [-3.0, 0, 0, 0]])
    score = atlas.score_object(states, np.zeros(4), obj)
    assert score.tolist() == [-2.0, 3.0]


def test_degenerate_subspace_score_is_rotation_invariant() -> None:
    obj = atlas.build_discovery_objects(derivation_fixture())[1]
    states = np.array([
        [0.0, 3.0, 4.0, 0.0],
        [0.0, -5.0, 12.0, 0.0],
    ])
    original = atlas.score_object(states, np.zeros(4), obj)
    theta = 0.73
    rotation = np.array([
        [math.cos(theta), -math.sin(theta)],
        [math.sin(theta),  math.cos(theta)],
    ])
    rotated = atlas.DiscoveryObject(
        **{**obj.__dict__, "basis": obj.basis @ rotation})
    after = atlas.score_object(states, np.zeros(4), rotated)
    assert np.allclose(original, [5.0, 13.0])
    assert np.allclose(after, original, atol=1e-12)


def test_weighted_percentiles_give_all_ties_the_same_value() -> None:
    values = np.array([0.0, 1.0, 1.0, 2.0])
    weights = np.array([1.0, 1.0, 3.0, 1.0])
    pct = atlas.weighted_percentile_midrank(values, weights)
    assert pct[1] == pytest.approx(pct[2])
    # Tie mass=4, mass below=1, total=6 => midpoint=(1+2)/6=0.5.
    assert pct[1] == pytest.approx(0.5)


def test_cell_ranking_tie_percentile_is_row_order_invariant() -> None:
    obj = atlas.build_discovery_objects(derivation_fixture())[0]
    kwargs = dict(
        donors=["D1", "D1", "D2", "D2"],
        sources=["S", "S", "S", "S"],
        operators=[0, 0, 0, 0],
        scores=[0.0, 1.0, 1.0, 2.0],
        weights=[0.5, 0.5, 0.5, 0.5],
        obj=obj,
        two_sided_tail_probabilities=[0.25],
    )
    first = atlas.cell_ranking_table(
        cell_ids=["a", "b", "c", "d"], **kwargs)
    second = atlas.cell_ranking_table(
        cell_ids=["a", "c", "b", "d"],
        donors=kwargs["donors"],
        sources=kwargs["sources"],
        operators=kwargs["operators"],
        scores=kwargs["scores"],
        weights=kwargs["weights"],
        obj=obj,
        two_sided_tail_probabilities=[0.25],
    )
    assert first[1]["global_weighted_percentile"] == pytest.approx(
        first[2]["global_weighted_percentile"])
    assert second[1]["global_weighted_percentile"] == pytest.approx(
        second[2]["global_weighted_percentile"])


def test_cell_ranking_rejects_negative_or_nonfinite_weights() -> None:
    obj = atlas.build_discovery_objects(derivation_fixture())[0]
    base = dict(
        cell_ids=["a", "b"], donors=["D1", "D2"], sources=["S", "S"],
        operators=[0, 0], scores=[1.0, 2.0], obj=obj,
        two_sided_tail_probabilities=[0.1])
    with pytest.raises(ValueError, match="invalid score weight"):
        atlas.cell_ranking_table(weights=[1.0, -1.0], **base)
    with pytest.raises(ValueError, match="nonfinite"):
        atlas.cell_ranking_table(weights=[1.0, float("nan")], **base)


def test_measured_zero_is_data_and_unmeasured_is_not() -> None:
    stats = atlas.AssociationStats.zeros(2)
    score = np.array([-1.0, 1.0])
    expression = np.array([[0.0, 100.0], [2.0, 200.0]])
    # address 0 is measured including the zero. address 1 is structurally absent.
    state = np.array([MEASURED_SCALAR, 0], dtype=np.uint8)
    stats.update(
        score=score, expression=expression, observation_state=state,
        weights=np.ones(2))
    out = stats.effects()
    assert out["effect"][0] == pytest.approx(1.0)
    assert bool(out["not_estimable"][0]) is False
    assert np.isnan(out["effect"][1])
    assert bool(out["not_estimable"][1]) is True
    assert out["measured_fraction"][0] == pytest.approx(1.0)
    assert out["measured_fraction"][1] == pytest.approx(0.0)


def test_donor_recurrence_does_not_sign_flip_a_negative_donor() -> None:
    global_effect = np.array([1.0, 2.0, 3.0])
    donors = {
        "same": {"effect": np.array([1.0, 2.0, 3.0])},
        "opposite": {"effect": np.array([-1.0, -2.0, -3.0])},
        "partial": {"effect": np.array([1.0, np.nan, 3.0])},
    }
    out = atlas.donor_recurrence_summary(global_effect, donors)
    assert out["cosines"]["same"] == pytest.approx(1.0)
    assert out["cosines"]["opposite"] == pytest.approx(-1.0)
    assert out["donor_diagnostics"]["partial"]["common_finite_addresses"] == 2
    assert out["positive_fraction"] == pytest.approx(2 / 3)


def test_source_operator_consistency_uses_the_less_consistent_family() -> None:
    global_effect = np.array([1.0, 0.0])
    sources = {
        "A": {"effect": np.array([1.0, 0.0])},
        "B": {"effect": np.array([0.8, 0.6])},
    }
    operators = {
        "0": {"effect": np.array([1.0, 0.0])},
        "1": {"effect": np.array([0.0, 1.0])},
    }
    out = atlas.source_operator_consistency_summary(
        global_effect, sources, operators)
    assert out["source_consistency"] > out["operator_consistency"]
    assert out["source_operator_consistency"] == pytest.approx(
        out["operator_consistency"])


def test_molecular_concentration_has_known_effective_address_count() -> None:
    out = atlas.molecular_concentration(np.array([1.0, -1.0, 0.0, np.nan]))
    # two equal nonzero addresses => HHI=1/2 and effective count=2.
    assert out["molecular_concentration"] == pytest.approx(0.5)
    assert out["molecular_effective_address_count"] == pytest.approx(2.0)


def test_bootstrap_effect_block_matches_explicit_donor_reconstruction() -> None:
    donors = []
    for shift in (0.0, 1.0, 2.0):
        stats = atlas.AssociationStats.zeros(2)
        score = np.array([-1.0, 0.0, 1.0])
        expression = np.stack([
            score + shift,
            2.0 * score - shift,
        ], axis=1)
        stats.update(
            score=score,
            expression=expression,
            observation_state=np.array([MEASURED_SCALAR, MEASURED_SCALAR]),
            weights=np.ones(3))
        donors.append(stats)
    counts = np.array([
        [1, 1, 1],
        [2, 0, 1],
        [0, 3, 0],
    ])
    got = atlas.bootstrap_effect_block(
        donors, bootstrap_counts=counts, address_slice=slice(0, 2))
    expected = []
    helper = atlas.AssociationStats.zeros(2)
    for row in counts:
        combined = helper.scaled_sum(row, donors)
        expected.append(combined.effects()["effect"])
    assert np.allclose(got, np.asarray(expected), equal_nan=True)


def test_catalog_keeps_not_estimable_object_without_favorable_sentinel() -> None:
    rows = [
        {
            "program_id": "good", "stability_margin": 0.2,
            "donor_recurrence": 0.8, "magnitude": 3.0,
            "source_operator_consistency": 0.7,
            "measurement_support": 0.9, "molecular_concentration": 0.1,
        },
        {
            "program_id": "missing", "stability_margin": 999.0,
            "donor_recurrence": None, "magnitude": 999.0,
            "source_operator_consistency": 999.0,
            "measurement_support": 999.0, "molecular_concentration": 999.0,
        },
    ]
    out = atlas.order_catalog(rows)
    assert [r["program_id"] for r in out["ordered_estimable"]] == ["good"]
    assert out["not_estimable"][0]["program_id"] == "missing"
    assert out["not_estimable"][0]["catalog_order_status"] == (
        atlas.STOP_CATALOG_NOT_ESTIMABLE)


def test_representative_donors_use_donor_primary_weights() -> None:
    rows = [
        {"donor_id": "D1", "raw_score": 0.0, "donor_primary_weight": 0.9},
        {"donor_id": "D1", "raw_score": 10.0, "donor_primary_weight": 0.1},
        {"donor_id": "D2", "raw_score": 2.0, "donor_primary_weight": 0.5},
        {"donor_id": "D2", "raw_score": 2.0, "donor_primary_weight": 0.5},
    ]
    out = atlas.representative_donors(rows, each_tail=2)
    by_id = {
        r["donor_id"]: r
        for r in out["lowest"]
    }
    assert by_id["D1"]["weighted_mean_score"] == pytest.approx(1.0)
    assert by_id["D2"]["weighted_mean_score"] == pytest.approx(2.0)
