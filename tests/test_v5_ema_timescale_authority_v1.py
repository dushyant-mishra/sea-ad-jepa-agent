import inspect
from pathlib import Path

import pytest

from sea_ad_jepa.v5.ema_timescale_authority_v1 import EmaTimescaleAuthorityV1


def make_authority() -> EmaTimescaleAuthorityV1:
    return EmaTimescaleAuthorityV1(
        "prospective-ema-timescale",
        "1" * 64,
        "2" * 64,
        "EXPLICIT_MOMENTUM_FUNCTION",
        "EXPLICIT_PRESENTATION_UNIT",
        1000,
    )


def test_inputs_explicit() -> None:
    sig = inspect.signature(EmaTimescaleAuthorityV1)
    for name, param in sig.parameters.items():
        if name == "training_authorized":
            continue
        assert param.default is inspect._empty


def test_binds_unit_half_life_training_off() -> None:
    authority = make_authority()
    authority.validate()
    assert authority.training_authorized is False
    assert len(authority.canonical_digest()) == 64


def test_invalid_half_life_fails_closed() -> None:
    values = make_authority().__dict__.copy()
    values["half_life_presentations"] = 0
    with pytest.raises(ValueError, match="half_life_presentations"):
        EmaTimescaleAuthorityV1(**values).validate()


def test_source_has_no_historical_or_selected_default() -> None:
    source = Path("src/sea_ad_jepa/v5/ema_timescale_authority_v1.py").read_text(encoding="utf-8")
    assert "0.996" not in source
    assert "half_life_presentations=" not in source
    assert "half_life_presentations =" not in source
