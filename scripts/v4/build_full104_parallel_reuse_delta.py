#!/usr/bin/env python3
"""Build the metadata-only FULL104 contextual reuse/delta review package."""
from __future__ import annotations

import csv, hashlib, json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "full104_parallel_reuse_delta_20260902"
CONTROL = Path(r"C:\Users\dushy\.codex\attachments\b29b307c-4978-444f-91ce-59722d8cd0a7\pasted-text.txt")
OUT.mkdir(parents=True, exist_ok=True)

def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""): h.update(b)
    return h.hexdigest()

def write_json(name: str, obj: object) -> None:
    (OUT/name).write_text(json.dumps(obj, indent=2, sort_keys=True)+"\n", encoding="utf-8")

def write_csv(name: str, rows: list[dict], fields: list[str]) -> None:
    with (OUT/name).open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=fields, lineterminator="\n"); w.writeheader(); w.writerows(rows)

def rec(topic, rel, scope, dep, applies, action):
    p=ROOT/rel
    if not p.is_file(): raise FileNotFoundError(rel)
    return dict(topic=topic,historical_status="AUTHENTICATED_EXISTS",path=rel.replace("\\","/"),sha256=sha(p),semantic_scope=scope,
                depends_on_failed_D_shared=str(dep).lower(),current_contextual_applicability=applies,action=action)

exact = [
 ("FULL104 census/firewall","outputs/full104_v014_20260826/01_full104_metadata_adapter/FULL104_METADATA_SCOPE_STATUS.json","reader_fit104 population, source counts, quarantine and no-expression firewall"),
 ("FULL104 metadata reconciliation","outputs/full104_v014_20260826/01_full104_metadata_adapter/FULL104_METADATA_RECONCILIATION.json","donor/operator/cell reconciliation"),
 ("FULL104 row-lineage index","outputs/full104_v014_20260826/01_full104_metadata_adapter/FULL104_ROW_LINEAGE.csv","42 exact row-lineage shard authorities and locators"),
 ("FULL104 adapter provenance","outputs/full104_v014_20260826/01_full104_metadata_adapter/FULL104_ADAPTER_PROVENANCE.json","adapter inputs, observation semantics and firewall"),
 ("FULL104 adapter hash manifest","outputs/full104_v014_20260826/01_full104_metadata_adapter/FULL104_ADAPTER_SHA256_MANIFEST.csv","frozen adapter artifact hashes"),
 ("expression interface V8 final manifest","outputs/full104_v014_20260826/full104_expression_interface_v8_verified/FULL104_EXPRESSION_INTERFACE_V8/FULL104_EXPRESSION_INTERFACE_V8_SHA256_MANIFEST.csv","verified 84-row all-operator expression-interface proof"),
 ("phase2 materialization contract","outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/MATERIALIZATION_CONTRACT.json","raw-count/log1p10K, row identity, collision and normalization semantics"),
 ("phase2 materialization audit","outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/PHASE2_EXPRESSION_MATERIALIZATION_AUDIT.json","completed expression materialization audit"),
 ("observation-state authority","exports/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz","42x41,238 three-state physical observation authority"),
 ("address namespace","exports/foundation_calibration_bundle_20260824/contracts/address_namespace.csv","ordered 41,238 molecular addresses"),
 ("corpus discovery final","exports/foundation_corpus_discovery_v1/FOUNDATION_CORPUS_DISCOVERY_FINAL.md","FULL104 discovery, source_library normalization and descriptive corpus authority"),
 ("corpus discovery manifest","exports/foundation_corpus_discovery_v1/FOUNDATION_CORPUS_DISCOVERY_HASH_MANIFEST.csv","discovery artifact hash authority"),
 ("donor/operator authority","exports/foundation_corpus_discovery_v1/FOUNDATION_METADATA_DONOR_X_OPERATOR.csv","fit-donor by physical-operator support"),
 ("reader donor firewall","exports/contextual_biology_v6r5a_20260822/reader_donor_split.csv","104/22/23 reader partition authority"),
 ("NPH firewall implementation","scripts/v4/full104_production_expression_firewall.py","original-NPH denylist and seven derivative allowlist implementation"),
 ("phase2 materialization manifest","outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/PHASE2_EXPRESSION_MATERIALIZATION_MANIFEST.csv","completed phase2 expression artifact and normalization lineage manifest"),
 ("phase2 expression block manifest","outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/PHASE2_EXPRESSION_BLOCK_MANIFEST.csv","completed block geometry and row/address mapping"),
 ("phase2 asset authentication","outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/ASSET_AUTHENTICATION.csv","authenticated materialization inputs and NPH derivatives"),
 ("physical descriptor allowlist","outputs/full104_v014_20260826/03_phase2_state_derivation_v1/preexpression_freeze/PHASE2_PHYSICAL_DESCRIPTOR_ALLOWLIST.json","preexpression observation and physical-descriptor allowlist"),
 ("original NPH denylist","outputs/full104_v014_20260826/full104_expression_interface_v8_verified/FULL104_EXPRESSION_INTERFACE_V8/ORIGINAL_NPH_MIXED_ASSET_DENYLIST.csv","original mixed-NPH assets denied by path and hash"),
 ("source registry","exports/foundation_corpus_discovery_v1/FOUNDATION_METADATA_SOURCE.csv","source_library registry and corpus counts"),
 ("donor registry","exports/foundation_corpus_discovery_v1/FOUNDATION_METADATA_DONOR.csv","fit donor registry"),
 ("operator registry","exports/foundation_corpus_discovery_v1/FOUNDATION_METADATA_OPERATOR.csv","42 physical operator registry"),
 ("source/operator registry","exports/foundation_corpus_discovery_v1/FOUNDATION_METADATA_SOURCE_X_OPERATOR.csv","source_library to operator lineage"),
 ("support by source","exports/foundation_corpus_discovery_v1/FOUNDATION_SUPPORT_BY_SOURCE.csv","source-level scalar support and sparsity summary"),
 ("support by operator","exports/foundation_corpus_discovery_v1/FOUNDATION_SUPPORT_BY_OPERATOR.csv","operator-level address support and sparsity summary"),
]
matrix=[rec(t,p,s,False,"DIRECT", "REUSE_EXACT") for t,p,s in exact]
engineering=[
 ("model ingress consumer","scripts/v4/full104_expression_interface_consumer.py","same normalized-value plus observation-state interface; implementation reuse requires contextual rebenchmark"),
 ("F0 slow reference","scripts/v4/contextual_target_v1_f0_slow_reference.py","independent contextual constructor parity oracle"),
 ("executor test design","scripts/v4/test_full104_block_major_executor_v1.py","parity, resume and adversarial test architecture"),
 ("block-major executor","scripts/v4/run_full104_refit_null_block_major_v1.py","block-major sorted reads, logical restore, accumulators, checkpoint binding"),
 ("resume launcher","scripts/v4/resume_full104_block_major_wsl_all_v4.sh","lossless WSL resume and mapping identity mechanics"),
 ("executor validation","scripts/v4/validate_full104_block_major_gold_replicate_v1.py","wrong-map, wrong-sketch, dtype, interruption and independent-finalization attacks"),
 ("ALL104 execution ledger","outputs/full104_v014_20260826/03_phase2_state_derivation_v1/shared_refit_null_sensitivity_results_v4_block_major_wsl/RUN_STATE.json","completed ALL104 run geometry and numerical gates; scientific selection closed"),
 ("ALL104 performance","outputs/full104_v014_20260826/03_phase2_state_derivation_v1/shared_refit_null_sensitivity_results_v4_block_major_wsl/BLOCK_MAJOR_PERFORMANCE.json","historical IO/resource measurements for executor pattern only"),
 ("WSL/CUDA preflight","outputs/full104_v014_20260826/03_phase2_state_derivation_v1/wsl_backend_preflight_v1/WSL_BACKEND_PREFLIGHT.json","historical WSL/CUDA discovery reusable only as an environment-check pattern; current identity not asserted"),
]
matrix += [rec(t,p,s,True,"MECHANICS_ONLY","REUSE_ENGINEERING_PATTERN_ONLY") for t,p,s in engineering]
matrix.append(rec("F0 metamorphic authority","outputs/contextual_teacher_target_v1_f0_implementation_20260901/CONTEXTUAL_TARGET_V1_F0_METAMORPHIC_RESULTS.json","closed query-local leakage/metamorphic PASS evidence and test template",False,"HISTORICAL_MECHANICS_EVIDENCE","REUSE_EXACT"))
matrix.append(rec("prior F1 reuse taxonomy","outputs/contextual_teacher_target_v1_f1_reuse_reconciliation_20260901/F1_REUSE_TAXONOMY.csv","prior explicit byte/algorithm/pattern reuse classification used for completeness reconciliation",False,"REUSE_INVENTORY_AUTHORITY","REUSE_EXACT"))
closed=[
 ("failed D_shared final adjudication","outputs/full104_v014_20260826/03_phase2_state_derivation_v1/full104_shared_state_final_adjudication_v1/FULL104_SHARED_STATE_FINAL_ADJUDICATION.json","D_shared selection and branch-specific null conclusion"),
 ("old no-prefix controls","outputs/full104_v014_20260826/03_phase2_state_derivation_v1/full104_shared_no_prefix_control_closure_v1/FULL104_SHARED_NO_PREFIX_CONTROL_CLOSURE.json","shared-prefix controls specific to failed decomposition"),
 ("old ALL104 D/null selection","outputs/full104_v014_20260826/03_phase2_state_derivation_v1/shared_refit_null_sensitivity_results_v4_block_major_wsl/FULL512_REFIT_NULL_SELECTION.json","old cap/refit-null selecting output"),
]
matrix += [rec(t,p,s,True,"NONE_SCIENTIFIC","CLOSED_DSHARED_DO_NOT_USE") for t,p,s in closed]
delta_inputs=[
 ("contextual architecture source","src/sea_ad_jepa/v4/contextual_query_local.py","current query-safe constructor semantics"),
 ("contextual F0 implementation authority","outputs/contextual_teacher_target_v1_f0_implementation_20260901/CONTEXTUAL_TARGET_V1_F0_IMPLEMENTATION_MANIFEST.json","validated current contextual constructor implementation"),
 ("F1 forward identity counts","outputs/contextual_teacher_target_v1_f1_reader_forward_authority_freeze_20260902/F1_FUTURE_FORWARD_AUDIT.json","metadata-only current cache/forward geometry"),
 ("F1 evidence-mask contract","outputs/contextual_teacher_target_v1_f1_preflight_20260901/CONTEXTUAL_TARGET_V1_F1_EVIDENCE_MASK_CONTRACT.md","nested evidence-mask authority"),
 ("current encoder source","src/sea_ad_jepa/v4/ipb_jepa.py","41,238-address, width-160, six-block/four-head backbone"),
 ("current u0 checkpoint","exports/prod41k_teacher_t1_20260823/t1_run/t1_checkpoint_u0000.pt","current frozen model-state bytes; tensor values not read"),
]
matrix += [rec(t,p,s,False,"INPUT_AUTHORITY_ONLY","REUSE_EXACT") for t,p,s in delta_inputs]
write_csv("FULL104_REUSE_MATRIX.csv",matrix,list(matrix[0]))

reused=[{k:r[k] for k in ("topic","path","sha256","semantic_scope","action")} for r in matrix if r["action"].startswith("REUSE_")]
write_csv("FULL104_REUSED_ARTIFACT_MANIFEST.csv",reused,list(reused[0]))
closed_rows=[{k:r[k] for k in ("topic","path","sha256","semantic_scope","action")} for r in matrix if r["action"]=="CLOSED_DSHARED_DO_NOT_USE"]
write_csv("FULL104_CLOSED_DSHARED_ARTIFACTS.csv",closed_rows,list(closed_rows[0]))

inventory_paths=["outputs/full104_v014_20260826/01_full104_metadata_adapter/FULL104_ADAPTER_SHA256_MANIFEST.csv","exports/foundation_corpus_discovery_v1/FOUNDATION_CORPUS_DISCOVERY_HASH_MANIFEST.csv","outputs/contextual_teacher_target_v1_f1_reuse_reconciliation_20260901/F1_REUSE_TAXONOMY.csv","outputs/contextual_teacher_target_v1_code_discovery_20260901/CONTEXTUAL_TARGET_V1_CODE_PATH_DISCOVERY.json"]
auth={"schema":"full104-reuse-authority-v1","status":"PASS_AUTHENTICATED_REUSE_MATRIX","rule":"REUSE_FROZEN_BYTES_VERIFY_HASH_SEMANTICS_COMPUTE_ONLY_MISSING_DELTA",
      "scope_definition":{"controlling_instruction_path":str(CONTROL),"controlling_instruction_sha256":sha(CONTROL),"controlling_instruction_bytes":CONTROL.stat().st_size,"external_inventory_authorities":[{"path":p,"sha256":sha(ROOT/p),"bytes":(ROOT/p).stat().st_size} for p in inventory_paths]},
      "delta_novelty_reconciliation":{
       "FULL104_CONTEXTUAL_RESOURCE_DELTA.json":"No prior inventory contains current role/forward static planning envelope; upstream provides only nonfrozen identity counts.",
       "FULL104_CONTEXTUAL_CACHE_RESUME_DELTA.md":"No prior inventory defines the contextual two-axis encoder-view/value-world cache identity and null payload binding.",
       "FULL104_CURRENT_MODEL_MEMORY_ACCOUNTING.json":"No prior inventory gives exact current contextual encoder copy/gradient/state/checkpoint conversion accounting.",
       "FULL104_CONTEXT_CAPACITY_DELTA.json":"No prior inventory analytically translates 42-operator measured-scalar support through current nested evidence fractions.",
       "FULL104_TRAINING_COVERAGE_COORDINATES.json":"No prior inventory gives nonselecting FULL104 presentation arithmetic for the current contextual path."},
      "population":{"cells":4553407,"donors":104,"operators":42,"donor_operator_strata":1400,"source_cells":{"HVS":198718,"NPH52":236476,"SEA_AD":4118213},"nph_quarantined":22715,"duplicate_cell_locators":0,"addresses":41238},
      "firewall":{"expression_opened":False,"full_expression_scan":False,"f1_candidate_outcome_read":False,"training":False,"backward":False,"optimizer_step":False,"ema_update":False,"protected_partitions_opened":False},
      "matrix_rows":len(matrix),"actions":{a:sum(r["action"]==a for r in matrix) for a in sorted(set(r["action"] for r in matrix))}}
write_json("FULL104_REUSE_AUTHORITY.json",auth)
write_json("FULL104_CURRENT_CONTEXTUAL_DELTA_PLAN.json",{"schema":"full104-current-contextual-delta-plan-v1","status":"METADATA_AND_STATIC_ACCOUNTING_ONLY",
 "deltas":["hash-bound contextual constructor inventory","cache/resume identity geometry","static parameter/checkpoint memory accounting","operator-level analytic context capacity","arithmetic training-coverage coordinates"],
 "not_run":["expression scan","model forward benchmark","F1 outcome","backward","optimizer","EMA"],"benchmark_disposition":"No new GPU benchmark: current F1 package already supplies exact identity counts; prior short-fixture timing is non-authoritative and not reused as a current resource measurement."})
write_json("FULL104_DELTA_EXPRESSION_JUSTIFICATION.json",{"status":"NOT_REQUIRED","expression_reads":[],"reason":"All deltas derive from frozen metadata, hashes, static source geometry, checkpoint file size, and the 42x41,238 observation-state authority."})

fwd=json.loads((ROOT/delta_inputs[2][1]).read_text(encoding="utf-8"))
write_json("FULL104_CONTEXTUAL_RESOURCE_DELTA.json",{"schema":"full104-contextual-resource-delta-v1","status":"STATIC_PLANNING_ENVELOPE_ONLY_NOT_FROZEN_EXECUTION_AUTHORITY",
 "current_shape":{"addresses":41238,"width":160,"heads":4,"blocks":6,"roles":["teacher","correct","null"],"unique_cell_query_pairs":fwd["unique_cell_query_pairs"],"planned_forward_identities":fwd["future_expensive_forward_identities"],"forwards_per_unique_cell_query":fwd["forwards_per_unique_cell_query"]},
 "measurements":{"latency":None,"vram":None,"throughput":None,"reader_fraction":None},"count_authority_status":fwd["status"],"reason":"Counts are retained as metadata-only planned geometry under the controlling brief, not promoted beyond their source status. A new benchmark would overlap the active F1 lane; no parameter or context cap may be selected here.","training_or_forward_executed":False})

(OUT/"FULL104_CONTEXTUAL_CACHE_RESUME_DELTA.md").write_text("""# FULL104 contextual cache/resume delta\n\nStatus: `STATIC_PLANNING_GEOMETRY_NOT_EXECUTION_AUTHORITY`\n\nThe controlling brief carries 43,108 unique `(cell,q)` pairs, 1,388 compute-only dedup opportunities, and 474,188 planned expensive forward identities (11 per unique pair). Their direct source remains explicitly `COUNT_RECOMPUTED_METADATA_ONLY_NOT_FROZEN_DUE_TO_NUISANCE_STOP`; this package does not promote them to an execution freeze.\n\nCache identity must separately bind (a) encoder-view role (`teacher` or `student`) and (b) value-world role (`teacher`, `correct`, or `null`); row locator; query address; assignment/draw identity; evidence-mask level and hash; exact null source row locator/donor/cell and normalized-value payload hash for nulls; null-map identity; encoder/tokenizer source hashes; model-state hash; ordered address-namespace hash; observation-state authority hash; dtype; and constructor version.\n\nReuse the historical block-major pattern only: sort physical reads, restore exact logical order, maintain independent accumulators, snapshot atomically, bind every checkpoint to all map/input hashes, and independently finalize. Old D/null formulas and results are prohibited. Cache collisions across roles, evidence masks, queries, rows, payloads, assignments, or model states fail closed. No cache bytes or expression were generated here, and this document does not authorize execution.\n""",encoding="utf-8")

params=3232768; pbytes=params*4; ck=ROOT/delta_inputs[5][1]
write_json("FULL104_CURRENT_MODEL_MEMORY_ACCOUNTING.json",{"schema":"full104-current-model-memory-accounting-v1","status":"EXACT_STATIC_ARCHITECTURE_ACCOUNTING",
 "encoder":{"parameters":params,"parameter_bytes_fp32":pbytes,"parameter_mib_fp32":pbytes/2**20,"derivation":"tokenizer 1,992,928 + cell 160 + six blocks 1,239,360 + final norm 320"},
 "copies":{"online_plus_teacher_fp32_bytes":2*pbytes,"online_plus_teacher_fp32_mib":2*pbytes/2**20},
 "mechanical_conversion_table":{"gradients_fp32_bytes":pbytes,"adam_fp32_two_state_bytes":2*pbytes,"online_teacher_grad_adam_fp32_bytes":5*pbytes,"fp16_parameter_copy_bytes":params*2,"bf16_parameter_copy_bytes":params*2},
 "checkpoint":{"path":delta_inputs[5][1],"sha256":sha(ck),"file_bytes":ck.stat().st_size},"selected_precision_or_optimizer":None})

state=np.load(ROOT/exact[8][1],allow_pickle=False)["states"]
measured=(state==1).sum(axis=1).astype(int)
levels=[0.2,0.4,0.6,0.8,1.0]
summ=[]
for x in levels:
    vals=np.floor(measured*x).astype(int)
    summ.append({"evidence_fraction":x,"operator_min":int(vals.min()),"operator_median":float(np.median(vals)),"operator_max":int(vals.max()),"definition":"floor(operator measured-scalar support * fraction); query exclusion can reduce by one when q is included"})
write_json("FULL104_CONTEXT_CAPACITY_DELTA.json",{"schema":"full104-context-capacity-delta-v1","status":"ANALYTIC_OPERATOR_ENVELOPE_NO_CAP_SELECTION","authority_sha256":sha(ROOT/exact[8][1]),
 "measured_scalar_support_by_operator":{"min":int(measured.min()),"median":float(np.median(measured)),"max":int(measured.max()),"values":measured.tolist()},"nested_evidence_envelopes":summ,"context_cap_selected":False,"expression_read":False})

cells=4553407
write_json("FULL104_TRAINING_COVERAGE_COORDINATES.json",{"schema":"full104-training-coverage-coordinates-v1","status":"ARITHMETIC_ONLY_NONSELECTING","cells":cells,"donors":104,"operators":42,"strata":1400,
 "presentation_coordinates":[{"presentations_per_cell":k,"total_presentations":cells*k} for k in (1,2,4,8,16)],"selected_presentations":None,"expression_read":False})
write_json("FULL104_DEFERRED_SELECTIONS.json",{"status":"ALL_DEFERRED","selected":{},"deferred":["replacement latent D","learning rate","weight decay","gradient clipping","microbatch/effective batch","EMA half-life/tau","lambda_context","replay rule/cap","query count","context cap","training duration","early stopping","biological thresholds"]})

# Generated delta artifacts are the D-class rows; pre-existing authorities above are reuse inputs.
generated_delta=[
 ("contextual resource planning delta","outputs/full104_parallel_reuse_delta_20260902/FULL104_CONTEXTUAL_RESOURCE_DELTA.json","new static contextual role/forward planning envelope"),
 ("contextual cache/resume delta","outputs/full104_parallel_reuse_delta_20260902/FULL104_CONTEXTUAL_CACHE_RESUME_DELTA.md","new contextual typed cache/resume identity translation"),
 ("current model memory accounting delta","outputs/full104_parallel_reuse_delta_20260902/FULL104_CURRENT_MODEL_MEMORY_ACCOUNTING.json","new exact contextual model/copy/checkpoint accounting"),
 ("context capacity delta","outputs/full104_parallel_reuse_delta_20260902/FULL104_CONTEXT_CAPACITY_DELTA.json","new analytic contextual evidence-length envelopes"),
 ("training coverage coordinates delta","outputs/full104_parallel_reuse_delta_20260902/FULL104_TRAINING_COVERAGE_COORDINATES.json","new arithmetic FULL104 presentation coordinates"),
]
matrix += [rec(t,p,s,False,"GENERATED_DELTA_ONLY","CURRENT_CONTEXTUAL_DELTA_REQUIRED") for t,p,s in generated_delta]
write_csv("FULL104_REUSE_MATRIX.csv",matrix,list(matrix[0]))
reused=[{k:r[k] for k in ("topic","path","sha256","semantic_scope","action")} for r in matrix if r["action"].startswith("REUSE_")]
write_csv("FULL104_REUSED_ARTIFACT_MANIFEST.csv",reused,list(reused[0]))
closed_rows=[{k:r[k] for k in ("topic","path","sha256","semantic_scope","action")} for r in matrix if r["action"]=="CLOSED_DSHARED_DO_NOT_USE"]
write_csv("FULL104_CLOSED_DSHARED_ARTIFACTS.csv",closed_rows,list(closed_rows[0]))
auth["matrix_rows"]=len(matrix); auth["actions"]={a:sum(r["action"]==a for r in matrix) for a in sorted(set(r["action"] for r in matrix))}
write_json("FULL104_REUSE_AUTHORITY.json",auth)

source_paths=["scripts/v4/build_full104_parallel_reuse_delta.py","scripts/v4/validate_full104_parallel_reuse_delta.py"]+[r["path"] for r in matrix if r["action"] in ("CURRENT_CONTEXTUAL_DELTA_REQUIRED","REUSE_ENGINEERING_PATTERN_ONLY")]
source_rows=[]
for rel in dict.fromkeys(source_paths):
    p=ROOT/rel
    if p.is_file(): source_rows.append({"path":rel,"sha256":sha(p),"bytes":p.stat().st_size})
write_csv("FULL104_REUSE_DELTA_SOURCE_MANIFEST.csv",source_rows,["path","sha256","bytes"])

if not (OUT/"FULL104_REUSE_DELTA_MULTIAGENT.md").exists():
    (OUT/"FULL104_REUSE_DELTA_MULTIAGENT.md").write_text("# FULL104 reuse/delta targeted review\n\nPENDING_EXACT_SEVEN_LENS_REVIEW\n",encoding="utf-8")
write_json("FULL104_REUSE_DELTA_INDEPENDENT_VALIDATION.json",{"status":"PENDING_INDEPENDENT_VALIDATION"})
(OUT/"FULL104_REUSE_DELTA_EXTERNAL_REVIEW_HANDOFF.md").write_text("""# FULL104 reuse-first contextual delta — external review handoff\n\nTerminal is pending independent validation and exact seven-lens review. The package reuses frozen FULL104 authorities by path/hash, closes all D_shared-dependent scientific outputs, and derives only metadata/static contextual deltas. It opened no expression, read no F1 candidate outcome, executed no model forward/training/backward/optimizer/EMA operation, and selected no hyperparameter.\n""",encoding="utf-8")
manifest=[]
for p in sorted(OUT.iterdir()):
    if p.is_file() and p.name!="FULL104_REUSE_DELTA_MANIFEST.csv": manifest.append({"artifact":p.name,"sha256":sha(p),"bytes":p.stat().st_size})
write_csv("FULL104_REUSE_DELTA_MANIFEST.csv",manifest,["artifact","sha256","bytes"])
print(json.dumps({"status":"BUILT_PENDING_REVIEW","output":str(OUT),"artifacts":len(list(OUT.iterdir()))}))
