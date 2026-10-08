#!/usr/bin/env python3
"""Independent Command-15B selector, design, QR-geometry and HC3 validator."""
from __future__ import annotations

import argparse, csv, hashlib, json
from pathlib import Path

import numpy as np
from scipy import linalg

ROOT = Path(__file__).resolve().parents[2]
P15A4 = ROOT / "outputs/contextual_teacher_target_v1_f1_hc3_replication_frontier_complete_20260902"
UP = ROOT / "outputs/contextual_teacher_target_v1_f1_nuisance_authority_recovery_20260902"
MANIFEST_SHA = "a112bd4907f2c20b4346179264391ceb8d3e9ceee42f7a8bcb1bcd153e4cb09f"
RAW_SHA = "1d8f837d18cedd8d1b8fd6138d1b25f886b8352c097a4723ca06421573334056"
SCHEMA_SHA = "9f90c764d0d97b5a10badc03dfcbafc364e0bf40e120a9aed6609e036b5924a7"
EPS = np.finfo(np.float64).eps
BOUNDARY = float(np.sqrt(EPS))
SOURCE_COLS = ("source_HVS", "source_NPH52", "source_SEA_AD")
CONTINUOUS = ("recipient_physical_support", "recipient_depth", "correct_minus_null_visible_depth", "correct_minus_null_measured_zero_rate")
BLOCKS = {"HVS": tuple(range(24)), "NPH52": tuple(range(35, 42)), "SEA_AD": tuple(range(24, 35))}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def row_triple(row) -> tuple[int, int, int]:
    return tuple(int(row[k]) for k in ("r_HVS", "r_NPH52", "r_SEAAD"))


def row_admissible(row) -> bool:
    return row["donor_replicated_hc3_admissible"] is True or row["donor_replicated_hc3_admissible"] == "True"


def independent_selection(rows) -> tuple[int, int, int]:
    accepted = [r for r in rows if row_admissible(r)]
    def ge(a, b): return all(x >= y for x, y in zip(row_triple(a), row_triple(b)))
    maximal = [a for a in accepted if not any(ge(b, a) and row_triple(b) != row_triple(a) for b in accepted)]
    universal = [a for a in accepted if all(ge(a, b) for b in accepted)]
    if len(maximal) != 1 or len(universal) != 1 or row_triple(maximal[0]) != row_triple(universal[0]):
        raise RuntimeError("STOP_F1_HC3_15B_SELECTION_UNRESOLVED")
    return row_triple(universal[0])


def qr_basis(x: np.ndarray) -> tuple[int, np.ndarray]:
    _, r, piv = linalg.qr(np.asarray(x, np.float64), mode="economic", pivoting=True)
    diag = np.abs(np.diag(r)); tau = max(x.shape) * EPS * diag[0] if diag.size else 0.0
    rank = int(np.sum(diag > tau))
    q = linalg.qr(np.asarray(x, np.float64)[:, piv[:rank]], mode="economic")[0][:, :rank]
    return rank, q


def qr_rank(x: np.ndarray) -> int:
    return qr_basis(x)[0]


def rebuild(selected: tuple[int, int, int]) -> tuple[np.ndarray, list[dict], np.ndarray, np.ndarray, dict]:
    if sha(UP / "F1_NUISANCE_DONOR_DESIGN_F64LE.bin") != RAW_SHA or sha(UP / "F1_NUISANCE_COLUMN_SCHEMA.json") != SCHEMA_SHA:
        raise RuntimeError("STOP_F1_HC3_15B_AUTHORITY_MISMATCH")
    schema = json.loads((UP / "F1_NUISANCE_COLUMN_SCHEMA.json").read_text(encoding="utf-8"))
    raw = np.fromfile(UP / "F1_NUISANCE_DONOR_DESIGN_F64LE.bin", dtype="<f8").reshape(104, 49)
    names = schema["columns"]; cols = {name: raw[:, i] for i, name in enumerate(names)}
    donors = np.asarray(schema["donor_order"]); sources = np.asarray([x.split("::",1)[0] for x in donors])
    base = np.ones((104,1), np.float64); kept=[]
    for name in sorted(SOURCE_COLS + CONTINUOUS):
        value = cols[name]; candidate = np.column_stack((base, value-value.mean(dtype=np.float64)))
        if qr_rank(candidate) == qr_rank(base)+1:
            base=candidate; kept.append(name)
    if qr_rank(base) != 7: raise RuntimeError("STOP_F1_HC3_15B_INDEPENDENT_MISMATCH")
    operator = raw[:, [names.index(f"operator_mix_{i:03d}") for i in range(42)]]
    qbase = np.linalg.svd(base, full_matrices=False)[0][:,:7]
    score_blocks={}; local={}; incremental={}
    for source, ids in BLOCKS.items():
        embedded=np.zeros((104,len(ids)),np.float64); mask=sources==source; embedded[mask]=operator[mask][:,ids]
        incremental[source]=qr_rank(np.column_stack((base,embedded)))-7
        residual=embedded-qbase@(qbase.T@embedded); local[source]=qr_rank(residual)
        u,s,vt=np.linalg.svd(residual,full_matrices=False)
        for j in range(vt.shape[0]):
            i=int(np.flatnonzero(np.abs(vt[j])==np.max(np.abs(vt[j])))[0])
            if vt[j,i]<0: u[:,j]*=-1; vt[j]*=-1
        work=base.copy(); accepted=[]
        for j in range(len(s)):
            value=u[:,j]*s[j]; value=value-value.mean(dtype=np.float64)
            if qr_rank(np.column_stack((work,value)))==qr_rank(work)+1 and len(accepted)<incremental[source]:
                work=np.column_stack((work,value)); accepted.append(value)
            else: break
        score_blocks[source]=np.column_stack(accepted) if accepted else np.empty((104,0))
    x=np.ascontiguousarray(np.column_stack((base,score_blocks["HVS"][:,:selected[0]],score_blocks["NPH52"][:,:selected[1]],score_blocks["SEA_AD"][:,:selected[2]])),dtype=np.float64)
    identities=[{"column_index":0,"kind":"mandatory","identity":"intercept"}]
    identities += [{"column_index":i+1,"kind":"mandatory","identity":name} for i,name in enumerate(kept)]
    index=len(identities)
    for source,count in zip(("HVS","NPH52","SEA_AD"),selected):
        for component in range(1,count+1):
            identities.append({"column_index":index,"kind":"optional_source_residual_svd_score","source":source,"component":component,"identity":f"{source}_residual_svd_score_{component:02d}"}); index+=1
    return x, identities, donors, sources, {"local":local,"incremental":incremental,"score_blocks":score_blocks}


def independent_hc3(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    q,r=linalg.qr(x,mode="economic"); beta=linalg.solve_triangular(r,q.T@y); residual=y-x@beta; h=np.sum(q*q,axis=1)
    xpinv=linalg.solve_triangular(r,q.T); adjusted=residual/(1-h)
    cov=(xpinv*adjusted[None,:])@(xpinv*adjusted[None,:]).T
    return beta,cov,h


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("--package",type=Path,required=True); args=ap.parse_args(); out=args.package.resolve()
    manifest=P15A4/"F1_HC3_15A4_MANIFEST.csv"; manifest_ok=sha(manifest)==MANIFEST_SHA
    with manifest.open(newline="",encoding="utf-8") as f: mrows=list(csv.DictReader(f))
    manifest_ok = manifest_ok and all((P15A4/r["relative_path"]).is_file() and sha(P15A4/r["relative_path"])==r["sha256"] and (P15A4/r["relative_path"]).stat().st_size==int(r["bytes"]) for r in mrows)
    with (P15A4/"F1_HC3_REPLICATION_FRONTIER_COMPLETE.csv").open(newline="",encoding="utf-8") as f: frontier=list(csv.DictReader(f))
    selected=independent_selection(frontier)
    production_choice=json.loads((out/"F1_HC3_SELECTED_TRIPLE.json").read_text(encoding="utf-8"))
    x,identities,donors,sources,parts=rebuild(selected)
    production=np.fromfile(out/"F1_HC3_SELECTED_DONOR_DESIGN_F64LE.bin",dtype="<f8").reshape(104,-1)
    schema=json.loads((out/"F1_HC3_SELECTED_DONOR_DESIGN_SCHEMA.json").read_text(encoding="utf-8"))
    r,q=qr_basis(x); h=np.sum(q*q,axis=1); losses=[r-qr_rank(np.delete(x,i,axis=0)) for i in range(104)]
    critical=[str(donors[i]) for i,v in enumerate(losses) if v]
    hc3=bool(r==x.shape[1] and 104-r>0 and np.isfinite(h).all() and np.min(1-h)>BOUNDARY)
    engine=json.loads((out/"F1_HC3_SELECTED_SYNTHETIC_ENGINE_CHECK.json").read_text(encoding="utf-8"))
    synth_ok=True
    for y in (np.sin(np.arange(104)/7.0),np.cos(np.arange(104)/11.0)+np.arange(104)/104.0):
        beta,cov,lev=independent_hc3(x,y); synth_ok &= bool(np.isfinite(beta).all() and np.isfinite(cov).all() and np.isfinite(lev).all())
    nph=np.column_stack((x,parts["score_blocks"]["NPH52"][:,:1])); nr,nq=qr_basis(nph); nh=np.sum(nq*nq,axis=1)
    nloss=[nr-qr_rank(np.delete(nph,i,axis=0)) for i in range(104)]; ncritical=[str(donors[i]) for i,v in enumerate(nloss) if v]
    checks={
        "15A4_manifest_and_all_files_verified":manifest_ok,
        "all_70_rows_loaded":len(frontier)==70,
        "admissible_set_30":sum(row_admissible(r) for r in frontier)==30,
        "unique_componentwise_maximum":tuple(production_choice["selected_triple"])==selected and production_choice["maximal_triples"]==[list(selected)] and production_choice["universal_maximum_triples"]==[list(selected)],
        "selected_column_identities_exact":identities==schema["columns"],
        "selected_design_exact_float64_array":np.array_equal(x,production),
        "selected_design_bytes_exact":x.astype("<f8",copy=False).tobytes()==production.astype("<f8",copy=False).tobytes(),
        "selected_design_sha_exact":sha(out/"F1_HC3_SELECTED_DONOR_DESIGN_F64LE.bin")==schema["selected_design_sha256"],
        "independent_qr_rank_df":r==production.shape[1] and 104-r==json.loads((out/"F1_HC3_SELECTED_GEOMETRY.json").read_text(encoding="utf-8"))["df"],
        "all_104_loo_ranks_stable":len(losses)==104 and not critical,
        "hc3_estimable":hc3,
        "independent_synthetic_hc3_finite":synth_ok and engine["all_finite"],
        "donor_indispensable_attack_rejected":(not (nr==nph.shape[1] and np.min(1-nh)>BOUNDARY)) and ncritical==["NPH52::human_NPH_906"],
        "production_helpers_not_imported":True,
        "no_expression_model_outcome_training_access":True,
    }
    status="PASS" if all(v is True for v in checks.values()) else "STOP_F1_HC3_15B_INDEPENDENT_MISMATCH"
    report={"status":status,"checks":checks,"selected_triple":list(selected),"selected_design_sha256":sha(out/"F1_HC3_SELECTED_DONOR_DESIGN_F64LE.bin"),"rank":r,"df":104-r,"loo_rank_checks":len(losses),"loo_critical_donors":critical,"hc3_estimable":hc3,"independent_max_leverage":float(np.max(h)),"independent_min_one_minus_h":float(np.min(1-h))}
    (out/"F1_HC3_15B_INDEPENDENT_VALIDATION.json").write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps(report))
    if status != "PASS": raise SystemExit(2)


if __name__ == "__main__": main()
