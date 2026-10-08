#!/usr/bin/env python3
"""Finalize the fail-closed Command-15A2 numerical-rank audit."""
from __future__ import annotations
import argparse,csv,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(8<<20),b""):h.update(b)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--staging",type=Path,required=True);a=ap.parse_args();o=a.staging.resolve()
 reviews="""# F1 HC3 numerical-rank repair — targeted review

Synthesis: **DO_NOT_RUN_INVALID**. Command 15A2's repair premise is falsified under its own unchanged rank rule.

1. **Historian / Statistical Authority — STOP; REVISIT_JUSTIFIED.** Authorities, old rank-18/df-86 failure, unit-leverage donors, and firewall reproduce. The required NPH52 premise fails, so the commanded STOP controls.
2. **Numerical Linear Algebra — STOP.** NumPy and SciPy `gesvd` both put component 2 above `tau(R)` (2.2966x and 2.2998x), while it does not increase full-design frozen-engine rank. The mismatch is matrix-scale dependent, not an SVD-driver disagreement.
3. **HC3 / Regression Geometry — STOP.** Mandatory base remains full-rank and estimable. A frontier cannot include the component without violating the engine gate, or discard it without violating the commanded residual cutoff.
4. **Operator / Dataset Semantics — STOP.** Exact source/operator supports and all 104 donors are preserved. No expression, outcomes, model, training, or semantic changes occurred.
5. **Decision-Engine Compatibility — PASS for the STOP.** The frozen engine and strict `s>tau(A)` rule are unchanged; the direct append remains rank 8 to 8. The frontier correctly remains unbuilt.
6. **Scientific Red-Team — STOP.** No lawful interpretation yields PASS. It also identified and prompted hardening of STOP process exits. The independent validator is adequate only for this early STOP, not a future PASS package.

Decisive blocker: residual-space rank is 2 but global engine-admissible count is 1. Resolving which matrix scale controls requires a new prospective authority. No repair design is selected or frozen.
"""
 (o/"F1_HC3_NUMRANK_MULTIAGENT.md").write_text(reviews,encoding="utf-8")
 handoff="""# F1 HC3 Command 15A2 — external-review handoff

Terminal: `STOP_F1_HC3_NPH_COMPONENT2_STATUS_CHANGED`.

All prior authorities and the old HC3 failure reproduce. The mandatory base is full-rank and estimable. Under the exact frozen rule, however, NPH52 component 2 is above `tau(R)` in both required SVD implementations while failing to increase rank in the full frozen-engine design. Thus Command 15A2's required numerical-null premise is false, and its residual-rank and direct-engine requirements cannot simultaneously be satisfied.

The repaired frontier was not constructed and the 105/35 reconciliation was not asserted. No rank triple, cutoff, estimator, donor deletion, operator subset, or production nuisance authority was selected. No expression, checkpoint, model, outcome, training, or EMA was accessed.

A later prospective instruction must resolve whether residual-local or full-design scale controls component admissibility. This package cannot authorize Command 15B or F1 execution.
"""
 (o/"F1_HC3_NUMRANK_EXTERNAL_REVIEW_HANDOFF.md").write_text(handoff,encoding="utf-8")
 snap=o/"source_snapshot";snap.mkdir(exist_ok=True)
 names=["audit_contextual_target_f1_hc3_numrank_repair_v1.py","validate_contextual_target_f1_hc3_numrank_repair_v1.py","finalize_contextual_target_f1_hc3_numrank_repair_v1.py"]
 sr=[]
 for n in names:
  p=ROOT/"scripts/v4"/n;q=snap/n;shutil.copy2(p,q);sr.append({"source_path":str(p.relative_to(ROOT)).replace('\\','/'),"snapshot_path":str(q.relative_to(ROOT)).replace('\\','/'),"source_sha256":sha(p),"snapshot_sha256":sha(q),"byte_identical":sha(p)==sha(q)})
 with (o/"F1_HC3_NUMRANK_SOURCE_MANIFEST.csv").open("w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=list(sr[0]));w.writeheader();w.writerows(sr)
 rows=[]
 for p in sorted(x for x in o.rglob("*") if x.is_file() and x.name!="F1_HC3_NUMRANK_MANIFEST.csv"):rows.append({"relative_path":str(p.relative_to(o)).replace('\\','/'),"bytes":p.stat().st_size,"sha256":sha(p)})
 with (o/"F1_HC3_NUMRANK_MANIFEST.csv").open("w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=["relative_path","bytes","sha256"]);w.writeheader();w.writerows(rows)
 print(json.dumps({"terminal":"STOP_F1_HC3_NPH_COMPONENT2_STATUS_CHANGED","manifest_sha256":sha(o/"F1_HC3_NUMRANK_MANIFEST.csv"),"manifested_files":len(rows)}))
if __name__=="__main__":main()
