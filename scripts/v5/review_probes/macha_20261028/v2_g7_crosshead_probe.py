"""Cross-head probe: #479 V2 normalization view against #476 G7 E3 + V3 (synthetic only).

usage: python -I v2_g7_crosshead_probe.py <v2-tree @ae762d70> <g7-tree @26031df2>

Neither tree is modified and neither decision law is changed. The adapter
below is a PROBE ONLY (`V2_TO_G7_PROBE_ADAPTER_V0`), not a proposed contract:
it exists to locate which G7 checks a V2 depth collides with.
"""
import hashlib
import importlib.util
import json
import random
import subprocess
import sys
import types
from copy import deepcopy

V2_TREE, G7_TREE = sys.argv[1], sys.argv[2]
sys.path.insert(0, G7_TREE)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def blob(tree, rel):
    with open(f"{tree}/{rel}", "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def head(tree):
    return subprocess.run(["git", "-C", tree, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()


import scripts.v5  # noqa: E402,F401  (G7 tree package)
pkg = types.ModuleType("scripts.v5.td_unified")
pkg.__path__ = []
sys.modules["scripts.v5.td_unified"] = pkg
load("scripts.v5.td_unified.canonical_v1", f"{V2_TREE}/scripts/v5/td_unified/canonical_v1.py")
Q = load("scripts.v5.td_unified.q_excluded_depth_v1", f"{V2_TREE}/scripts/v5/td_unified/q_excluded_depth_v1.py")
V2 = load("scripts.v5.td_unified.observation_normalization_view_v2_fixture",
          f"{V2_TREE}/scripts/v5/td_unified/observation_normalization_view_v2_fixture.py")
from scripts.v5 import td_real_g7_content_enforcement_v1 as E  # noqa: E402
from scripts.v5 import td_real_g7_terminal_decision_v3 as V3  # noqa: E402

MS, MCU = "MEASURED_SCALAR", "MEASURED_COLLISION_UNRESOLVED"
RIGHTS = ["RNA:CORE", "RNA:EXTENDED", "CONTEXT:LAWFUL"]
LADDER = [{"level_id": f"L{i}", "evidence_rights": RIGHTS[: i + 1]} for i in range(3)]


def manifest(ladder):
    return {"schema": "JEPA_TD_REAL_EVIDENCE_LADDER_MANIFEST_V1", "frozen": True,
            "candidate_id": "DUMMY_CANDIDATE", "full_evidence_rights": list(ladder[-1]["evidence_rights"]),
            "levels": [{"level_id": lv["level_id"], "operator_family": "BIOLOGICAL_EVIDENCE_RIGHTS_RESTRICTION",
                        "evidence_rights": list(lv["evidence_rights"])} for lv in ladder]}


def world(seed, zero_withheld_every_k=0):
    """V2-conserving world: physical total == sum of mapped scalar counts."""
    rng = random.Random(seed)
    addresses = [f"G{i:02d}" for i in range(9)]
    rights = {a: RIGHTS[i % 3] for i, a in enumerate(addresses)}
    rights["G08"] = "CONTEXT:LAWFUL"
    states = {"OP": {a: (MCU if a == "G03" else MS) for a in addresses}}
    cells = []
    for d in range(9):
        counts = {a: rng.randint(0, 12) for a in addresses if states["OP"][a] == MS}
        if zero_withheld_every_k and d % zero_withheld_every_k == 0:
            counts = {a: (c if rights[a] == "RNA:CORE" else 0) for a, c in counts.items()}
        counts["G00"] = counts.get("G00", 0) + 1  # keep base depth >= 1
        cells.append({"cell_id": f"c{d}", "donor_id": f"D{d:02d}", "source_id": "SEA_AD", "operator_id": "OP",
                      "library_total": sum(counts.values()), "counts": counts})
    return {"cells": cells, "address_rights": rights, "operator_states": states,
            "ladder": deepcopy(LADDER), "query_address_id": "G08"}


def g7_outcome(fn):
    try:
        out = fn()
        return out.get("status", "RETURNED")
    except E.G7ContentError as exc:
        return "G7ContentError: " + str(exc)


def package(per_level_atoms, ladder):
    m = manifest(ladder)
    full = deepcopy(per_level_atoms[-1])
    mh, fh = E.canonical_sha256(m), E.canonical_sha256(full)
    levels, tok, atm = [], {}, {}
    for atoms, frozen in zip(per_level_atoms, m["levels"]):
        token = {"schema": E.RIGHTS_TOKEN_SCHEMA, "candidate_id": m["candidate_id"], "level_id": frozen["level_id"],
                 "evidence_rights": list(frozen["evidence_rights"]), "manifest_sha256": mh, "full_atoms_sha256": fh}
        levels.append({"level_id": frozen["level_id"], "rights_token": token, "atoms": deepcopy(atoms)})
        tok[frozen["level_id"]], atm[frozen["level_id"]] = E.canonical_sha256(token), E.canonical_sha256(atoms)
    return m, full, levels, dict(manifest_sha256=mh, full_atoms_sha256=fh, token_sha256_by_level=tok,
                                 atoms_sha256_by_level=atm)


def adapt(v2_rows):
    """V2_TO_G7_PROBE_ADAPTER_V0: rename depth into library_size, recompute #474 atom ids."""
    return [{"atom_id": Q.canonical_sha256(["JEPA_Q_EXCLUDED_ATOM_V1", r["source_id"], r["operator_id"],
                                            r["cell_id"], r["address_id"]]),
             "source": r["source_id"], "donor_id": r["donor_id"], "right": r["evidence_right"],
             "state": r["state"], "count": r["count"], "library_size": r["base_rights_normalization_depth"]}
            for r in v2_rows]


def v2_rows_at(w, level_index):
    """V2 exposes only L0 and terminal; intermediate levels come from the producer V2 wraps,
    passed through V2's own conservation gate and field renaming."""
    if level_index == 0:
        return V2.produce_fixture_student_view_v2(**deepcopy(w))["rows"]
    if level_index == len(w["ladder"]) - 1:
        return V2.produce_fixture_teacher_view_v2(**deepcopy(w))["rows"]
    V2.produce_fixture_student_view_v2(**deepcopy(w))  # conservation and query gates
    lv = Q.produce_rights_ladder_observations(
        **{k: deepcopy(v) for k, v in w.items() if k != "query_address_id"})["levels"][level_index]
    return [{"cell_id": r["cell_id"], "donor_id": r["donor_id"], "source_id": r["source_id"],
             "operator_id": r["operator_id"], "address_id": r["address_id"], "evidence_right": r["right"],
             "state": r["state"], "count": r["count"], "base_rights_normalization_depth": r["library_size"]}
            for r in lv["rows"]]


out = {"trees": {"v2": {"head": head(V2_TREE), "observation_normalization_view_v2_fixture.py":
                        blob(V2_TREE, "scripts/v5/td_unified/observation_normalization_view_v2_fixture.py"),
                        "q_excluded_depth_v1.py": blob(V2_TREE, "scripts/v5/td_unified/q_excluded_depth_v1.py")},
                 "g7": {"head": head(G7_TREE), "td_real_g7_content_enforcement_v1.py":
                        blob(G7_TREE, "scripts/v5/td_real_g7_content_enforcement_v1.py"),
                        "td_real_g7_terminal_decision_v3.py":
                        blob(G7_TREE, "scripts/v5/td_real_g7_terminal_decision_v3.py")}}}

# 1. Schema: V2 rows presented to G7 E3 unchanged.
w = world(1)
raw_levels = [v2_rows_at(w, i) for i in range(3)]
m, full, levels, pins = package(raw_levels, LADDER)
out["1_direct_v2_rows_as_g7_atoms"] = g7_outcome(
    lambda: E.validate_g7_e3_content(manifest=m, full_atoms=full, levels=levels, expected_pins=pins))

# 2. V2's native two-view ladder (student base, teacher terminal).
two = [LADDER[0], LADDER[2]]
m2, full2, levels2, pins2 = package([adapt(raw_levels[0]), adapt(raw_levels[2])], two)
out["2_v2_native_two_view_ladder"] = g7_outcome(
    lambda: E.validate_g7_e3_content(manifest=m2, full_atoms=full2, levels=levels2, expected_pins=pins2))

# 3. Probe adapter over 200 conserved worlds, then the binder with content-true rows.
for label, k in (("3_adapter_random_worlds", 0), ("4_adapter_worlds_with_zero_withheld_units", 3)):
    tally = {}
    for seed in range(200):
        wk = world(seed, k)
        try:
            per_level = [adapt(v2_rows_at(wk, i)) for i in range(3)]
        except Q.QExcludedObservationError as exc:
            key = "V2 refused: " + str(exc)
            tally[key] = tally.get(key, 0) + 1
            continue
        mk, fk, lk, pk = package(per_level, LADDER)
        r = g7_outcome(lambda: E.validate_g7_e3_content(manifest=mk, full_atoms=fk, levels=lk, expected_pins=pk))
        tally[r] = tally.get(r, 0) + 1
    out[label] = dict(sorted(tally.items()))

# 5. Same-code-path reach: binder and V3 on an accepted package (content-true rows, fixture qualification).
reach = {"binder": None, "v3_with_fixture_qualification": None}
for seed in range(200):
    try:
        per_level = [adapt(v2_rows_at(world(seed), i)) for i in range(3)]
    except Q.QExcludedObservationError:
        continue
    mk, fk, lk, pk = package(per_level, LADDER)
    if not g7_outcome(lambda: E.validate_g7_e3_content(manifest=mk, full_atoms=fk, levels=lk,
                                                      expected_pins=pk)).startswith("E3_"):
        continue
    binding = E.derive_fixture_g7_e3_input_binding(mk, pk, required_sources=["SEA_AD"])
    pen = E._measured_counts(lk[-2]["atoms"])
    fin = E._measured_counts(lk[-1]["atoms"])
    rows = [{"source": s, "donor_id": d, "input_binding_sha256": binding,
             "penultimate_supported_evidence": pen[(s, d)], "full_supported_evidence": fin[(s, d)],
             "added_supported_evidence": fin[(s, d)] - pen[(s, d)], "terminal_displacement": 0.02}
            for (s, d) in sorted(fin)]
    reach["binder"] = g7_outcome(lambda: E.bind_g7_terminal_inputs_e3(
        manifest=mk, full_atoms=fk, levels=lk, expected_pins=pk, required_sources=["SEA_AD"],
        rows=deepcopy(rows), reference_input_binding_sha256=binding))
    reach["v3_decision_requires"] = ["decision_qualification (known-truth qualified token)",
                                     "reference_artifact with substantive margins per unit",
                                     "terminal_displacement from a frozen representation (none exists)"]
    reach["v3_takes_binder_receipt"] = "receipt" in V3.adjudicate_g7_terminal_v3.__code__.co_varnames
    break
out["5_same_code_path_reach"] = reach
print(json.dumps(out, indent=1, sort_keys=True))
