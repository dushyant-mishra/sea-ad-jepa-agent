import numpy as np
import pytest

from sea_ad_jepa.v5.structure_preservation_probe_v1 import audit_pair_structure_preservation_v1


def _fixture():
    rng=np.random.default_rng(101)
    base=rng.normal(size=(40,6))
    good=base + 0.01*rng.normal(size=base.shape)
    pairs=[(i,(i+1)%40) for i in range(40)] + [(i,(i+7)%40) for i in range(40)]
    return base,good,pairs


def test_small_perturbation_preserves_prefrozen_pair_geometry_without_authority_escalation():
    base,good,pairs=_fixture()
    out=audit_pair_structure_preservation_v1(
        baseline_representation=base,
        candidate_representation=good,
        pair_indices=pairs,
        pair_plan_sha256="a"*64,
        parent_sha256="b"*64,
    )
    assert out["pair_count"] == len(pairs)
    assert out["distance_spearman"] > 0.99
    assert out["median_relative_distance_change"] < 0.05
    assert out["authority_classification"] == "STRUCTURE_PRESERVATION_MECHANICS_ONLY__NOT_BIOLOGICAL_AUTHORITY"
    assert out["d_shared_real_outcome_access_authorized"] is False
    assert out["training_authorized"] is False


def test_scrambled_geometry_is_visible():
    base,_,pairs=_fixture()
    candidate=base[::-1].copy()
    out=audit_pair_structure_preservation_v1(
        baseline_representation=base,
        candidate_representation=candidate,
        pair_indices=pairs,
        pair_plan_sha256="a"*64,
        parent_sha256="b"*64,
    )
    assert out["distance_spearman"] < 0.8 or out["median_relative_distance_change"] > 0.25


def test_pairs_must_be_prefrozen_valid_distinct_indices():
    base,good,_=_fixture()
    common=dict(
        baseline_representation=base,
        candidate_representation=good,
        pair_plan_sha256="a"*64,
        parent_sha256="b"*64,
    )
    with pytest.raises(ValueError,match="pair_indices"):
        audit_pair_structure_preservation_v1(pair_indices=[],**common)
    with pytest.raises(ValueError,match="distinct"):
        audit_pair_structure_preservation_v1(pair_indices=[(0,0)],**common)
    with pytest.raises(ValueError,match="range"):
        audit_pair_structure_preservation_v1(pair_indices=[(0,99)],**common)
    with pytest.raises(ValueError,match="integer"):
        audit_pair_structure_preservation_v1(pair_indices=[(0,1.5)],**common)


def test_duplicate_undirected_pairs_are_rejected_to_avoid_hidden_reweighting():
    base,good,_=_fixture()
    with pytest.raises(ValueError,match="duplicate"):
        audit_pair_structure_preservation_v1(
            baseline_representation=base,
            candidate_representation=good,
            pair_indices=[(0,1),(1,0)],
            pair_plan_sha256="a"*64,
            parent_sha256="b"*64,
        )


def test_outcome_feedback_or_training_authority_is_forbidden():
    base,good,pairs=_fixture()
    common=dict(
        baseline_representation=base,
        candidate_representation=good,
        pair_indices=pairs,
        pair_plan_sha256="a"*64,
        parent_sha256="b"*64,
    )
    for field in ("d_shared_outcomes_used","protected_data_used","pathology_used","training_authorized"):
        with pytest.raises(RuntimeError,match="STOP_STRUCTURE_PRESERVATION_FORBIDDEN"):
            audit_pair_structure_preservation_v1(**common,**{field:True})


def test_hashes_and_finite_aligned_matrices_are_required():
    base,good,pairs=_fixture()
    with pytest.raises(ValueError):
        audit_pair_structure_preservation_v1(
            baseline_representation=base,candidate_representation=good,pair_indices=pairs,
            pair_plan_sha256="bad",parent_sha256="b"*64,
        )
    bad=good.copy(); bad[0,0]=np.nan
    with pytest.raises(ValueError,match="finite"):
        audit_pair_structure_preservation_v1(
            baseline_representation=base,candidate_representation=bad,pair_indices=pairs,
            pair_plan_sha256="a"*64,parent_sha256="b"*64,
        )
