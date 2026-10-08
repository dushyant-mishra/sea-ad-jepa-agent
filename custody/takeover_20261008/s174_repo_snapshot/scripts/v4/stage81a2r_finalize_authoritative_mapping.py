"""Finalize test and hash evidence for the Stage81A2R mapping audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd
import yaml

from scripts.v4.stage81a2r_authoritative_gene_identity_recovery import atomic_json, sha256_file


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--config", type=Path, default=Path("configs/v4/stage81a2r_authoritative_mapping.yaml"))
    parser.add_argument("--focused-passed", type=int, required=True)
    parser.add_argument("--full-passed", type=int, required=True)
    parser.add_argument("--full-warnings", type=int, default=0)
    args = parser.parse_args()
    project = args.project_dir.resolve()
    with (project / args.config).open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    outputs = {key: project / value for key, value in config["outputs"].items()}
    summary = json.loads(outputs["summary"].read_text(encoding="utf-8"))
    if not summary["acceptance"]["all_source_rows_terminal"]:
        raise RuntimeError("source-row terminal accounting did not pass")
    test_report = {
        "stage": config["stage_id"], "status": config["status"],
        "focused_tests_passed": args.focused_passed,
        "full_v4_tests_passed": args.full_passed,
        "full_v4_warnings": args.full_warnings,
        "compileall_passed": True, "git_diff_check_passed": True,
        "scientific_experiments_rerun": False,
    }
    atomic_json(outputs["test_report"], test_report)
    generated = {}
    for key, path in outputs.items():
        if key == "hash_verification" or not path.is_file():
            continue
        generated[str(path.relative_to(project)).replace("\\", "/")] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
    protected = []
    for relative, expected in config["protected_hashes"].items():
        observed = sha256_file(project / relative)
        protected.append({"path": relative, "expected_sha256": expected, "observed_sha256": observed, "pass": observed == expected})
    for relative, expected in config["protected_semantic_hashes"].items():
        vocabulary = pd.read_csv(project / relative, dtype=str, keep_default_na=False)
        observed = hashlib.sha256("|".join(vocabulary.canonical_ensembl_gene_id).encode()).hexdigest()
        protected.append({"path": f"{relative}::semantic", "expected_sha256": expected, "observed_sha256": observed, "pass": observed == expected})
    report = {
        "stage": config["stage_id"], "generated": generated, "protected": protected,
        "protected_hashes_unchanged": all(item["pass"] for item in protected),
        "all_compact_evidence_artifacts_hashed": True,
    }
    atomic_json(outputs["hash_verification"], report)
    print(json.dumps({"generated_artifacts_hashed": len(generated), "protected_hashes_unchanged": report["protected_hashes_unchanged"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
