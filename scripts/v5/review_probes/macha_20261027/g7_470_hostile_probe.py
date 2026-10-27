"""Macha independent probe of #470 (G7 E3 R3-R5). Synthetic fixture values only.

usage: python -I probe.py <tree-root>   -> JSON on stdout
"""
import itertools
import json
import sys
from copy import deepcopy

sys.path.insert(0, sys.argv[1])
from scripts.v5 import td_real_g7_content_enforcement_v1 as E  # noqa: E402
from scripts.v5 import td_real_g7_terminal_decision_v3 as V3  # noqa: E402

RIGHTS = ["RNA:CORE", "RNA:EXTENDED", "CONTEXT:LAWFUL"]


def manifest():
    return {"schema": "JEPA_TD_REAL_EVIDENCE_LADDER_MANIFEST_V1", "frozen": True,
            "candidate_id": "DUMMY_CANDIDATE", "full_evidence_rights": list(RIGHTS),
            "levels": [{"level_id": f"L{i}", "operator_family": "BIOLOGICAL_EVIDENCE_RIGHTS_RESTRICTION",
                        "evidence_rights": list(RIGHTS[: i + 1])} for i in range(3)]}


def atom(aid, right, count, lib, source="SEA_AD", donor="D1", state="MEASURED_SCALAR"):
    if state != "MEASURED_SCALAR":
        count = lib = None
    return {"atom_id": aid, "source": source, "donor_id": donor, "right": right,
            "state": state, "count": count, "library_size": lib}


def package(full):
    m = manifest()
    mh, fh = E.canonical_sha256(m), E.canonical_sha256(full)
    levels, tok, atm = [], {}, {}
    for lv in m["levels"]:
        atoms = deepcopy(full)
        for a in atoms:
            if a["state"] == "MEASURED_SCALAR" and a["right"] not in lv["evidence_rights"]:
                a.update(state="WITHHELD_BY_EVIDENCE_RIGHTS", count=None, library_size=None)
        token = {"schema": E.RIGHTS_TOKEN_SCHEMA, "candidate_id": m["candidate_id"], "level_id": lv["level_id"],
                 "evidence_rights": list(lv["evidence_rights"]), "manifest_sha256": mh, "full_atoms_sha256": fh}
        levels.append({"level_id": lv["level_id"], "rights_token": token, "atoms": atoms})
        tok[lv["level_id"]] = E.canonical_sha256(token)
        atm[lv["level_id"]] = E.canonical_sha256(atoms)
    return m, full, levels, dict(manifest_sha256=mh, full_atoms_sha256=fh,
                                 token_sha256_by_level=tok, atoms_sha256_by_level=atm)


def row(b, pen, fin, source="SEA_AD", donor="D1", disp=0.02):
    return {"source": source, "donor_id": donor, "terminal_displacement": disp,
            "penultimate_supported_evidence": pen, "full_supported_evidence": fin,
            "added_supported_evidence": fin - pen, "input_binding_sha256": b}


def bind(m, full, levels, pins, roster, rows, b):
    return E.bind_g7_terminal_inputs_e3(manifest=m, full_atoms=full, levels=levels, expected_pins=pins,
                                        required_sources=roster, rows=rows, reference_input_binding_sha256=b)


def outcome(fn):
    try:
        r = fn()
        return r.get("status", "RETURNED")
    except E.G7ContentError:
        return "G7ContentError"
    except BaseException as exc:  # noqa: BLE001 - the escape type is the measurement
        return "ESCAPED:" + type(exc).__name__


out = {"tree": sys.argv[1]}

# ---- R3: exhaustive two-unit rosters over the alphabet {a, :} up to length 3 ----
S = ["".join(p) for n in (1, 2, 3) for p in itertools.product("a:", repeat=n)]
units = [(s, d) for s in S for d in S]
tally = {"pairs": 0, "v3_collide": 0, "bound_and_collide": 0, "bound": 0,
         "refused_no_collision_no_dcolon": 0, "refused_dcolon_only": 0, "escaped": 0}
for u1, u2 in itertools.combinations(units, 2):
    full = [atom("x1", "RNA:CORE", 1, 9, *u1), atom("x2", "RNA:CORE", 1, 9, *u2)]
    roster = sorted({u1[0], u2[0]})
    m, full, levels, pins = package(full)
    b = E.derive_fixture_g7_e3_input_binding(m, pins, required_sources=roster)
    rows = [row(b, 1, 1, *u1), row(b, 1, 1, *u2)]
    res = outcome(lambda: bind(m, full, levels, pins, roster, rows, b))
    collide = V3._unit_key(*u1) == V3._unit_key(*u2)
    dcolon = any("::" in x for x in u1 + u2)
    tally["pairs"] += 1
    tally["v3_collide"] += collide
    if res.startswith("ESCAPED"):
        tally["escaped"] += 1
    elif res == "E3_TERMINAL_INPUTS_BOUND_FIXTURE_ONLY":
        tally["bound"] += 1
        tally["bound_and_collide"] += collide
    elif not collide and not dcolon:
        tally["refused_no_collision_no_dcolon"] += 1
    elif not collide:
        tally["refused_dcolon_only"] += 1
out["r3_exhaustive"] = tally

# R3 with a colliding unit that has NO measured scalar (structural only): still in the roster.
full = [atom("x1", "RNA:CORE", 1, 9, "A:", "B"),
        atom("x2", "RNA:CORE", None, None, "A", ":B", state="STRUCTURALLY_UNMEASURED")]
m, full, levels, pins = package(full)
b = E.derive_fixture_g7_e3_input_binding(m, pins, required_sources=["A", "A:"])
out["r3_structural_only_collider"] = outcome(lambda: bind(m, full, levels, pins, ["A", "A:"],
                                                         [row(b, 1, 1, "A:", "B"), row(b, 0, 0, "A", ":B")], b))
# Legitimate single-colon identities that do not collide must still bind.
full = [atom("x1", "RNA:CORE", 1, 9, "SEA-AD:MTG", "H20.33.001"), atom("x2", "RNA:CORE", 1, 9, "SEA-AD:MTG", "H21:7")]
m, full, levels, pins = package(full)
b = E.derive_fixture_g7_e3_input_binding(m, pins, required_sources=["SEA-AD:MTG"])
out["r3_legit_colon_ids"] = outcome(lambda: bind(m, full, levels, pins, ["SEA-AD:MTG"],
                                                [row(b, 1, 1, "SEA-AD:MTG", "H20.33.001"),
                                                 row(b, 1, 1, "SEA-AD:MTG", "H21:7")], b))


# ---- R5: non-recursion escapes through containers never canonicalized before comparison ----
class Boom(str):
    __hash__ = str.__hash__

    def __eq__(self, other):
        raise RuntimeError("payload-chosen exception")

    __ne__ = __eq__


def honest3():
    full = [atom("a", "RNA:CORE", 0, 31), atom("b", "RNA:EXTENDED", 5, 31), atom("c", "CONTEXT:LAWFUL", 3, 31)]
    m, full, levels, pins = package(full)
    b = E.derive_fixture_g7_e3_input_binding(m, pins, required_sources=["SEA_AD"])
    return m, full, levels, pins, b


def rekey(d, key):
    v = d.pop(key)
    d[Boom(key)] = v


escapes = {}
m, full, levels, pins, b = honest3()
out["r5_honest_baseline"] = outcome(lambda: bind(m, full, levels, pins, ["SEA_AD"], [row(b, 2, 3)], b))
for name in ("level_id_value", "level_key", "token_key", "pins_key", "pins_level_map_key", "row_key"):
    m, full, levels, pins, b = honest3()
    rows = [row(b, 2, 3)]
    if name == "level_id_value":
        levels[0]["level_id"] = Boom("L0")
    elif name == "level_key":
        rekey(levels[0], "atoms")
    elif name == "token_key":
        rekey(levels[0]["rights_token"], "schema")
    elif name == "pins_key":
        rekey(pins, "manifest_sha256")
    elif name == "pins_level_map_key":
        rekey(pins["token_sha256_by_level"], "L0")
    elif name == "row_key":
        rekey(rows[0], "source")
    escapes[name] = outcome(lambda: bind(m, full, levels, pins, ["SEA_AD"], rows, b))
out["r5_hostile_key_or_value"] = escapes
# Deep nesting on each canonicalized surface (the R5 repair itself).
deep = 0
for _ in range(5000):
    deep = [deep]
deepd = 0
for _ in range(5000):
    deepd = {"k": deepd}
deep_res = {}
for name in ("atom_count_list", "atom_count_dict", "token_value", "manifest_extra_key"):
    m, full, levels, pins, b = honest3()
    if name == "atom_count_list":
        full = deepcopy(full); full[1]["count"] = deep
    elif name == "atom_count_dict":
        full = deepcopy(full); full[1]["count"] = deepd
    elif name == "token_value":
        levels[0]["rights_token"]["candidate_id"] = deep
    elif name == "manifest_extra_key":
        m = dict(m, extra=deepd)
    deep_res[name] = outcome(lambda: bind(m, full, levels, pins, ["SEA_AD"], [row(b, 2, 3)], b))
out["r5_deep"] = deep_res


def depth(o, d=0):
    if isinstance(o, dict):
        return max([depth(v, d + 1) for v in o.values()] + [d])
    if isinstance(o, list):
        return max([depth(v, d + 1) for v in o] + [d])
    return d


m, full, levels, pins, b = honest3()
out["r5_max_lawful_fixture_depth"] = max(depth(m), depth(full), depth(levels), depth(pins))
out["kat_honest_pins_sha256"] = E.canonical_sha256(pins)
out["kat_honest_receipt_rows_sha256"] = bind(m, full, levels, pins, ["SEA_AD"], [row(b, 2, 3)], b)["deciding_rows_sha256"]


# ---- R6: hostile row key re-writes already-validated rows; the receipt binds the forgery ----
def r6_world(n=9):
    full = [atom(f"x{i}", "RNA:CORE", 1, 9, "SEA_AD", f"D{i:02d}") for i in range(n)]
    m, full, levels, pins = package(full)
    b = E.derive_fixture_g7_e3_input_binding(m, pins, required_sources=["SEA_AD"])
    honest = [row(b, 1, 1, "SEA_AD", f"D{i:02d}") for i in range(n)]  # content: added support 0 everywhere
    return m, full, levels, pins, b, honest


m, full, levels, pins, b, honest = r6_world()
rows = deepcopy(honest)
victim_rows, hostile = rows[:-1], rows[-1]


class Forger(str):
    __hash__ = str.__hash__
    fired = False

    def __eq__(self, other):
        if not Forger.fired:
            Forger.fired = True
            for r in victim_rows:  # already validated by the binder
                r.update(penultimate_supported_evidence=1, full_supported_evidence=3,
                         added_supported_evidence=2, terminal_displacement=0.0)
            value = hostile.pop(self)
            hostile["source"] = value  # leave only exact str keys for the final digest
        return str.__eq__(self, other)

    def __ne__(self, other):
        return not self.__eq__(other)


rekey(hostile, "source")
hostile[Forger("source")] = hostile.pop(next(k for k in hostile if type(k) is Boom))
receipt = outcome(lambda: bind(m, full, levels, pins, ["SEA_AD"], rows, b))
r6 = {"binder_on_toctou_rows": receipt, "forger_fired": Forger.fired}
if receipt == "E3_TERMINAL_INPUTS_BOUND_FIXTURE_ONLY":
    Forger.fired = True  # rows are now plain
    rec = bind(m, full, levels, pins, ["SEA_AD"], deepcopy(honest), b)
    r6["honest_rows_sha256"] = rec["deciding_rows_sha256"]
    Forger.fired = False
    m2, full2, levels2, pins2, b2, honest2 = r6_world()
    rows2 = deepcopy(honest2)
    victim_rows, hostile = rows2[:-1], rows2[-1]
    rekey(hostile, "source")
    hostile[Forger("source")] = hostile.pop(next(k for k in hostile if type(k) is Boom))
    rec2 = bind(m2, full2, levels2, pins2, ["SEA_AD"], rows2, b2)
    r6["toctou_receipt_rows_sha256"] = rec2["deciding_rows_sha256"]
    r6["receipt_matches_final_rows"] = rec2["deciding_rows_sha256"] == E.canonical_sha256(
        sorted(rows2, key=lambda r: (r["source"], r["donor_id"])))
    r6["same_rows_presented_directly"] = outcome(lambda: bind(m2, full2, levels2, pins2, ["SEA_AD"],
                                                               deepcopy(rows2), b2))
    for label, rs in (("honest", honest2), ("forged", rows2)):
        d = V3.adjudicate_g7_terminal_v3(rows=rs, required_sources=["SEA_AD"], decision_qualification=V3._qual(),
                                         reference_artifact=V3._ref(rs, binding=b2))
        r6[f"v3_{label}"] = [d["status"], d["reason"]]
out["r6_toctou"] = r6

# ---- R1-D: one physical donor under several donor_id strings is bound as several donors ----
spec = [f"H20.33.001-{blk}" for blk in ("MTG", "DLPFC", "A9", "A1", "M1", "S1", "V1", "CB")]
full = [atom(f"x{i}", "RNA:CORE", 1, 9, "SEA_AD", d) for i, d in enumerate(spec)] + \
       [atom(f"y{i}", "CONTEXT:LAWFUL", 2, 9, "SEA_AD", d) for i, d in enumerate(spec)]
m, full, levels, pins = package(full)
b = E.derive_fixture_g7_e3_input_binding(m, pins, required_sources=["SEA_AD"])
rows = [row(b, 1, 2, "SEA_AD", d, disp=0.0) for d in spec]
out["r1d_specimen_ids_as_donors"] = outcome(lambda: bind(m, full, levels, pins, ["SEA_AD"], rows, b))
d = V3.adjudicate_g7_terminal_v3(rows=rows, required_sources=["SEA_AD"], decision_qualification=V3._qual(),
                                 reference_artifact=V3._ref(rows, binding=b))
out["r1d_v3_on_one_physical_donor"] = [d["status"], d["reason"], d["source_details"]["SEA_AD"]["donor_count"]]
print(json.dumps(out, indent=1, sort_keys=True))
