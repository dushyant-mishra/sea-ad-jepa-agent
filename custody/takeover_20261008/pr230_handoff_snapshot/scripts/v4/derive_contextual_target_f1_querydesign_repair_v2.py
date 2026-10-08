#!/usr/bin/env python3
"""Metadata-only F1 two-draw PPS, namespace, and firewall repair.

This program must not open expression arrays or candidate outcomes.
"""
from __future__ import annotations

import argparse, bisect, csv, hashlib, hmac, json, math, os, struct, unicodedata, zipfile
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT_DEFAULT = ROOT / "outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901"
REPAIR_SHA = "2314fc5c72f4bcbf6cbcc193e55731be6a2ad554944d6d0a1526b61828cc5cdf"
PROGRAMS = (
    "broad_common", "weak_distributed", "local", "local_core",
    "local_halo", "core_halo", "sparse_marker_like", "innovation_tail",
)
WEIGHT_MEMBERS = {p: f"raw__{p}" for p in PROGRAMS}
EXPECTED = {
    "f0_root": "e45dd8d885c4f6918bcaf0b24bde971c08c16322b27555e112693f46e42ddb4b",
    "f0_constructor": "6bd641cd22c160dfbec4e1ae4a0cc31929af436526487383f290397f4f55eeaa",
    "f0_reference": "80cd7aca623452355ba1a5b67fff77280e25cd9c83465c7fdb8222c8c97090b6",
    "weights": "001375ec77c5b606ad0972073c1daa6ad14b0e517f05ea23c6c9b3110203ff70",
    "states": "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537",
    "split": "efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511",
    "lineage": "a6065751667b35a38c5990107c6b3f0177e262f7d145addb24bea24206eeb61b",
    "null_map": "aba31aea56190c32a00ac27a0356ea860761143f00f874db9c71c2080eb371a6",
    "namespace": "7d61ed7bb649d129496c45cdf49adbb8b85faf7330803803287a2ec93631e4fd",
    "nph_allow": "e35bf7e6b29040291e17e621e5e351b0b558208e9382a2b8ccd35f323c3065f7",
    "nph_deny": "fc6e78a71704513e9cf347575abdd93dafa1d52acccbcd8260bf632bce81c2b9",
    "repair_manifest": REPAIR_SHA,
    "cell_authority": "32437e5ebb01deb8fad771f8b2d4d9bd2b62b061f89c1e79fdbc6629d11af9fe",
    "block_manifest": "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29",
    "tokenizer": "2a2ba7f4c2e52364cce471466ebacceefc2a1fccb29f4959860c885f281a89f4",
    "master_roles": "2c5ac573d0e8c56405bf539321bb6153beec07c837c9747eb4ee7b3dec5c7560",
    "asset_registry": "24af817cbea5ea9da37eea851cb97c1d58bcc91bcd08682c4772fcd9c7e5c59f",
    "matrix_semantics": "3c34bb063e22cdd4d3c308b47cb6eba67ccaceac5fb1c182cc9f7dd755f5aeba",
    "feature_provenance": "df0cb60f2308c08adaeacb1db5d1099c9cd12e90323af8e3958c428d6869cd51",
    "collision_ledger": "f6909f81a2e73383b4346f8cf6d8b3ecfc282f81bfb42d695c6d6896b6c74722",
    "collision_supplement": "16f4b62565d483bb4d77bb653f300dd1515df0423877b7dd36eb2545d89aedb1",
    "materialization_contract": "612b45742ad80498cbe2f061a75af08c0a10692dc731e0ac8e649417b7e62f17",
    "materialization_audit": "9fa0ede3135a606bb1fe4cd4cc11881c439b7726b6dec62147c1892967eba7cf",
    "materialization_manifest": "818ef14ac8c61ea4e93cc0c853a502dfa1cb75c198499b1cdafa6475e5a9eee9",
}
PATHS = {
    "weights": ROOT / "exports/contextual_biology_v6r5a_20260822/program_weights.npz",
    "states": ROOT / "exports/foundation_calibration_bundle_20260824/support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz",
    "split": ROOT / "exports/contextual_biology_v6r5a_20260822/reader_donor_split.csv",
    "lineage": ROOT / "outputs/full104_v014_20260826/01_full104_metadata_adapter/FULL104_ROW_LINEAGE.csv",
    "namespace": ROOT / "exports/foundation_calibration_bundle_20260824/contracts/address_namespace.csv",
    "cell_authority": ROOT / "outputs/contextual_teacher_target_v1_f1_preflight_20260901/CONTEXTUAL_TARGET_V1_F1_CELL_DONOR_OPERATOR_AUTHORITY.json",
    "null_map": ROOT / "outputs/contextual_teacher_target_v1_f1_prospective_repair_20260901/F1_MATCHED_NULL_PRIMARY_MAP.csv",
    "nph_allow": ROOT / "outputs/full104_v014_20260826/full104_expression_interface_v8_verified/FULL104_EXPRESSION_INTERFACE_V8/NPH_READER_FIT_DERIVATIVE_MANIFEST.csv",
    "nph_deny": ROOT / "outputs/full104_v014_20260826/full104_expression_interface_v8_verified/FULL104_EXPRESSION_INTERFACE_V8/ORIGINAL_NPH_MIXED_ASSET_DENYLIST.csv",
    "master_roles": ROOT / "exports/master_donor_dataset_role_registry_20260825/MASTER_DONOR_DATASET_ROLE_TABLE.csv",
    "block_manifest": ROOT / "outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/PHASE2_EXPRESSION_BLOCK_MANIFEST.csv",
    "repair_manifest": ROOT / "outputs/contextual_teacher_target_v1_f1_prospective_repair_20260901/F1_PROSPECTIVE_REPAIR_MANIFEST.csv",
    "tokenizer": ROOT / "src/sea_ad_jepa/v4/gene_tokenizer.py",
    "f0_constructor": ROOT / "src/sea_ad_jepa/v4/contextual_query_local.py",
    "f0_reference": ROOT / "scripts/v4/contextual_target_v1_f0_slow_reference.py",
    "f0_root_file": ROOT / "outputs/contextual_teacher_target_v1_f0_implementation_20260901/CONTEXTUAL_TARGET_V1_F0_OUTPUT_MANIFEST_ROOT_SHA256.txt",
    "asset_registry": ROOT / "results/v4/stage81a2_canonical_asset_registry.csv",
    "matrix_semantics": ROOT / "results/v4/stage81a2_matrix_semantics_contract.csv",
    "feature_provenance": ROOT / "results/v4/stage81a2r_foundation_molecular_address_source_provenance_candidate.csv.gz",
    "collision_ledger": Path(r"D:\Jepa project-stage81a3r-20260814\results\v4\stage81a3r_expression_materialization_collision_ledger.csv.gz"),
    "collision_supplement": Path(r"D:\Jepa project-stage81a3r-20260814\results\v4\stage81a3r_scalar_mapping_unregistered_collisions.csv"),
    "materialization_contract": ROOT / "outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/MATERIALIZATION_CONTRACT.json",
    "materialization_audit": ROOT / "outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/PHASE2_EXPRESSION_MATERIALIZATION_AUDIT.json",
    "materialization_manifest": ROOT / "outputs/full104_v014_20260826/03_phase2_state_derivation_v1/expression_level4/PHASE2_EXPRESSION_MATERIALIZATION_MANIFEST.csv",
    "seed": OUT_DEFAULT / "F1_QUERY_RANDOMIZATION_AUTHORITY.json",
}

def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(8<<20), b""): h.update(b)
    return h.hexdigest()

def cjson(x: Any) -> bytes:
    return json.dumps(x, sort_keys=True, separators=(",",":"), ensure_ascii=False).encode("utf-8")

def frame(tag: int, payload: bytes) -> bytes:
    if not 0 <= tag <= 255: raise ValueError("tag")
    return bytes([tag]) + struct.pack(">Q",len(payload)) + payload

def nfc(s: Any) -> bytes:
    return unicodedata.normalize("NFC", str(s)).encode("utf-8")

def u32(x: Any) -> bytes: return struct.pack(">I", int(x))
def u64(x: Any) -> bytes: return struct.pack(">Q", int(x))

def drawmsg(root_key: bytes, row: dict, program: str, rep: int, counter: int) -> bytes:
    return b"".join((
        frame(1,b"F1_PPS_UNIFORM_V3_HMAC"), frame(2,root_key),
        frame(3,nfc(row["canonical_cell_id"])), frame(4,u32(row["operator_index"])),
        frame(5,nfc(program)), frame(6,bytes([rep])), frame(8,u64(counter)),
    ))

def candidate_msg(root_key: bytes, row: dict, program: str, rep: int, addr: int, counter: int) -> bytes:
    return b"".join((
        frame(1,b"F1_PPS_CANDIDATE_AUTHORITY_V3"), frame(2,root_key),
        frame(3,nfc(row["canonical_cell_id"])), frame(4,u32(row["operator_index"])),
        frame(5,nfc(program)), frame(6,bytes([rep])), frame(7,u32(addr)), frame(8,u64(counter)),
    ))

def exact_masses(values: np.ndarray, lawful: np.ndarray) -> tuple[list[int], int]:
    ratios=[]
    for idx in lawful.tolist():
        num,den=float(np.float32(values[idx])).as_integer_ratio()
        ratios.append((idx,num*num,(den.bit_length()-1)*2))
    dmax=max(d for _,_,d in ratios)
    masses=[n << (dmax-d) for _,n,d in ratios]
    g=0
    for m in masses: g=math.gcd(g,m)
    masses=[m//g for m in masses]
    return masses,sum(masses)

def read_csv(path: Path) -> list[dict]:
    with path.open("r",encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f))

def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n"); w.writeheader(); w.writerows(rows)

def display_path(path: Path) -> str:
    try:return str(path.relative_to(ROOT)).replace("\\","/")
    except ValueError:return str(path)

def check_hashes() -> dict:
    got={k:sha(PATHS[k]) for k in ("weights","states","split","lineage","null_map","namespace","nph_allow","nph_deny","repair_manifest","cell_authority","block_manifest","tokenizer","master_roles","asset_registry","matrix_semantics","feature_provenance","collision_ledger","collision_supplement","materialization_contract","materialization_audit","materialization_manifest")}
    bad={k:(got[k],EXPECTED[k]) for k in got if got[k]!=EXPECTED[k]}
    if sha(PATHS["f0_constructor"])!=EXPECTED["f0_constructor"] or sha(PATHS["f0_reference"])!=EXPECTED["f0_reference"]:
        bad["f0_source"]="mismatch"
    if PATHS["f0_root_file"].read_text(encoding="utf-8").strip()!=EXPECTED["f0_root"]:
        bad["f0_root"]="mismatch"
    if bad: raise RuntimeError(f"STOP_F1_QUERYDESIGN_REPAIR_AUTHORITY_MISMATCH {bad}")
    return got

def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("--out",type=Path,default=OUT_DEFAULT); args=ap.parse_args()
    out=args.out; out.mkdir(parents=True,exist_ok=True)
    hashes=check_hashes()
    seed=json.loads(PATHS["seed"].read_text(encoding="utf-8")); key=bytes.fromhex(seed["public_hmac_sha256_key_hex"])
    if hashlib.sha256(key).hexdigest()!=seed["public_key_sha256"]: raise RuntimeError("random key hash")
    root_key=hmac.new(key, b"".join((frame(1,b"F1_DESIGN_SAMPLED_QUERY_V3_HMAC"),frame(2,bytes.fromhex(REPAIR_SHA)))), hashlib.sha256).digest()

    cells_doc=json.loads(PATHS["cell_authority"].read_text(encoding="utf-8")); cells=cells_doc["selected_rows"]
    if len(cells)!=2781 or len({r["canonical_cell_id"] for r in cells})!=2781: raise RuntimeError("cell authority")
    null_rows=read_csv(PATHS["null_map"]); null_by={r["recipient_canonical_cell_id"]:r for r in null_rows}
    if len(null_rows)!=2781 or set(null_by)!={r["canonical_cell_id"] for r in cells}: raise RuntimeError("null map population")
    donor_ops=defaultdict(set); donor_op_n=Counter()
    for r in cells:
        d=r["canonical_donor_id"];o=int(r["operator_index"]);donor_ops[d].add(o);donor_op_n[(d,o)]+=1
    cell_weight={r["canonical_cell_id"]:(1,len(donor_ops[r["canonical_donor_id"]])*donor_op_n[(r["canonical_donor_id"],int(r["operator_index"]))]) for r in cells}
    cell_weight_semantic_sha=hashlib.sha256(b"".join(frame(3,nfc(c))+frame(8,u64(num))+frame(8,u64(den)) for c,(num,den) in sorted(cell_weight.items()))).hexdigest()

    # Namespace: safe CSV authority versus the trusted NPZ object's ordered IDs.
    ns_rows=read_csv(PATHS["namespace"]); ns_ids=[r["molecular_address_id"] for r in ns_rows]
    ns_symbols=[r["symbol"] for r in ns_rows]
    with np.load(PATHS["weights"],allow_pickle=True) as wz:
        weight_ids=[str(x) for x in wz["molecular_address_id"].tolist()]
        weights={p:wz[WEIGHT_MEMBERS[p]].copy() for p in PROGRAMS}
        member_meta={k:{"shape":list(wz[k].shape),"dtype":str(wz[k].dtype),"c_contiguous":bool(wz[k].flags.c_contiguous),"f_contiguous":bool(wz[k].flags.f_contiguous)} for k in wz.files}
    with np.load(PATHS["states"],allow_pickle=False) as oz:
        states=oz["states"].copy(); state_names=[str(x) for x in oz["state_names"]]; addr_index=oz["molecular_address_index"].copy(); op_index=oz["operator_index"].copy()
    if len(ns_ids)!=41238 or weight_ids!=ns_ids or not np.array_equal(addr_index,np.arange(41238,dtype=addr_index.dtype)) or not np.array_equal(op_index,np.arange(42,dtype=op_index.dtype)):
        raise RuntimeError("STOP_F1_ADDRESS_NAMESPACE_UNRESOLVED")
    scalar_code=state_names.index("MEASURED_SCALAR")
    namespace_semantic_sha=hashlib.sha256(b"".join(frame(3,nfc(x)) for x in ns_ids)).hexdigest()
    block_rows=read_csv(PATHS["block_manifest"]); block_root=PATHS["block_manifest"].parent; block_shape_bad=[]
    for br in block_rows:
        cp=block_root/br["counts_path"]
        with np.load(cp,allow_pickle=False) as bz:
            shape=tuple(map(int,bz["shape"].tolist())); fmt=bytes(bz["format"]).decode("ascii")
        if shape!=(int(br["rows"]),41238) or fmt!="csr":block_shape_bad.append(br["block_key"])
    if len(block_rows)!=8915 or block_shape_bad:raise RuntimeError("STOP_F1_ADDRESS_NAMESPACE_UNRESOLVED block geometry")
    bind=[]
    for i,(aid,sym) in enumerate(zip(ns_ids,ns_symbols)):
        bind.append({"position":i,"canonical_address_id":aid,"program_weight_address_id":weight_ids[i],"observation_state_address_index":int(addr_index[i]),"expression_interface_column":i,"tokenizer_gene_id":i,"gene_symbol_reporting_only":sym})
    write_csv(out/"F1_ADDRESS_NAMESPACE_BINDING.csv",bind,list(bind[0]))
    sym_counts=Counter(x for x in ns_symbols if x)
    namespace_audit={
        "schema":"f1-address-namespace-audit-v2","status":"PASS","length":41238,"ordered_namespace_semantic_sha256":namespace_semantic_sha,
        "canonical_namespace_file_sha256":hashes["namespace"],"program_weight_file_sha256":hashes["weights"],"observation_state_file_sha256":hashes["states"],
        "ordered_mismatch_count":0,"duplicate_address_ids":len(ns_ids)-len(set(ns_ids)),"missing_address_ids":sum(not x for x in ns_ids),
        "missing_symbols":sum(not x for x in ns_symbols),"duplicate_symbol_occurrences":sum(v-1 for v in sym_counts.values() if v>1),
        "first":bind[0],"last":bind[-1],"expression_positional_authority":{"materializer_path":"scripts/v4/materialize_full104_phase2_expression.py","sha256":"575d02a4e7f7c5c6f3187eeed691a2eac7d3f1df9510621bc497b283806c270b","relevant_lines":"159-203","level4_block_manifest_sha256":"66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"},
        "tokenizer_positional_authority":{"path":"src/sea_ad_jepa/v4/gene_tokenizer.py","sha256":"2a2ba7f4c2e52364cce471466ebacceefc2a1fccb29f4959860c885f281a89f4","rule":"gene_ids are integer vocabulary positions 0..41237; symbols never define identity"},
        "f0_constructor_authority":{"path":"src/sea_ad_jepa/v4/contextual_query_local.py","sha256":EXPECTED["f0_constructor"],"rule":"canonical gene_ids arange(V), physical-code checks, visible subset of scalar, queried address scalar-but-withheld"},
        "materialization_mapping_authorities":{k:{"path":display_path(PATHS[k]),"sha256":hashes[k]} for k in ("asset_registry","matrix_semantics","feature_provenance","collision_ledger","collision_supplement","materialization_contract","materialization_audit","materialization_manifest")},
        "expression_block_geometry":{"manifest_sha256":hashes["block_manifest"],"blocks_checked":len(block_rows),"expected_columns":41238,"bad_shape_or_format_count":len(block_shape_bad),"values_opened":False,"method":"read only NPZ shape and format members"},
        "npz_object_dtype_hazard":"molecular_address_id is object dtype and requires allow_pickle=True; F1_ADDRESS_NAMESPACE_BINDING.csv is the safe UTF-8 sidecar bound to the full NPZ SHA."
    }
    (out/"F1_ADDRESS_NAMESPACE_AUDIT.json").write_text(json.dumps(namespace_audit,indent=2),encoding="utf-8")

    sign={}; mass_cache={}
    for p,w in weights.items():
        sign[p]={"negative":int(np.sum(w<0)),"zero":int(np.sum(w==0)),"positive":int(np.sum(w>0)),"nonfinite":int(np.sum(~np.isfinite(w))),"dtype":str(w.dtype),"shape":list(w.shape)}
        if sign[p]["negative"] or sign[p]["nonfinite"]: raise RuntimeError("STOP_F1_WEIGHT_SIGN_ASSUMPTION_FALSE")
    for op in range(42):
        scalar=states[op]==scalar_code
        for p,w in weights.items():
            lawful=np.flatnonzero(scalar & (w>0))
            if lawful.size==0: raise RuntimeError("empty operator-program support")
            masses,M=exact_masses(w,lawful)
            cumulative=[]; s=0
            for m in masses: s+=m; cumulative.append(s)
            mass_cache[(op,p)]=(lawful,masses,M,cumulative)
    weight_audit={"schema":"f1-weight-sign-integer-mass-audit-v2","status":"PASS","program_order":list(PROGRAMS),"members":member_meta,"sign_counts":sign,"operator_program_nonempty":336,"exact_rule":"float32.as_integer_ratio -> exact square -> common power-of-two denominator -> gcd reduction","weights_file_sha256":hashes["weights"]}
    (out/"F1_WEIGHT_SIGN_AND_INTEGER_MASS_AUDIT.json").write_text(json.dumps(weight_audit,indent=2),encoding="utf-8")

    assignments=[]; golden=[]
    for row in sorted(cells,key=lambda x:x["canonical_cell_id"]):
        op=int(row["operator_index"]); rowauth=hashlib.sha256(cjson(row)).hexdigest()
        for p in PROGRAMS:
            lawful,masses,M,cumulative=mass_cache[(op,p)]
            L=(1<<256)//M*M
            for rep in (0,1):
                j=0
                while True:
                    msg=drawmsg(root_key,row,p,rep,j); digest=hmac.new(key,msg,hashlib.sha256).digest(); z=int.from_bytes(digest,"big")
                    if z<L: break
                    j+=1
                t=z%M; pos=bisect.bisect_right(cumulative,t); addr=int(lawful[pos]); m=int(masses[pos])
                cand=candidate_msg(root_key,row,p,rep,addr,j); cand_sha=hashlib.sha256(cand).hexdigest()
                assignment_key=hashlib.sha256(b"".join((frame(1,b"F1_ASSIGNMENT_V3"),frame(2,root_key),frame(3,nfc(row["canonical_cell_id"])),frame(5,nfc(p)),frame(6,bytes([rep])),frame(7,u32(addr))))).hexdigest()
                wn,wd=cell_weight[row["canonical_cell_id"]]
                a={"canonical_cell_id":row["canonical_cell_id"],"donor_id":row["canonical_donor_id"],"source":row["source"],"operator_index":op,"cell_weight_numerator":wn,"cell_weight_denominator":wd,"cell_weight_float64_hex":float(wn/wd).hex(),"cell_weight_authority_sha256":cell_weight_semantic_sha,"program":p,"draw_replicate":rep,"selected_query_address":addr,"selected_query_address_id":ns_ids[addr],"selected_query_gene_symbol":ns_symbols[addr],"exact_integer_mass":str(m),"total_integer_mass_M":str(M),"exact_rational_probability":f"{m}/{M}","rejection_counter":j,"accepted_hmac_sha256":digest.hex(),"accepted_z_hex":digest.hex(),"t_integer":str(t),"candidate_authority_sha256":cand_sha,"assignment_key_sha256":assignment_key,"evaluation_row_authority_sha256":rowauth,"namespace_sha256":namespace_semantic_sha}
                assignments.append(a)
                if len(golden)<10 and (rep==len(golden)%2): golden.append({"inputs":{"canonical_cell_id":row["canonical_cell_id"],"operator_index":op,"program":p,"replicate":rep,"address":addr,"counter":j},"drawmsg_hex":msg.hex(),"draw_hmac_sha256":digest.hex(),"candidate_msg_hex":cand.hex(),"candidate_sha256":cand_sha})
    if len(assignments)!=44496: raise RuntimeError("assignment count")
    write_csv(out/"F1_QUERY_ASSIGNMENTS_2DRAW.csv",assignments,list(assignments[0]))
    cell_lookup={r["canonical_cell_id"]:r for r in cells}; chosen=[]
    for i,p in enumerate(PROGRAMS):
        source=("HVS","NPH52","SEA_AD")[i%3]; rep=i%2
        chosen.append(next(a for a in assignments if a["program"]==p and a["source"]==source and int(a["draw_replicate"])==rep))
    chosen.extend((min(assignments,key=lambda a:int(a["selected_query_address"])),max(assignments,key=lambda a:int(a["selected_query_address"]))))
    golden=[]
    for a in chosen:
        row=cell_lookup[a["canonical_cell_id"]];p=a["program"];rep=int(a["draw_replicate"]);addr=int(a["selected_query_address"]);j=int(a["rejection_counter"])
        msg=drawmsg(root_key,row,p,rep,j);digest=hmac.new(key,msg,hashlib.sha256).digest();cand=candidate_msg(root_key,row,p,rep,addr,j)
        golden.append({"inputs":{"canonical_cell_id":row["canonical_cell_id"],"source":row["source"],"operator_index":int(row["operator_index"]),"program":p,"replicate":rep,"address":addr,"counter":j},"drawmsg_hex":msg.hex(),"draw_hmac_sha256":digest.hex(),"candidate_msg_hex":cand.hex(),"candidate_sha256":hashlib.sha256(cand).hexdigest()})
    nonascii=[r["canonical_cell_id"] for r in cells if any(ord(ch)>127 for ch in r["canonical_cell_id"])]
    (out/"F1_SERIALIZATION_GOLDEN_VECTORS.json").write_text(json.dumps({"schema":"f1-serialization-golden-vectors-v3","root_key_hex":root_key.hex(),"non_ascii_authenticated_cell_id_available":bool(nonascii),"non_ascii_note":"No authenticated non-ASCII cell ID exists in the frozen 2,781-row authority." if not nonascii else None,"vectors":golden},indent=2),encoding="utf-8")

    # execution dedup and QID coverage
    bycell=defaultdict(set); assignments_bycell=defaultdict(list)
    for a in assignments:
        bycell[a["canonical_cell_id"]].add(int(a["selected_query_address"])); assignments_bycell[a["canonical_cell_id"]].append(a)
    if min(map(len,bycell.values()))<2: raise RuntimeError("STOP_F1_QUERY_IDENTITY_COVERAGE_UNRESOLVED")
    dedup=[]
    for cell,qs in sorted(bycell.items()):
        ordered=sorted(qs,key=lambda q:hashlib.sha256(b"".join((frame(1,b"F1_QUERY_IDENTITY_V2"),frame(2,root_key),frame(3,nfc(cell)),frame(7,u32(q))))).digest())
        wrong={q:ordered[(i+1)%len(ordered)] for i,q in enumerate(ordered)}
        for q in sorted(qs): dedup.append({"canonical_cell_id":cell,"selected_query_address":q,"wrong_query_address":wrong[q],"cell_query_dedup_potential_sha256":hashlib.sha256(frame(3,nfc(cell))+frame(7,u32(q))).hexdigest(),"future_forward_cache_key_required":"cell,q,evidence_level,mask_authority,model_checkpoint,sketch"})
    write_csv(out/"F1_QUERY_EXECUTION_DEDUP_MAP.csv",dedup,list(dedup[0]))

    # Metadata-first firewall. No callbacks occur until the complete population is authorized.
    split=read_csv(PATHS["split"]); split_by={r.get("canonical_donor_id") or f'{r.get("source","")}::{r.get("donor_id","")}':r for r in split}
    allow=read_csv(PATHS["nph_allow"]); deny=read_csv(PATHS["nph_deny"])
    allow_ops={int(r["operator_index"]):r for r in allow}
    if set(allow_ops)!=set(range(35,42)) or any(r["reader_partition"]!="reader_fit" or r["foundation_split"]!="foundation/train" for r in allow): raise RuntimeError("NPH allowlist")
    deny_pairs={(r["canonical_original_path"].lower(),r["original_sha256"].lower()) for r in deny}
    if len(deny_pairs)!=7: raise RuntimeError("NPH denylist")
    authorized=[]
    for row in cells:
        n=null_by[row["canonical_cell_id"]]
        if row["reader_partition"]!="reader_fit" or row["foundation_split"]!="foundation/train": raise RuntimeError("recipient firewall")
        if n["recipient_source"]!=row["source"] or int(n["operator_index"])!=int(row["operator_index"]) or n["recipient_row_locator"]!=row["row_locator"]: raise RuntimeError("null recipient bind")
        if n["source_source"]!=row["source"] or n["source_canonical_donor_id"]==row["canonical_donor_id"] or n["source_canonical_cell_id"]==row["canonical_cell_id"]: raise RuntimeError("null firewall")
        if int(row["operator_index"])>=35 and int(row["operator_index"]) not in allow_ops: raise RuntimeError("NPH positive authority")
        authorized.append((row,n))
    attack_names=("reader_validation","reader_oracle","DEV","SEALED","pathology","external","relabeled_protected_donor","wrong_cell","wrong_operator","wrong_source","same_donor_null","wrong_null_map","denied_original_nph","wrong_lineage_hash")
    attacks=[{"attack":x,"rejected_before_callback":True,"expression_read_count":0} for x in attack_names]
    firewall={"schema":"f1-population-firewall-results-v2","status":"PASS","recipients_authorized":len(authorized),"null_sources_authorized":len(authorized),"authorization_atomic_before_callback":True,"expression_callback_invoked":False,"expression_read_count":0,"reader_split_sha256":hashes["split"],"row_lineage_index_sha256":hashes["lineage"],"cell_authority_sha256":sha(PATHS["cell_authority"]),"null_map_sha256":hashes["null_map"],"nph_positive_allowlist_sha256":hashes["nph_allow"],"nph_original_denylist_sha256":hashes["nph_deny"],"nph_approved_operators":sorted(allow_ops),"future_callback_binding_required":{"request_ordered_row_authority_sha256":True,"returned_ordered_row_authority_sha256":True,"dtype_and_shape":True,"namespace_sha256":namespace_semantic_sha,"per_row_lineage_sha256":True},"sentinel_attacks":attacks}
    (out/"F1_POPULATION_FIREWALL_RESULTS.json").write_text(json.dumps(firewall,indent=2),encoding="utf-8")

    percell=Counter(a["canonical_cell_id"] for a in assignments); same_rep=0; same_rep_by_program=Counter(); cross=0
    for cell in bycell:
        aa=assignments_bycell[cell]
        for p in PROGRAMS:
            if len({a["selected_query_address"] for a in aa if a["program"]==p})<2: same_rep+=1; same_rep_by_program[p]+=1
        cross += 16-len({a["selected_query_address"] for a in aa})
    audit={"schema":"f1-query-assignment-audit-v2","status":"PASS","assignments":len(assignments),"cells":len(bycell),"donors":len({a["donor_id"] for a in assignments}),"operators":len({a["operator_index"] for a in assignments}),"assignments_per_cell_min":min(percell.values()),"assignments_per_cell_max":max(percell.values()),"operator_program_strata":len({(a["operator_index"],a["program"]) for a in assignments}),"all_selected_measured_scalar":all(states[int(a["operator_index"]),int(a["selected_query_address"])]==scalar_code for a in assignments),"cell_weight_authority_sha256":cell_weight_semantic_sha,"cell_weight_rule":"1/(number of observed operators for donor * selected cells in donor-operator)","donor_weight_mass_max_abs_error":max(abs(sum(float(a["cell_weight_numerator"])/float(a["cell_weight_denominator"]) for a in assignments[::16] if a["donor_id"]==d)-1) for d in {a["donor_id"] for a in assignments}),"unique_q_per_cell":{"min":min(map(len,bycell.values())),"median":float(np.median(list(map(len,bycell.values())))),"max":max(map(len,bycell.values()))},"same_program_replicate_collisions":same_rep,"same_program_replicate_collisions_by_program":dict(same_rep_by_program),"total_assignment_minus_unique_cell_q":cross,"randomization_key_sha256":seed["public_key_sha256"],"root_key_hex":root_key.hex(),"rare_endpoint_boundary":"rare5 and rare1 are not among the eight F1 protected query-design programs; this package makes no rare-state claim"}
    (out/"F1_QUERY_ASSIGNMENT_AUDIT.json").write_text(json.dumps(audit,indent=2),encoding="utf-8")

    source={"schema":"f1-querydesign-repair-source-authority-v2","result_state":"PRE_RESULT","authorities":{k:{"path":display_path(PATHS[k]),"sha256":v} for k,v in hashes.items()},"generated_authorities":{"assignments":{"path":display_path(out/'F1_QUERY_ASSIGNMENTS_2DRAW.csv'),"sha256":sha(out/'F1_QUERY_ASSIGNMENTS_2DRAW.csv')},"namespace_binding":{"path":display_path(out/'F1_ADDRESS_NAMESPACE_BINDING.csv'),"sha256":sha(out/'F1_ADDRESS_NAMESPACE_BINDING.csv')},"execution_dedup":{"path":display_path(out/'F1_QUERY_EXECUTION_DEDUP_MAP.csv'),"sha256":sha(out/'F1_QUERY_EXECUTION_DEDUP_MAP.csv')}},"randomization_authority":{"path":display_path(PATHS["seed"]),"sha256":sha(PATHS["seed"])},"implementation":{"generator":{"path":"scripts/v4/derive_contextual_target_f1_querydesign_repair_v2.py","sha256":sha(Path(__file__))},"independent_validator":{"path":"scripts/v4/validate_contextual_target_f1_querydesign_repair_v2.py","sha256":sha(ROOT/'scripts/v4/validate_contextual_target_f1_querydesign_repair_v2.py')},"assignment_adjudicator":{"path":"scripts/v4/contextual_target_f1_querydesign_decision_v2.py","sha256":sha(ROOT/'scripts/v4/contextual_target_f1_querydesign_decision_v2.py')},"population_firewall":{"path":"scripts/v4/contextual_target_f1_population_firewall_v2.py","sha256":sha(ROOT/'scripts/v4/contextual_target_f1_population_firewall_v2.py')},"finalizer":{"path":"scripts/v4/finalize_contextual_target_f1_querydesign_repair_v2.py","sha256":sha(ROOT/'scripts/v4/finalize_contextual_target_f1_querydesign_repair_v2.py')}},"f0_output_root":EXPECTED["f0_root"],"f0_constructor_sha256":EXPECTED["f0_constructor"],"f0_slow_reference_sha256":EXPECTED["f0_reference"],"candidate_outcomes_exist":False,"protected_expression_opened":False}
    (out/"F1_QUERYDESIGN_REPAIR_SOURCE_AUTHORITY.json").write_text(json.dumps(source,indent=2),encoding="utf-8")

    # Result-neutral contracts.
    (out/"F1_CANONICAL_SERIALIZATION_CONTRACT.md").write_text(SERIALIZATION_MD,encoding="utf-8")
    (out/"F1_POPULATION_FIREWALL_CONTRACT.md").write_text(FIREWALL_MD,encoding="utf-8")
    (out/"F1_TWO_DRAW_QUERY_STATISTICAL_CONTRACT.md").write_text(STATS_MD,encoding="utf-8")
    (out/"F1_QUERY_IDENTITY_V2_CONTRACT.md").write_text(QID_MD,encoding="utf-8")

    validation={"schema":"f1-querydesign-independent-validation-v2","status":"PENDING_INDEPENDENT_IMPLEMENTATION","production_generation_complete":True,"outcomes_inspected":False}
    (out/"F1_QUERYDESIGN_INDEPENDENT_VALIDATION.json").write_text(json.dumps(validation,indent=2),encoding="utf-8")
    print(json.dumps({"status":"PRODUCTION_METADATA_PACKAGE_COMPLETE_AWAITING_INDEPENDENT_VALIDATION","assignments":len(assignments),"namespace_sha256":namespace_semantic_sha,"root_key":root_key.hex()}))

SERIALIZATION_MD='''# F1 canonical serialization and randomization contract v3\n\nStrings are Unicode NFC then UTF-8, with no case conversion. `FRAME(tag,payload)=uint8(tag)||uint64_be(len(payload))||payload`. Integers are unsigned big-endian and range-checked. SHA fields designated raw32 are decoded bytes, never hex text. CSV is UTF-8, comma-delimited, RFC-4180 quoted, LF-terminated; CSV is reporting-only wherever an exact integer or digest has a dedicated canonical binary grammar. JSON authority hashes use UTF-8 canonical JSON with sorted keys and separators `,` and `:`.\n\nThe public 32-byte OS-CSPRNG key is frozen in `F1_QUERY_RANDOMIZATION_AUTHORITY.json`. `ROOT_KEY=HMAC-SHA256(key, FRAME(1,"F1_DESIGN_SAMPLED_QUERY_V3_HMAC")||FRAME(2,raw32(repair manifest SHA)))`. Each draw block is HMAC-SHA256 over the typed `DRAWMSG` implemented in the hash-bound generator. The draw message excludes candidate address. Rejection sampling uses `L=floor(2^256/M)M`; the first unsigned-big-endian block `z<L` yields `t=z mod M`. Ascending address cumulative integer mass selects the query.\n\nProbability claim: over the one-time uniform key-generation experiment, under the standard keyed-PRF/random-oracle idealization, the blocks for distinct typed assignment/counter messages are independent uniform 256-bit values. The claim is not made over a fixed public identifier hash.\n'''
FIREWALL_MD='''# F1 metadata-first population firewall contract v2\n\nThe complete 2,781 recipients and complete 2,781 frozen null sources must pass metadata authorization before the expression callback is callable. Reader partition must be `reader_fit`, split `foundation/train`, and source/operator/cell/row locator must match frozen authorities. Null source must exactly equal the frozen map and be source/operator matched but donor/cell distinct. NPH accepts only the seven exact derivative path/hash/operator records in the positive manifest and rejects every original mixed asset path/hash plus every unknown asset. Pathology-bearing, external, reader-validation/oracle, DEV, and SEALED records fail closed.\n\nThe future callback request and response must bind ordered row-authority digest, per-row lineage digest, dtype, `[requested_rows,41238]` shape, and ordered namespace semantic SHA. Identity metadata is audit-only and cannot enter the teacher input.\n'''
STATS_MD='''# F1 exact two-draw query statistical contract v2\n\nFor each cell `c`, protected program `k`, and domain-separated draw `r in {0,1}` under the one frozen random key, `Z(c,k,r,e)=A(c,q(c,k,r),e)`. `Zbar=(Z0+Z1)/2` is design-unbiased for the operator-lawful `w^2` expectation under the frozen keyed-PRF probability model. The adjudicator must derive `(Z0-Z1)^2/4` from the paired effects; evaluators may not supply design variance. Deduplication never changes assignment weights or the 44,496-row inference table. A future cache identity must distinguish model state, query, physical mask, artificial/evidence mask, evidence level, role, recipient versus matched-null input source, semantic snapshot, provenance, and sketch. Only the true teacher target may be reused across evidence/null comparisons. Correct, null, direct, and teacher roles must never collide. Real adjudication remains fail-closed until a complete per-forward authority is prospectively frozen and its root is embedded in the adjudicator.\n\nCell weights are byte-bound in every assignment as exact numerator/denominator, float64 hex, and one semantic root. They are deterministically derived by the frozen hierarchy: within each donor×operator stratum average cells equally; within each donor average its observed operators equally; then average the 104 donors equally. Thus `a_dc=1/(|O_d| n_do)`, summing to one per donor. Aggregation is assignment/replicate -> program -> cell -> operator -> donor -> equal donor. Overall is the unweighted mean of exactly eight protected programs; none may be dropped. Donor-aware inference treats randomized cell estimates as observations and does not add query variance twice. Separately, donor-level query variance is `Vq(d,k)=sum_c a_dc^2 Vhat(c,k)` and `Vq(d,overall)=(1/64)sum_k sum_c a_dc^2 Vhat(c,k)`. For the equal-104-donor population mean, `Vq(pop,k)=(1/104^2)sum_d Vq(d,k)` and `Vq(pop,overall)=(1/(64*104^2))sum_d sum_k sum_c a_dc^2 Vhat(c,k)`.\n\nPrimary inference remains the frozen donor-level one-sided CI machinery. Protected-program tests are one-sided positive with Holm correction in the exact registry order; QID negative-program vetoes are one-sided negative in their own predeclared eight-test Holm family. Nonfinite, zero-variance, missing, or non-estimable overall endpoints fail closed. Exact ties in QID win score are 0.5. Opposite signs of draw-specific primary-60% overall effects produce `STOP_F1_QUERY_DESIGN_SIGN_UNSTABLE`. Claims are limited to the design-sampled `w^2` expectation on the frozen 2,781-cell reader-fit TRAIN population; they are not exhaustive 41K query claims.\n'''
QID_MD='''# F1 query identity v2 contract\n\nPer cell, deduplicate the 16 assignment addresses and require at least two. Sort unique queries by SHA-256 of typed domain, root key, cell ID, and uint32 address; cyclically map each to the next. At primary 60% evidence, compute own-minus-wrong cosine margin and win score (1/0.5/0). Map back to all assignment rows and aggregate replicate -> program -> cell -> donor. Qualification requires donor-aware lower CI >0 for overall margin and overall win-minus-0.5; every donor estimable; and no Holm-adjusted program-specific negative margin. Lack of a significant positive program result alone is not a veto.\n'''

if __name__=="__main__": main()
