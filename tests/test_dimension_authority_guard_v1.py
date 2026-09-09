import pytest

from sea_ad_jepa.v5.dimension_authority_guard_v1 import DimensionAuthorityGuardV1


def guard():
    return DimensionAuthorityGuardV1("meta",4553407,104,True,True,True)


def good():
    return {
        "metadata_sha256":"meta",
        "cells":4553407,
        "donors":104,
        "population_mode":"FULL_READER_FIT_STREAM",
        "expression_location_terminal":"PASS_D1_V2_EXPRESSION_LOCATION_BINDING",
        "estimand":"EQUAL_DONOR__EQUAL_CELL_WITHIN_DONOR",
        "null_geometry":"FULL_REFIT_EVERY_REPLICATE",
        "sampled_stratum_cap":None,
        "synthetic_data_used":False,
        "pathology_used":False,
        "checkpoint_outcomes_used":False,
        "D_shared":7,
        "D_private":0,
        "D_total":7,
        "D_obs":3,
    }


def test_good():
    assert guard().validate(good())["passed"]


def test_fixed_axis_null_rejected():
    x=good(); x["null_geometry"]="FROZEN_OBSERVED_AXES"
    with pytest.raises(RuntimeError,match="NULL_GEOMETRY"):
        guard().validate(x)


def test_four_cell_stratum_cap_rejected():
    x=good(); x["sampled_stratum_cap"]=4
    with pytest.raises(RuntimeError,match="SAMPLED_STRATUM"):
        guard().validate(x)


def test_50k_or_synthetic_rejected():
    x=good(); x["population_mode"]="DISCOVERY_50K"
    with pytest.raises(RuntimeError,match="NOT_FULL_READER"):
        guard().validate(x)
    x=good(); x["synthetic_data_used"]=True
    with pytest.raises(RuntimeError,match="SYNTHETIC"):
        guard().validate(x)


def test_D_arithmetic():
    x=good(); x["D_total"]=8
    with pytest.raises(RuntimeError,match="DIMENSION_ARITHMETIC"):
        guard().validate(x)
