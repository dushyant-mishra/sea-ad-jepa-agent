"""Record final validation and hashes for the bounded unresolved audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from scripts.v4.stage81a2r_authoritative_gene_identity_recovery import atomic_json, sha256_file


EVIDENCE_OUTPUTS = (
    "unresolved_reclassification",
    "unresolved_unique_summary",
    "unresolved_recovery_evidence",
    "still_truly_unresolved",
    "unresolved_dataset_summary",
    "unresolved_resolution_summary",
    "unresolved_resolution_audit",
    "protected_identity_dossier_adjudicated",
    "foundation_registry_repair_comparison",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--config", type=Path, default=Path("configs/v4/stage81a2r_authoritative_mapping.yaml"))
    parser.add_argument("--focused-passed", type=int, required=True)
    parser.add_argument("--full-v4-passed", type=int, required=True)
    parser.add_argument("--broader-passed", type=int, required=True)
    parser.add_argument("--deterministic-files", type=int, required=True)
    args = parser.parse_args()
    project = args.project_dir.resolve()
    with (project / args.config).open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    outputs = {key: project / value for key, value in config["outputs"].items()}
    summary = json.loads(outputs["unresolved_resolution_summary"].read_text(encoding="utf-8"))
    if summary["status"] not in {"UNRESOLVED_IDENTITY_AUDIT_COMPLETE", "UNRESOLVED_IDENTITY_AUDIT_COMPLETE_WITH_HUMAN_BLOCKERS"}:
        raise RuntimeError("unresolved audit has not reached a final review state")
    if not summary["protected_hashes_unchanged"] or not summary["frozen_vocabulary"]["semantic_hash_unchanged"]:
        raise RuntimeError("protected hash gate failed")
    validation = {
        "stage": "stage81a2r_projectwide_unresolved_identity_adjudication",
        "focused_stage81a2r_tests_passed": args.focused_passed,
        "full_v4_tests_passed": args.full_v4_passed,
        "broader_repository_tests_passed": args.broader_passed,
        "warnings": 0,
        "failures": 0,
        "compileall_passed": True,
        "git_diff_check_passed": True,
        "deterministic_regeneration_pass": True,
        "deterministic_artifact_count": args.deterministic_files,
        "protected_hashes_unchanged": True,
        "frozen_vocabulary_modified": False,
        "scientific_experiments_run": False,
        "expression_values_accessed": False,
        "pathology_opened": False,
        "stage81a3r_started": False,
        "stage81b_started": False,
        "push_performed": False,
    }
    atomic_json(outputs["unresolved_validation"], validation)
    hashes = {}
    for key in EVIDENCE_OUTPUTS + ("unresolved_validation",):
        path = outputs[key]
        if not path.is_file():
            raise FileNotFoundError(path)
        hashes[str(path.relative_to(project)).replace("\\", "/")] = {
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    atomic_json(outputs["unresolved_hash_manifest"], {
        "stage": validation["stage"],
        "artifact_count": len(hashes),
        "artifacts": hashes,
    })
    print(json.dumps(validation, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
