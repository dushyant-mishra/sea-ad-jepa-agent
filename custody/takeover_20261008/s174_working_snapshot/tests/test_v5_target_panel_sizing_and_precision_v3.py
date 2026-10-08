import hashlib
import numpy as np
import pytest

from sea_ad_jepa.v5.target_panel_sizing_authority_v1 import (
    FROZEN_TARGET_COUNT, TargetPanelSizingAuthorityV1, next_power_of_two_at_least
)
from sea_ad_jepa.v5.precision_authority_v3 import QualificationPrecisionAuthorityV3


def h(x):
    return hashlib.sha256(x.encode()).hexdigest()


def sizing(**updates):
    values=dict(
        authority_id="TEST",
        census_authority_sha256=h("census"),
        target_eligibility_receipt_sha256=h("elig"),
        sizing_rule_id="NEXT_POWER_OF_TWO_AT_LEAST_FULL104_DONOR_COUNT_V1",
        independent_donor_count=104,
        eligible_target_count=17053,
        target_count=128,
    )
    values.update(updates)
    return TargetPanelSizingAuthorityV1(**values)


def precision(**updates):
    values=dict(
        authority_id="TEST",
        support_estimability_authority_sha256=h("support"),
        target_panel_authority_sha256=h("panel"),
        outer_split_authority_sha256=h("split"),
    )
    values.update(updates)
    return QualificationPrecisionAuthorityV3(**values)


def test_target_count_is_current_data_derived_not_historical_fixture():
    assert next_power_of_two_at_least(104) == 128 == FROZEN_TARGET_COUNT
    sizing().validate()
    with pytest.raises(ValueError, match="128"):
        sizing(target_count=64).validate()
    with pytest.raises(ValueError, match="128"):
        sizing(target_count=32).validate()


def test_precision_is_frozen_to_128_targets_104_donors_four_folds():
    p=precision()
    p.validate()
    p.assert_sufficient(target_count=128, donor_count=104, outer_fold_count=4)
    with pytest.raises(ValueError):
        p.assert_sufficient(target_count=127, donor_count=104, outer_fold_count=4)


def test_precision_seed_is_root_derived_and_replays():
    assert precision().bootstrap_seed == precision().bootstrap_seed
    assert precision().bootstrap_seed != precision(target_panel_authority_sha256=h("panel2")).bootstrap_seed


def test_4096_replicates_and_95pct_are_explicit():
    p=precision()
    assert p.bootstrap_replicates == 4096
    assert p.confidence_level == pytest.approx(0.95)


def test_precision_interval_runs_on_target_by_donor_matrix():
    p=precision()
    matrix=np.ones((128,104), dtype=float)*0.01
    source=np.repeat(np.arange(4),26)
    out=p.interval(matrix, source)
    assert out.mean == pytest.approx(0.01)
    assert out.lower_two_sided == pytest.approx(0.01)
    assert out.upper_two_sided == pytest.approx(0.01)
