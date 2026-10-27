#!/usr/bin/env python3
"""Fail-closed checks for the compact, non-deciding E2G source receipt."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
from pathlib import Path

EXPECTED_STAGE75_BLOB="87117c485c25f9c7295a6ac4ba5ca48b45c844aa"
HEADERS=["gene","MAC_U","MAC_LPS1","MAC_LPS4","SC_MAC3","SC_MAC1","BRAIN","SC_CORONARY"]
TOTALS=[190,194,199,197,225,62,273]
DISTAL=[59,60,65,60,77,23,106]
SOURCE_TOTALS=[84593,85719,84048,52580,57159,62378,70980]
SOURCE_IDS=[
 "inflammatory_macrophage_ENCSR593WXK",
 "inflammatory_macrophage_ENCSR643ZGR",
 "inflammatory_macrophage_ENCSR226JLK",
 "Macrophage","Immune_monocyte_1","brain_ENCSR344FLH","Stitziel_hCA_Myeloid",
]


class AuditError(ValueError):
    pass


def load_csv(path: Path):
    with path.open(encoding="utf-8",newline="") as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=HEADERS:
            raise AuditError("Fixed source-column order drift")
        rows=list(reader)
    if len(rows)!=27:
        raise AuditError("Target gene row count drift")
    genes=[r["gene"] for r in rows]
    if len(set(genes))!=27 or genes!=sorted(genes):
        raise AuditError("Target gene identities not uniquely sorted")
    vals=[]
    for r in rows:
        try:
            v=[int(r[k]) for k in HEADERS[1:]]
        except (TypeError,ValueError,KeyError) as e:
            raise AuditError("Malformed count") from e
        if any(t<0 for t in v):
            raise AuditError("Negative count")
        vals.append(v)
    return genes,vals


def check(stage75: Path, counts_csv: Path, distal_csv: Path, receipt_path: Path):
    frozen=stage75.read_bytes()
    git_sha=hashlib.sha1(b"blob "+str(len(frozen)).encode()+bytes([0])+frozen).hexdigest()
    if git_sha!=EXPECTED_STAGE75_BLOB:
        raise AuditError("Frozen Stage75 source changed")
    stage_rows=list(csv.DictReader(io.StringIO(frozen.decode("utf-8-sig"))))
    target_set={r["target_gene"] for r in stage_rows}
    if len(stage_rows)!=96 or len(target_set)!=27:
        raise AuditError("Stage75 identity/size drift")
    names, counts=load_csv(counts_csv)
    distal_names, distals=load_csv(distal_csv)
    if names!=distal_names or set(names)!=target_set:
        raise AuditError("Compact mirrors do not match frozen genes")
    if any(d>c for crow,drow in zip(counts,distals) for c,d in zip(crow,drow)):
        raise AuditError("Distal counts exceed all links")
    for table,expected in [(counts,TOTALS),(distals,DISTAL)]:
        actual=[sum(row[i] for row in table) for i in range(7)]
        if actual!=expected:
            raise AuditError(f"Mirror tally changed: {actual} vs {expected}")
    receipt=json.loads(receipt_path.read_text(encoding="utf-8"))
    rows=receipt.get("source_results")
    if not isinstance(rows,list) or [r.get("source_id") for r in rows]!=SOURCE_IDS:
        raise AuditError("Source identity/order drift")
    if any(r.get("total_thresholded_track_rows")!=SOURCE_TOTALS[i] or
           r.get("panel_prediction_rows")!=TOTALS[i] or
           r.get("panel_distal_ge_20kb_rows")!=DISTAL[i] or
           not re.fullmatch(r"[0-9a-f]{64}",str(r.get("source_sha256")))
           for i,r in enumerate(rows)):
        raise AuditError("Source receipt fields drifted")
    if receipt["execution"].get("conclusion")!="success" or receipt["execution"].get("hostile_tests_passed")!=10:
        raise AuditError("Execution did not retain exact original PASS")
    if (not receipt["results"].get("symbol_only") or
        receipt["results"].get("canonical_ensembl_identity_verified") is not False):
        raise AuditError("External symbol matches silently promoted to canonical")
    gate=receipt["hard_prohibitions"]
    if gate.get("tf_target_edge_validation") is not None or
       gate.get("selected_target_winner") is not None or
       any(gate.get(key) is not False for key in (
         "independent_microglia_validation","causality","disease_effect",
         "donor_level_inference","trajectory_inference","real_training","stage4"
       )):
        raise AuditError("Prohibited biological authority introduced")
    return {"result":"PASS_COMPACT_MIRRORS__SOURCE_PINNED__NO_BIOLOGICAL_AUTHORITY",
            "genes":27,"tracks":7,"counts":TOTALS,"distal_counts":DISTAL}


if __name__=="__main__":
    if len(sys.argv)!=5:
        raise SystemExit("Usage: stage75 counts.csv distal.csv receipt.json")
    print(json.dumps(check(*(Path(a) for a in sys.argv[1:])),indent=2))
