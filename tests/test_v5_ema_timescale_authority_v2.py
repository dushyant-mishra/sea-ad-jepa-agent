from __future__ import annotations

import hashlib

import pytest

from sea_ad_jepa.v5.ema_timescale_authority_v2 import EmaTimescaleAuthorityV2


def h(name: str) -> str:
    return hashlib.sha256(name.encode()).hexdigest()


def authority(**updates):
    values = dict(
        authority_id="JEPA_V5_EMA_TIMESCALE_AUTHORITY_V2",
        base_training_estimand_sha256=h("estimand"),
        schedule_authority_sha256=h("schedule"),
        momentum_function_id="PRESENTATION_HALF_LIFE_EXPONENTIAL_V1",
        presentation_unit_id="AUTHORIZED_SCIENTIFIC_PRESENTATIONS_V1",
        half_life_presentations=1000,
        training_authorized=False,
    )
    values.update(updates)
    return EmaTimescaleAuthorityV2(**values)


def test_valid_ema_v2_is_deterministic() -> None:
    a = authority(); a.validate()
    assert a.canonical_digest() == authority().canonical_digest()


def test_ema_function_and_presentation_unit_are_enumerated() -> None:
    with pytest.raises(ValueError, match="momentum_function_id"):
        authority(momentum_function_id="CONSTANT_0_996").validate()
    with pytest.raises(ValueError, match="presentation_unit_id"):
        authority(presentation_unit_id="OPTIMIZER_STEPS_OR_WHATEVER").validate()


def test_half_life_is_explicit_positive_and_not_a_hidden_default() -> None:
    with pytest.raises(ValueError, match="half_life_presentations"):
        authority(half_life_presentations=0).validate()
    with pytest.raises(ValueError, match="half_life_presentations"):
        authority(half_life_presentations=0.996).validate()


def test_momentum_matches_presentation_half_life_formula() -> None:
    a = authority(half_life_presentations=100)
    assert a.momentum_for_presentations(0) == pytest.approx(1.0)
    assert a.momentum_for_presentations(100) == pytest.approx(0.5)
    assert a.momentum_for_presentations(200) == pytest.approx(0.25)
    with pytest.raises(ValueError, match="presentations"):
        a.momentum_for_presentations(-1)


def test_ema_v2_cannot_authorize_training() -> None:
    with pytest.raises(ValueError, match="cannot authorize training"):
        authority(training_authorized=True).validate()
