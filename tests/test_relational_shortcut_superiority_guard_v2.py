import pathlib
import sys
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sea_ad_jepa.v5.relational_shortcut_superiority_guard_v2 import (
    RelationalShortcutSuperiorityAuthorityV2,
    qualify_relational_superiority,
)


def auth(**kw):
    base = dict(
        shortcut_family_authority_id="shortcuts-v2",
        expected_shortcut_ids=("depth", "donor", "source"),
        shortcut_family_frozen_before_checkpoint_outcome=True,
        minimum_absolute_increment=0.03,
        increment_frozen_before_checkpoint_outcome=True,
        heldout_unit_policy_id="heldout-donor-v1",
        multiplicity_policy_id="multiplicity-v1",
        require_every_case=True,
    )
    base.update(kw)
    return RelationalShortcutSuperiorityAuthorityV2(**base)


def shortcuts():
    return {
        "depth": {"a": 0.60, "b": 0.58},
        "donor": {"a": 0.55, "b": 0.62},
        "source": {"a": 0.64, "b": 0.59},
    }


def test_beats_strongest_shortcut_in_every_case():
    out = qualify_relational_superiority(
        learned_case_metrics={"a": 0.70, "b": 0.67},
        shortcut_metrics_by_id=shortcuts(), authority=auth())
    assert out["passed"] is True
    assert out["cases"]["a"]["strongest_shortcut_ids"] == ("source",)
    assert out["cases"]["b"]["strongest_shortcut_ids"] == ("donor",)
    assert out["training_authorized"] is False


def test_cherry_picking_weaker_shortcut_cannot_pass():
    with pytest.raises(ValueError, match="shortcut family mismatch"):
        qualify_relational_superiority(
            learned_case_metrics={"a": 0.63, "b": 0.66},
            shortcut_metrics_by_id={"depth": shortcuts()["depth"]}, authority=auth())


def test_full_family_uses_strongest_and_stops():
    with pytest.raises(RuntimeError, match="SUPERIORITY_NOT_EARNED"):
        qualify_relational_superiority(
            learned_case_metrics={"a": 0.66, "b": 0.66},
            shortcut_metrics_by_id=shortcuts(), authority=auth())


def test_equal_to_required_margin_is_failure_because_increment_is_strict():
    with pytest.raises(RuntimeError, match="SUPERIORITY_NOT_EARNED"):
        qualify_relational_superiority(
            learned_case_metrics={"a": 0.67, "b": 0.65},
            shortcut_metrics_by_id=shortcuts(), authority=auth())


def test_increment_must_be_positive():
    with pytest.raises(ValueError, match="strictly positive"):
        qualify_relational_superiority(
            learned_case_metrics={"a": 0.7, "b": 0.7},
            shortcut_metrics_by_id=shortcuts(), authority=auth(minimum_absolute_increment=0.0))


def test_shortcut_family_must_be_frozen_before_outcome():
    with pytest.raises(ValueError, match="family must be frozen"):
        qualify_relational_superiority(
            learned_case_metrics={"a": 0.7, "b": 0.7},
            shortcut_metrics_by_id=shortcuts(), authority=auth(shortcut_family_frozen_before_checkpoint_outcome=False))


def test_increment_must_be_frozen_before_outcome():
    with pytest.raises(ValueError, match="increment must be frozen"):
        qualify_relational_superiority(
            learned_case_metrics={"a": 0.7, "b": 0.7},
            shortcut_metrics_by_id=shortcuts(), authority=auth(increment_frozen_before_checkpoint_outcome=False))


def test_extra_shortcut_is_not_silently_ignored():
    s = shortcuts(); s["composition"] = {"a": 0.1, "b": 0.1}
    with pytest.raises(ValueError, match="shortcut family mismatch"):
        qualify_relational_superiority(
            learned_case_metrics={"a": 0.7, "b": 0.7}, shortcut_metrics_by_id=s, authority=auth())


def test_case_sets_must_match_every_shortcut():
    s = shortcuts(); s["depth"] = {"a": 0.6}
    with pytest.raises(ValueError, match="case set mismatch"):
        qualify_relational_superiority(
            learned_case_metrics={"a": 0.7, "b": 0.7}, shortcut_metrics_by_id=s, authority=auth())


def test_shortcut_ids_are_canonical_and_unique():
    with pytest.raises(ValueError, match="canonical sorted order"):
        qualify_relational_superiority(
            learned_case_metrics={"a": 0.7, "b": 0.7}, shortcut_metrics_by_id=shortcuts(),
            authority=auth(expected_shortcut_ids=("source", "depth", "donor")))
