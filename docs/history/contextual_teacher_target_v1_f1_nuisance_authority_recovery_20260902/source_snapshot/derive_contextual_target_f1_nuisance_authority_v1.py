#!/usr/bin/env python3
"""Outcome-blind F1 nuisance authority derivation from authenticated FULL104 rows."""
from __future__ import annotations

import argparse, csv, hashlib, json, multiprocessing as mp, os, shutil, struct
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
FINAL = ROOT / "outputs/contextual_teacher_target_v1_f1_nuisance_authority_recovery_20260902"
STAGING = ROOT / "outputs/_staging_contextual_teacher_target_v1_f1_nuisance_authority_recovery_20260902"
ASSIGN = ROOT / "outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_QUERY_ASSIGNMENTS_2DRAW.csv"
CELL_AUTH = ROOT / "outputs/contextual_teacher_target_v1_f1_preflight_20260901/CONTEXTUAL_TARGET_V1_F1_CELL_DONOR_OPERATOR_AUTHORITY.json"
NULL_MAP = ROOT / "outputs/contextual_teacher_target_v1_f1_prospective_repair_20260901/F1_MATCHED_NULL_PRIMARY_MAP.csv"
STATES = ROOT / "exports/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz"
SPLIT = ROOT / "exports/contextual_biology_v6r5a_20260822/reader_donor_split.csv"
REGISTRY = ROOT / "results/v4/stage81a2_canonical_asset_registry.csv"
SELECTION = ROOT / "outputs/full104_v014_20260826/03_phase2_state_derivation_v1/metadata_selection_level4/PHASE2_METADATA_SELECTION_LEVEL4.csv.gz"
EXPR = ROOT / "outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4"
BLOCK_MANIFEST = EXPR / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
V8 = ROOT / "outputs/full104_v014_20260826/full104_expression_interface_v8_verified/FULL104_EXPRESSION_INTERFACE_V8"
V8_SELECTION = V8 / "interface_check_v8r1/FULL104_EXPRESSION_INTERFACE_SELECTION.csv"
V8_PAYLOAD = V8 / "model_inputs/FULL104_EXPRESSION_INTERFACE_PAYLOAD.npz"
EVIDENCE = ROOT / "outputs/contextual_teacher_target_v1_f1_preflight_20260901/CONTEXTUAL_TARGET_V1_F1_EVIDENCE_MASK_CONTRACT.md"
SEED = "c5c5bc472850f17f0ca6249e3a2765e5924d411ef054691a5e7a5d9d29363a4f"
PROGRAMS = ("broad_common","weak_distributed","local","local_core","local_halo","core_halo","sparse_marker_like","innovation_tail")

EXPECTED = {
    ASSIGN:"12fd5f1549bb600e6bf52605196024f91bae28d7d20cb35a327d67c383f2c617",
    NULL_MAP:"aba31aea56190c32a00ac27a0356ea860761143f00f874db9c71c2080eb371a6",
    STATES:"852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537",
    SPLIT:"efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511",
    BLOCK_MANIFEST:"66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29",
    EVIDENCE:"d1eefdab177501a00370d71521ae86932e60540fb9f769dfe2b56c7994ca5c5a",
    ROOT/"scripts/v4/derive_full104_phase2_shared_state.py":"395562010dcfa3a546e50d22164de70e40d995d0ca02245230a1deb96166db8f",
    ROOT/"scripts/v4/audit_full104_phase2_capacity_and_materialization.py":"3d5e5e67ca4406e7f003dd69c997481bce4018d11a374eca1d4bc951f2ba7e2d",
    ROOT/"scripts/v4/materialize_full104_phase2_expression.py":"575d02a4e7f7c5c6f3187eeed691a2eac7d3f1df9510621bc497b283806c270b",
    ROOT/"scripts/v4/build_full104_phase2_multiview_features.py":"217d00332e2021797b4900710bb330a1d99ee30d9c8d7fb26532d59593b3acf5",
}

G_ROWS: dict[str,dict] = {}
G_ASSIGN: dict[str,list[tuple[int,str,int]]] = {}
G_NULL: dict[str,str] = {}
G_STATES: np.ndarray | None = None

def sha(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(8<<20),b""): h.update(b)
    return h.hexdigest()

def cjson(x:Any)->bytes:return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def dump(p:Path,x:Any)->None:p.write_text(json.dumps(x,indent=2,sort_keys=True)+"\n",encoding="utf-8")
def rel(p:Path)->str:
    try:return p.relative_to(ROOT).as_posix()
    except ValueError:return str(p)

def semantic_root(donors:list[str], columns:list[str], matrix:np.ndarray)->str:
    b=bytearray(b"F1_NUISANCE_DONOR_DESIGN_V1\0")
    for seq in (donors,columns):
        b.extend(struct.pack("<I",len(seq)))
        for s in seq:
            x=s.encode("utf-8");b.extend(struct.pack("<I",len(x)));b.extend(x)
    b.extend(struct.pack("<QQ",*matrix.shape));b.extend(np.asarray(matrix,dtype="<f8",order="C").tobytes(order="C"))
    return hashlib.sha256(b).hexdigest()

def locate_rows(target:set[str])->dict[str,dict]:
    counters=Counter(); found={}
    use=["selection_row","source","operator_index","matrix_id","donor_id","canonical_cell_id","row_locator"]
    for chunk in pd.read_csv(SELECTION,usecols=use,chunksize=100_000,dtype={"canonical_cell_id":str,"donor_id":str}):
        for r in chunk.itertuples(index=False):
            pos=counters[r.matrix_id]; counters[r.matrix_id]+=1
            if r.canonical_cell_id in target:
                if r.canonical_cell_id in found:raise RuntimeError("duplicate selected cell")
                found[r.canonical_cell_id]={"selection_row":int(r.selection_row),"source":str(r.source),"operator":int(r.operator_index),"matrix_id":str(r.matrix_id),"donor_id":str(r.donor_id),"row_locator":str(r.row_locator),"block_key":f"op{int(r.operator_index):02d}/block-{pos//512:05d}","local_row":pos%512}
    if set(found)!=target:raise RuntimeError(f"STOP_PROVENANCE_OR_FIREWALL missing={len(target-set(found))}")
    return found

def load_rows(loc:dict[str,dict])->tuple[dict[str,dict],list[dict]]:
    bm=pd.read_csv(BLOCK_MANIFEST,dtype=str).set_index("block_key")
    by=defaultdict(list)
    for cell,r in loc.items():by[r["block_key"]].append((cell,r))
    out={}; used=[]
    for key,items in sorted(by.items()):
        if key not in bm.index:raise RuntimeError("block missing "+key)
        br=bm.loc[key];cp=EXPR/br.counts_path;mpath=EXPR/br.meta_path
        if sha(cp)!=br.counts_sha256 or sha(mpath)!=br.meta_sha256:raise RuntimeError("STOP_PROVENANCE_OR_FIREWALL block hash "+key)
        meta=pd.read_csv(mpath,dtype={"canonical_cell_id":str,"donor_id":str});z=np.load(cp,allow_pickle=False)
        data=z["data"];idx=z["indices"];ind=z["indptr"]
        for cell,r in items:
            i=int(r["local_row"]);mr=meta.iloc[i]
            if str(mr.canonical_cell_id)!=cell or int(mr.selection_row)!=r["selection_row"] or float(mr.source_library)<=0:raise RuntimeError("STOP_PROVENANCE_OR_FIREWALL row identity")
            a,b=int(ind[i]),int(ind[i+1]);counts=np.asarray(data[a:b],np.int64);indices=np.asarray(idx[a:b],np.int32);L=int(mr.source_library)
            x=np.log1p(counts.astype(np.float64)*(10000.0/L)).astype(np.float32)
            back=np.rint(np.expm1(x.astype(np.float64))*L/10000.0).astype(np.int64)
            if not np.array_equal(back,counts):raise RuntimeError("STOP_F1_NUISANCE_COUNT_ROUNDTRIP_FAILURE")
            out[cell]={**r,"source_library":L,"indices":indices,"counts":back,"normalized":x}
        used.append({"block_key":key,"counts_path":rel(cp),"counts_sha256":br.counts_sha256,"meta_path":rel(mpath),"meta_sha256":br.meta_sha256})
    return out,used

def mask60(row_locator:str,q:int,op:int)->np.ndarray:
    assert G_STATES is not None
    eligible=np.flatnonzero(G_STATES[op]==1).astype(np.int32);eligible=eligible[eligible!=q]
    prefix=f"{SEED}|{row_locator}|{q}|".encode(); keys=np.empty(len(eligible),np.uint64)
    full=None
    for i,j in enumerate(eligible):keys[i]=int.from_bytes(hashlib.sha256(prefix+str(int(j)).encode()).digest()[:8],"big")
    k=len(eligible)*60//100
    if k<=0:raise RuntimeError("STOP_F1_NUISANCE_MASK_SEMANTIC_MISMATCH")
    part=np.argpartition(keys,k-1)[:k]; threshold=keys[part].max()
    if np.count_nonzero(keys==threshold)>1:
        full=sorted((hashlib.sha256(prefix+str(int(j)).encode()).digest(),int(j)) for j in eligible);selected=np.asarray([j for _,j in full[:k]],np.int32)
    else:selected=eligible[part]
    if q in selected or np.any(G_STATES[op,selected]!=1):raise RuntimeError("STOP_F1_NUISANCE_MASK_SEMANTIC_MISMATCH")
    return selected

def cell_calc(cell:str)->dict:
    rec=G_ROWS[cell];nul=G_ROWS[G_NULL[cell]];op=rec["operator"]
    if nul["operator"]!=op or nul["source"]!=rec["source"]:raise RuntimeError("null source/operator mismatch")
    vals=[]
    for q,program,rep in G_ASSIGN[cell]:
        u=mask60(rec["row_locator"],q,op); visible=np.zeros(41238,np.bool_);visible[u]=True
        rn=visible[rec["indices"]];nn=visible[nul["indices"]]
        rf=float(rec["counts"][rn].sum(dtype=np.int64)/rec["source_library"]);nf=float(nul["counts"][nn].sum(dtype=np.int64)/nul["source_library"])
        rz=float((len(u)-np.count_nonzero(rn))/len(u));nz=float((len(u)-np.count_nonzero(nn))/len(u))
        if not (-1e-14<=rf<=1+1e-14 and -1e-14<=nf<=1+1e-14 and 0<=rz<=1 and 0<=nz<=1):raise RuntimeError("nuisance domain")
        vals.append((rf-nf,rz-nz,q,program,rep,hashlib.sha256(np.sort(u).astype("<i4").tobytes()).hexdigest()))
    if len(vals)!=16:raise RuntimeError("assignment hierarchy")
    return {"cell":cell,"delta_visible":float(np.mean([v[0] for v in vals])),"delta_zero":float(np.mean([v[1] for v in vals])),"pairs":vals}

def v8_gate(rows:dict[str,dict])->dict:
    sel=pd.read_csv(V8_SELECTION).sort_values("selection_row")
    with np.load(V8_PAYLOAD,allow_pickle=False) as z: expected=np.asarray(z["normalized_values"]);st=np.asarray(z["observation_states"])
    maxabs=0.;round_fail=0
    for i,r in enumerate(sel.itertuples(index=False)):
        x=np.zeros(41238,np.float32);rr=rows[str(r.canonical_cell_id)];x[rr["indices"]]=rr["normalized"]
        maxabs=max(maxabs,float(np.max(np.abs(x-expected[i]))));back=np.rint(np.expm1(x.astype(np.float64))*rr["source_library"]/10000).astype(np.int64)
        raw=np.zeros(41238,np.int64);raw[rr["indices"]]=rr["counts"];round_fail+=int(np.count_nonzero(back!=raw))
        if not np.array_equal(st[i],G_STATES[int(r.operator_index)]):raise RuntimeError("STOP_F1_NUISANCE_MASK_SEMANTIC_MISMATCH")
    if maxabs!=0 or round_fail:raise RuntimeError("STOP_F1_NUISANCE_COUNT_ROUNDTRIP_FAILURE")
    return {"status":"PASS","cells":84,"operators":int(sel.operator_index.nunique()),"max_abs_normalized_vs_v8":maxabs,"integer_roundtrip_failures":round_fail}

def main()->None:
    ap=argparse.ArgumentParser();ap.add_argument("--workers",type=int,default=max(1,min(16,os.cpu_count() or 1)));a=ap.parse_args()
    if FINAL.exists():raise RuntimeError("final output already exists")
    STAGING.mkdir(parents=True,exist_ok=True)
    bad={rel(p):(sha(p),h) for p,h in EXPECTED.items() if not p.is_file() or sha(p)!=h}
    if bad:raise RuntimeError("STOP_PROVENANCE_OR_FIREWALL "+repr(bad))
    assignments=pd.read_csv(ASSIGN,dtype={"canonical_cell_id":str,"donor_id":str});null=pd.read_csv(NULL_MAP,dtype=str)
    cells=json.loads(CELL_AUTH.read_text(encoding="utf-8"))["selected_rows"];cellmeta={r["canonical_cell_id"]:r for r in cells}
    if len(assignments)!=44496 or len(cellmeta)!=2781 or len(null)!=2781:raise RuntimeError("population geometry")
    global G_STATES,G_NULL,G_ASSIGN,G_ROWS
    with np.load(STATES,allow_pickle=False) as z:G_STATES=np.asarray(z["states"],np.uint8)
    G_NULL=dict(zip(null.recipient_canonical_cell_id,null.source_canonical_cell_id))
    G_ASSIGN=defaultdict(list)
    for r in assignments.itertuples(index=False):G_ASSIGN[r.canonical_cell_id].append((int(r.selected_query_address),str(r.program),int(r.draw_replicate)))
    v8cells=set(pd.read_csv(V8_SELECTION,dtype=str).canonical_cell_id);targets=set(cellmeta)|set(G_NULL.values())|v8cells
    loc=locate_rows(targets);G_ROWS,used=load_rows(loc)
    vg=v8_gate(G_ROWS)
    if os.name=="posix" and a.workers>1:
        with mp.get_context("fork").Pool(a.workers) as pool:calc=pool.map(cell_calc,sorted(cellmeta),chunksize=8)
    else:calc=[cell_calc(c) for c in sorted(cellmeta)]
    bycalc={r["cell"]:r for r in calc}

    donors=sorted(assignments.donor_id.unique());sources=pd.read_csv(REGISTRY,dtype=str).study_id.drop_duplicates().tolist()
    if sources!=["HVS","NPH52","SEA_AD"]:raise RuntimeError("source registry order")
    unique=assignments.drop_duplicates("canonical_cell_id").copy();weights={r.canonical_cell_id:int(r.cell_weight_numerator)/int(r.cell_weight_denominator) for r in unique.itertuples(index=False)}
    donor_mass={d:sum(weights[c] for c in unique.loc[unique.donor_id.eq(d),"canonical_cell_id"]) for d in donors}
    if max(abs(x-1) for x in donor_mass.values())>1e-14:raise RuntimeError("donor mass")
    support=np.count_nonzero(G_STATES==1,axis=1)
    columns=[f"source_{s}" for s in sources]+[f"operator_mix_{o:03d}" for o in range(42)]+["recipient_physical_support","recipient_depth","correct_minus_null_visible_depth","correct_minus_null_measured_zero_rate"]
    matrix=np.zeros((104,len(columns)),np.float64)
    for di,d in enumerate(donors):
        dcells=unique.loc[unique.donor_id.eq(d),"canonical_cell_id"].tolist();src=unique.loc[unique.donor_id.eq(d),"source"].unique().tolist()
        if len(src)!=1:raise RuntimeError("donor source")
        matrix[di,sources.index(src[0])]=1.
        for c in dcells:
            w=weights[c];m=cellmeta[c];op=int(m["operator_index"]);matrix[di,3+op]+=w;matrix[di,45]+=w*support[op];matrix[di,46]+=w*G_ROWS[c]["source_library"];matrix[di,47]+=w*bycalc[c]["delta_visible"];matrix[di,48]+=w*bycalc[c]["delta_zero"]
    if np.max(np.abs(matrix[:,3:45].sum(1)-1))>1e-14:raise RuntimeError("operator mixture mass")
    root=semantic_root(donors,columns,matrix)
    (STAGING/"F1_NUISANCE_DONOR_DESIGN_F64LE.bin").write_bytes(matrix.astype("<f8").tobytes())
    report=pd.DataFrame(matrix,columns=columns);report.insert(0,"donor_id",donors)
    for col in columns:report[col+"__float64_hex"]=[float(x).hex() for x in report[col]]
    report.to_csv(STAGING/"F1_NUISANCE_DONOR_DESIGN.csv",index=False,lineterminator="\n")
    pair_rows=[]
    for r in calc:
        for dv,dz,q,p,rep,mh in r["pairs"]:pair_rows.append({"canonical_cell_id":r["cell"],"query_address":q,"program":p,"draw_replicate":rep,"delta_visible_depth":dv,"delta_measured_zero_rate":dz,"recipient_u60_sorted_index_sha256":mh})
    pd.DataFrame(pair_rows).to_csv(STAGING/"F1_NUISANCE_CELL_ASSIGNMENT_COMPONENTS.csv.gz",index=False,compression="gzip",lineterminator="\n")
    pd.DataFrame(used).to_csv(STAGING/"F1_NUISANCE_EXPRESSION_BLOCKS_USED.csv",index=False,lineterminator="\n")

    history={"status":"PASS_HISTORICAL_PRIMITIVES_RECOVERED","physical_support":{"path":"scripts/v4/derive_full104_phase2_shared_state.py","sha256":EXPECTED[ROOT/'scripts/v4/derive_full104_phase2_shared_state.py'],"lines":"370-371","symbol":"scalar_support / scalar_measured_addresses","formula":"count_nonzero(states == MEASURED_SCALAR, axis=1)"},"normalization":{"materializer":{"path":"scripts/v4/materialize_full104_phase2_expression.py","sha256":EXPECTED[ROOT/'scripts/v4/materialize_full104_phase2_expression.py'],"source_library_lines":"215-240, 298"},"audit":{"path":"scripts/v4/audit_full104_phase2_capacity_and_materialization.py","sha256":EXPECTED[ROOT/'scripts/v4/audit_full104_phase2_capacity_and_materialization.py'],"lines":"85-100"},"feature_consumer":{"path":"scripts/v4/build_full104_phase2_multiview_features.py","sha256":EXPECTED[ROOT/'scripts/v4/build_full104_phase2_multiview_features.py'],"lines":"168","formula":"log1p(raw_count*10000/source_library) exactly once"},"inverse":"round(expm1(x)*source_library/10000)"},"weights":{"assignment_sha256":EXPECTED[ASSIGN],"cell_weight_semantic_root":"018d80428c25a0060168a942ca03dc9e814783463cc077e3661008ba5f7b5eeb","a_dc":"1/(|O_d|*n_do)","operator_mass":"sum a_dc within donor/operator","max_donor_operator_mass_sum_error":float(np.max(np.abs(matrix[:,3:45].sum(1)-1)))},"null":{"map_sha256":EXPECTED[NULL_MAP],"same_source_operator":True,"donor_cell_distinct":True,"recipient_mask_query_retained":True,"count_u_correct_minus_count_u_null":0},"older_conflicting_exact_f1_equation_found":False}
    dump(STAGING/"F1_NUISANCE_HISTORICAL_RECOVERY.json",history)
    contract=CONTRACT_MD
    (STAGING/"F1_NUISANCE_FORMULA_CONTRACT.md").write_text(contract,encoding="utf-8")
    schema={"schema":"f1-nuisance-column-schema-v1","donor_order":donors,"columns":columns,"shape":[104,len(columns)],"dtype":"IEEE-754 float64","byte_order":"little","layout":"C","standardization":"none before frozen downstream centering","source_registry_order":sources,"semantic_root_grammar":"domain NUL; uint32_le sequence lengths; each UTF8 item uint32_le byte length+bytes; uint64_le shape; C-order little-endian float64 bytes"}
    dump(STAGING/"F1_NUISANCE_COLUMN_SCHEMA.json",schema)
    authority={"status":"PROSPECTIVE_PRE_OUTCOME_FROZEN_AWAITING_INDEPENDENT_VALIDATION","semantic_root_sha256":root,"binary_sha256":sha(STAGING/"F1_NUISANCE_DONOR_DESIGN_F64LE.bin"),"report_csv_sha256":sha(STAGING/"F1_NUISANCE_DONOR_DESIGN.csv"),"assignment_components_sha256":sha(STAGING/"F1_NUISANCE_CELL_ASSIGNMENT_COMPONENTS.csv.gz"),"source_library_rows":len(G_ROWS),"recipient_rows":2781,"null_rows":2781,"v8_roundtrip":vg,"model_outcomes_read":False,"encoder_or_model_imported":False,"training_or_ema":False}
    dump(STAGING/"F1_NUISANCE_DONOR_DESIGN_AUTHORITY.json",authority)
    dump(STAGING/"F1_NUISANCE_ADVERSARIAL.json",{"status":"PENDING_INDEPENDENT_VALIDATION"});dump(STAGING/"F1_NUISANCE_INDEPENDENT_VALIDATION.json",{"status":"PENDING"})
    print(json.dumps({"status":"PRODUCTION_NUISANCE_DESIGN_COMPLETE","semantic_root":root,"workers":a.workers,"blocks":len(used),"v8":vg}))

CONTRACT_MD='''# F1 nuisance formula contract v1\n\nThis prospective, outcome-blind contract recovers historical dataset primitives and freezes only the two previously unspecified paired quantities. Physical support for operator `o` is `count_g[state[o,g]==MEASURED_SCALAR]`. Sequencing depth is the raw full-source `source_library L` used by `x=log1p(10000*c/L)`; integer counts are recovered as `round(expm1(x)*L/10000)` and must round-trip exactly. Cell weight is `a_dc=1/(|O_d| n_do)` and `m_do=sum_{c in(d,o)}a_dc`.\n\nAt the frozen primary 60% recipient evidence mask `U`, `visible_read_fraction(r,U)=sum_{g in U}c_rg/L_r` and `measured_zero_rate(r,U)=count_{g in U}[c_rg=0]/|U|`. Correct-minus-null quantities subtract the frozen matched-null source value using its own library and the identical recipient U. For each cell, average exactly eight protected programs times two PPS draws, then aggregate cells with `a_dc`.\n\nThe 104-row matrix contains source one-hots in frozen registry order HVS,NPH52,SEA_AD; operator masses 000..041; weighted recipient physical support; weighted recipient source library; weighted paired visible-read-fraction delta; weighted paired measured-zero-rate delta. No pooled-cell weighting and no pre-centering variance standardization are permitted. The existing downstream centering, lexicographic rank selection, numerical rank tolerance, HC3, df, and cross-source rule remain unchanged.\n'''

if __name__=="__main__":main()
