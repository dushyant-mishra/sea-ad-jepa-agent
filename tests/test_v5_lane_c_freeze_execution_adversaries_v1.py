"""Planted failures against the Phase-IV freeze and the execution-contract builder.

Deliberately NOT reimplemented here
-----------------------------------
* PR #153 (`audit/v29-mechanical-precommit-and-checkpoint-20260926`) already
  carries 17 failure-injection tests for the training-step path: missing and
  malformed per-parameter gradient reports, skipped and repeated optimizer
  steps, empty Adam first/second moments, decay-only movement, teacher pre-EMA
  mutation, EMA/step ordering, cursor non-advance, truncated and missing
  checkpoint parts, and exclusive atomic publication.
* The six inline gradient negative controls on
  `review/v27-authority-root-inventory-20260925` already prove a damaged update
  stops before the optimizer and the EMA, and that a refused update leaves the
  optimizer able to run afterwards.

This file covers the path neither of those touches, and the one that actually
broke: the bound-input binding and the builder standing on it.

Every case names the exact refusal it must produce and checks the observable
state afterwards. "It raised" is not evidence that nothing was written.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / (
    "analysis/v5_lane_c_planner_freeze_repair_20260926/scripts/"
    "run_freeze_execution_adversaries_v1.py"
)
RECEIPT = ROOT / (
    "analysis/v5_lane_c_planner_freeze_repair_20260926/evidence/"
    "FREEZE_EXECUTION_ADVERSARIES_V1.json"
)

_spec = importlib.util.spec_from_file_location("lane_c_freeze_adversaries", MOD)
A = importlib.util.module_from_spec(_spec)
sys.modules["lane_c_freeze_adversaries"] = A
_spec.loader.exec_module(A)

ADVERSARIES = A.ADVERSARIES
run_all = A.run_all


@pytest.fixture(scope="module")
def report(tmp_path_factory):
    return run_all(tmp_path_factory.mktemp("lane_c_adversaries"))


# --------------------------------------------------------------------------- #
# POSITIVE CONTROL
# --------------------------------------------------------------------------- #


def test_positive_control_the_builder_still_succeeds_on_good_inputs(report):
    """A builder that refused everything would satisfy every adversary below."""
    control = report["positive_control"]
    assert control["returncode"] == 0, control["stderr_tail"]
    assert control["artifact_written"] is True
    assert control["phase_iv_sample_freeze_digest"].startswith("c2c5e1b5")
    # and succeeding must still not authorize anything
    assert control["execution_authorized"] is False
    assert control["precision_scope_id"] == "UNRESOLVED__EXECUTION_FORBIDDEN"


# --------------------------------------------------------------------------- #
# Each planted failure
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("name", [a[0] for a in ADVERSARIES])
def test_adversary_is_refused_at_the_named_point(report, name):
    case = next(c for c in report["cases"] if c["adversary"] == name)
    assert case["refused"], f"{name} was ACCEPTED"
    assert case["refusal_point_matches"], (
        f"{name} refused at the wrong point: {case['refusal_point']!r}; "
        f"expected to contain {case['expected_refusal_fragment']!r}. A refusal "
        "from an unrelated gate hides the defect under test."
    )


@pytest.mark.parametrize("name", [a[0] for a in ADVERSARIES])
def test_adversary_changed_no_state(report, name):
    """An exception is not evidence of rollback; the state is measured."""
    case = next(c for c in report["cases"] if c["adversary"] == name)
    assert case["watched_artifacts_unchanged"], case["state_delta"]
    assert not case["contract_artifact_created"], (
        f"{name} left a contract artifact behind after refusing"
    )
    assert case["training_state_artifacts_created"] == [], (
        f"{name} created training-side state: "
        f"{case['training_state_artifacts_created']}"
    )


def test_every_adversary_refused_and_nothing_moved(report):
    assert report["all_refused_at_the_expected_point"] is True
    assert report["no_state_changed_on_any_refusal"] is True


def test_the_suite_declares_what_it_did_not_reimplement(report):
    assert report["pr153_training_step_adversaries"] == (
        "ALREADY_COVERED__NOT_REIMPLEMENTED"
    )
    assert report["v27_inline_gradient_negative_controls"] == (
        "PRESERVED__NOT_REIMPLEMENTED"
    )
    assert report["training_authorized"] is False
    assert report["terminal_masking_outcomes_inspected"] is False


def test_the_shipped_adversary_receipt_agrees_with_a_fresh_run(report):
    """The committed receipt is reproducible, not a snapshot of a lucky run."""
    shipped = json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert shipped["all_refused_at_the_expected_point"] is True
    assert shipped["no_state_changed_on_any_refusal"] is True
    assert [c["adversary"] for c in shipped["cases"]] == [
        c["adversary"] for c in report["cases"]
    ]
    for a, b in zip(shipped["cases"], report["cases"]):
        assert a["expected_refusal_fragment"] == b["expected_refusal_fragment"]
        assert a["refused"] == b["refused"]
