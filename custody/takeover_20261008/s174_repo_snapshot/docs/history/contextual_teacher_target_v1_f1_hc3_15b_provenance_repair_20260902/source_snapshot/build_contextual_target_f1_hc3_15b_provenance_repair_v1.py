#!/usr/bin/env python3
"""Build a provenance-only supplement for the frozen Command-15B package."""
from __future__ import annotations

import argparse, csv, hashlib, json, os, re, shutil, subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P15B = ROOT / "outputs/contextual_teacher_target_v1_f1_hc3_nuisance_design_freeze_20260902"
REVIEWS = ROOT / "outputs/contextual_teacher_target_v1_f1_hc3_nuisance_design_external_review_20260902"
MANIFEST_SHA = "a9d10fa17f162f3552c15095f3ef3ed7111f71c7a83978682303a2138088e174"
CONTRACT_SHA = "3fc95316ad51205dd758bf93c6425ecfaebe3ed52e2bfacd6f03bb0406d0a4ac"
DESIGN_SHA = "5d2fda2e81a6edd63241ccf996fe0e5086275233e765daae19509be24cd518e3"
DECISIONS = {"PASS", "CONCERN", "STOP"}
INTERNAL_REVIEWERS = {
    "Historian / Authority": "/root/a4_largecohort",
    "Statistical Design": "/root/a4_largecohort",
    "Numerical Linear Algebra": "/root/a4_synthesis",
    "HC3 / Robust Inference": "/root/a4_dataset",
    "Dataset / Biology Semantics": "/root/a4_dataset",
    "Red-Team": "/root/a4_synthesis",
}
EXTERNAL_REVIEWERS = {
    "Review 1: prospective selection, statistics and authority chronology": "/root/a4_largecohort",
    "Review 2: numerical linear algebra and HC3": "/root/a4_synthesis",
    "Review 3: provenance, firewall, dataset and biology semantics": "/root/a4_dataset",
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def canonical_bytes(value: dict) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def extract_review_sections(text: str, source_path: str, reviewers: dict[str, str]) -> list[dict]:
    matches = list(re.finditer(r"(?m)^## (.+)\n", text))
    records = []
    for i, match in enumerate(matches):
        heading = match.group(1).strip()
        lens = re.sub(r"^\d+\.\s+", "", heading)
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[match.start():end]
        verdict = re.search(r"(?m)^VERDICT: (PASS|CONCERN|STOP)\s*$", content)
        if lens not in reviewers or verdict is None:
            raise RuntimeError("STOP_F1_HC3_15B_PROVENANCE_REVIEW_RECORD")
        decision = verdict.group(1)
        if decision not in DECISIONS:
            raise RuntimeError("STOP_F1_HC3_15B_PROVENANCE_REVIEW_RECORD")
        records.append({"lens_id": lens, "source_heading": heading, "reviewer_id": reviewers[lens], "decision": decision,
                        "source_review_path": source_path, "review_content": content})
    if set(r["lens_id"] for r in records) != set(reviewers):
        raise RuntimeError("STOP_F1_HC3_15B_PROVENANCE_REVIEW_RECORD")
    return records


def chronology_record(contract_sha: str, creation_utc: str, modified_utc: str,
                      git_blob: str | None, external_pre_result_anchor: str | None) -> dict:
    independently_anchored = bool(git_blob or external_pre_result_anchor)
    return {
        "chronology_claim": ("EXTERNALLY_ANCHORED_PRE_RESULT_CONTRACT" if independently_anchored
                             else "EXECUTION_ENFORCED_PROSPECTIVELY__EXTERNAL_TIME_ANCHOR_UNAVAILABLE"),
        "contract_sha256": contract_sha,
        "filesystem_creation_time_utc": creation_utc,
        "filesystem_last_write_time_utc": modified_utc,
        "filesystem_times_are_independent_proof": False,
        "git_blob_identity": git_blob,
        "external_pre_result_anchor": external_pre_result_anchor,
        "independent_pre_result_time_anchor_available": independently_anchored,
        "execution_order_evidence": "15B derivation required the exact contract SHA before reading/applying the frontier selector",
        "limitation": None if independently_anchored else "No pre-existing Git blob/commit or independent pre-result timestamp artifact was recoverable. Filesystem metadata is recorded but is not treated as cryptographic time proof.",
    }


def verify_15b_tree() -> list[dict]:
    manifest = P15B / "F1_HC3_15B_MANIFEST.csv"
    if sha256(manifest) != MANIFEST_SHA:
        raise RuntimeError("STOP_F1_HC3_15B_PROVENANCE_AUTHORITY_MISMATCH")
    with manifest.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    output = [{"relative_path": "F1_HC3_15B_MANIFEST.csv", "bytes": manifest.stat().st_size, "sha256": MANIFEST_SHA}]
    for row in rows:
        path = P15B / row["relative_path"]
        if not path.is_file() or path.stat().st_size != int(row["bytes"]) or sha256(path) != row["sha256"]:
            raise RuntimeError("STOP_F1_HC3_15B_PROVENANCE_AUTHORITY_MISMATCH")
        output.append({"relative_path": row["relative_path"], "bytes": int(row["bytes"]), "sha256": row["sha256"]})
    actual = sorted(str(p.relative_to(P15B)).replace("\\", "/") for p in P15B.rglob("*") if p.is_file())
    if actual != sorted(r["relative_path"] for r in output) or len(output) != 18:
        raise RuntimeError("STOP_F1_HC3_15B_PROVENANCE_AUTHORITY_MISMATCH")
    return sorted(output, key=lambda r: r["relative_path"])


def git_blob_for_contract() -> str | None:
    relative = str((P15B / "F1_HC3_15B_SELECTION_CONTRACT.md").relative_to(ROOT)).replace("\\", "/")
    result = subprocess.run(["git", "ls-files", "--stage", "--", relative], cwd=ROOT,
                            text=True, capture_output=True, check=False)
    if result.returncode or not result.stdout.strip():
        return None
    parts = result.stdout.strip().split()
    return parts[1] if len(parts) >= 2 else None


def utc_iso(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat().replace("+00:00", "Z")


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--out", type=Path, required=True); args = ap.parse_args()
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=False)
    tree = verify_15b_tree()
    contract = P15B / "F1_HC3_15B_SELECTION_CONTRACT.md"
    if sha256(contract) != CONTRACT_SHA or sha256(P15B / "F1_HC3_SELECTED_DONOR_DESIGN_F64LE.bin") != DESIGN_SHA:
        raise RuntimeError("STOP_F1_HC3_15B_PROVENANCE_AUTHORITY_MISMATCH")
    stat = contract.stat()
    chronology = chronology_record(CONTRACT_SHA, utc_iso(stat.st_ctime), utc_iso(stat.st_mtime),
                                   git_blob_for_contract(), None)
    authority_snapshot = out / "authority_snapshot"; authority_snapshot.mkdir()
    shutil.copy2(contract, authority_snapshot / contract.name)
    write_json(out / "F1_HC3_15B_CHRONOLOGY_RECORD.json", chronology)
    write_json(out / "F1_HC3_15B_BYTE_IDENTITY.json", {
        "authority_package_path": str(P15B.relative_to(ROOT)).replace("\\", "/"),
        "authority_manifest_sha256": MANIFEST_SHA, "selected_design_sha256": DESIGN_SHA,
        "selection_contract_sha256": CONTRACT_SHA, "file_count_including_manifest": len(tree),
        "files": tree, "scientific_bytes_changed": False,
    })
    internal_path = P15B / "F1_HC3_15B_MULTIAGENT.md"
    external_path = REVIEWS / "F1_HC3_15B_INDEPENDENT_REVIEWS.md"
    sources = [(internal_path, INTERNAL_REVIEWERS, "INTERNAL_15B_TARGETED_REVIEW"),
               (external_path, EXTERNAL_REVIEWERS, "POST_15B_EXTERNAL_REVIEW")]
    content_dir = out / "review_content"; records_dir = out / "review_records"
    content_dir.mkdir(); records_dir.mkdir(); index=[]
    sequence = 0
    for source, mapping, round_id in sources:
        source_rel = str(source.relative_to(ROOT)).replace("\\", "/")
        extracted = extract_review_sections(source.read_text(encoding="utf-8"), source_rel, mapping)
        for item in extracted:
            sequence += 1
            slug = re.sub(r"[^a-z0-9]+", "_", item["lens_id"].lower()).strip("_")
            content_name = f"{sequence:02d}_{slug}.md"; content_bytes = item.pop("review_content").encode("utf-8")
            (content_dir / content_name).write_bytes(content_bytes)
            record = {
                "schema": "F1_HC3_15B_STRUCTURED_REVIEW_V1", "review_round_id": round_id,
                "reviewer_id": item["reviewer_id"], "lens_id": item["lens_id"], "decision": item["decision"],
                "source_review_path": item["source_review_path"], "source_review_sha256": sha256(source),
                "review_content_path": f"review_content/{content_name}",
                "review_content_sha256": sha256_bytes(content_bytes),
                "reviewed_artifacts": [
                    {"path": str((P15B / "F1_HC3_15B_MANIFEST.csv").relative_to(ROOT)).replace("\\", "/"), "sha256": MANIFEST_SHA},
                    {"path": str((P15B / "F1_HC3_SELECTED_DONOR_DESIGN_F64LE.bin").relative_to(ROOT)).replace("\\", "/"), "sha256": DESIGN_SHA},
                ],
                "temporal_sequence": {"mode": "PRESENTATION_ORDER_ONLY_NOT_WALL_CLOCK", "ordinal": sequence,
                                      "review_timestamp_utc": None, "timestamp_status": "UNAVAILABLE_IN_DURABLE_REVIEW_ARTIFACT"},
                "scientific_judgment_regenerated": False,
            }
            record["record_sha256"] = sha256_bytes(canonical_bytes(record))
            record_name = f"{sequence:02d}_{slug}.json"; write_json(records_dir / record_name, record)
            index.append({"record_path": f"review_records/{record_name}", "record_sha256": record["record_sha256"],
                          "reviewer_id": record["reviewer_id"], "lens_id": record["lens_id"],
                          "decision": record["decision"], "review_round_id": round_id})
    write_json(out / "F1_HC3_15B_STRUCTURED_REVIEW_INDEX.json", {
        "schema": "F1_HC3_15B_STRUCTURED_REVIEW_INDEX_V1", "authority_manifest_sha256": MANIFEST_SHA,
        "required_internal_pass_lenses": list(INTERNAL_REVIEWERS), "record_count": len(index), "records": index,
        "review_prose_reinterpreted": False,
    })
    write_json(out / "F1_HC3_15B_PROVENANCE_REPAIR_AUTHORITY.json", {
        "status": "BUILT_AWAITING_INDEPENDENT_VALIDATION", "authority_manifest_sha256": MANIFEST_SHA,
        "selection_contract_sha256": CONTRACT_SHA, "selected_design_sha256": DESIGN_SHA,
        "chronology_claim": chronology["chronology_claim"], "15B_scientific_bytes_changed": False,
        "new_scientific_judgment_generated": False, "f1_run_authorized": False,
    })
    print(json.dumps({"status":"BUILT","records":len(index),"chronology_claim":chronology["chronology_claim"],"15B_files_verified":len(tree)}))


if __name__ == "__main__": main()
