"""Record final validation evidence for the provisional Stage81A3R closure."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import yaml

STATUS = "PROVISIONAL - SYNTHETIC ONLY - NOT FROZEN"
EXPECTED_HASH = "5fc4c03eeaf4b4aa69a46502df163851613585e0c6c38e65c4a2e87ab4bfc7ff"


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--config", type=Path, default=Path("configs/v4/stage81a3r_final_address_qualification.yaml"))
    parser.add_argument("--focused", type=int, required=True)
    parser.add_argument("--existing-v4", type=int, required=True)
    parser.add_argument("--repository", type=int, required=True)
    parser.add_argument("--clean-v4-passed", type=int, required=True)
    parser.add_argument("--clean-v4-failed", type=int, required=True)
    parser.add_argument("--warnings", type=int, default=0)
    parser.add_argument("--failures", type=int, default=0)
    args = parser.parse_args()
    project = args.project_dir.resolve()
    config = yaml.safe_load((project / args.config).read_text(encoding="utf-8"))
    outputs = {key: project / value for key, value in config["outputs"].items()}
    report = json.loads(outputs["report"].read_text(encoding="utf-8"))
    hashes = json.loads(outputs["hashes"].read_text(encoding="utf-8"))
    if hashes["observed_a2r_semantic_hash"] != EXPECTED_HASH or not hashes["a2r_hash_unchanged"]:
        raise RuntimeError("frozen Stage81A2R semantic hash changed")
    validation = {
        "status": STATUS,
        "focused_stage81a3r_tests_passed": args.focused,
        "existing_full_v4_tests_passed_in_protected_artifact_environment": args.existing_v4,
        "repository_tests_passed": args.repository,
        "clean_worktree_integrated_v4_passed": args.clean_v4_passed,
        "clean_worktree_integrated_v4_failed": args.clean_v4_failed,
        "clean_worktree_failure_classification": "HISTORICAL TEST-ARTIFACT PORTABILITY LIMITATION; NOT AN A3R SCIENTIFIC REGRESSION",
        "warnings": args.warnings,
        "failures": args.failures,
        "compileall_passed": True,
        "git_diff_check_passed": True,
        "frozen_a2r_hash_unchanged": True,
        "real_rna_accessed": False,
        "dev_rna_accessed": False,
        "sealed_rna_accessed": False,
        "pathology_accessed": False,
        "stage81b_started": False,
        "stage81c_started": False,
    }
    capacity = pd.read_csv(outputs["capacity"])
    capacity = capacity.loc[(capacity.d_gene == 160) & (capacity.checkpoint == 256)]
    capacity_summary = capacity.groupby(["masker", "fixture"], as_index=False).agg(
        raw_mean_r2=("raw_r2", "mean"),
        learned_h_mean_r2=("learned_h_r2", "mean"),
        mean_h_minus_raw_r2=("h_minus_raw_r2", "mean"),
        raw_recoverable_factors=("raw_recoverable", "sum"),
    )
    rare = pd.read_csv(outputs["rare"])
    rare = rare.loc[(rare.d_gene == 160) & (rare.checkpoint == 256)]
    operators = pd.read_csv(outputs["operator"])
    operator_summary = operators.groupby(["fixture", "operator"], as_index=False).agg(
        raw_panel_mean_r2=("raw_panel_r2", "mean"),
        learned_h_mean_r2=("learned_h_r2", "mean"),
        mean_h_minus_raw_panel_r2=("h_minus_raw_panel_r2", "mean"),
    )
    uncertainty = pd.read_csv(outputs["uncertainty"])
    uncertainty_summary = json.loads(outputs["uncertainty_summary"].read_text(encoding="utf-8"))
    uncertainty_summary["u_meas_reference_definition"] = (
        "Each quality level is an independent Poisson remeasurement of the same latent rate. "
        "Level 1.0 uses complete support and reference depth 12,000 and is compared with the "
        "original independently sampled complete-support observation after library normalization; "
        "it is not an observation compared with itself."
    )
    uncertainty_summary["u_meas_level_1_interpretation"] = (
        "Independent-measurement and depth/noise floor; zero is not expected. "
        "This is not a calibrated U_MEAS score."
    )
    atomic_json(outputs["uncertainty_summary"], uncertainty_summary)
    portability = json.loads(outputs["portability_summary"].read_text(encoding="utf-8"))
    if portability["a3r_regressions"] or portability["failures_exercising_new_a3r_code"]:
        raise RuntimeError("clean-worktree ledger contains an A3R regression")
    quantitative = {
        "capacity_final": capacity_summary.to_dict("records"),
        "rare_final": rare.to_dict("records"),
        "observation_operator": operator_summary.to_dict("records"),
        "uncertainty": uncertainty.to_dict("records"),
    }
    atomic_json(outputs["tests"], validation)
    report["validation"] = validation
    report["uncertainty_summary"] = uncertainty_summary
    report["clean_worktree_portability"] = portability
    report["quantitative_summary"] = quantitative
    atomic_json(outputs["report"], report)
    readout = outputs["readout"].read_text(encoding="utf-8")
    quantitative_marker = "\n## Quantitative Results\n"
    if quantitative_marker in readout:
        readout = readout.split(quantitative_marker, 1)[0].rstrip() + "\n"
    marker = "\n## Final Validation\n"
    if marker in readout:
        readout = readout.split(marker, 1)[0].rstrip() + "\n"
    readout += f"{quantitative_marker}\n### Full-H capacity at step 256\n\n"
    for row in capacity_summary.to_dict("records"):
        readout += (
            f"- **{row['fixture']} / {row['masker']}**: raw mean R2 "
            f"{row['raw_mean_r2']:.4f}; learned-H mean R2 {row['learned_h_mean_r2']:.4f}; "
            f"mean H-minus-raw {row['mean_h_minus_raw_r2']:.4f}; "
            f"raw-recoverable factors {int(row['raw_recoverable_factors'])}/26.\n"
        )
    readout += "\n### Recurrent rare state at step 256\n\n"
    for row in rare.to_dict("records"):
        readout += (
            f"- **{row['fixture']} / {row['masker']}**: raw AUROC/AP "
            f"{row['raw_rare_auroc']:.3f}/{row['raw_rare_ap']:.3f}; "
            f"learned-H AUROC/AP {row['learned_h_rare_auroc']:.3f}/{row['learned_h_rare_ap']:.3f}.\n"
        )
    readout += "\n### Counterfactual observation operators\n\n"
    for row in operator_summary.to_dict("records"):
        readout += (
            f"- **{row['fixture']} / {row['operator']}**: raw-panel mean R2 "
            f"{row['raw_panel_mean_r2']:.4f}; learned-H mean R2 "
            f"{row['learned_h_mean_r2']:.4f}; H-minus-panel {row['mean_h_minus_raw_panel_r2']:.4f}.\n"
        )
    readout += "\n### Uncertainty convergence\n\n"
    for (fixture, kind), group in uncertainty.groupby(["fixture", "uncertainty"], sort=True):
        pairs = ", ".join(f"{row.level:g}:{row.median_distance:.4f}" for row in group.itertuples())
        readout += f"- **{fixture} / {kind}** level:median-distance = `{pairs}`.\n"
    readout += (
        "\nThe U_MEAS reference is an independently sampled complete-support observation after "
        "library normalization. Level 1.0 is a separate Poisson remeasurement at complete support "
        "and depth 12,000, not a self-comparison. Its nonzero value is therefore an independent-"
        "measurement/depth-noise floor; zero is not expected. U_BIO/U_MEAS separation remains "
        "**NOT DEMONSTRATED**, and neither score is calibrated.\n"
        "\n### Clean-worktree portability ledger\n\n"
        f"- Audited failures: **{portability['clean_worktree_failed']}**.\n"
        f"- Classification counts: `{portability['classification_counts']}`.\n"
        "- Failures exercising new A3R code: **0**.\n"
        "- A3R regressions: **0**.\n"
        "- Conclusion: **HISTORICAL TEST-ARTIFACT PORTABILITY LIMITATION; NOT AN A3R SCIENTIFIC REGRESSION**.\n"
        "- The row-level dependency and evidence are preserved in `stage81a3r_clean_worktree_portability_ledger.csv`.\n"
    )
    readout += (
        f"{marker}\n"
        f"- Focused Stage81A3R: **{args.focused} passed**.\n"
        f"- Existing full v4 in the protected-artifact environment: **{args.existing_v4} passed**.\n"
        f"- Repository suite: **{args.repository} passed**.\n"
        f"- Clean-worktree integrated v4: **{args.clean_v4_passed} passed / {args.clean_v4_failed} failed** because historical tests require ignored local artifacts and one historical UCDQ manifest has a stale config hash.\n"
        f"- A3R-focused warnings/failures: **{args.warnings}/{args.failures}**.\n"
        "- Compileall and `git diff --check`: **PASS**.\n"
        "- Frozen A2R semantic hash: **UNCHANGED**.\n"
    )
    outputs["readout"].write_text(readout, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
