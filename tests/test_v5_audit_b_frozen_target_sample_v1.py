"""Tests for the Phase IV frozen Audit B target sample.

The freeze exists so the sample cannot be chosen, extended or re-rolled after
seeing a burden result. These tests check the properties that make that true:

* the ordering is a **prefix** ordering, so escalating extends the sample and can
  never drop an already-measured target;
* the draw is reproducible and depends on nothing but the salt and the address;
* the escalation criterion is a function of precision only — a static check that
  it does not reference the observed value, its sign, or which arm looks better;
* the freeze is bound to every input that could change its meaning, and the
  digest moves when any of them does.

Nothing here opens a terminal masking outcome, target-panel ladder,
null-equivalence margin, D_shared, protected/pathology/DEV/SEALED data, or
training.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / ("analysis/v5_full104_information_channel_redteam_20260920/scripts/"
              "freeze_audit_b_target_sample_20260921.py")
FROZEN = ROOT / ("analysis/v5_full104_information_channel_redteam_20260920/evidence/"
                 "phase_iv/AUDIT_B_FROZEN_TARGET_SAMPLE.json")

_spec = importlib.util.spec_from_file_location("freeze_b", MOD)
F = importlib.util.module_from_spec(_spec)
sys.modules["freeze_b"] = F
_spec.loader.exec_module(F)


@pytest.fixture(scope="module")
def frozen() -> dict:
    if not FROZEN.is_file():
        pytest.fail(
            f"{FROZEN} missing. Deliberately not skipped: without the frozen sample "
            "Phase IV has no prospective specification and its burden numbers would "
            "be unfalsifiable.")
    return json.loads(FROZEN.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# The ordering
# --------------------------------------------------------------------------- #

def test_ladder_is_a_prefix_ordering(frozen):
    """Escalation must EXTEND the sample, never re-roll it.

    If N1 were not a subset of N2, escalating could drop a target that had
    already been measured -- which would let an inconvenient target disappear
    under the cover of a sample-size increase.
    """
    n1 = set(frozen["samples"]["N1"]["targets"])
    n2 = set(frozen["samples"]["N2"]["targets"])
    n3 = set(frozen["samples"]["N3"]["targets"])
    assert n1 < n2 < n3
    assert frozen["prefix_ordering"] is True


def test_ladder_sizes_are_the_declared_ones(frozen):
    assert [frozen["samples"][k]["n"] for k in ("N1", "N2", "N3")] == [256, 1024, 4096]
    assert frozen["ladder"] == [256, 1024, 4096]
    for k in ("N1", "N2", "N3"):
        assert len(frozen["samples"][k]["targets"]) == frozen["samples"][k]["n"]
        assert len(set(frozen["samples"][k]["targets"])) == frozen["samples"][k]["n"]


def test_selection_is_reproducible_and_salt_driven():
    addresses = list(range(5000))
    a = F.ordered_targets(addresses)
    assert a == F.ordered_targets(addresses), "selection is not reproducible"
    b = F.ordered_targets(addresses, salt="A_DIFFERENT_SALT")
    assert a != b, "selection does not depend on the salt, so it is not hash-driven"


def test_selection_depends_on_nothing_but_the_address():
    """Order must not change when the input list is permuted or the data differs."""
    addresses = list(range(2000))
    assert F.ordered_targets(addresses) == F.ordered_targets(list(reversed(addresses)))


def test_sample_is_drawn_from_the_authenticated_universe(frozen):
    universe = json.loads(
        (ROOT / "analysis/v5_full104_pass1_rebuild_20260920/evidence/"
                "full104_target_eligibility_v1.json").read_text(encoding="utf-8"))
    eligible = set(int(a) for a in universe["eligible_target_cols_all_folds"])
    assert len(eligible) == 17053
    for k in ("N1", "N2", "N3"):
        assert set(frozen["samples"][k]["targets"]).issubset(eligible), (
            f"{k} contains targets outside the authenticated 17,053 universe")


# --------------------------------------------------------------------------- #
# The escalation criterion must not be steerable by results
# --------------------------------------------------------------------------- #

def test_escalation_criterion_depends_on_precision_only(frozen):
    crit = frozen["escalation_criterion"]
    assert crit["depends_only_on_precision"] is True
    assert crit["max_relative_standard_error"] == 0.05
    assert "relative standard error" in crit["rule"]
    for forbidden in ("the observed burden ratio", "its sign",
                      "which masking policy looks better", "any terminal masking outcome"):
        assert forbidden in crit["explicitly_not_a_function_of"]


def test_ladder_terminates_rather_than_growing_opportunistically(frozen):
    crit = frozen["escalation_criterion"]
    assert crit["ladder_does_not_continue_past_N3"] is True
    assert crit["terminal_outcome_if_unmet_at_N3"] == "INSUFFICIENT_PRECISION_AT_N3"


def test_criterion_source_does_not_reference_an_outcome_value():
    """Static guard on the module itself, not only on its emitted JSON."""
    source = MOD.read_text(encoding="utf-8")
    body = source.split('"""', 2)[2]
    for smell in ("observed_ratio", "if ratio >", "if delta >", "best_policy",
                  "favourable", "favorable"):
        assert smell not in body, (
            f"the freeze module references {smell!r}; escalation could be steered "
            "by a result")


# --------------------------------------------------------------------------- #
# Binding
# --------------------------------------------------------------------------- #

def test_every_bound_input_is_recorded_with_a_digest(frozen):
    required = {"target_universe", "split_receipt", "planner_source",
                "qualification_runner", "masking_parameters_authority",
                "evidence_budget_authority", "mask_plan_generator"}
    assert set(frozen["bound_inputs"]) == required
    for role, rec in frozen["bound_inputs"].items():
        assert len(rec["sha256"]) == 64, role
        assert (ROOT / rec["path"]).is_file(), f"{role}: {rec['path']} is missing"


def test_bound_digests_still_match_the_repository(frozen):
    """A bound input may only move through a reviewed, versioned successor.

    The frozen record itself is never edited. If a bound input has drifted, the
    ONLY acceptable state is that a successor record covers that exact role with
    the exact recorded old digest, the exact observed new digest, an
    authorizing classification and executed equivalence evidence. Anything else
    - including a drift with no successor, or a successor for a different
    transition - is still a failure, exactly as before.
    """
    from sea_ad_jepa.v5.audit_b_bound_input_successor_v2 import (
        SUCCESSOR_RECORD_PATH,
        load_successor,
        resolve_drift,
    )

    drifted = {}
    for role, rec in frozen["bound_inputs"].items():
        actual = F.sha256_file(ROOT / rec["path"])
        if actual != rec["sha256"]:
            drifted[role] = (rec["sha256"], actual)

    if not drifted:
        return

    assert SUCCESSOR_RECORD_PATH.is_file(), (
        "bound inputs changed since the freeze and no successor record exists; "
        "the sample must be re-frozen as a NEW version and the change explained "
        f"rather than silently reused: {sorted(drifted)}")
    successor = load_successor(SUCCESSOR_RECORD_PATH, repo_root=ROOT)
    for role, (recorded, actual) in sorted(drifted.items()):
        # Raises with the reason if this exact transition is not authorized.
        resolve_drift(role, recorded=recorded, observed=actual, successor=successor)


def test_freeze_digest_covers_the_samples_and_the_bindings(frozen):
    material = json.dumps(
        {"schema": frozen["schema"], "salt": frozen["salt"], "ladder": frozen["ladder"],
         "bound": frozen["bound_inputs"],
         "samples": {k: v["targets"] for k, v in frozen["samples"].items()}},
        sort_keys=True, separators=(",", ":")).encode("utf-8")
    assert hashlib.sha256(material).hexdigest() == frozen["freeze_digest"]


def test_execution_requirements_are_recorded(frozen):
    reqs = " ".join(frozen["execution_requirements"]).lower()
    assert "training-side" in reqs
    assert "held-out" in reqs
    assert "no policy adaptation" in reqs
    assert "source x donor x fold" in reqs
    assert frozen["frozen_before_any_burden_was_computed"] is True
    assert frozen["terminal_masking_outcomes_inspected"] is False
    assert frozen["training_authorized"] is False
