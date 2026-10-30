"""Local probe: q-excluded depth producer output through the #470 G7 E3 validator.

usage: python -I g7_conformance_probe.py <producer-tree> <g7-tree>   (synthetic values only)
"""
import importlib.util
import json
import random
import sys
from copy import deepcopy

PRODUCER_TREE, G7_TREE = sys.argv[1], sys.argv[2]
sys.path.insert(0, G7_TREE)  # G7 module + its ladder contract


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


import scripts.v5  # noqa: E402,F401  (G7 tree package)
import types  # noqa: E402
pkg = types.ModuleType("scripts.v5.td_unified")
pkg.__path__ = []
sys.modules["scripts.v5.td_unified"] = pkg
load("scripts.v5.td_unified.canonical_v1", f"{PRODUCER_TREE}/scripts/v5/td_unified/canonical_v1.py")
Q = load("scripts.v5.td_unified.q_excluded_depth_v1", f"{PRODUCER_TREE}/scripts/v5/td_unified/q_excluded_depth_v1.py")
from scripts.v5 import td_real_g7_content_enforcement_v1 as E  # noqa: E402

MS, SU, MCU = "MEASURED_SCALAR", "STRUCTURALLY_UNMEASURED", "MEASURED_COLLISION_UNRESOLVED"
RIGHTS = ["RNA:CORE", "RNA:EXTENDED", "CONTEXT:LAWFUL"]
LADDER = [{"level_id": f"L{i}", "evidence_rights": RIGHTS[: i + 1]} for i in range(3)]


def manifest():
    return {"schema": "JEPA_TD_REAL_EVIDENCE_LADDER_MANIFEST_V1", "frozen": True,
            "candidate_id": "DUMMY_CANDIDATE", "full_evidence_rights": list(RIGHTS),
            "levels": [{"level_id": lv["level_id"], "operator_family": "BIOLOGICAL_EVIDENCE_RIGHTS_RESTRICTION",
                        "evidence_rights": list(lv["evidence_rights"])} for lv in LADDER]}


def world(seed, hidden_bump=0):
    rng = random.Random(seed)
    addresses = [f"G{i:02d}" for i in range(9)]
    rights = {a: RIGHTS[i % 3] for i, a in enumerate(addresses)}
    states = {"OP": {a: (MCU if rights[a] == "RNA:CORE" and i == 3 else MS) for i, a in enumerate(addresses)}}
    cells = []
    for d in range(9):
        counts = {a: rng.randint(0, 12) for a in addresses if states["OP"][a] == MS}
        if hidden_bump:
            for a in addresses:
                if rights[a] != "RNA:CORE" and states["OP"][a] == MS:
                    counts[a] += hidden_bump
        cells.append({"cell_id": f"c{d}", "donor_id": f"D{d:02d}", "source_id": "SEA_AD", "operator_id": "OP",
                      "library_total": sum(counts.values()) + rng.randint(0, 20) + 5, "counts": counts})
    # keep the physical total equal across the two worlds except for the bumped withheld mass
    return {"cells": cells, "address_rights": rights, "operator_states": states, "ladder": deepcopy(LADDER)}


def package(result):
    m = manifest()
    full = deepcopy(next(lv for lv in result["levels"] if lv["level_id"] == "L2")["g7_atoms"])
    mh, fh = E.canonical_sha256(m), E.canonical_sha256(full)
    levels, tok, atm = [], {}, {}
    for lv, frozen in zip(result["levels"], m["levels"]):
        assert frozen["evidence_rights"] == lv["evidence_rights"]
        token = {"schema": E.RIGHTS_TOKEN_SCHEMA, "candidate_id": m["candidate_id"], "level_id": lv["level_id"],
                 "evidence_rights": list(frozen["evidence_rights"]), "manifest_sha256": mh, "full_atoms_sha256": fh}
        atoms = deepcopy(lv["g7_atoms"])
        levels.append({"level_id": lv["level_id"], "rights_token": token, "atoms": atoms})
        tok[lv["level_id"]], atm[lv["level_id"]] = E.canonical_sha256(token), E.canonical_sha256(atoms)
    return m, full, levels, dict(manifest_sha256=mh, full_atoms_sha256=fh, token_sha256_by_level=tok,
                                 atoms_sha256_by_level=atm)


def outcome(fn):
    try:
        return fn()["status"]
    except E.G7ContentError as exc:
        return "G7ContentError: " + str(exc)


out = {}
accepted = refused = 0
reasons = {}
for seed in range(200):
    res = Q.produce_rights_ladder_observations(**world(seed))
    m, full, levels, pins = package(res)
    r = outcome(lambda: E.validate_g7_e3_content(manifest=m, full_atoms=full, levels=levels, expected_pins=pins))
    if r.startswith("E3_"):
        accepted += 1
    else:
        refused += 1
        reasons[r] = reasons.get(r, 0) + 1
out["g7_validate_producer_packages"] = {"accepted": accepted, "refused": refused, "refusal_reasons": reasons}

# Two worlds that differ ONLY in withheld-at-L0 mass (physical totals move with it).
a = Q.produce_rights_ladder_observations(**world(7))
w2 = world(7, hidden_bump=5)
for c1, c2 in zip(world(7)["cells"], w2["cells"]):
    c2["library_total"] = c1["library_total"] + sum(c2["counts"].values()) - sum(c1["counts"].values())
b = Q.produce_rights_ladder_observations(**w2)
lv = lambda r, i: next(x for x in r["levels"] if x["level_id"] == i)  # noqa: E731
out["two_world_L0_rows_identical"] = lv(a, "L0")["rows_sha256"] == lv(b, "L0")["rows_sha256"]
naive = lambda w: sorted((c["cell_id"], c["library_total"]) for c in w["cells"])  # noqa: E731
out["two_world_naive_physical_totals_identical"] = naive(world(7)) == naive(w2)
print(json.dumps(out, indent=1, sort_keys=True))
