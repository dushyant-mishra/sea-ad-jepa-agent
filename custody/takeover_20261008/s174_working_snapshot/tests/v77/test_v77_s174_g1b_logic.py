"""G1b's logic: each requirement passes on the configuration it describes and fails, by itself, on
the violation it guards against."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("s174_g1b", ROOT / "scripts" / "v77" / "gate_s174_g1b.py")
G = importlib.util.module_from_spec(spec)
sys.modules["s174_g1b"] = G
spec.loader.exec_module(G)

ZERO = dict(entries=10, disagreements=0, disagreements_outside_remap=0, entries_outside_remap=10, remap_checked=0,
            remap_wrong=0, collision_checked=0, collision_wrong=0, reread_ambiguity_outside_collisions=0)


def _m(study, **over):
    return dict(study=study, **{**ZERO, **over})


def test_a_remapped_address_disagrees_with_the_reread_but_is_explained():
    new = {1: 5, 2: 7}            # address 2 holds the remapped source gene's count
    reread = {1: 5}               # the simple re-read cannot resolve the remapped ID
    c = G.check_cell(new, reread, set(), set(), {2}, {2: 7}, {})
    assert c["disagreements"] == 1 and c["disagreements_outside_remap"] == 0 and c["remap_wrong"] == 0


def test_a_summed_collision_is_caught():
    new = {9: 3 + 4}              # kept column 3 plus an excluded column 4: summed, forbidden
    c = G.check_cell(new, {}, set(), {9}, set(), {}, {9: 3})
    assert c["collision_wrong"] == 1


def test_the_passing_configuration_passes_every_requirement():
    per = [_m("HVS"), _m("SEA_AD", disagreements=3, remap_checked=3, collision_checked=2)]
    assert all(G.requirements_hold(per, True).values())


def test_each_violation_fails_its_own_requirement():
    base = [_m("HVS"), _m("SEA_AD", disagreements=3, remap_checked=3)]
    cases = {
        "R1": [_m("HVS", disagreements=1), base[1]],
        "R2": [base[0], _m("SEA_AD", disagreements=3, disagreements_outside_remap=1)],
        "R3": [base[0], _m("SEA_AD", remap_wrong=1)],
        "R6": [base[0], _m("SEA_AD", collision_wrong=1)],
    }
    for req, per in cases.items():
        got = G.requirements_hold(per, True)
        assert got[req] is False and got["R5"] is False, req
    assert G.requirements_hold(base, False)["R7"] is False
    amb = G.requirements_hold([base[0], _m("SEA_AD", reread_ambiguity_outside_collisions=1)], True)
    assert amb["R5"] is False, "an ambiguity the collision policy does not explain is an unexplained discrepancy"
