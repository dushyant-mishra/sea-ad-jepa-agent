#!/usr/bin/env python3
"""Fail-closed SHA-256 census of committed perturbation output binaries.

Only a verified Git checkout can issue a physical manifest. Distinguish source
uncompressed CSV digests from committed compressed bytes. No duplicate binaries.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT="analysis/therapeutic_perturbation_etl/outputs/"
REVIEWED_SOURCE_REF="4213dd73e9a017daf776e898c6c7c68edf345f7a"
# Reviewed committed compressed/raw byte sizes and 16-character digests.
EXPECTED={
    "gse178317/gse178317_cell_guide_umi_counts_v2.npz":(3121266,"170a16797d681124"),
    "gse178317/gse178317_cell_guide_assignments_v2.csv.gz":(227864,"87d032b6a4b84367"),
    "gse178317/gse178317_target_engagement_v2.csv":(2573,"c6d6f0013d791147"),
    "gse178317/gse178317_top_effects_v2.csv.gz":(22119,"b55bd4b22c51fcf1"),
    "gse178317/gse178317_vs_crisprbrain_engagement_v1.csv":(2231,"fff45935c994d3fb"),
    "crisprbrain/iTF_Microglia-Day-8-CROP-seq-CRISPRi.csv.gz":(13586532,"201e8fb28a63dfb9"),
    "crisprbrain/iTF-Microglia-CROP-seq-CRISPRi.csv.gz":(20358929,"58c48fa4400d469a"),
    "crisprbrain/iPSC-Microglia-CROP-seq-CRISPRi.csv.gz":(16133002,"818ae3c383811c94"),
    "crisprbrain/iTF-Microglia-CITE-seq-CRISPRi.csv.gz":(187443,"dcc204e858264e1e"),
    "crisprbrain/iPSC-Microglia-CITE-seq-CRISPRi.csv.gz":(188965,"d032364a457e1406"),
}
class IntegrityStop(ValueError):
    pass

def require(value,why):
    if not value:
        raise IntegrityStop(why)

def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda:fh.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def inventory(repo_root:Path,expected=None,require_git=True):
    expected=EXPECTED if expected is None else expected
    root=repo_root/ROOT
    observed={p.relative_to(root).as_posix() for p in root.rglob("*")
              if p.is_file() and p.suffix.lower() in (".csv",".gz",".npz")}
    require(observed==set(expected),
            "missing or extra committed output binaries: missing="+str(sorted(set(expected)-observed))
            +" extra="+str(sorted(observed-set(expected))))
    records=[]
    for short in sorted(expected):
        size,prefix=expected[short]
        path=root/short
        require(not path.is_symlink() and path.stat().st_size==size,
                "size or symlink violation: "+short)
        sha=digest(path)
        require(len(prefix)==16 and sha.startswith(prefix),
                "reviewed digest prefix mismatch: "+short)
        relative=ROOT+short
        blob=None
        if require_git:
            p=subprocess.run(["git","ls-files","--stage","--",relative],
                             cwd=repo_root,capture_output=True,text=True,check=True)
            parts=p.stdout.split()
            require(len(parts)==4 and parts[0]=="100644" and parts[3]==relative,
                    "file untracked or unexpected Git mode: "+short)
            blob=parts[1]
            live=subprocess.check_output(["git","hash-object","--",relative],
                                         cwd=repo_root,text=True).strip()
            require(blob==live,"working bytes differ from indexed Git blob: "+short)
        records.append({"repo_relative_path":relative,
                        "exact_bytes":size,"sha256":sha,"git_blob_sha1":blob,
                        "source_or_regeneration":"reviewed_PR77_physical_output"})
    return {"schema":"JEPA_PERTURBATION_COMMITTED_OUTPUT_SHA256_V1",
            "reviewed_source_ref":REVIEWED_SOURCE_REF,
            "scope":"COMMITTED_DEVELOPMENT_BINARIES_ONLY",
            "source_git_blob_verified":bool(require_git),
            "n_committed_output_binaries":len(records),
            "files":records,
            "regenerate_on_demand_neuron_ipsc":4,
            "uncommitted_reference_tables_included":False,
            "biological_validation_authorized":False,
            "jepa_training_authorized":False}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root",default=".")
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    dst=Path(a.out)
    require(not dst.exists(),"refuse existing manifest output")
    result=inventory(Path(a.repo_root).resolve())
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"n":result["n_committed_output_binaries"],
                      "files":[(a["repo_relative_path"],a["sha256"]) for a in result["files"]]}))
if __name__=="__main__":
    main()
