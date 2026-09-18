import copy

import pytest

from sea_ad_jepa.v5.masking_structural_controls_v1 import build_structural_control_receipt


def rows():
    return [{
        "method":"UNIFORM_RANDOM",
        "score":0.1,
        "uniform_score":0.1,
        "mask_cardinality":5,
        "uniform_mask_cardinality":5,
        "targeted_n":0,
        "effective_targeted_n":0,
        "targeted_cols":(),
    }]


def test_structural_receipt_computes_replay_and_identity():
    a=rows()
    r=build_structural_control_receipt(a, copy.deepcopy(a))
    assert r.replay_exact
    assert r.untreated_identity_exact
    assert r.no_privileged_metadata


def test_replay_mismatch_fails_closed():
    a=rows(); b=rows(); b[0]["score"]=0.2
    with pytest.raises(ValueError, match="replay"):
        build_structural_control_receipt(a,b)


def test_uniform_identity_mismatch_fails_closed():
    a=rows(); a[0]["score"]=0.2
    with pytest.raises(ValueError, match="identity"):
        build_structural_control_receipt(a,copy.deepcopy(a))
