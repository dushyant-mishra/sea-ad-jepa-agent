#!/usr/bin/env python3
"""POST-HOC DESCRIPTIVE comparison of the spent corrected replay with the historical outputs. Read-only.

Not a gate and not part of the frozen interpretation: it changes no stage status, pattern or route. Historical
outputs are those the adapter-fed exact executors reproduced byte-exactly in the 7819aabd equivalence run.

Reports, per invocation:
  - the stage statistic minus the null p95 (index 60) for each case, historical and corrected;
  - for NPH52, whether the corrected output equals the historical one exactly (TD56: every result array; modules:
    the whole payload except input_sha256). NPH52 is G6's authenticated historical pass-through, so exact equality
    was the disclosed expectation for this free post-run adapter check.

usage: compare_corrected_vs_historical.py <replay namespace> <equivalence work dir>
"""
import json
import sys
from pathlib import Path

import numpy as np

NS, H = Path(sys.argv[1]), Path(sys.argv[2])
STAT = {"TD57B": "observed_median_donor_triplet_agreement", "TD57C": "observed_median_donor_local_triplet_agreement",
        "TD59": "observed_median_donor_local_triplet_agreement"}
out = {"schema": "JEPA_TD_CORRECTED_REPLAY_POST_HOC_DESCRIPTIVE_COMPARISON_V1", "post_hoc": True,
       "changes_any_frozen_result": False, "td56": {}, "modules": {}, "nph52_pass_through_identical": {}}
for s in ("HVS", "NPH52", "SEA_AD"):
    c = np.load(NS / f"adapter_inputs/mnt/td56_{s}_result.npz", allow_pickle=True)
    h = np.load(H / f"mnt/td56_{s}_result.npz", allow_pickle=True)
    out["td56"][s] = {"historical": {"obs": float(h["obs"]), "p95": float(h["p95"]), "margin": float(h["obs"]) - float(h["p95"])},
                      "corrected": {"obs": float(c["obs"]), "p95": float(c["p95"]), "margin": float(c["obs"]) - float(c["p95"])}}
    if s == "NPH52":
        same = sorted(c.files) == sorted(h.files) and all(np.array_equal(c[k], h[k]) for k in c.files)
        out["nph52_pass_through_identical"]["TD56"] = bool(same)


def case_margins(path, stat):
    o = json.loads(Path(path).read_text())
    return {"status": o["status"], "cases_pass": sum(bool(x["pass"]) for x in o["cases"]),
            "margins": [x[stat] - x["null_p95_index60"] for x in o["cases"]]}, o


for st, stat in STAT.items():
    for f in sorted((NS / st).glob(f"{st}_*.output.json")):
        tag = f.name[len(st) + 1:-len(".output.json")]
        corr, co = case_margins(f, stat)
        hp = H / "results" / f"{st}_{tag}.output.json"
        rec = {"corrected": corr}
        if hp.is_file():
            hist, ho = case_margins(hp, stat)
            rec["historical"] = hist
            if tag.startswith("NPH52"):
                strip = lambda o: {k: v for k, v in o.items() if k != "input_sha256"}  # noqa: E731
                out["nph52_pass_through_identical"][f"{st}_{tag}"] = strip(co) == strip(ho)
        else:
            rec["historical"] = "NOT_IN_EQUIVALENCE_FIXTURE"
        out["modules"][f"{st}_{tag}"] = rec
print(json.dumps(out, indent=1, sort_keys=True))
