#!/usr/bin/env python3
"""Old-vs-new routing over the complete logical outcome space of the corrected TD replay. Read-only; opens no data.

  dump <root>                       write one routing line per allowed outcome combination, computed by the package
                                    code at <root> (its own execute + routing V2 modules), as JSON lines to stdout
  compare <old dump> <new dump|-> <out dir> <root holding the frozen routing V2>
                                    compare the f5673f9b routing with the revised interpretation. The revised rule is
                                    re-implemented here independently (PROTOTYPE) and, when a new dump is given, every
                                    combination must match it exactly. Also evaluates the considered alternative (U1).

Outcome space: each stage runs its frozen invocation order and stops at the first non-PASS; each invocation is PASS,
FAIL or NOT_ESTIMABLE (an IMPLEMENTATION_FAILURE yields no routing input and is excluded). TD56 has 7 sequences and
each panel stage 13, so 7 x 13^3 = 15,379 combinations. These are logical possibilities, not probabilities.

Source-order analyses:
  (a) observed space: for every combination, move a stage's first non-PASS to a different source in the same panel
      (same outcome type, earlier sources PASS) and check whether the biological state changes;
  (b) latent truth: assign PASS/FAIL/NOT_ESTIMABLE to every planned invocation (27 x 729^3 configurations, counted with
      multiplicities), observe it under each of the 6 source orders, and count configurations whose biological state
      depends on the source order.
"""
from __future__ import annotations

import collections
import csv
import itertools
import json
import sys
from pathlib import Path

STAGES = ("TD56", "TD57B", "TD57C", "TD59")
SOURCES = ("HVS", "NPH52", "SEA_AD")
OUTCOMES = ("PASS", "FAIL", "NOT_ESTIMABLE")
ORDERS = {"TD56": [(None, s) for s in SOURCES],
          **{st: [(p, s) for p in (0, 1) for s in SOURCES] for st in ("TD57B", "TD57C", "TD59")}}


def stage_status(outs):
    return next((o for o in outs if o != "PASS"), "PASS")


def sequences(order):
    out = [[(p, s, "PASS") for p, s in order]]
    for k in range(len(order)):
        for bad in ("FAIL", "NOT_ESTIMABLE"):
            out.append([(p, s, "PASS") for p, s in order[:k]] + [(order[k][0], order[k][1], bad)])
    return out


def combos():
    per = [sequences(ORDERS[st]) for st in STAGES]
    for combo in itertools.product(*per):
        yield {st: seq for st, seq in zip(STAGES, combo)}


def key(c) -> str:
    return " | ".join(f"{st}:" + ",".join(f"{'' if p is None else f'P{p}.'}{s}={o[0] if o != 'NOT_ESTIMABLE' else 'N'}"
                                             for p, s, o in c[st]) for st in STAGES)


def discordant(seq) -> bool:
    by_panel = collections.defaultdict(set)
    for p, _s, o in seq:
        by_panel[p].add(o)
    return any({"PASS", "FAIL"} <= v for v in by_panel.values())


# ------------------------------------------------------------------------------------------- rules (independent)
def universal_old(c):          # f5673f9b rule, restated: same-panel PASS+FAIL anywhere -> FAIL
    if any(discordant(c[st]) for st in STAGES):
        return "FAIL"
    return "NOT_ESTIMABLE" if any(stage_status([o for *_, o in c[st]]) == "NOT_ESTIMABLE" for st in STAGES) else "PASS"


def universal_new(c):          # PROTOTYPE of the revised rule: never FAIL; NOT_ESTIMABLE iff a stage is NOT_ESTIMABLE
    return "NOT_ESTIMABLE" if any(stage_status([o for *_, o in c[st]]) == "NOT_ESTIMABLE" for st in STAGES) else "PASS"


def universal_u1(c):           # considered alternative: discordance -> NOT_ESTIMABLE (unresolved), never FAIL
    if any(discordant(c[st]) for st in STAGES) or any(stage_status([o for *_, o in c[st]]) == "NOT_ESTIMABLE" for st in STAGES):
        return "NOT_ESTIMABLE"
    return "PASS"


def load_routing(root: Path):
    sys.path.insert(0, str(root / "scripts" / "v5"))
    import td_corrected_replay_routing_v2 as R  # noqa: E402
    return R


def route(R, statuses: dict, universal: str) -> dict:
    out = R.interpret_corrected_replay(td56=statuses["TD56"], td57b=statuses["TD57B"], td57c=statuses["TD57C"],
                                       td59=statuses["TD59"], universal_source=universal)
    cr = out["candidate_routes"]
    return {"state": out["biological_state"], "v4": out["v4_relational_status"], "C2": cr["C2_RELATIONAL_SHARED"],
            "C4": cr["C4_STRUCTURED_COMPOSITE"], "C6": cr["C6_SHARED_QUERY_COMPOSITE"],
            "authority_false": all(out.get(k) is False for k in ("target_selected", "representation_selected", "td60_authorized",
                                                                  "stage4_authorized", "training_authorized"))}


# ------------------------------------------------------------------------------------------------------- dump
def dump(root: Path) -> None:
    sys.path.insert(0, str(root / "scripts" / "v5"))
    import td_corrected_replay_execute_v1 as X  # noqa: E402
    import td_corrected_replay_routing_v2 as R  # noqa: E402
    for c in combos():
        stages = {st: {"invocations": [{"panel": p, "source": s, "outcome": o} for p, s, o in c[st]],
                       "status": stage_status([o for *_, o in c[st]])} for st in STAGES}
        ri = X.routing_inputs(stages)
        r = route(R, {st: ri[st.lower()] for st in STAGES}, ri["universal_source"])
        print(json.dumps({"combo": key(c), "universal_source": ri["universal_source"], **r}, sort_keys=True))


# ---------------------------------------------------------------------------------------------------- compare
def latent_signatures(st: str, rule: str) -> collections.Counter:
    """Per stage: multiplicity of each per-source-order signature of (status, discordance) over latent truths."""
    order = ORDERS[st]
    panels = sorted({p for p, _ in order}, key=lambda x: -1 if x is None else x)
    out = collections.Counter()
    for truth in itertools.product(OUTCOMES, repeat=len(order)):
        t = dict(zip(order, truth))
        sig = []
        for perm in itertools.permutations(SOURCES):
            seq = []
            for p in panels:
                for s in perm:
                    o = t[(p, s)]
                    seq.append((p, s, o))
                    if o != "PASS":
                        break
                if seq[-1][2] != "PASS":
                    break
            sig.append((stage_status([o for *_, o in seq]), discordant(seq) if rule != "new" else False))
        out[tuple(sig)] += 1
    return out


def latent_order_sensitivity(R, rule: str) -> dict:
    per = {st: latent_signatures(st, rule) for st in STAGES}
    total = sensitive = sensitive_v4 = fail_vs_ne = 0
    kinds = collections.Counter()
    cache: dict = {}
    for parts in itertools.product(*(per[st].items() for st in STAGES)):
        mult = 1
        for _sig, m in parts:
            mult *= m
        states, v4s, status_sets = set(), set(), [set() for _ in STAGES]
        for i in range(6):
            statuses = {st: parts[j][0][i][0] for j, st in enumerate(STAGES)}
            disc = any(parts[j][0][i][1] for j in range(4))
            ne = any(v == "NOT_ESTIMABLE" for v in statuses.values())
            uni = ("FAIL" if disc else "NOT_ESTIMABLE" if ne else "PASS") if rule == "old" else \
                  ("NOT_ESTIMABLE" if (disc or ne) else "PASS") if rule == "u1" else ("NOT_ESTIMABLE" if ne else "PASS")
            ck = (tuple(statuses[x] for x in STAGES), uni)
            if ck not in cache:
                r = route(R, statuses, uni)
                cache[ck] = (r["state"], r["v4"])
            states.add(cache[ck][0])
            v4s.add(cache[ck][1])
            for j, x in enumerate(STAGES):
                status_sets[j].add(statuses[x])
        total += mult
        if len(states) > 1:
            sensitive += mult
            kinds[" / ".join(sorted(states))] += mult
            sensitive_v4 += mult * (len(v4s) > 1)
            fail_vs_ne += mult * any(ss == {"FAIL", "NOT_ESTIMABLE"} for ss in status_sets)
    return {"latent_configurations": total, "order_sensitive": sensitive, "order_sensitive_v4_c2_c4": sensitive_v4,
            "order_sensitive_with_a_stage_flipping_between_FAIL_and_NOT_ESTIMABLE": fail_vs_ne,
            "order_sensitive_by_state_set": dict(kinds.most_common())}


def first_failure_variants(c):
    """Single-stage variants in which a different source in the same panel fails first (same outcome type)."""
    for st in STAGES:
        p, s, o = c[st][-1]
        if o == "PASS":
            continue
        order = ORDERS[st]
        for i, (q, r) in enumerate(order):
            if q != p or r == s:
                continue
            yield st, {**c, st: [(a, b, "PASS") for a, b in order[:i]] + [(q, r, o)]}


def compare(old_dump: Path, new_dump: str, out_dir: Path, routing_root: Path) -> None:
    R = load_routing(routing_root)
    old = {json.loads(ln)["combo"]: json.loads(ln) for ln in old_dump.read_text().splitlines()}
    new_code = None if new_dump == "-" else {json.loads(ln)["combo"]: json.loads(ln) for ln in Path(new_dump).read_text().splitlines()}
    trans = {k: collections.Counter() for k in ("v4", "state", "C2", "C4", "C6")}
    trans_u1 = collections.Counter()
    mismatch_old = mismatch_new = changed = 0
    authority_true = 0
    never_fail = True
    rows = []
    by_status_tuple = collections.defaultdict(set)
    for c in combos():
        k = key(c)
        st = {s: stage_status([o for *_, o in c[s]]) for s in STAGES}
        r_old = route(R, st, universal_old(c))
        r_new = route(R, st, universal_new(c))
        r_u1 = route(R, st, universal_u1(c))
        o = old[k]
        if any(o[f] != r_old[f] for f in ("state", "v4", "C2", "C4", "C6")):
            mismatch_old += 1
        if new_code is not None:
            n = new_code[k]
            if any(n[f] != r_new[f] for f in ("state", "v4", "C2", "C4", "C6")) or n["universal_source"] != universal_new(c):
                mismatch_new += 1
            never_fail &= n["universal_source"] != "FAIL"
        authority_true += (not r_old["authority_false"]) + (not r_new["authority_false"])
        by_status_tuple[tuple(st.values())].add(r_new["state"])
        for f in trans:
            trans[f][f"{r_old[f]} -> {r_new[f]}"] += 1
        trans_u1[f"{r_new['v4']} -> {r_u1['v4']}"] += 1
        if r_old["state"] != r_new["state"]:
            changed += 1
            rows.append({"combo": k, "TD56": st["TD56"], "TD57B": st["TD57B"], "TD57C": st["TD57C"], "TD59": st["TD59"],
                         "old_universal": universal_old(c), "new_universal": universal_new(c), "old_state": r_old["state"],
                         "new_state": r_new["state"], "old_v4": r_old["v4"], "new_v4": r_new["v4"],
                         "old_C2": r_old["C2"], "new_C2": r_new["C2"], "old_C4": r_old["C4"], "new_C4": r_new["C4"]})
    order_a = {}
    for name, uni in (("f5673f9b", universal_old), ("revised", universal_new), ("alternative_U1", universal_u1)):
        n_sens, examples = 0, []
        for c in combos():
            base = route(R, {s: stage_status([o for *_, o in c[s]]) for s in STAGES}, uni(c))["state"]
            for st_changed, v in first_failure_variants(c):
                alt = route(R, {s: stage_status([o for *_, o in v[s]]) for s in STAGES}, uni(v))["state"]
                if alt != base:
                    n_sens += 1
                    if len(examples) < 3:
                        examples.append({"combo": key(c), "variant": key(v), "stage": st_changed, "state": base, "variant_state": alt})
                    break
        order_a[name] = {"combinations_whose_state_changes_when_a_different_source_fails_first": n_sens, "examples": examples}
    order_b = {name: latent_order_sensitivity(R, rule) for name, rule in (("f5673f9b", "old"), ("revised", "new"), ("alternative_U1", "u1"))}
    summary = {
        "schema": "JEPA_TD_CORRECTED_REPLAY_ROUTING_ENUMERATION_V2",
        "combinations": sum(trans["v4"].values()),
        "old_code_reproduced_by_restated_old_rule": mismatch_old == 0,
        "new_code_matches_independent_prototype": None if new_code is None else mismatch_new == 0,
        "new_code_routing_universal_input_never_fail": None if new_code is None else never_fail,
        "biological_state_unchanged": sum(trans["state"].values()) - changed, "biological_state_changed": changed,
        "v4_transitions_old_to_new": dict(trans["v4"]),
        "state_transitions_old_to_new": dict(trans["state"]),
        "C2_transitions": dict(trans["C2"]), "C4_transitions": dict(trans["C4"]), "C6_transitions": dict(trans["C6"]),
        "revised_route_is_a_function_of_stage_statuses_only": all(len(v) == 1 for v in by_status_tuple.values()),
        "downstream_authority_true_anywhere": authority_true,
        "alternative_U1_vs_revised_v4": dict(trans_u1),
        "order_a_observed_first_failing_source": order_a,
        "order_b_latent_truth_source_permutations": order_b,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "ROUTING_ENUMERATION_SUMMARY.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n")
    with open(out_dir / "ROUTING_CHANGED_COMBINATIONS.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["combo"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(json.dumps({k: v for k, v in summary.items() if not k.startswith("order_")}, indent=1, sort_keys=True))
    print(json.dumps({"order_a": {k: v["combinations_whose_state_changes_when_a_different_source_fails_first"] for k, v in order_a.items()},
                      "order_b": {k: {x: v[x] for x in ("order_sensitive", "order_sensitive_v4_c2_c4",
                                                         "order_sensitive_with_a_stage_flipping_between_FAIL_and_NOT_ESTIMABLE",
                                                         "latent_configurations")} for k, v in order_b.items()}}, indent=1))


if __name__ == "__main__":
    if sys.argv[1] == "dump":
        dump(Path(sys.argv[2]))
    else:
        compare(Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4]), Path(sys.argv[5]))
