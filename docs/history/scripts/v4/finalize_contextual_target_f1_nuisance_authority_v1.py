#!/usr/bin/env python3
"""Publish the outcome-blind nuisance recovery as a truthful HC3 STOP package."""
from pathlib import Path
import csv, hashlib, json, os, shutil

ROOT=Path(__file__).resolve().parents[2]
STAGE=ROOT/"outputs/_staging_contextual_teacher_target_v1_f1_nuisance_authority_recovery_20260902"
FINAL=ROOT/"outputs/contextual_teacher_target_v1_f1_nuisance_authority_recovery_20260902"
STOP="STOP_F1_NUISANCE_HC3_DESIGN_NONESTIMABLE"

def sha(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for b in iter(lambda:f.read(8<<20),b""):h.update(b)
 return h.hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+"\n",encoding="utf-8")

if FINAL.exists():raise RuntimeError("final exists")
ind=json.loads((STAGE/"F1_NUISANCE_INDEPENDENT_VALIDATION.json").read_text());hc3=json.loads((STAGE/"F1_NUISANCE_HC3_COMPATIBILITY.json").read_text())
if ind["status"]!="PASS_F1_NUISANCE_INDEPENDENT_VALIDATION" or hc3["status"]!=STOP:raise RuntimeError("adjudication inputs")
auth=json.loads((STAGE/"F1_NUISANCE_DONOR_DESIGN_AUTHORITY.json").read_text());auth.update({"status":"NOT_FROZEN_STOPPED_BEFORE_PROMOTION","terminal_status":STOP,"hc3_compatibility_path":"F1_NUISANCE_HC3_COMPATIBILITY.json","hc3_compatibility_sha256":sha(STAGE/"F1_NUISANCE_HC3_COMPATIBILITY.json")});dump(STAGE/"F1_NUISANCE_DONOR_DESIGN_AUTHORITY.json",auth)

review='''# F1 nuisance authority recovery — six-lens adjudication\n\nOverall verdict: `STOP_F1_NUISANCE_HC3_DESIGN_NONESTIMABLE`. Dataset primitives and the 104×49 matrix reproduce, but the nuisance authority is not frozen or execution-ready.\n\n## 1. Historian / Dataset Authority — PASS\nHistorical FULL104 support, source-library normalization, cell weights, and null-map primitives were recovered with matching hashes. No older conflicting exact F1 equations were found.\n\n## 2. Observation-State / Support — PASS\nPhysical support is exactly the count of `MEASURED_SCALAR` addresses. Measured zeros remain evidence. Production and independent U60 hashes agree for all 44,496 assignments.\n\n## 3. Sequencing-Depth / Normalization — PASS\nFull-source `source_library`, log1p10K, and inverse integer recovery are exact. The 84-cell/all-42-operator V8 fixture has zero normalization or round-trip failures.\n\n## 4. Statistics / HC3 Design — STOP\nThe binary 104×49 float64 matrix is independently byte-identical at semantic root `2f0c95b1d9c098f8593827f240f64a0b8e5512ead92fe50540f6e2dc231742ec`. However, the frozen lexicographic rank selector retains 17 covariates plus intercept and gives two unit-leverage donors. Frozen HC3 therefore returns non-estimable before any outcome is used.\n\n## 5. Matched-Null Semantics — PASS on construction; STOP on promotion\nCorrect and null use the identical recipient U60, same source/operator, distinct donors/cells, and each row's own library. The exact eight-program×two-draw hierarchy is represented in the frozen assignments. The resulting design still cannot be promoted because HC3 is structurally non-estimable.\n\n## 6. Scientific Red-Team — STOP\nRed-Team independently confirmed the two leverage failures and traced them to donor-unique operator contrasts (`operator_mix_000` vs `_001`, and `_035` vs `_036`). Dropping or regularizing columns, or changing rank selection, would change the frozen statistical rule and requires a new prospective outcome-blind repair. It also noted that a future promoted implementation should explicitly hash-pin CELL_AUTH, source registry, V8 selection/payload; assert exact 8×2 uniqueness; and use deterministic gzip metadata. These do not rescue the present STOP.\n\nNo candidate model outcome, encoder forward, training, optimizer, or EMA state was accessed.\n'''
(STAGE/"F1_NUISANCE_MULTIAGENT.md").write_text(review,encoding="utf-8")
handoff=f'''# F1 nuisance recovery external-review handoff\n\nTerminal: `{STOP}`.\n\nRecovered primitives and the prescribed paired formulas were successfully computed outcome-blind. Production and independent implementations agree on every U60 hash, all paired values within CSV round-trip precision (`9.97e-17`), and the authoritative 104×49 binary matrix byte-for-byte. Semantic root: `2f0c95b1d9c098f8593827f240f64a0b8e5512ead92fe50540f6e2dc231742ec`.\n\nPromotion is blocked because the unchanged frozen rank/HC3 engine produces two unit-leverage donors: `HVS::H20.06.354` and `NPH52::human_NPH_906`. HC3 is consequently non-estimable for every possible outcome. The design authority is explicitly marked NOT_FROZEN.\n\nNext required action is a separately authorized, prospective, outcome-blind HC3 design repair. Do not run the F1 reader/forward evaluation.\n'''
(STAGE/"F1_NUISANCE_EXTERNAL_REVIEW_HANDOFF.md").write_text(handoff,encoding="utf-8")

snap=STAGE/"source_snapshot";snap.mkdir(exist_ok=True)
sources=[ROOT/"scripts/v4/derive_contextual_target_f1_nuisance_authority_v1.py",ROOT/"scripts/v4/validate_contextual_target_f1_nuisance_authority_v1.py",ROOT/"scripts/v4/audit_contextual_target_f1_nuisance_hc3_compatibility_v1.py",Path(__file__),ROOT/"scripts/v4/contextual_target_f1_decision_v1.py",ROOT/"scripts/v4/derive_full104_phase2_shared_state.py",ROOT/"scripts/v4/audit_full104_phase2_capacity_and_materialization.py",ROOT/"scripts/v4/materialize_full104_phase2_expression.py",ROOT/"scripts/v4/build_full104_phase2_multiview_features.py"]
rows=[]
for p in sources:
 shutil.copy2(p,snap/p.name);rows.append({"path":p.relative_to(ROOT).as_posix(),"sha256":sha(p),"snapshot_path":(snap/p.name).relative_to(STAGE).as_posix(),"snapshot_sha256":sha(snap/p.name)})
with (STAGE/"F1_NUISANCE_SOURCE_MANIFEST.csv").open("w",encoding="utf-8",newline="") as f:w=csv.DictWriter(f,fieldnames=rows[0].keys(),lineterminator="\n");w.writeheader();w.writerows(rows)

entries=[]
for p in sorted(x for x in STAGE.rglob("*") if x.is_file() and x.name not in {"F1_NUISANCE_MANIFEST.csv","run.stdout.log","run.stderr.log"}):entries.append({"path":p.relative_to(STAGE).as_posix(),"bytes":p.stat().st_size,"sha256":sha(p)})
with (STAGE/"F1_NUISANCE_MANIFEST.csv").open("w",encoding="utf-8",newline="") as f:w=csv.DictWriter(f,fieldnames=entries[0].keys(),lineterminator="\n");w.writeheader();w.writerows(entries)
os.replace(STAGE,FINAL)
print(json.dumps({"terminal":STOP,"output":str(FINAL),"manifest_sha256":sha(FINAL/"F1_NUISANCE_MANIFEST.csv"),"semantic_root":auth["semantic_root_sha256"]}))
