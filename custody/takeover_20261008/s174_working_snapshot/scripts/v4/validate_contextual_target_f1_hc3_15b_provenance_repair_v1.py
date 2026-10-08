#!/usr/bin/env python3
"""Independent fail-closed validator for the Command-15B provenance supplement."""
from __future__ import annotations

import argparse, csv, hashlib, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P15B = ROOT / "outputs/contextual_teacher_target_v1_f1_hc3_nuisance_design_freeze_20260902"
MANIFEST_SHA = "a9d10fa17f162f3552c15095f3ef3ed7111f71c7a83978682303a2138088e174"
CONTRACT_SHA = "3fc95316ad51205dd758bf93c6425ecfaebe3ed52e2bfacd6f03bb0406d0a4ac"
DESIGN_SHA = "5d2fda2e81a6edd63241ccf996fe0e5086275233e765daae19509be24cd518e3"
REQUIRED_LENSES = {"Historian / Authority", "Statistical Design", "Numerical Linear Algebra",
                   "HC3 / Robust Inference", "Dataset / Biology Semantics", "Red-Team"}


def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(8<<20),b""): h.update(block)
    return h.hexdigest()


def canonical_record_hash(record: dict) -> str:
    unsigned=dict(record); unsigned.pop("record_sha256",None)
    data=(json.dumps(unsigned,sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def require_review_authority(record: dict, expected_manifest_sha: str) -> None:
    if type(record.get("reviewer_id")) is not str or not record["reviewer_id"] or type(record.get("lens_id")) is not str:
        raise RuntimeError("STOP_F1_HC3_15B_PROVENANCE_REVIEW_RECORD")
    if record.get("decision") not in {"PASS","CONCERN","STOP"}:
        raise RuntimeError("STOP_F1_HC3_15B_PROVENANCE_REVIEW_RECORD")
    bindings=record.get("reviewed_artifacts",[])
    if not any(x.get("sha256")==expected_manifest_sha and x.get("path","").endswith("F1_HC3_15B_MANIFEST.csv") for x in bindings):
        raise RuntimeError("STOP_F1_HC3_15B_PROVENANCE_REVIEW_BINDING")


def exact_section(source: str, lens: str) -> str:
    matches=list(re.finditer(r"(?m)^## (.+)\n",source))
    for i,m in enumerate(matches):
        heading=m.group(1).strip()
        if re.sub(r"^\d+\.\s+","",heading)==lens:
            end=matches[i+1].start() if i+1<len(matches) else len(source)
            return source[m.start():end]
    raise RuntimeError("STOP_F1_HC3_15B_PROVENANCE_REVIEW_RECORD")


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("--package",type=Path,required=True); args=ap.parse_args(); out=args.package.resolve()
    # Recompute original 15B identity without importing builder helpers.
    manifest=P15B/"F1_HC3_15B_MANIFEST.csv"; manifest_ok=sha(manifest)==MANIFEST_SHA
    with manifest.open(newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
    files_ok=all((P15B/r["relative_path"]).is_file() and (P15B/r["relative_path"]).stat().st_size==int(r["bytes"]) and sha(P15B/r["relative_path"])==r["sha256"] for r in rows)
    tree=json.loads((out/"F1_HC3_15B_BYTE_IDENTITY.json").read_text(encoding="utf-8"))
    tree_ok=(tree["authority_manifest_sha256"]==MANIFEST_SHA and tree["file_count_including_manifest"]==18 and tree["scientific_bytes_changed"] is False)
    chronology=json.loads((out/"F1_HC3_15B_CHRONOLOGY_RECORD.json").read_text(encoding="utf-8"))
    chronology_ok=(chronology["contract_sha256"]==CONTRACT_SHA and chronology["chronology_claim"]=="EXECUTION_ENFORCED_PROSPECTIVELY__EXTERNAL_TIME_ANCHOR_UNAVAILABLE" and chronology["independent_pre_result_time_anchor_available"] is False and chronology["filesystem_times_are_independent_proof"] is False and chronology["git_blob_identity"] is None and chronology["external_pre_result_anchor"] is None)
    snapshot_ok=sha(out/"authority_snapshot/F1_HC3_15B_SELECTION_CONTRACT.md")==CONTRACT_SHA and sha(P15B/"F1_HC3_15B_SELECTION_CONTRACT.md")==CONTRACT_SHA
    index=json.loads((out/"F1_HC3_15B_STRUCTURED_REVIEW_INDEX.json").read_text(encoding="utf-8"))
    review_checks=[]; internal_pass=set(); all_same=True
    for item in index["records"]:
        record_path=out/item["record_path"]; record=json.loads(record_path.read_text(encoding="utf-8"))
        require_review_authority(record,MANIFEST_SHA)
        content=(out/record["review_content_path"]).read_bytes()
        source=(ROOT/record["source_review_path"]).read_text(encoding="utf-8")
        exact=exact_section(source,record["lens_id"]).encode("utf-8")
        valid=(hashlib.sha256(content).hexdigest()==record["review_content_sha256"] and content==exact and
               canonical_record_hash(record)==record["record_sha256"]==item["record_sha256"] and
               record["decision"]==item["decision"] and sha(ROOT/record["source_review_path"])==record["source_review_sha256"] and
               record["scientific_judgment_regenerated"] is False and
               record["temporal_sequence"]["review_timestamp_utc"] is None and
               record["temporal_sequence"]["timestamp_status"]=="UNAVAILABLE_IN_DURABLE_REVIEW_ARTIFACT")
        review_checks.append(valid); all_same &= all(x["sha256"] in {MANIFEST_SHA,DESIGN_SHA} for x in record["reviewed_artifacts"])
        if record["review_round_id"]=="INTERNAL_15B_TARGETED_REVIEW" and record["decision"]=="PASS": internal_pass.add(record["lens_id"])
    checks={"15B_manifest_sha_exact":manifest_ok,"all_15B_manifested_files_exact":files_ok,"15B_tree_identity_exact":tree_ok,
            "selection_contract_snapshot_exact":snapshot_ok,"truthful_limited_chronology":chronology_ok,
            "nine_structured_records":index["record_count"]==len(index["records"])==9,
            "all_review_records_and_exact_content_valid":all(review_checks),"all_reviews_bind_same_frozen_authority":all_same,
            "six_required_internal_passes":internal_pass==REQUIRED_LENSES,"no_scientific_bytes_changed":tree["scientific_bytes_changed"] is False}
    status="PASS" if all(v is True for v in checks.values()) else "STOP_F1_HC3_15B_PROVENANCE_INDEPENDENT_MISMATCH"
    report={"status":status,"checks":checks,"authority_manifest_sha256":MANIFEST_SHA,"selection_contract_sha256":CONTRACT_SHA,"selected_design_sha256":DESIGN_SHA,"structured_review_records":len(review_checks),"chronology_claim":chronology["chronology_claim"]}
    (out/"F1_HC3_15B_PROVENANCE_INDEPENDENT_VALIDATION.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(report))
    if status!="PASS": raise SystemExit(2)


if __name__=="__main__": main()
