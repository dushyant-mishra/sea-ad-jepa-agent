import numpy as np
import pytest

from sea_ad_jepa.v5.structure_preservation_probe_v1 import (
    audit_pair_structure_preservation_v1,
    canonical_pair_indices_sha256,
)

ROW_SHA="c"*64


def _fixture():
    rng=np.random.default_rng(101)
    base=rng.normal(size=(40,6))
    good=base + 0.01*rng.normal(size=base.shape)
    pairs=[(i,(i+1)%40) for i in range(40)] + [(i,(i+7)%40) for i in range(40)]
    return base,good,pairs


def _common(base,good,pairs):
    return dict(
        baseline_representation=base,
        candidate_representation=good,
        pair_indices=pairs,
        expected_pair_indices_sha256=canonical_pair_indices_sha256(pairs),
        pair_plan_sha256="a"*64,
        parent_sha256="b"*64,
        baseline_row_identity_sha256=ROW_SHA,
        candidate_row_identity_sha256=ROW_SHA,
    )


def test_small_perturbation_preserves_prefrozen_pair_geometry_without_authority_escalation():
    base,good,pairs=_fixture()
    out=audit_pair_structure_preservation_v1(**_common(base,good,pairs))
    assert out["pair_count"] == len(pairs)
    assert out["distance_spearman"] > 0.99
    assert out["median_relative_distance_change"] < 0.05
    assert out["pair_indices_sha256"] == canonical_pair_indices_sha256(pairs)
    assert out["row_identity_sha256"] == ROW_SHA
    assert out["authority_classification"] == "STRUCTURE_PRESERVATION_MECHANICS_ONLY__NOT_BIOLOGICAL_AUTHORITY"
    assert out["d_shared_real_outcome_access_authorized"] is False
    assert out["training_authorized"] is False


def test_scrambled_geometry_is_visible():
    base,_,pairs=_fixture()
    candidate=base[::-1].copy()
    out=audit_pair_structure_preservation_v1(**_common(base,candidate,pairs))
    assert out["distance_spearman"] < 0.8 or out["median_relative_distance_change"] > 0.25


def test_pairs_must_be_prefrozen_valid_distinct_indices():
    base,good,pairs=_fixture()
    common=_common(base,good,pairs)
    common.pop("pair_indices")
    common.pop("expected_pair_indices_sha256")
    with pytest.raises(ValueError,match="pair_indices"):
        audit_pair_structure_preservation_v1(pair_indices=[],expected_pair_indices_sha256="d"*64,**common)
    with pytest.raises(ValueError,match="distinct"):
        audit_pair_structure_preservation_v1(pair_indices=[(0,0)],expected_pair_indices_sha256="d"*64,**common)
    with pytest.raises(ValueError,match="range"):
        audit_pair_structure_preservation_v1(pair_indices=[(0,99)],expected_pair_indices_sha256="d"*64,**common)
    with pytest.raises(ValueError,match="integer"):
        audit_pair_structure_preservation_v1(pair_indices=[(0,1.5)],expected_pair_indices_sha256="d"*64,**common)


def test_duplicate_undirected_pairs_are_rejected_to_avoid_hidden_reweighting():
    base,good,_=_fixture()
    with pytest.raises(ValueError,match="duplicate"):
        audit_pair_structure_preservation_v1(
            baseline_representation=base,
            candidate_representation=good,
            pair_indices=[(0,1),(1,0)],
            expected_pair_indices_sha256="d"*64,
            pair_plan_sha256="a"*64,
            parent_sha256="b"*64,
            baseline_row_identity_sha256=ROW_SHA,
            candidate_row_identity_sha256=ROW_SHA,
        )


def test_pair_list_substitution_and_row_reordering_fail_closed():
    base,good,pairs=_fixture()
    common=_common(base,good,pairs)
    bad_pairs=list(pairs); bad_pairs[-1]=(0,9)
    common["pair_indices"]=bad_pairs
    with pytest.raises(RuntimeError,match="PAIR_BINDING"):
        audit_pair_structure_preservation_v1(**common)

    common=_common(base,good,pairs)
    common["candidate_row_identity_sha256"]="d"*64
    with pytest.raises(RuntimeError,match="ROW_IDENTITY"):
        audit_pair_structure_preservation_v1(**common)


def test_outcome_feedback_or_training_authority_is_forbidden():
    base,good,pairs=_fixture()
    common=_common(base,good,pairs)
    for field in ("d_shared_outcomes_used","protected_data_used","pathology_used","training_authorized"):
        with pytest.raises(RuntimeError,match="STOP_STRUCTURE_PRESERVATION_FORBIDDEN"):
            audit_pair_structure_preservation_v1(**common,**{field:True})


def test_hashes_and_finite_aligned_matrices_are_required():
    base,good,pairs=_fixture()
    common=_common(base,good,pairs)
    common["pair_plan_sha256"]="bad"
    with pytest.raises(ValueError):
        audit_pair_structure_preservation_v1(**common)
    bad=good.copy(); bad[0,0]=np.nan
    common=_common(base,bad,pairs)
    with pytest.raises(ValueError,match="finite"):
        audit_pair_structure_preservation_v1(**common)
