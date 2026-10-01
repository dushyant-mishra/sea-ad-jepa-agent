#!/usr/bin/env python3
from __future__ import annotations
import csv,gzip,hashlib,json
from pathlib import Path
import numpy as np

TRUTH_TOKENS=("TRUTH","HIDDEN_TRUTH","z_reg_shared","z_reg_private","z_global")

def sha256(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def validate(root: Path):
    raw=root/"observable_raw"; e=[]
    if not raw.exists(): return ["RAW_ROOT_MISSING"]
    for p in raw.rglob("*"):
        if any(t.lower() in p.name.lower() for t in ("truth","hidden_truth")):
            e.append(f"TRUTH_FIREWALL_PATH:{p.name}")
    obs_path=raw/"OBSERVABLES.json"; man_path=raw/"MANIFEST.json"
    if not obs_path.exists(): e.append("OBSERVABLES_MISSING")
    if not man_path.exists(): e.append("MANIFEST_MISSING")
    if e: return e
    obs=json.loads(obs_path.read_text()); man=json.loads(man_path.read_text())
    for name,rec in man.get("files",{}).items():
        p=raw/name
        if not p.exists(): e.append(f"MANIFEST_FILE_MISSING:{name}"); continue
        if p.stat().st_size!=rec.get("bytes"): e.append(f"BYTE_MISMATCH:{name}")
        if sha256(p)!=rec.get("sha256"): e.append(f"DIGEST_MISMATCH:{name}")
    m=np.load(raw/obs["matrix_file"],allow_pickle=False)
    matrix=m["matrix"]; features=m["features"]; ftypes=m["feature_types"]; barcodes=m["barcodes"]; avail=m["availability"]
    if matrix.shape!=(len(features),len(barcodes)): e.append("MATRIX_AXIS_SHAPE_MISMATCH")
    if avail.shape!=matrix.shape: e.append("AVAILABILITY_SHAPE_MISMATCH")
    if len(set(barcodes.tolist()))!=len(barcodes): e.append("DUPLICATE_BARCODE")
    if len(set(features.tolist()))!=len(features): e.append("DUPLICATE_FEATURE")
    if obs.get("n_cells")!=len(barcodes): e.append("OBS_CELL_COUNT_MISMATCH")
    if obs.get("n_features")!=len(features): e.append("OBS_FEATURE_COUNT_MISMATCH")
    if int((ftypes=="Gene Expression").sum())!=obs.get("n_genes"): e.append("GENE_COUNT_MISMATCH")
    if int((ftypes=="Peaks").sum())!=obs.get("n_peaks"): e.append("PEAK_COUNT_MISMATCH")
    # Structural missingness must be explicitly masked. Zero values are allowed only because the mask distinguishes them.
    if not np.all(matrix[avail==0]==0): e.append("STRUCTURAL_MISSING_NONZERO")
    meta=[]
    with gzip.open(raw/obs["metadata_file"],"rt",newline="") as f:
        reader=csv.DictReader(f); meta=list(reader)
    if len(meta)!=len(barcodes): e.append("METADATA_ROW_COUNT_MISMATCH")
    meta_bc=[r["barcode"] for r in meta]
    if meta_bc!=barcodes.tolist(): e.append("METADATA_BARCODE_ORDER_OR_ID_MISMATCH")
    forbidden=set(obs.get("forbidden_selection_fields",[]))
    if not forbidden.issubset(set(meta[0].keys()) if meta else set()): e.append("FORBIDDEN_FIELD_DECLARATION_MISMATCH")
    return e

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument("root"); a=ap.parse_args()
    errors=validate(Path(a.root))
    if errors:
        print("\n".join(errors)); raise SystemExit(1)
    print("PASS")
