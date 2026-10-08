#!/usr/bin/env python3
from __future__ import annotations
import json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CONTRACT=ROOT/"results/v64/V70_MACHA_SCENICPLUS_RETURN_MANIFEST_CONTRACT_V1.json"

HEX64=re.compile(r"^[0-9a-f]{64}$")

def load_contract(): return json.loads(CONTRACT.read_text())

def validate(manifest, contract=None):
    c=contract or load_contract(); e=[]
    for k in c["required_top_level"]:
        if k not in manifest: e.append(f"MISSING_TOP_LEVEL:{k}")
    if e:return e
    acq=manifest["acquisition"]
    for sec in ("matrix","metadata","fragments"):
        obj=acq.get(sec,{})
        for k in c["acquisition_required"][sec]:
            if k not in obj:e.append(f"MISSING_ACQUISITION:{sec}:{k}")
        if obj.get("sha256") and not HEX64.match(str(obj["sha256"])):
            e.append(f"BAD_SHA256:{sec}")
        if obj.get("bytes") is not None and int(obj["bytes"])<=0:
            e.append(f"BAD_BYTES:{sec}")
    if acq.get("genome_build")!=c["acquisition_required"]["genome_build"]:
        e.append("GENOME_BUILD_NOT_HG38")
    pop=manifest["development_population"]
    for k in c["development_population_required"]:
        if k not in pop:e.append(f"MISSING_DEVELOPMENT_POPULATION:{k}")
    if pop.get("diagnosis_pathology_used_for_network_construction") is not False:
        e.append("DIAGNOSIS_PATHOLOGY_MUST_NOT_DEFINE_NETWORK")
    exclusions={str(x) for x in pop.get("prospective_overlap_exclusions",[])}
    if not {"1224","1230","1238"}.issubset(exclusions):
        e.append("REQUIRED_PROSPECTIVE_OVERLAP_EXCLUSIONS_MISSING")
    for name in ("route_a","route_b"):
        r=manifest[name]
        for k in c["route_required"]:
            if k not in r:e.append(f"MISSING_{name.upper()}:{k}")
        for k in ("network_manifest_sha256","program_table_sha256"):
            if r.get(k) and not HEX64.match(str(r[k])):
                e.append(f"BAD_{name.upper()}_{k.upper()}")
    if manifest["route_a"].get("network_version")==manifest["route_b"].get("network_version"):
        e.append("ROUTE_VERSIONS_MUST_DIFFER")
    if manifest["route_a"].get("program_table_sha256")==manifest["route_b"].get("program_table_sha256"):
        e.append("ROUTE_PROGRAM_TABLES_MUST_BE_DISTINCT")
    if "submitted" not in str(manifest["route_a"].get("definition_source","")).lower():
        e.append("ROUTE_A_NOT_IDENTIFIED_AS_SUBMITTED_PEAKS")
    rb=str(manifest["route_b"].get("definition_source","")).lower()
    if not ("fragment" in rb or "consensus" in rb):
        e.append("ROUTE_B_NOT_IDENTIFIED_AS_FRAGMENT_CONSENSUS")
    controls=manifest["controls"]
    for k in c["controls_required"]:
        if k not in controls:e.append(f"MISSING_CONTROL:{k}")
    gov=manifest["governance"]
    for k,want in c["governance_required"].items():
        if gov.get(k) is not want:e.append(f"GOVERNANCE_VIOLATION:{k}")
    if manifest.get("crosswalks",{}).get("contains_biological_effect_statistics") is not False:
        e.append("CROSSWALKS_MUST_BE_STRUCTURAL_ONLY")
    return e

def main():
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument("manifest"); a=ap.parse_args()
    m=json.loads(Path(a.manifest).read_text()); e=validate(m)
    if e:
        print("\n".join(e)); raise SystemExit(1)
    print("PASS")
if __name__=="__main__": main()
