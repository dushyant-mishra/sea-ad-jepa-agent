"""Independent synthetic exercises of mandatory E3 -> V3 composed fixture path.

The old V3 may still be called by historical tests; those direct calls have
NO scientific source or human authority. The new entry is only mechanical.
"""
from copy import deepcopy
import json

import pytest

from scripts.v5 import td_real_g7_content_enforcement_v1 as E3
from scripts.v5 import td_real_g7_terminal_decision_v3 as V3
from scripts.v5 import td_real_g7_e3_v3_composed_fixture as C
from tests.v5 import test_td_real_g7_content_enforcement_v1_macha_470_red as M


def make(no_support=True):
    if no_support:
        m, full, levels, pins, b, rows = M._no_support_world()
    else:
        full = []
        for i in range(9):
            d = f"D{i:02d}"
            full.append(M._atom(f"core{i}", "RNA:CORE", 1, 9, donor=d))
            full.append(M._atom(f"extra{i}", "CONTEXT:LAWFUL", 1, 9, donor=d))
        m, full, levels, pins = M._honest_package(full)
        b = E3.derive_fixture_g7_e3_input_binding(m, pins, required_sources=["SEA_AD"])
        rows = [M._row(b, 1, 2, donor=f"D{i:02d}", displacement=0.0)
                for i in range(9)]
    return {
        "manifest": m, "full_atoms": full, "levels": levels,
        "expected_pins": pins, "required_sources": ["SEA_AD"],
        "rows": rows, "reference_input_binding_sha256": b,
        "decision_qualification": V3._qual(),
        "reference_artifact": V3._ref(rows, binding=b),
    }


@pytest.mark.parametrize("no_support,expect", [(True,"NOT_ESTIMABLE"),(False,"PASS")])
def test_honest_bind_then_v3_only_reports_mechanics(no_support,expect):
    raw = make(no_support)
    receipt = C.adjudicate_fixture_g7_e3_v3_composed(**json.loads(json.dumps(raw)))
    assert receipt["status"] == "E3_BIND_TO_V3_COMPOSED_FIXTURE_ONLY"
    assert receipt["v3_mechanics_status"] == expect
    assert receipt["authority_effect"] == "NONE"
    assert not any(v for k,v in receipt.items() if k.endswith("_authorized") or k.endswith("_authenticated"))
    assert "source_details" not in receipt
    assert "donor_contrasts" not in str(receipt)


def test_direct_v3_forgery_cannot_cross_composed_content_boundary():
    raw = make()
    forged = deepcopy(raw["rows"])
    for row in forged:
        row.update(penultimate_supported_evidence=1, full_supported_evidence=3,
                   added_supported_evidence=2, terminal_displacement=0.0)
    assert M._v3(forged, raw["reference_input_binding_sha256"])["status"] == "PASS"
    raw["rows"] = forged
    with pytest.raises(E3.G7ContentError, match="supported evidence"):
        C.adjudicate_fixture_g7_e3_v3_composed(**raw)


def test_reference_cannot_be_swapped_after_binding():
    raw = make()
    raw["reference_artifact"]["input_binding_sha256"] = "f"*64
    with pytest.raises(E3.G7ContentError, match="reference"):
        C.adjudicate_fixture_g7_e3_v3_composed(**raw)


def test_composed_entry_screens_hostile_metaclass_before_side_effect():
    class TrapMeta(type):
        calls = 0
        def __eq__(cls, other):
            TrapMeta.calls += 1
            raise RuntimeError("payload ran")
        __hash__ = type.__hash__
    class Trap(metaclass=TrapMeta):
        pass
    raw = make()
    raw["rows"][0]["terminal_displacement"] = Trap()
    with pytest.raises(E3.G7ContentError):
        C.adjudicate_fixture_g7_e3_v3_composed(**raw)
    assert TrapMeta.calls == 0


def test_caller_mutation_does_not_change_returned_receipt_or_replay():
    raw = make()
    original = deepcopy(raw)
    result = C.adjudicate_fixture_g7_e3_v3_composed(**raw)
    for row in raw["rows"]:
        row["full_supported_evidence"] += 30
    assert result == C.adjudicate_fixture_g7_e3_v3_composed(**original)


def test_bound_status_even_if_historical_v3_qualification_self_claims_true():
    raw = make(no_support=False)
    assert raw["decision_qualification"]["known_truth_power_qualified"] is True
    result = C.adjudicate_fixture_g7_e3_v3_composed(**raw)
    assert result["v3_mechanics_status"] == "PASS"
    assert result["reference_issuer_authenticated"] is False
    assert result["known_truth_issuer_authenticated"] is False
    assert result["human_g7_authorized"] is False


@pytest.mark.parametrize("surface", [
    "manifest","full_atoms","levels","expected_pins","rows",
    "required_sources","reference_input_binding_sha256",
    "decision_qualification","reference_artifact","alpha",
])
def test_every_untrusted_surface_requires_exact_snapshot(surface):
    raw = make()
    class Fake:
        def __getattribute__(self, key):
            raise AssertionError("payload getter invoked")
    raw[surface] = Fake()
    with pytest.raises(E3.G7ContentError):
        C.adjudicate_fixture_g7_e3_v3_composed(**raw)
