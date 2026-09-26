"""Independent read-only reconciliation of PR131 dirty-origin and PR137 clean-origin results.

NO raw-screen analysis, replacement producer, training, protected outcomes, or benchmark
approval. Both branch inputs are pinned to observed exact commit SHA and immutable
existing output CSV hashes. Fail closed on any unexpected scientific-field change.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import subprocess
from pathlib import Path

ORIGINAL_SHA = "8647d21174c5e7eab2ad01fc6b9251b069ba0e03"
CLEAN_SHA = "e130f55c7471b74b387f0bd0aca586c4a1614921"
ROOT = Path("analysis/therapeutic_perturbation_etl")
RECEIPT = ROOT / "evidence/crisprbrain_reliability/CRISPRBRAIN_SCREEN_RELIABILITY_RECEIPT_V1.json"
PRODUCER = ROOT / "scripts/assess_crisprbrain_screen_reliability_v1.py"
EXPECTED_OUTPUT_NAMES = frozenset({
    "concordance_by_abundance.csv", "fdr_threshold_sensitivity.csv",
    "jointly_significant_rows.csv", "non_replication_classification.csv",
    "per_target_concordance.csv", "target_engagement.csv", "target_identity.csv",
})
EXACT_SCIENCE_SECTIONS = (
    "inputs", "S1_identity", "S2_engagement", "S4_power", "S5_abundance",
    "S6_independence", "S7_cross_screen_overlap", "POSITIVE_CONTROLS",
    "PRELIMINARY_CLAIMS_CHECK", "VERDICT",
)
# The new receipt ADDITIONALLY documents non-independent hypergeometric inference
# and that jointly significant target×gene rows are not distinct targets.
PERMITTED_CLEAN_ONLY_S3 = frozenset({
    "hypergeom_caveat", "n_jointly_significant_rows",
    "n_distinct_readout_genes_among_jointly_significant",
    "n_distinct_targets_among_jointly_significant", "joint_count_unit",
})


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def require(condition: bool, description: str) -> None:
    if not condition:
        raise ValueError("STOP_RECONCILIATION: " + description)


def get_head(repo: Path) -> str:
    p = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       text=True, check=True)
    return p.stdout.strip()


def show_at(repo: Path, commit: str, path: Path) -> bytes:
    return subprocess.run(["git", "show", commit + ":" + path.as_posix()],
                          cwd=repo, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=True).stdout


def parse_receipt(path: Path) -> dict:
    with path.open("rb") as f:
        result = json.loads(f.read())
    require(isinstance(result, dict), "receipt is not a JSON object")
    require(result.get("schema") == "CRISPRBRAIN_SCREEN_RELIABILITY_V1",
            "wrong CRISPRbrain receipt schema")
    return result


def normalize_outputs(root: Path, receipt: dict) -> dict:
    rows = receipt.get("outputs")
    require(isinstance(rows, list) and len(rows) == len(EXPECTED_OUTPUT_NAMES),
            "must declare exactly seven output files")
    output = {}
    for item in rows:
        require(isinstance(item, dict), "invalid output row")
        declared = item.get("path")
        require(isinstance(declared, str), "missing output path")
        relative = Path(declared)
        require(not relative.is_absolute() and ".." not in relative.parts
                and relative.parts[:2] == ("analysis", "therapeutic_perturbation_etl"),
                "output path escapes the declared result subtree")
        require(relative.name in EXPECTED_OUTPUT_NAMES
                and "evidence/crisprbrain_reliability" in relative.as_posix(),
                "unknown CRISPRbrain output path")
        expected_hash = item.get("sha256")
        require(isinstance(expected_hash, str)
                and len(expected_hash) == 64
                and all(ch in "0123456789abcdef" for ch in expected_hash),
                "invalid output digest")
        path = root / relative
        raw = path.read_bytes()
        require(sha(raw) == expected_hash,
                "committed output SHA-256 differs from declared receipt: " + relative.name)
        nrows = sum(1 for _ in csv.reader(io.StringIO(raw.decode("utf-8-sig"),
                                                      newline=""))) - 1
        require(isinstance(item.get("rows"), int) and nrows == item["rows"],
                "committed output row count differs from receipt: " + relative.name)
        require(relative.name not in output, "duplicate output file")
        output[relative.name] = {
            "sha256": expected_hash, "rows": nrows, "raw": raw,
            "relative_path": relative.as_posix(),
        }
    require(frozenset(output) == EXPECTED_OUTPUT_NAMES, "missing output table")
    return output


def compare_science(original: dict, clean: dict) -> dict:
    for section in EXACT_SCIENCE_SECTIONS:
        require(section in original and original[section] == clean.get(section),
                "science changed outside separately allowed annotations: " + section)
    old = original.get("S3_concordance")
    new = clean.get("S3_concordance")
    require(isinstance(old, dict) and isinstance(new, dict),
            "missing continuous-concordance section")
    additions = set(new) - set(old)
    require(additions == PERMITTED_CLEAN_ONLY_S3,
            "unexpected or missing new science annotations: " + str(sorted(additions)))
    require(set(old) <= set(new), "clean receipt deleted a historical science field")
    for k, v in old.items():
        require(v == new[k], "continuous-concordance field changed: " + k)
    require(new["n_jointly_significant_rows"] == old["n_sig_both"],
            "new jointly significant row count not supported by original")
    return {
        "exact_common_science_sections": list(EXACT_SCIENCE_SECTIONS),
        "s3_original_fields_equal": len(old),
        "s3_allowed_new_annotation_fields": sorted(additions),
    }


def validate_joint_table(table: bytes, clean: dict) -> dict:
    rows = list(csv.DictReader(io.StringIO(table.decode("utf-8-sig"), newline="")))
    require(rows and all("name" in r and "Gene" in r for r in rows),
            "joint output has wrong gene/target schema")
    targets = {r["name"] for r in rows}
    genes = {r["Gene"] for r in rows}
    report = clean["S3_concordance"]
    require(len(rows) == report["n_jointly_significant_rows"]
            and len(genes) == report["n_distinct_readout_genes_among_jointly_significant"]
            and len(targets) == report["n_distinct_targets_among_jointly_significant"],
            "new annotation disagrees with raw committed jointly significant CSV")
    counts = {name: sum(r["name"] == name for r in rows) for name in sorted(targets)}
    require(counts == report["jointly_significant_rows_by_target"],
            "target concentration differs from CSV")
    return {"target_gene_rows": len(rows), "distinct_readout_genes": len(genes),
            "distinct_targets": len(targets), "counts_by_target": counts}


def reconcile(original_root: Path, clean_root: Path, *, verify_git: bool = True) -> dict:
    if verify_git:
        require(get_head(original_root) == ORIGINAL_SHA, "wrong original PR131 HEAD")
        require(get_head(clean_root) == CLEAN_SHA, "wrong clean PR137 HEAD")
    old = parse_receipt(original_root / RECEIPT)
    new = parse_receipt(clean_root / RECEIPT)
    require(old.get("git_dirty") is True and new.get("git_dirty") is False,
            "historical dirty/clean provenance distinction lost")
    require(old.get("status") == new.get("status") == "COMPLETE",
            "source receipts not marked executed")
    old_p = sha((original_root / PRODUCER).read_bytes())
    clean_p = sha((clean_root / PRODUCER).read_bytes())
    require(old_p != old["producer_sha256"],
            "historical dirty-producer mismatch not reproduced; review receipt history")
    require(clean_p == new["producer_sha256"],
            "clean current producer differs from clean executed digest")
    if verify_git:
        require(new.get("git_head") and len(new["git_head"]) == 40,
                "missing clean producer anchor")
        require(sha(show_at(clean_root, new["git_head"], PRODUCER))
                == new["producer_sha256"], "clean producer does not exist at declared anchor")
    old_out = normalize_outputs(original_root, old)
    clean_out = normalize_outputs(clean_root, new)
    for name in sorted(EXPECTED_OUTPUT_NAMES):
        require(old_out[name]["sha256"] == clean_out[name]["sha256"]
                and old_out[name]["rows"] == clean_out[name]["rows"]
                and old_out[name]["raw"] == clean_out[name]["raw"],
                "scientific CSV changed between commits: " + name)
    science = compare_science(old, new)
    joint = validate_joint_table(clean_out["jointly_significant_rows.csv"]["raw"], new)
    return {
        "schema": "JEPA_V26_PR131_PR137_EXISTING_EVIDENCE_RECONCILIATION_V1",
        "status": "PASS_EXISTING_OUTPUT_BYTES_AND_COMMON_SCIENCE_MATCH",
        "original_commit": ORIGINAL_SHA, "clean_commit": CLEAN_SHA,
        "historical_dirty_receipt": True,
        "historical_executed_producer_sha256": old["producer_sha256"],
        "historical_committed_producer_sha256": old_p,
        "historical_original_dirty_producer_replay": "NOT_REPRODUCED",
        "clean_executed_producer_sha256": clean_p,
        "clean_receipt_anchor": new.get("git_head"),
        "clean_source_at_declared_anchor_verified": verify_git,
        "all_existing_output_csvs_byte_identical": True,
        "output_files": [
            {"name": n, "sha256": clean_out[n]["sha256"], "rows": clean_out[n]["rows"]}
            for n in sorted(clean_out)
        ],
        "science": science, "joint_table_crosscheck": joint,
        "raw_deposited_screens_reexecuted_by_this_script": False,
        "biologically_independent_replication": False,
        "protected_outcomes_opened": False, "training_authorized": False,
        "disposition": (
            "Keep original PR131 dirty receipt as immutable historical evidence; "
            "use PR137 clean receipt for CURRENT reproducible scientific numbers. "
            "PR134's failed attempt to replay the dirty producer must not be "
            "silently relabeled a pass."
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-root", required=True, type=Path)
    p.add_argument("--clean-root", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    require(not a.out.exists(), "refuse to overwrite old audit receipt")
    report = reconcile(a.original_root.resolve(), a.clean_root.resolve())
    require(a.out.parent.is_dir(), "create a new output parent explicitly")
    with a.out.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")
    print(json.dumps({"status": report["status"], "file": str(a.out)}, sort_keys=True))


if __name__ == "__main__":
    main()
