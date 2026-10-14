from __future__ import annotations

import math
import pytest

import scripts.v5.td_r1_known_truth_stress_v1 as S


def _row(donor, rid, qx, qy, *, source="SEA_AD", operator="opA", support="S", eligible=True, weight=1):
    return {
        "donor_id": donor,
        "relation_id": rid,
        "source_x": source,
        "source_y": source,
        "operator_x": operator,
        "operator_y": operator,
        "support_stratum_x": support,
        "support_stratum_y": support,
        "q_x": qx,
        "q_y": qy,
        "eligible": eligible,
        "cell_weight": weight,
    }


def test_scale_free_relation_is_invariant_to_strictly_increasing_distance_transform():
    pairs = [(0.1, 0.4), (2.0, 1.0), (3.0, 3.0)]
    for dij, dik in pairs:
        q = S.anchored_triplet_order(dij, dik)
        q2 = S.anchored_triplet_order(math.exp(dij), math.exp(dik))
        assert q2 == q


def test_donor_primary_summary_cannot_be_swamped_by_large_donor():
    rows = [_row("D_BIG", f"R{i}", 1, 1, weight=1000) for i in range(100)]
    rows.append(_row("D_SMALL", "R100", 1, -1, weight=1))
    out = S.summarize_recurrence(rows, minimum_informative_relations_per_donor=1)
    assert out["donor_agreement"] == {"D_BIG": 1.0, "D_SMALL": 0.0}
    assert out["donor_mean_agreement"] == 0.5
    assert out["cell_weighted_agreement_has_authority"] is False


def test_source_operator_or_support_cross_stratum_pairing_is_rejected():
    bad = _row("D1", "R1", 1, 1); bad["source_y"] = "HVS"
    with pytest.raises(S.R1StressError, match="source"):
        S.summarize_recurrence([bad], minimum_informative_relations_per_donor=1)
    bad = _row("D1", "R1", 1, 1); bad["operator_y"] = "opB"
    with pytest.raises(S.R1StressError, match="operator"):
        S.summarize_recurrence([bad], minimum_informative_relations_per_donor=1)
    bad = _row("D1", "R1", 1, 1); bad["support_stratum_y"] = "OTHER"
    with pytest.raises(S.R1StressError, match="support"):
        S.summarize_recurrence([bad], minimum_informative_relations_per_donor=1)


def test_sparse_or_unresolved_support_abstains_instead_of_becoming_failure():
    out = S.summarize_recurrence(
        [_row("D1", "R1", 1, 1, eligible=False), _row("D2", "R2", 1, -1, eligible=False)],
        minimum_informative_relations_per_donor=1,
    )
    assert out["status"] == "NOT_ESTIMABLE_SUPPORT"
    assert out["donor_mean_agreement"] is None
    assert out["failed_biology"] is False


def test_relation_ties_are_preserved_as_relation_ties_not_imputed_direction():
    assert S.anchored_triplet_order(2.0, 2.0) == 0
    out = S.summarize_recurrence(
        [_row("D1", "R1", 0, 0), _row("D2", "R2", 0, 1)],
        minimum_informative_relations_per_donor=1,
    )
    assert out["donor_agreement"] == {"D1": 1.0, "D2": 0.0}


def test_td57b_semantic_fixture_matches_anchored_cell_triplet_not_address_triplet():
    fixture = S.td57b_semantic_fixture()
    assert fixture["relation_object"] == "ANCHORED_CELL_TRIPLET_ORDER"
    assert fixture["distance_views"] == "DISJOINT_MOLECULAR_VIEWS"
    assert fixture["donor_primary"] is True
    assert fixture["matched_null_preserves"] == ["donor", "operator", "depth", "detection"]
    assert fixture["imports_historical_threshold"] is False


def test_distribution_stress_profile_preserves_real_etl_extremes_without_claiming_biology():
    p = S.foundation_distribution_stress_profile()
    assert (p["donor_cells_min"], p["donor_cells_max"]) == (81, 174111)
    assert (p["operator_cells_min"], p["operator_cells_max"]) == (179, 732360)
    assert (p["address_operator_support_min"], p["address_operator_support_max"]) == (0, 42)
    assert p["HVS_measured_scalar_fraction"] < p["NPH52_measured_scalar_fraction"] < p["SEA_AD_measured_scalar_fraction"]
    assert p["biological_threshold_authority"] is False


def test_all_stress_qualification_authority_is_false():
    q = S.qualify_r1_known_truth_stress()
    assert q["status"] == "PASS_R1_KNOWN_TRUTH_STRESS_MECHANICS"
    assert all(value is False for value in q["authority"].values())
    assert q["human_candidate_pass_authorized"] is False
