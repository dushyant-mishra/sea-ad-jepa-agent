import pytest

from sea_ad_jepa.qualification.qsafe import (
    NegativeControlArm,
    QSafetyPolicyV1,
    REQUIRED_Q_SAFETY_CHANNELS,
    SyntheticControlRosterV1,
)


def test_complete_q_safety_policy_passes():
    policy = QSafetyPolicyV1(forbidden_descendant_channels=REQUIRED_Q_SAFETY_CHANNELS)
    policy.validate()


def test_deleting_any_required_q_descendant_channel_fails_closed():
    for channel in REQUIRED_Q_SAFETY_CHANNELS:
        weakened = tuple(x for x in REQUIRED_Q_SAFETY_CHANNELS if x != channel)
        with pytest.raises(ValueError, match="q-safety"):
            QSafetyPolicyV1(forbidden_descendant_channels=weakened)


def test_extra_unknown_q_safety_channel_requires_successor_contract():
    with pytest.raises(ValueError, match="unknown"):
        QSafetyPolicyV1(
            forbidden_descendant_channels=REQUIRED_Q_SAFETY_CHANNELS + ("UNREVIEWED_NEW_CHANNEL",)
        )


def test_serious_synthetic_roster_requires_private_and_query_leak_controls():
    complete = SyntheticControlRosterV1(
        arms=(
            NegativeControlArm.CLEAN_NEGATIVE,
            NegativeControlArm.TECHNICAL_OPERATOR_SHORTCUT,
            NegativeControlArm.PLANTED_RECOVERABLE_BIOLOGICAL,
            NegativeControlArm.PLANTED_INACCESSIBLE_PRIVATE_STATE,
            NegativeControlArm.QUERY_LEAK,
        )
    )
    complete.validate(require_private_state=True, require_query_leak=True)

    missing_private = SyntheticControlRosterV1(
        arms=tuple(x for x in complete.arms if x is not NegativeControlArm.PLANTED_INACCESSIBLE_PRIVATE_STATE)
    )
    with pytest.raises(ValueError, match="private"):
        missing_private.validate(require_private_state=True, require_query_leak=True)

    missing_query = SyntheticControlRosterV1(
        arms=tuple(x for x in complete.arms if x is not NegativeControlArm.QUERY_LEAK)
    )
    with pytest.raises(ValueError, match="query"):
        missing_query.validate(require_private_state=True, require_query_leak=True)


def test_duplicate_control_arms_fail_closed():
    with pytest.raises(ValueError, match="duplicate"):
        SyntheticControlRosterV1(
            arms=(NegativeControlArm.CLEAN_NEGATIVE, NegativeControlArm.CLEAN_NEGATIVE)
        )
