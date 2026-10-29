"""ChatGPT repair guards for PR #476 against immutable Macha #482.

Fixture only. The historical V3 decision law remains unchanged. These tests
exercise only the repaired exact-type snapshot and the composed
bind->snapshot->decide entry point. R1/R1D/R2 external provenance remains RED.
"""
from copy import deepcopy

import pytest

from scripts.v5 import td_real_g7_content_enforcement_v1 as E
from scripts.v5 import td_real_g7_terminal_decision_v3 as V3
from tests.v5 import test_td_real_g7_content_enforcement_v1_macha_470_red as M


def _args():
    manifest, full, levels, pins, binding, rows = M._no_support_world()
    return {
        "manifest": manifest,
        "full_atoms": full,
        "levels": levels,
        "expected_pins": pins,
        "required_sources": ["SEA_AD"],
        "rows": deepcopy(rows),
        "reference_input_binding_sha256": binding,
        "decision_qualification": V3._qual(),
        "reference_artifact": V3._ref(rows, binding=binding),
        "alpha": 0.01,
    }


def test_composed_path_consumes_exact_binder_rows_and_matches_honest_v3():
    args = _args()
    direct = V3.adjudicate_g7_terminal_v3(
        rows=deepcopy(args["rows"]),
        required_sources=deepcopy(args["required_sources"]),
        decision_qualification=deepcopy(args["decision_qualification"]),
        reference_artifact=deepcopy(args["reference_artifact"]),
        alpha=args["alpha"],
    )
    out = E.adjudicate_fixture_g7_terminal_v3_bound(**deepcopy(args))
    assert out["status"] == "BOUND_V3_DECISION_FIXTURE_ONLY"
    assert out["decision"] == direct
    assert out["deciding_rows_sha256"] == out["binder_receipt"]["deciding_rows_sha256"]
    assert out["binder_receipt"]["input_binding_sha256"] == args["reference_input_binding_sha256"]
    assert out["externally_authenticated"] is False
    assert out["donor_identity_authenticated"] is False
    assert out["q_excluded_library_provenance_authenticated"] is False
    assert out["human_g7_authorized"] is False
    assert out["authority_effect"] == "NONE"


def test_composed_path_refuses_rows_direct_v3_can_turn_into_pass():
    args = _args()
    forged = deepcopy(args["rows"])
    for row in forged:
        row.update(
            penultimate_supported_evidence=1,
            full_supported_evidence=3,
            added_supported_evidence=2,
            terminal_displacement=0.0,
        )

    # Preserve the #482 characterization: historical direct V3 is still a
    # lower-level primitive and can decide these caller-forged rows.
    assert M._v3(deepcopy(forged), args["reference_input_binding_sha256"])["status"] == "PASS"

    args["rows"] = forged
    args["reference_artifact"] = V3._ref(
        forged, binding=args["reference_input_binding_sha256"]
    )
    with pytest.raises(E.G7ContentError):
        E.adjudicate_fixture_g7_terminal_v3_bound(**args)


def test_composed_result_is_independent_of_caller_mutation_after_return():
    args = _args()
    out = E.adjudicate_fixture_g7_terminal_v3_bound(**args)
    before = deepcopy(out)

    for row in args["rows"]:
        row.update(
            penultimate_supported_evidence=1,
            full_supported_evidence=3,
            added_supported_evidence=2,
            terminal_displacement=0.0,
        )
    args["required_sources"].append("FORGED")
    args["decision_qualification"]["known_truth_power_qualified"] = False

    assert out == before


class _Meta(type):
    calls = []

    def __eq__(cls, other):
        _Meta.calls.append("eq")
        raise RuntimeError("payload metaclass equality executed")

    __hash__ = type.__hash__


class _Payload(metaclass=_Meta):
    pass


def test_composed_snapshot_rejects_payload_type_without_running_metaclass_eq():
    args = _args()
    args["alpha"] = _Payload()
    _Meta.calls.clear()
    try:
        E.adjudicate_fixture_g7_terminal_v3_bound(**args)
        escaped = "returned"
    except E.G7ContentError:
        escaped = None
    except BaseException as exc:  # noqa: BLE001
        escaped = type(exc).__qualname__

    if escaped is not None or _Meta.calls:
        pytest.fail(
            f"escape={escaped} payload_calls={len(_Meta.calls)}",
            pytrace=False,
        )
