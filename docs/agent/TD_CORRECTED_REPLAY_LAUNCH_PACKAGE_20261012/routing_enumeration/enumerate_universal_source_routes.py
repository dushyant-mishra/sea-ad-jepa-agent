#!/usr/bin/env python3
"""Enumerate every stage-outcome combination the frozen sequential order allows and count where the proposed
universal_source rule changes the routing V2 / V4 result. Logical possibilities, not probabilities. Read-only.

usage: python enumerate_universal_source_routes.py <repo root at the implementation commit>
"""
import itertools
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
sys.path.insert(0, str(root / "scripts" / "v5"))
import td_corrected_replay_execute_v1 as X  # noqa: E402
import td_corrected_replay_routing_v2 as R  # noqa: E402

c = json.loads((root / "target_discovery/iterations/corrected_replay_20261012/TD_CORRECTED_REPLAY_CONTRACT_V1.json").read_text())
STAGES = ("TD56", "TD57B", "TD57C", "TD59")


def sequences(order):
    """All invocation sequences under the within-stage sequential stop (PASS / FAIL / NOT_ESTIMABLE)."""
    out = [[(p, s, "PASS") for p, s in order]]
    for k in range(len(order)):
        for bad in ("FAIL", "NOT_ESTIMABLE"):
            out.append([(p, s, "PASS") for p, s in order[:k]] + [(order[k][0], order[k][1], bad)])
    return out


per = {sp["stage"]: sequences([tuple(x) for x in sp["invocation_order"]]) for sp in c["stages"]}
total = changed = 0
kinds: dict = {}
example: dict = {}
for combo in itertools.product(*(per[s] for s in STAGES)):
    stages = {}
    for st, seq in zip(STAGES, combo):
        invs = [{"panel": p, "source": s, "outcome": o} for p, s, o in seq]
        stages[st] = {"invocations": invs, "status": X.stage_status([i["outcome"] for i in invs])}
    total += 1
    ri = X.routing_inputs(stages)
    if ri["universal_source"] != "FAIL":
        continue
    alt = dict(ri, universal_source="NOT_ESTIMABLE" if any(v["status"] == "NOT_ESTIMABLE" for v in stages.values()) else "PASS")
    a, b = R.interpret_corrected_replay(**ri)["v4_relational_status"], R.interpret_corrected_replay(**alt)["v4_relational_status"]
    if a != b:
        changed += 1
        kinds[f"{b}->{a}"] = kinds.get(f"{b}->{a}", 0) + 1
        example.setdefault(f"{b}->{a}", {k: [(i["panel"], i["source"], i["outcome"]) for i in v["invocations"]] for k, v in stages.items()})
print(json.dumps({"combinations": total, "universal_fail_changes_v4_route": changed, "by_kind": kinds,
                  "first_example_by_kind": example}, indent=1))
