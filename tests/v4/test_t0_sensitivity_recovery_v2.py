import copy
import pytest

import sys
from pathlib import Path

# The lane's modules import one another by bare name, the way the frozen V20
# package does, so `scripts/v4` has to be importable. Resolved here rather than
# left to an ambient PYTHONPATH: without it a clean clone reports collection
# errors instead of running these tests, which is the failure mode where a
# suite looks absent rather than red.
_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts" / "v4"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from t0_replay_equivalence_v1 import ReplayEquivalenceError
from t0_sensitivity_recovery_v2 import (
    STOP,
    derive_r8_router_source,
    verify_replay_decision,
    build_payload,
)


def _router_source():
    return '''def _adjudicator_through_r8():\n    frozen = stage2a._frozen("t0_adjudicator_v2")\n    source = inspect.getsource(frozen._adjudicate_from_raw_v2)\n    namespace = dict(frozen.__dict__)\n    namespace["verify_pretarget_execution_authority"] = v2.verify_pretarget_execution_authority\n    namespace["verify_preadjudication_execution_authority"] = v2.verify_preadjudication_execution_authority\n    exec(compile(source, "<r8>", "exec"), namespace)\n    return namespace["_adjudicate_from_raw_v2"]\n'''


def _decision():
    return {
        "state_terminal": "BROAD_IMMUNE_EXPRESSION_TARGET_SUPPORTED_INTERNAL",
        "tail_terminal": "RARE_TAIL_UNDERDETERMINED_MEASUREMENT",
        "state_primary": {
            "beta": 124.94507515835764,
            "estimable": True,
            "hc3_se": 65.48932245523241,
            "n": 18,
            "p_full": 5,
            "p_lower": 0.9791,
            "p_reduced": 4,
            "p_upper": 0.021,
            "permutations": 9999,
            "residual_df": 13,
            "t_observed": 1.9078694125102356,
            "null_t": "[frozen-string-representation]",
        },
        "state_composition": {"beta": 2.0, "p_upper": 0.01},
        "state_measurements": {"Q_DEPTH_Q_DETECT": {"beta": 1.0, "p_upper": 0.02}},
    }


def test_router_patch_injects_only_reporting_and_replay_hooks_before_r8_authority_bindings():
    src = _router_source()
    patched = derive_r8_router_source(src)
    assert patched.count("_recovery_state_adjudicator") == 1
    assert patched.count("_recovery_target_verifier") == 1
    assert patched.count('namespace["verify_pretarget_execution_authority"]') == 1
    assert patched.count('namespace["verify_preadjudication_execution_authority"]') == 1
    assert patched.index("_recovery_target_verifier") < patched.index("verify_pretarget_execution_authority")
    # No substitution of the R8 authority routing itself.
    assert 'v2.verify_pretarget_execution_authority' in patched
    assert 'v2.verify_preadjudication_execution_authority' in patched


def test_router_patch_fails_closed_if_required_r8_markers_move_or_duplicate():
    with pytest.raises(RuntimeError, match=STOP):
        derive_r8_router_source(_router_source().replace("    namespace = dict(frozen.__dict__)\n", ""))
    with pytest.raises(RuntimeError, match=STOP):
        derive_r8_router_source(_router_source().replace(
            '    namespace["verify_pretarget_execution_authority"] = v2.verify_pretarget_execution_authority\n', ""))
    with pytest.raises(RuntimeError, match=STOP):
        derive_r8_router_source(_router_source().replace(
            '    source = inspect.getsource(frozen._adjudicate_from_raw_v2)\n', ""))
    doubled = _router_source().replace(
        "    namespace = dict(frozen.__dict__)\n",
        "    namespace = dict(frozen.__dict__)\n    namespace = dict(frozen.__dict__)\n",
    )
    with pytest.raises(RuntimeError, match=STOP):
        derive_r8_router_source(doubled)


def test_decision_replay_accepts_tiny_continuous_drift_but_preserves_exact_pvalues_and_terminals():
    committed = _decision(); recomputed = copy.deepcopy(committed)
    recomputed["state_primary"]["beta"] *= 1 + 8e-13
    report = verify_replay_decision(committed, recomputed)
    assert report["equivalent"] is True

    bad = copy.deepcopy(recomputed)
    bad["state_primary"]["p_upper"] = 0.021000000000000005
    with pytest.raises(ReplayEquivalenceError, match="p_upper"):
        verify_replay_decision(committed, bad)

    bad = copy.deepcopy(recomputed)
    bad["tail_terminal"] = "OTHER"
    with pytest.raises(ReplayEquivalenceError, match="tail_terminal"):
        verify_replay_decision(committed, bad)


def test_payload_explicitly_denies_authority_and_records_both_equivalence_reports():
    decision = _decision()
    target_report = {
        "verified": True,
        "equivalence_schema": "JEPA_T0_V20_TARGET_REPLAY_EQUIVALENCE_V1",
        "equivalence_report": {"equivalent": True},
    }
    decision_report = verify_replay_decision(decision, copy.deepcopy(decision))
    payload = build_payload(decision, target_report, decision_report, {
        "changed_lines": 5,
        "added_keys": ["state_composition", "state_measurements"],
    })
    assert payload["schema"] == "JEPA_T0_V20_RECOVERED_SENSITIVITY_STATISTICS_V2"
    assert payload["training_authorized"] is False
    assert payload["historical_bit_exact_verifier_modified"] is False
    assert payload["model_changed"] is False
    assert payload["decision_procedure_changed"] is False
    assert payload["reporting_surface_changed"] is True
    assert payload["discovery_fit_recomputed_for_replay"] is True
    assert payload["discovery_target_changed"] is False
    assert payload["target_replay_equivalence"]["verified"] is True
    assert payload["decision_replay_equivalence"]["equivalent"] is True
    assert payload["state_composition"] == decision["state_composition"]
    assert payload["state_measurements"] == decision["state_measurements"]


def test_payload_fails_if_sensitivities_are_not_surfaced():
    decision = _decision(); decision.pop("state_composition")
    with pytest.raises(RuntimeError, match=STOP):
        build_payload(decision, {"verified": True}, {"equivalent": True}, {"changed_lines": 5, "added_keys": []})


# --- Stage-3 tail-freeze routing -------------------------------------------
# Without this substitution the tail freeze at step 4 resolves
# `verify_target_v2_against_raw` through `t0_tail_authority_v1`'s own globals and
# reaches the frozen bit-exact verifier, stopping the replay before the
# adjudicator is ever called.

from t0_sensitivity_recovery_v2 import (  # noqa: E402
    EXPECTED_TARGET_REPLAYS,
    FREEZE_ANCHOR,
    derive_stage3_run_source,
)


def test_the_tail_freeze_module_resolution_is_redirected():
    source = "    x = 1\n" + FREEZE_ANCHOR + "\n    y = 2\n"
    derived = derive_stage3_run_source(source)
    assert FREEZE_ANCHOR not in derived
    assert "_recovery_freeze_module" in derived
    # Nothing else moved.
    assert derived.count("x = 1") == 1 and derived.count("y = 2") == 1


def test_a_missing_tail_freeze_anchor_is_refused():
    with pytest.raises(RuntimeError) as caught:
        derive_stage3_run_source("    freeze_mod = something_else()\n")
    assert STOP in str(caught.value)


def test_a_duplicated_tail_freeze_anchor_is_refused():
    """Two resolutions would leave one of them on the bit-exact verifier."""
    with pytest.raises(RuntimeError) as caught:
        derive_stage3_run_source(FREEZE_ANCHOR + "\n" + FREEZE_ANCHOR + "\n")
    assert STOP in str(caught.value)


def test_both_frozen_call_sites_are_expected():
    """One at the tail freeze, one in the adjudicator.

    Counted from the frozen call sites rather than from whatever a run
    produced, so the check cannot be satisfied by a routing that silently
    covered only one of them.
    """
    assert EXPECTED_TARGET_REPLAYS == 2
