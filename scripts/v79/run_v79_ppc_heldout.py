#!/usr/bin/env python3
"""V79 held-out-donor posterior predictive checks for phases A, B and B0 (contract validation section).

  fold    --phase P --fold f [--without dk]   fit phase P on the donors outside fold f and check the held-out
                                              donors (v79_ppc); --without dk drops the donor-class component
  merge   --phase P [--without dk]            pool the fold records into one record per run
  support --phase P                           Q5: held-out lpd with minus without donor-class (contract rule)

Folds: source-stratified donor folds with the contract seed base; their number comes from the benchmark. The
response of each phase is built by run_v79_inference.phase_response, the same code as the fit. Gated like every
real-data runner. A model failing a check is reported as inadequate for that statistic, never tuned.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import v79_data as DA  # noqa: E402
import v79_firewall as FW  # noqa: E402
import v79_ppc as PPC  # noqa: E402
import run_v79_inference as INF  # noqa: E402

OUT = INF.ROOT / "results/v79/internal/ppc"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["fold", "merge", "support"])
    ap.add_argument("--without", choices=["none", "dk"], default="none")
    ap.add_argument("--phase", choices=["A", "B", "B0"], required=True)
    ap.add_argument("--fold", type=int, default=0)
    ap.add_argument("--chains", type=int, default=4)
    ap.add_argument("--warmup", type=int, default=1000)
    ap.add_argument("--draws", type=int, default=1000)
    a = ap.parse_args()
    tag = a.phase + ("_nodk" if a.without == "dk" else "")
    if a.mode == "support":
        recs = {t: json.loads((OUT / f"V79_HELDOUT_PPC_{t}_INTERNAL_V1.json").read_text(encoding="utf-8"))
                for t in (a.phase, a.phase + "_nodk")}
        rec = dict(schema=f"V79_DONOR_CLASS_SUPPORT_{a.phase}_INTERNAL_V1", phase=a.phase,
                   status="INTERNAL__NOT_SYNTHETIC_CONSUMABLE",
                   comparison=PPC.heldout_lpd_comparison(recs[a.phase], recs[a.phase + "_nodk"]),
                   lane=FW.LANE_TERMINAL)
        path = OUT / f"V79_DONOR_CLASS_SUPPORT_{a.phase}_INTERNAL_V1.json"
    elif a.mode == "merge":
        parts = sorted(OUT.glob(f"fold_{tag}_[0-9]*.json"))
        rec = PPC.merge_heldout(json.loads(p.read_text(encoding="utf-8")) for p in parts)
        rec.update(schema=f"V79_HELDOUT_PPC_{tag}_INTERNAL_V1", parts=[p.name for p in parts])
        path = OUT / f"V79_HELDOUT_PPC_{tag}_INTERNAL_V1.json"
    else:
        pre = INF.preconditions()
        contract = json.loads(INF.CONTRACT.read_text(encoding="utf-8"))
        base = contract["inference"]["seed_base"]
        d = FW.load_cell_design(DA.local_path(INF.CACHE), DA.local_path(INF.BRIDGE))
        di = DA.design_indices(d)
        X = DA.load_counts(DA.local_path(INF.CACHE), DA.local_path(INF.BRIDGE))
        pr = INF.phase_response(a.phase, d, X, pre["gene_count"])
        if a.without == "dk" and a.phase == "B0":
            raise SystemExit("donor-class support is defined for the gene phases A and B")
        comps = tuple(c for c in PPC.COMPONENTS if not (a.without == "dk" and c == "dk"))
        rec = PPC.run_heldout(di, pr["y"], pr["likelihood"], k=pre["held_out_folds"], seed=base,
                              chains=a.chains, warmup=a.warmup, draws=a.draws, depth=pr["depth"],
                              only_folds=[a.fold], components=comps)
        rec.update(phase=a.phase, preconditions=pre, status="INTERNAL__NOT_SYNTHETIC_CONSUMABLE",
                   responses=pr["responses"], lane=FW.LANE_TERMINAL)
        path = OUT / f"fold_{tag}_{a.fold}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline=chr(10)) as fh:
        fh.write(json.dumps(rec) + chr(10))
    print(path.name, "all folds diagnosed" if rec.get("all_folds_diagnosed") else "NOT all diagnosed")


if __name__ == "__main__":
    main()
