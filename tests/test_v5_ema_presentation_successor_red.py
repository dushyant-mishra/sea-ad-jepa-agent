import importlib
import math

import pytest


def test_current_v5_ema_mechanics_are_presentation_normalized_not_constant_momentum():
    try:
        module = importlib.import_module("sea_ad_jepa.v5.ema_presentation_v1")
    except ModuleNotFoundError as exc:
        pytest.fail(f"canonical successor omitted authenticated V5 presentation-normalized EMA mechanics: {exc}")
    fn = getattr(module, "ema_momentum_for_presentations", None)
    assert callable(fn)
    half_life = 1000
    m6 = fn(presentations_this_update=6, half_life_presentations=half_life)
    assert m6 == pytest.approx(math.exp(math.log(0.5) * 6 / half_life), rel=0, abs=1e-15)
    m2 = fn(presentations_this_update=2, half_life_presentations=half_life)
    m4 = fn(presentations_this_update=4, half_life_presentations=half_life)
    assert m6 == pytest.approx(m2 * m4, rel=0, abs=1e-15)


def test_ema_rehearsal_configuration_binds_presentation_unit_and_half_life_without_selecting_production_value():
    proof = importlib.import_module("sea_ad_jepa.v5.ema_bound_runtime_proof_v1")
    identity_fn = getattr(proof, "presentation_ema_configuration_identity", None)
    assert callable(identity_fn), "EMA successor still binds a constant momentum instead of presentation-timescale mechanics"
    a = identity_fn(half_life_presentations=1000, presentation_unit_id="SUCCESSFUL_BASE_CELL_PRESENTATIONS")
    b = identity_fn(half_life_presentations=1001, presentation_unit_id="SUCCESSFUL_BASE_CELL_PRESENTATIONS")
    c = identity_fn(half_life_presentations=1000, presentation_unit_id="OTHER_UNIT")
    assert a.startswith("V5_PRESENTATION_EMA:")
    assert a != b and a != c
    with pytest.raises(Exception):
        identity_fn(half_life_presentations=0, presentation_unit_id="SUCCESSFUL_BASE_CELL_PRESENTATIONS")


def test_constant_momentum_helper_is_not_the_canonical_ema_configuration_identity():
    proof = importlib.import_module("sea_ad_jepa.v5.ema_bound_runtime_proof_v1")
    canonical = getattr(proof, "presentation_ema_configuration_identity", None)
    assert callable(canonical)
    constant = getattr(proof, "constant_ema_configuration_identity", None)
    if constant is not None:
        assert constant(0.996) != canonical(
            half_life_presentations=1000,
            presentation_unit_id="SUCCESSFUL_BASE_CELL_PRESENTATIONS",
        )
