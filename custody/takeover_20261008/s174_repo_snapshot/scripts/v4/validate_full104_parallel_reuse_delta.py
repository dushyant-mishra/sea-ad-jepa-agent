#!/usr/bin/env python3
"""Independent fail-closed validator for the FULL104 reuse/delta package."""
from __future__ import annotations
import csv, hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/"outputs"/"full104_parallel_reuse_delta_20260902"
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(8<<20),b""): h.update(b)
 return h.hexdigest()
required=["FULL104_REUSE_AUTHORITY.json","FULL104_REUSE_MATRIX.csv","FULL104_REUSED_ARTIFACT_MANIFEST.csv","FULL104_CLOSED_DSHARED_ARTIFACTS.csv","FULL104_CURRENT_CONTEXTUAL_DELTA_PLAN.json","FULL104_DELTA_EXPRESSION_JUSTIFICATION.json","FULL104_CONTEXTUAL_RESOURCE_DELTA.json","FULL104_CONTEXTUAL_CACHE_RESUME_DELTA.md","FULL104_CURRENT_MODEL_MEMORY_ACCOUNTING.json","FULL104_CONTEXT_CAPACITY_DELTA.json","FULL104_TRAINING_COVERAGE_COORDINATES.json","FULL104_DEFERRED_SELECTIONS.json","FULL104_REUSE_DELTA_INDEPENDENT_VALIDATION.json","FULL104_REUSE_DELTA_MULTIAGENT.md","FULL104_REUSE_DELTA_SOURCE_MANIFEST.csv","FULL104_REUSE_DELTA_MANIFEST.csv","FULL104_REUSE_DELTA_EXTERNAL_REVIEW_HANDOFF.md"]
checks={"required_17_present":all((OUT/x).is_file() for x in required)}
rows=list(csv.DictReader((OUT/"FULL104_REUSE_MATRIX.csv").open(encoding="utf-8")))
allowed={"REUSE_EXACT","REUSE_ENGINEERING_PATTERN_ONLY","CLOSED_DSHARED_DO_NOT_USE","CURRENT_CONTEXTUAL_DELTA_REQUIRED","PROVENANCE_STOP"}
checks["allowed_actions_only"]=all(r["action"] in allowed for r in rows)
checks["all_paths_exist_and_hash_match"]=all((ROOT/r["path"]).is_file() and sha(ROOT/r["path"])==r["sha256"] for r in rows)
checks["no_dshared_scientific_reuse_exact"]=all(not (r["action"]=="REUSE_EXACT" and r["depends_on_failed_D_shared"]=="true") for r in rows)
closed=[r for r in rows if r["action"]=="CLOSED_DSHARED_DO_NOT_USE"]
checks["dshared_closure_present"]=len(closed)>=3 and all(r["depends_on_failed_D_shared"]=="true" for r in closed)
auth=json.loads((OUT/required[0]).read_text()); expr=json.loads((OUT/required[5]).read_text()); defer=json.loads((OUT/required[11]).read_text())
checks["reader_fit104_firewall_exact"]=auth["population"]=={"addresses":41238,"cells":4553407,"donor_operator_strata":1400,"donors":104,"duplicate_cell_locators":0,"nph_quarantined":22715,"operators":42,"source_cells":{"HVS":198718,"NPH52":236476,"SEA_AD":4118213}}
checks["no_expression_scan"]=expr["status"]=="NOT_REQUIRED" and expr["expression_reads"]==[] and not auth["firewall"]["expression_opened"] and not auth["firewall"]["full_expression_scan"]
checks["no_f1_outcome"]=not auth["firewall"]["f1_candidate_outcome_read"]
checks["no_training_optimizer_ema"]=not any(auth["firewall"][k] for k in ("training","backward","optimizer_step","ema_update"))
checks["no_hyperparameter_selected"]=defer["status"]=="ALL_DEFERRED" and defer["selected"]=={}
checks["contextual_deltas_genuinely_new"]=sum(r["action"]=="CURRENT_CONTEXTUAL_DELTA_REQUIRED" for r in rows)>=5
expected_topics={"FULL104 census/firewall","FULL104 row-lineage index","expression interface V8 final manifest","phase2 materialization contract","phase2 materialization audit","phase2 materialization manifest","phase2 expression block manifest","phase2 asset authentication","physical descriptor allowlist","original NPH denylist","observation-state authority","address namespace","source registry","donor registry","operator registry","source/operator registry","support by source","support by operator","model ingress consumer","F0 slow reference","F0 metamorphic authority","prior F1 reuse taxonomy","executor test design","ALL104 execution ledger","WSL/CUDA preflight","failed D_shared final adjudication","old ALL104 D/null selection","contextual architecture source","F1 forward identity counts","F1 evidence-mask contract","current encoder source","current u0 checkpoint"}
checks["mandatory_authority_inventory_complete"]=expected_topics.issubset({r["topic"] for r in rows})
checks["historical_runtime_not_claimed_current_exact"]=all(not (r["topic"]=="WSL/CUDA preflight" and r["action"]=="REUSE_EXACT") for r in rows)
prior_art={r["topic"]:r["action"] for r in rows}
checks["novelty_semantics_explicit"]=all(prior_art.get(t)=="CURRENT_CONTEXTUAL_DELTA_REQUIRED" for t in ("contextual resource planning delta","contextual cache/resume delta","current model memory accounting delta","context capacity delta","training coverage coordinates delta")) and all(prior_art.get(t)=="REUSE_EXACT" for t in ("contextual architecture source","F1 forward identity counts","F1 evidence-mask contract","current encoder source","current u0 checkpoint"))
scope=auth["scope_definition"]
control=Path(scope["controlling_instruction_path"])
checks["external_scope_inventory_authenticated"]=control.is_file() and sha(control)==scope["controlling_instruction_sha256"] and control.stat().st_size==scope["controlling_instruction_bytes"] and all((ROOT/r["path"]).is_file() and sha(ROOT/r["path"])==r["sha256"] and (ROOT/r["path"]).stat().st_size==r["bytes"] for r in scope["external_inventory_authorities"])
delta_files={"FULL104_CONTEXTUAL_RESOURCE_DELTA.json","FULL104_CONTEXTUAL_CACHE_RESUME_DELTA.md","FULL104_CURRENT_MODEL_MEMORY_ACCOUNTING.json","FULL104_CONTEXT_CAPACITY_DELTA.json","FULL104_TRAINING_COVERAGE_COORDINATES.json"}
inventory_text="\n".join((ROOT/r["path"]).read_text(encoding="utf-8",errors="replace") for r in scope["external_inventory_authorities"])
checks["delta_absent_from_prior_inventories_with_reconciliation"]=set(auth["delta_novelty_reconciliation"])==delta_files and all(name not in inventory_text and len(auth["delta_novelty_reconciliation"][name])>40 for name in delta_files)
source_rows=list(csv.DictReader((OUT/"FULL104_REUSE_DELTA_SOURCE_MANIFEST.csv").open(encoding="utf-8")))
checks["source_manifest_current"]=all((ROOT/r["path"]).is_file() and sha(ROOT/r["path"])==r["sha256"] and (ROOT/r["path"]).stat().st_size==int(r["bytes"]) for r in source_rows)
resource=json.loads((OUT/"FULL104_CONTEXTUAL_RESOURCE_DELTA.json").read_text()); upstream_counts=json.loads((ROOT/"outputs/contextual_teacher_target_v1_f1_reader_forward_authority_freeze_20260902/F1_FUTURE_FORWARD_AUDIT.json").read_text())
checks["forward_counts_preserve_upstream_nonfrozen_status"]=resource["count_authority_status"]==upstream_counts["status"] and "NOT_FROZEN" in resource["status"]
memory=json.loads((OUT/"FULL104_CURRENT_MODEL_MEMORY_ACCOUNTING.json").read_text())
expected_params=(41238*48)+(48*160+160)+(1*32+32)+(32*160+160)+(2*160)+160+6*((2*2*160)+(4*(160*160+160))+(160*320+320)+(320*160+160))+(2*160)
checks["static_parameter_arithmetic"]=expected_params==3232768==memory["encoder"]["parameters"] and memory["encoder"]["parameter_bytes_fp32"]==expected_params*4
cache_text=(OUT/"FULL104_CONTEXTUAL_CACHE_RESUME_DELTA.md").read_text()
checks["cache_identity_axes_explicit"]=all(x in cache_text for x in ("encoder-view role","value-world role","null source row locator","payload hash","does not authorize execution"))
status="PASS_INDEPENDENT_VALIDATION" if all(checks.values()) else "STOP_FULL104_REUSE_DELTA_INDEPENDENT_MISMATCH"
obj={"schema":"full104-reuse-delta-independent-validation-v1","status":status,"validator_source":"scripts/v4/validate_full104_parallel_reuse_delta.py","validator_sha256":sha(Path(__file__)),"checks":checks,"matrix_rows":len(rows)}
(OUT/"FULL104_REUSE_DELTA_INDEPENDENT_VALIDATION.json").write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")
manifest=[]
for p in sorted(OUT.iterdir()):
 if p.is_file() and p.name!="FULL104_REUSE_DELTA_MANIFEST.csv": manifest.append({"artifact":p.name,"sha256":sha(p),"bytes":p.stat().st_size})
with (OUT/"FULL104_REUSE_DELTA_MANIFEST.csv").open("w",newline="",encoding="utf-8") as f:
 w=csv.DictWriter(f,fieldnames=["artifact","sha256","bytes"],lineterminator="\n"); w.writeheader(); w.writerows(manifest)
print(json.dumps(obj,indent=2)); sys.exit(0 if status.startswith("PASS") else 2)
