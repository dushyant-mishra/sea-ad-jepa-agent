import hashlib
from types import SimpleNamespace

import pytest

from sea_ad_jepa.v5.precision_authority_v4 import QualificationPrecisionAuthorityV4


def h(x):
    return hashlib.sha256(x.encode()).hexdigest()


def authority(**updates):
    values = dict(
        authority_id="TEST",
        support_estimability_authority_sha256=h("support"),
        target_panel_authority_sha256=h("panel"),
        outer_split_authority_sha256=h("split"),
        historical_primary32_summary_sha256=h("primary32"),
        historical_nonlinear32_summary_sha256=h("nonlinear32"),
    )
    values.update(updates)
    return QualificationPrecisionAuthorityV4(**values)


def test_v4_requires_128_targets_but_does_not_treat_count_as_precision_proof():
    p = authority()
    p.assert_sufficient(target_count=128, donor_count=104, outer_fold_count=4)
    narrow = SimpleNamespace(lower_two_sided=-0.002, upper_two_sided=0.002)
    p.assert_interval_precise(narrow, label="primary")


def test_interval_wider_than_predeclared_three_per_thousand_halfwidth_fails():
    p = authority()
    wide = SimpleNamespace(lower_two_sided=-0.0031, upper_two_sided=0.0031)
    with pytest.raises(ValueError, match="exceeds frozen precision ceiling"):
        p.assert_interval_precise(wide, label="primary")


def test_historical_planning_roots_are_bound_and_distinct():
    p = authority()
    p.validate()
    with pytest.raises(ValueError, match="role-distinct"):
        authority(
            historical_primary32_summary_sha256=h("same"),
            historical_nonlinear32_summary_sha256=h("same"),
        ).validate()


def test_width_ceiling_is_exactly_three_per_thousand():
    assert authority().max_two_sided_half_width == pytest.approx(0.003)
