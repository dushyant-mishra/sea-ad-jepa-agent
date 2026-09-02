#!/usr/bin/env python3
"""Finalize and separately anchor the provenance-only Command-15B supplement."""
from __future__ import annotations

import argparse, csv, hashlib, json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FINAL_REL = "outputs/contextual_teacher_target_v1_f1_hc3_15b_provenance_repair_20260902"
SOURCES = (
    "build_contextual_target_f1_hc3_15b_provenance_repair_v1.py",
    "validate_contextual_target_f1_hc3_15b_provenance_repair_v1.py",
    "finalize_contextual_target_f1_hc3_15b_provenance_repair_v1.py",
)


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(8<<20),b""): h.update(block)
    return h.hexdigest()


def snapshot_path(name: str) -> str:
    return f"source_snapshot/{name}"


def external_anchor_path() -> Path:
    return ROOT / "docs/agent/provenance-anchors/F1_HC3_15B_PROVENANCE_REPAIR_ROOT_20260902.json"


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n",encoding="utf-8")


def finalize(out: Path) -> dict:
    validation=json.loads((out/"F1_HC3_15B_PROVENANCE_INDEPENDENT_VALIDATION.json").read_text(encoding="utf-8"))
    chronology=json.loads((out/"F1_HC3_15B_CHRONOLOGY_RECORD.json").read_text(encoding="utf-8"))
    identity=json.loads((out/"F1_HC3_15B_BYTE_IDENTITY.json").read_text(encoding="utf-8"))
    index=json.loads((out/"F1_HC3_15B_STRUCTURED_REVIEW_INDEX.json").read_text(encoding="utf-8"))
    if validation["status"]!="PASS" or identity["scientific_bytes_changed"] is not False or index["record_count"]!=9 or chronology["chronology_claim"]!="EXECUTION_ENFORCED_PROSPECTIVELY__EXTERNAL_TIME_ANCHOR_UNAVAILABLE":
        raise RuntimeError("STOP_F1_HC3_15B_PROVENANCE_INDEPENDENT_MISMATCH")
    authority=json.loads((out/"F1_HC3_15B_PROVENANCE_REPAIR_AUTHORITY.json").read_text(encoding="utf-8"))
    authority["status"]="PASS_F1_HC3_15B_PROVENANCE_REPAIR_AWAITING_EXTERNAL_REVIEW"
    authority["independent_validation_status"]="PASS"
    write_json(out/"F1_HC3_15B_PROVENANCE_REPAIR_AUTHORITY.json",authority)
    handoff="""# F1 HC3 Command 15B provenance repair — external-review handoff

Terminal: `PASS_F1_HC3_15B_PROVENANCE_REPAIR_AWAITING_EXTERNAL_REVIEW`.

- The frozen 15B package remains byte-for-byte unchanged and is bound by manifest SHA-256 `a9d10fa17f162f3552c15095f3ef3ed7111f71c7a83978682303a2138088e174`.
- The exact selection-contract bytes are SHA-256 `3fc95316ad51205dd758bf93c6425ecfaebe3ed52e2bfacd6f03bb0406d0a4ac`.
- No pre-existing Git blob/commit or independent pre-result timestamp artifact was recoverable. The truthful chronology claim is `EXECUTION_ENFORCED_PROSPECTIVELY__EXTERNAL_TIME_ANCHOR_UNAVAILABLE`.
- Filesystem creation/modification metadata is recorded but is not represented as cryptographic time proof.
- Nine existing reviews are represented as structured records with exact content hashes; all bind the same frozen 15B manifest and selected-design SHA.
- All six required internal PASS reviews are authenticated by reviewer/lens IDs, exact source-section bytes, record hashes, and authority hashes. The three post-15B external reviews are preserved with their original PASS/CONCERN judgments.
- Independent validation confirms every 15B byte, chronology limitation, review record, source section and authority binding.
- No scientific judgment was regenerated. No nuisance rank, donor, threshold, HC3 rule, selection criterion, expression, outcome, model, training, EMA, F1 run, or 15C integration was introduced.

A separate local root anchor binds this supplemental package manifest after atomic publication. External review remains required before 15C.
"""
    (out/"F1_HC3_15B_PROVENANCE_REPAIR_EXTERNAL_REVIEW_HANDOFF.md").write_text(handoff,encoding="utf-8")
    terminal={"terminal_status":"PASS_F1_HC3_15B_PROVENANCE_REPAIR_AWAITING_EXTERNAL_REVIEW","chronology_claim":chronology["chronology_claim"],"15B_authority_manifest_sha256":identity["authority_manifest_sha256"],"15B_scientific_bytes_changed":False,"structured_review_records":9,"f1_run_authorized":False,"15c_integration_authorized":False}
    write_json(out/"F1_HC3_15B_PROVENANCE_REPAIR_TERMINAL_STATUS.json",terminal)
    snapshots=out/"source_snapshot"; snapshots.mkdir(exist_ok=True)
    source_rows=[]
    for name in SOURCES:
        source=ROOT/"scripts/v4"/name; target=snapshots/name; shutil.copy2(source,target)
        source_rows.append({"source_path":str(source.relative_to(ROOT)).replace("\\","/"),"snapshot_path":snapshot_path(name),"snapshot_path_scope":"PACKAGE_RELATIVE","source_sha256":sha256(source),"snapshot_sha256":sha256(target),"byte_identical":sha256(source)==sha256(target)})
    with (out/"F1_HC3_15B_PROVENANCE_REPAIR_SOURCE_MANIFEST.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(source_rows[0]));w.writeheader();w.writerows(source_rows)
    rows=[]
    manifest=out/"F1_HC3_15B_PROVENANCE_REPAIR_MANIFEST.csv"
    for path in sorted(p for p in out.rglob("*") if p.is_file() and p!=manifest):
        rows.append({"relative_path":str(path.relative_to(out)).replace("\\","/"),"bytes":path.stat().st_size,"sha256":sha256(path)})
    with manifest.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["relative_path","bytes","sha256"]);w.writeheader();w.writerows(rows)
    return {**terminal,"manifest_sha256":sha256(manifest),"manifested_files":len(rows)}


def publish_anchor(package: Path) -> dict:
    manifest=package/"F1_HC3_15B_PROVENANCE_REPAIR_MANIFEST.csv"
    if not manifest.is_file(): raise RuntimeError("STOP_F1_HC3_15B_PROVENANCE_ANCHOR_MISSING_PACKAGE")
    value={"schema":"F1_HC3_15B_PROVENANCE_REPAIR_EXTERNAL_LOCAL_ROOT_V1","package_path":FINAL_REL,"package_manifest_path":f"{FINAL_REL}/F1_HC3_15B_PROVENANCE_REPAIR_MANIFEST.csv","package_manifest_sha256":sha256(manifest),"15B_authority_manifest_sha256":"a9d10fa17f162f3552c15095f3ef3ed7111f71c7a83978682303a2138088e174","anchor_role":"SEPARATE_LOCAL_ROOT_BINDING_NOT_PRE_RESULT_TIME_PROOF","chronology_claim":"EXECUTION_ENFORCED_PROSPECTIVELY__EXTERNAL_TIME_ANCHOR_UNAVAILABLE"}
    write_json(external_anchor_path(),value)
    return {**value,"anchor_sha256":sha256(external_anchor_path())}


def main() -> None:
    ap=argparse.ArgumentParser();ap.add_argument("--package",type=Path,required=True);ap.add_argument("--anchor-only",action="store_true");args=ap.parse_args();out=args.package.resolve()
    result=publish_anchor(out) if args.anchor_only else finalize(out)
    print(json.dumps(result))


if __name__=="__main__":main()
