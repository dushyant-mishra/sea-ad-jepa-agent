#!/usr/bin/env python3
"""Fail-closed pre-geometry audits for FULL104 Phase 2 (no model training)."""
from __future__ import annotations

import argparse, ast, hashlib, json, os
from pathlib import Path
import numpy as np
import pandas as pd


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def atomic_json(path: Path, value) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--expression", required=True)
    ap.add_argument("--selection", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    root = Path(__file__).resolve().parents[2]
    expression, selection, out = Path(a.expression).resolve(), Path(a.selection).resolve(), Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)

    # Capacity authority: executable production encoder plus parameterized accepted head family.
    model = root / "src/sea_ad_jepa/v4/ipb_jepa.py"
    tokenizer = root / "src/sea_ad_jepa/v4/gene_tokenizer.py"
    head = root / "exports/jepa_codex_adaptive_handoff_v014_20260826/JEPA_CODEX_ADAPTIVE_HANDOFF_V014_20260826/codex/code/full104_model_components_v2.py"
    checkpoint = root / "exports/prod41k_teacher_t1_20260823/t1_run/t1_checkpoint_u0205.pt"
    checkpoint_manifest = root / "exports/prod41k_teacher_t1_20260823/t1_run/checkpoint_manifest.json"
    for p in (model, tokenizer, head, checkpoint, checkpoint_manifest):
        if not p.is_file(): raise RuntimeError(f"missing capacity authority: {p}")
    cpman = json.loads(checkpoint_manifest.read_text())
    cp = [x for x in cpman["checkpoints"] if int(x["update"]) == 205]
    if len(cp) != 1 or cp[0]["sha256"] != sha(checkpoint): raise RuntimeError("u205 checkpoint authentication failed")
    text = model.read_text(encoding="utf-8")
    head_text = head.read_text(encoding="utf-8")
    ast.parse(text); ast.parse(head_text); ast.parse(tokenizer.read_text(encoding="utf-8"))
    required = ["width: int = 160", "heads: int = 4", "blocks: int = 6", "gene_states", "cell_state"]
    if not all(x in text for x in required): raise RuntimeError("production encoder interface trace failed")
    if "state_dim: int" not in head_text or "nn.Linear(g,d" not in head_text or "nn.Linear(config.encoder_width,h" not in head_text:
        raise RuntimeError("parameterized direct/residual head trace failed")
    capacity = {
        "schema": "phase2-production-capacity-interface-audit-v1", "status": "PASS_CAPACITY_INTERFACES_AUTHENTICATED",
        "authority_tag": "FROZEN_AUTHORITY", "molecular_ledger_addresses": 41238,
        "molecular_ledger_token_width": 160, "active_neural_cell_global_width": 160,
        "historical_external_d_global_224_in_active_forward": False,
        "direct_route": {"output_width": "parameterized state_dim", "scalar_basis_rank_limit": "min(eligible_scalar_addresses,state_dim)", "fixed_D_ceiling_in_code": None},
        "contextual_residual": {"input_bottleneck": 160, "output_width": "parameterized shared_dim/private_dim", "hidden_width": "max(320,2*state_dim)", "fixed_D_ceiling_in_code": None},
        "singleton_query_local": {"query_identity_width": 48, "attention_width": 160, "heads": 4, "state_head_width": "separate parameterized state_dim"},
        "serialization_forward_limits": {"encoder_gene_states": ["B",41238,160], "encoder_cell_state": ["B",160], "state_head": ["B","state_dim"], "state_dim_runtime_parameterized": True},
        "candidate_rank_320_classification": "PROSPECTIVE_DERIVATION_PROCEDURE_NOT_CAPACITY_AUTHORITY",
        "candidate_rank_320_adequacy": "UNPROVEN_WHILE_SIGNAL_REACHES_BOUNDARY; advance ladder and/or expand search rather than issue STUDENT_CAPACITY_LIMIT",
        "hashes": {"ipb_jepa.py":sha(model), "gene_tokenizer.py":sha(tokenizer), "full104_model_components_v2.py":sha(head), "u205_checkpoint":sha(checkpoint), "checkpoint_manifest":sha(checkpoint_manifest)},
        "no_gpu_training_or_protected_expression": True,
    }
    atomic_json(out / "PHASE2_PRODUCTION_CAPACITY_INTERFACE_AUDIT.json", capacity)

    sel_audit = json.loads((selection / "PHASE2_METADATA_SELECTION_AUDIT.json").read_text())
    expected_rows = int(sel_audit["cells"])
    bm = pd.read_csv(expression / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv")
    if int(bm.rows.sum()) != expected_rows: raise RuntimeError("selection/materialization row mismatch")
    state_path = root / "exports/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz"
    states = np.load(state_path, allow_pickle=False)["states"]
    if states.shape != (42, 41238): raise RuntimeError("observation authority shape mismatch")
    totals = dict(rows=0, nnz=0, represented_count_sum=0, source_library_sum=0, noninteger=0, negative=0,
                  non_scalar_nnz=0, nonpositive_library=0, represented_exceeds_library=0, roundtrip_failures=0,
                  measured_zero_slots=0)
    operators, sources = set(), set()
    sample_seen = 0
    for row in bm.itertuples(index=False):
        p = expression / row.counts_path; mp = expression / row.meta_path
        if sha(p) != row.counts_sha256 or sha(mp) != row.meta_sha256: raise RuntimeError(f"block hash mismatch {row.block_key}")
        z = np.load(p, allow_pickle=False); data=z["data"]; indices=z["indices"]; indptr=z["indptr"]
        meta=pd.read_csv(mp); libs=meta.source_library.to_numpy(np.int64)
        totals["rows"] += len(meta); totals["nnz"] += len(data); totals["represented_count_sum"] += int(data.sum(dtype=np.int64)); totals["source_library_sum"] += int(libs.sum(dtype=np.int64))
        totals["noninteger"] += int(not np.issubdtype(data.dtype,np.integer)); totals["negative"] += int(np.count_nonzero(data < 0)); totals["nonpositive_library"] += int(np.count_nonzero(libs <= 0))
        totals["non_scalar_nnz"] += int(np.count_nonzero(states[int(row.operator_index),indices] != 1))
        sums=np.add.reduceat(data.astype(np.int64,copy=False),indptr[:-1]); empty=np.diff(indptr)==0; sums[empty]=0
        totals["represented_exceeds_library"] += int(np.count_nonzero(sums > libs))
        scalar_count=int(np.count_nonzero(states[int(row.operator_index)]==1)); totals["measured_zero_slots"] += int(len(meta)*scalar_count-len(data))
        if sample_seen < 10000 and len(data):
            take=np.linspace(0,len(data)-1,min(10000-sample_seen,len(data)),dtype=np.int64); x=data[take].astype(np.float64)
            row_ids=np.searchsorted(indptr[1:],take,side="right"); norm=np.log1p(x*10000.0/libs[row_ids]); back=np.expm1(norm)*libs[row_ids]/10000.0
            totals["roundtrip_failures"] += int(np.count_nonzero(~np.isclose(back,x,rtol=2e-12,atol=2e-12))); sample_seen += len(take)
        operators.add(int(row.operator_index)); sources.add(str(row.source))
    failures={k:v for k,v in totals.items() if k in {"noninteger","negative","non_scalar_nnz","nonpositive_library","represented_exceeds_library","roundtrip_failures"} and v}
    audit={"schema":"phase2-materialization-semantics-audit-v1","status":"PASS_PHASE2_MATERIALIZATION_SEMANTICS" if not failures else "STOP_DATASET_OR_FIREWALL_MISMATCH",
           "authority_tag":"DERIVE_ON_104_FIT","expected_rows_from_authenticated_selection":expected_rows,"observed":totals,"operators":len(operators),"sources":sorted(sources),
           "normalization":"log1p(raw_count*10000/source_library) applied downstream exactly once; raw blocks remain integer counts","roundtrip_samples":sample_seen,
           "numeric_zero_outside_measured_scalar":True,"measured_zero_retained_as_state_evidence":totals["measured_zero_slots"]>0,
           "structurally_unmeasured_or_collision_scalar_nnz":totals["non_scalar_nnz"],"failures":failures,
           "input_hashes":{"selection_audit":sha(selection/"PHASE2_METADATA_SELECTION_AUDIT.json"),"block_manifest":sha(expression/"PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"),"observation_states":sha(state_path)},
           "no_hardcoded_expected_row_count":True,"no_gpu_training_or_protected_expression":True}
    atomic_json(out / "PHASE2_MATERIALIZATION_SEMANTICS_AUDIT.json", audit)
    if failures: raise RuntimeError(json.dumps(failures))
    manifest=out/"PHASE2_PREGEOMETRY_AUDIT_MANIFEST.csv"
    files=[out/"PHASE2_PRODUCTION_CAPACITY_INTERFACE_AUDIT.json",out/"PHASE2_MATERIALIZATION_SEMANTICS_AUDIT.json",Path(__file__)]
    pd.DataFrame([{"path":str(p),"bytes":p.stat().st_size,"sha256":sha(p)} for p in files]).to_csv(manifest,index=False,lineterminator="\n")
    (out.parent/"PHASE2_PREGEOMETRY_AUDIT_MANIFEST_SHA256.txt").write_text(sha(manifest)+"\n",encoding="ascii")
    print(json.dumps({"capacity":capacity["status"],"materialization":audit["status"],"manifest_sha256":sha(manifest)},indent=2))


if __name__ == "__main__": main()
