import inspect
import pytest
from sea_ad_jepa.v5.relational_shortcut_increment_guard_v1 import (
    RelationalShortcutIncrementAuthorityV1,qualify_relational_increment)

def auth(margin=0.03):
    return RelationalShortcutIncrementAuthorityV1(
        "FROZEN_SHORTCUT_BASELINE",True,margin,True,"HELDOUT_DONOR_SOURCE")

def test_increment_beyond_shortcut_passes():
    assert qualify_relational_increment(
        learned_case_metrics={"a":0.70,"b":0.66},
        shortcut_case_metrics={"a":0.62,"b":0.60},authority=auth())["passed"]

def test_above_chance_can_still_fail():
    with pytest.raises(RuntimeError,match="STOP_RELATIONAL_SHORTCUT"):
        qualify_relational_increment(
            learned_case_metrics={"a":0.61},
            shortcut_case_metrics={"a":0.60},authority=auth(0.02))

def test_case_sets_must_match():
    with pytest.raises(ValueError,match="match exactly"):
        qualify_relational_increment(
            learned_case_metrics={"a":0.7},
            shortcut_case_metrics={"b":0.6},authority=auth())

def test_no_numeric_defaults():
    sig=inspect.signature(RelationalShortcutIncrementAuthorityV1)
    assert all(p.default is inspect._empty for p in sig.parameters.values())
