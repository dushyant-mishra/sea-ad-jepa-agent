import pytest

from sea_ad_jepa.v5.current_training_policy_v2 import require_current_training_authority


def test_current_policy_rejects_historical_or_untyped_authority():
    with pytest.raises(ValueError, match="CurrentTrainingAuthorityV2"):
        require_current_training_authority(object())
