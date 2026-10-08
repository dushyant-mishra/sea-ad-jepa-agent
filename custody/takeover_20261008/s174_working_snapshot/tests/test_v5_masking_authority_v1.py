import inspect
from pathlib import Path

import pytest

from sea_ad_jepa.v5.masking_authority_v1 import MaskingAuthorityV1


def test_masking_authority_requires_every_policy_input_explicitly() -> None:
    sig = inspect.signature(MaskingAuthorityV1)
    for name, param in sig.parameters.items():
        if name == "training_authorized":
            continue
        assert param.default is inspect._empty


def test_masking_authority_validates_exact_mixture_without_choosing_it() -> None:
    authority = MaskingAuthorityV1("candidate", "dependency", 1, 1, 2, "budget", "rng")
    authority.validate()
    assert authority.training_authorized is False
    assert len(authority.canonical_digest()) == 64


def test_masking_authority_rejects_incoherent_mixture() -> None:
    authority = MaskingAuthorityV1("bad", "dep", 1, 1, 3, "budget", "rng")
    with pytest.raises(ValueError, match="sum to mixture_denominator"):
        authority.validate()


def test_source_has_no_historical_mask_defaults() -> None:
    source = Path("src/sea_ad_jepa/v5/masking_authority_v1.py").read_text(encoding="utf-8")
    for token in ("0.40", "target_blocks", "Pearson", "16 target"):
        assert token not in source
