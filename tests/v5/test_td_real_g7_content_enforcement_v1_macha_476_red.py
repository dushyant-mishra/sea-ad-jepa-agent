"""Macha independent review of PR #476 (G7 E3 R5X/R6 snapshot) at 26031df2.

Fixture-only and synthetic; reuses the honest worlds of Macha #472. Nothing
here closes R1, R1D or R2: identity and depth provenance stay external.

GREEN tests are guards or measured characterizations of a limitation.
`test_red_*` cases state required behavior the reviewed head lacks.
"""
from __future__ import annotations

from copy import deepcopy

import pytest

from scripts.v5 import td_real_g7_content_enforcement_v1 as E
from tests.v5 import test_td_real_g7_content_enforcement_v1_macha_470_red as M


class _Meta(type):
    calls: list = []

    def __eq__(cls, other):
        _Meta.calls.append("eq")
        if cls.__dict__.get("mode") == "lie":
            return True
        raise RuntimeError("payload-chosen exception")

    __hash__ = type.__hash__


class _Raises(metaclass=_Meta):
    mode = "raise"


class _Lies(metaclass=_Meta):
    mode = "lie"


def _args():
    m, full, levels, pins, b, honest = M._no_support_world()
    return {"manifest": m, "full_atoms": full, "levels": levels, "expected_pins": pins,
            "required_sources": ["SEA_AD"], "rows": deepcopy(honest),
            "reference_input_binding_sha256": b}


def _plant(args, where, obj):
    if where == "manifest":
        args["manifest"]["fixture_note"] = obj
    elif where == "full_atoms":
        args["full_atoms"][0]["count"] = obj
    elif where == "levels":
        args["levels"][-1]["atoms"][0]["count"] = obj
    elif where == "expected_pins":
        args["expected_pins"][next(iter(args["expected_pins"]))] = obj
    elif where == "required_sources":
        args["required_sources"].append(obj)
    elif where == "rows":
        args["rows"][0]["terminal_displacement"] = obj
    elif where == "reference_input_binding_sha256":
        args["reference_input_binding_sha256"] = obj
    return args


def _escape(call):
    _Meta.calls.clear()
    try:
        call()
        outcome = "returned"
    except E.G7ContentError:
        outcome = None
    except BaseException as exc:  # noqa: BLE001 - the escape is the finding
        outcome = f"{type(exc).__module__}.{type(exc).__qualname__}"
    ran = len(_Meta.calls)
    return None if outcome is None and not ran else f"escape={outcome} payload_calls={ran}"


_SEVEN = ["manifest", "full_atoms", "levels", "expected_pins", "required_sources", "rows",
          "reference_input_binding_sha256"]


@pytest.mark.parametrize("cls", [_Raises, _Lies], ids=["raises", "lies"])
@pytest.mark.parametrize("where", _SEVEN)
def test_red_metaclass_payload_runs_inside_the_binder_snapshot(where, cls):
    """R5X class survives the snapshot: `_strict_json` tests leaves with
    `type(obj) in (bool, int, str)`, which compares the payload's type and so
    runs a payload metaclass __eq__. 'raises' leaves the binder as RuntimeError
    (not in `_snapshot`'s except tuple); 'lies' runs payload code before the
    encoder refuses. Pre-existing since the #470 R5 `_strict_json`."""
    args = _plant(_args(), where, cls())
    finding = _escape(lambda: E.bind_g7_terminal_inputs_e3(**args))
    if finding:
        pytest.fail(finding, pytrace=False)


@pytest.mark.parametrize("cls", [_Raises, _Lies], ids=["raises", "lies"])
@pytest.mark.parametrize("entry", ["validate_g7_e3_content", "derive_fixture_g7_e3_input_binding"])
def test_red_metaclass_payload_runs_inside_the_other_entry_points(entry, cls):
    args = _plant(_args(), "manifest", cls())
    if entry == "validate_g7_e3_content":
        call = lambda: E.validate_g7_e3_content(  # noqa: E731
            manifest=args["manifest"], full_atoms=args["full_atoms"],
            levels=args["levels"], expected_pins=args["expected_pins"])
    else:
        call = lambda: E.derive_fixture_g7_e3_input_binding(  # noqa: E731
            args["manifest"], args["expected_pins"], required_sources=["SEA_AD"])
    finding = _escape(call)
    if finding:
        pytest.fail(finding, pytrace=False)


def test_sort_and_laundering_routes_are_closed_before_canonical_encoding():
    """Guards: a str-subclass key whose __lt__ would run during sort_keys, an
    int key that json.dumps would launder into a string, and a tuple that it
    would launder into a list are all refused before encoding."""
    calls = []

    class LtKey(str):
        __hash__ = str.__hash__

        def __lt__(self, other):
            calls.append("lt")
            raise RuntimeError("payload sort")

    for mutate in (
        lambda a: a["manifest"].__setitem__(LtKey("zz"), 1),
        lambda a: a["manifest"].__setitem__(1, "laundered key"),
        lambda a: a["rows"].__setitem__(0, tuple(a["rows"][0].items())),
    ):
        args = _args()
        mutate(args)
        with pytest.raises(E.G7ContentError):
            E.bind_g7_terminal_inputs_e3(**args)
    assert calls == []


def test_receipt_is_independent_of_caller_objects_after_return():
    args = _args()
    receipt = E.bind_g7_terminal_inputs_e3(**args)
    before = deepcopy(receipt)
    for row in args["rows"]:
        row.update(penultimate_supported_evidence=1, full_supported_evidence=3,
                   added_supported_evidence=2, terminal_displacement=0.0)
    assert receipt == before
    assert M._rows_sha(args["rows"]) != receipt["deciding_rows_sha256"]


def test_characterize_v3_still_decides_pass_on_rows_the_binder_refuses():
    """LIMITATION (composition). The binder now refuses forged support, but
    adjudicate_g7_terminal_v3 takes no binder receipt and nothing in the
    repository checks deciding_rows_sha256 before deciding. Called without the
    binder, V3 turns the same forged rows into PASS. R6 is closed at the
    binder, not on the path to a V3 decision."""
    args = _args()
    b = args["reference_input_binding_sha256"]
    assert M._v3(deepcopy(args["rows"]), b)["status"] == "NOT_ESTIMABLE"
    forged = deepcopy(args["rows"])
    for row in forged:
        row.update(penultimate_supported_evidence=1, full_supported_evidence=3,
                   added_supported_evidence=2, terminal_displacement=0.0)
    with pytest.raises(E.G7ContentError):
        E.bind_g7_terminal_inputs_e3(**{**args, "rows": deepcopy(forged)})
    assert M._v3(forged, b)["status"] == "PASS"
