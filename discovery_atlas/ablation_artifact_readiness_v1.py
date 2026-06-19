from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inventory existing ablation artifacts and safe future templates."
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "results/tables/discovery_ablation_artifact_inventory_v1.csv"
        ),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path(
            "results/reports/discovery_ablation_artifact_readiness_v1.md"
        ),
    )
    return parser.parse_args()


def help_info(script: Path) -> tuple[list[str], str]:
    if not script.exists():
        return [], "script_missing"
    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    output = result.stdout + "\n" + result.stderr
    flags = sorted(set(re.findall(r"(?<!\w)--[A-Za-z0-9_.-]+", output)))
    status = "help_inspected" if result.returncode == 0 else f"help_failed_returncode_{result.returncode}"
    return flags, status


def find_artifacts(patterns: list[str]) -> list[Path]:
    root = Path("results/models")
    if not root.exists():
        return []
    found = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        lower = str(path).lower()
        if any(re.search(pattern, lower) for pattern in patterns):
            found.append(path)
    return sorted(found)


def main() -> None:
    args = parse_args()
    stage_a_script = Path("scripts/train_graph_jepa_stage_a_fast.py")
    stage_b_script = Path("scripts/train_graph_jepa_stage_b_adversarial.py")
    expression_script = Path("scripts/train_jepa_snrna.py")
    stage_a_flags, stage_a_help = help_info(stage_a_script)
    stage_b_flags, stage_b_help = help_info(stage_b_script)
    expression_flags, expression_help = help_info(expression_script)

    real_graph = Path(
        "results/models/v2_2_stage_b_adversarial/stage_b_adversarial.pt"
    )
    pathology_head = Path(
        "results/models/pathology_heads_stage_b_lp/best_pathology_head.pt"
    )
    shuffled = find_artifacts([r"shuffl"])
    no_graph = find_artifacts([r"no[_-]?graph", r"nograph", r"identity[_-]?graph"])
    autoencoder = find_artifacts([r"autoencoder", r"\bae\b"])

    stage_a_flag_text = " ".join(stage_a_flags)
    stage_b_flag_text = " ".join(stage_b_flags)
    expression_flag_text = " ".join(expression_flags)
    stage_a_smoke_supported = all(
        flag in stage_a_flags
        for flag in ["--epochs", "--max-cells", "--batch-size", "--out-dir"]
    )
    stage_a_smoke = (
        "python scripts/train_graph_jepa_stage_a_fast.py "
        "--epochs 1 --max-cells 256 --batch-size 32 "
        "--out-dir results/models/smoke_tests/graph_jepa_stage_a "
        "--history-csv results/tables/smoke_graph_jepa_stage_a_history.csv "
        "--log-file results/logs/smoke_graph_jepa_stage_a.log"
        if stage_a_smoke_supported
        else "smoke_training_not_supported_without_script_patch"
    )
    stage_b_smoke = (
        "python scripts/train_graph_jepa_stage_b_adversarial.py "
        "epochs=1 max_steps_per_epoch=2 per_domain_batch_size=8 "
        "out_dir=results/models/smoke_tests/stage_b_adversarial "
        "history_csv=results/tables/smoke_stage_b_adversarial_history.csv "
        "log_file=results/logs/smoke_stage_b_adversarial.log"
        if stage_b_help == "help_inspected"
        and all(
            token in stage_b_flag_text or token in (Path("configs/train/stage_b_adversarial.yaml").read_text(encoding="utf-8") if Path("configs/train/stage_b_adversarial.yaml").exists() else "")
            for token in ["epochs", "max_steps_per_epoch", "per_domain_batch_size", "out_dir"]
        )
        else "smoke_training_not_supported_without_script_patch"
    )

    rows = [
        {
            "artifact_name": "real_graph_stage_b_jepa",
            "artifact_type": "trained_graph_jepa",
            "expected_path": str(real_graph),
            "status": "found_existing_artifact" if real_graph.exists() else "missing_required_artifact",
            "existing_path": str(real_graph) if real_graph.exists() else "",
            "training_script_candidate": str(stage_b_script),
            "confirmed_script_flags": stage_b_flag_text,
            "config_candidate": "configs/train/stage_b_adversarial.yaml",
            "smoke_test_command": stage_b_smoke,
            "full_training_command_template": (
                "python scripts/train_graph_jepa_stage_b_adversarial.py "
                "stage_a_checkpoint=<checkpoint> out_dir=<output> epochs=<epochs>"
            ),
            "notes": stage_b_help,
        },
        {
            "artifact_name": "pathology_head",
            "artifact_type": "frozen_pathology_readout",
            "expected_path": str(pathology_head),
            "status": "found_existing_artifact" if pathology_head.exists() else "missing_required_artifact",
            "existing_path": str(pathology_head) if pathology_head.exists() else "",
            "training_script_candidate": "",
            "confirmed_script_flags": "",
            "config_candidate": "",
            "smoke_test_command": "not_applicable",
            "full_training_command_template": "not_assessed_in_ablation_stage",
            "notes": "Existing frozen pathology head used by current counterfactual pipeline.",
        },
        {
            "artifact_name": "shuffled_graph_jepa",
            "artifact_type": "graph_ablation",
            "expected_path": "results/models/<future_shuffled_graph_jepa>/",
            "status": "found_existing_artifact" if shuffled else "not_available_existing_artifact",
            "existing_path": "|".join(map(str, shuffled)),
            "training_script_candidate": str(stage_a_script),
            "confirmed_script_flags": stage_a_flag_text,
            "config_candidate": "configs/train/graph_jepa_stage_a_fast.yaml",
            "smoke_test_command": (
                "smoke_training_not_supported_without_script_patch; "
                "a reproducible shuffled-edge generator/input is not exposed by confirmed flags"
            ),
            "full_training_command_template": (
                "python scripts/train_graph_jepa_stage_a_fast.py "
                "--edge-csv <precomputed_shuffled_edge_csv> --out-dir <output> "
                "--epochs <epochs> --h5ad <h5ad>"
            ),
            "notes": f"{stage_a_help}; requires a precomputed deterministic shuffled edge CSV.",
        },
        {
            "artifact_name": "no_graph_jepa",
            "artifact_type": "graph_ablation",
            "expected_path": "results/models/<future_no_graph_jepa>/",
            "status": "found_existing_artifact" if no_graph else "not_available_existing_artifact",
            "existing_path": "|".join(map(str, no_graph)),
            "training_script_candidate": str(stage_a_script),
            "confirmed_script_flags": stage_a_flag_text,
            "config_candidate": "configs/train/graph_jepa_stage_a_fast.yaml",
            "smoke_test_command": (
                "smoke_training_not_supported_without_script_patch; "
                "identity/no-graph topology is not exposed by confirmed flags"
            ),
            "full_training_command_template": (
                "requires_script_patch_or_precomputed_identity_edge_csv; "
                "then use confirmed --edge-csv --out-dir --epochs --h5ad flags"
            ),
            "notes": f"{stage_a_help}; no explicit no-graph/identity-graph mode was confirmed.",
        },
        {
            "artifact_name": "expression_only_autoencoder",
            "artifact_type": "expression_baseline",
            "expected_path": "results/models/<future_expression_only_autoencoder>/",
            "status": "found_existing_artifact" if autoencoder else "not_available_existing_artifact",
            "existing_path": "|".join(map(str, autoencoder)),
            "training_script_candidate": str(expression_script),
            "confirmed_script_flags": expression_flag_text,
            "config_candidate": "",
            "smoke_test_command": "smoke_training_not_supported_without_script_patch",
            "full_training_command_template": "not_generated_help_failed_or_no_confirmed_flags",
            "notes": expression_help,
        },
    ]
    inventory = pd.DataFrame(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    inventory.to_csv(args.out, index=False)

    existing = inventory[inventory["status"].eq("found_existing_artifact")]
    missing = inventory[inventory["status"].eq("not_available_existing_artifact")]
    lines = [
        "# Discovery Ablation Artifact Readiness v1",
        "",
        "## Existing usable artifacts",
        "",
        *[
            f"- `{row.artifact_name}`: `{row.existing_path}`"
            for row in existing.itertuples(index=False)
        ],
        "",
        "## Missing ablation artifacts",
        "",
        *[
            f"- `{row.artifact_name}`: `{row.status}`"
            for row in missing.itertuples(index=False)
        ],
        "",
        "## Confirmed script flags and safe command templates",
        "",
        "| artifact | script | help status / notes | smoke command | full template |",
        "| --- | --- | --- | --- | --- |",
        *[
            "| "
            + " | ".join(
                str(value).replace("|", "/")
                for value in [
                    row.artifact_name,
                    row.training_script_candidate,
                    row.notes,
                    row.smoke_test_command,
                    row.full_training_command_template,
                ]
            )
            + " |"
            for row in inventory.itertuples(index=False)
        ],
        "",
        "## What is needed to test graph contribution rigorously",
        "",
        "- Train matched shuffled-graph and identity/no-graph models with the same feature space, architecture, masks, optimization budget, seeds, and evaluation folds.",
        "- Define the shuffled topology generator and identity/no-graph semantics before training.",
        "- Add an expression-only learned baseline only after its training script and objective are explicitly specified.",
        "",
        "## Boundary",
        "",
        "- Missing ablations are not negative evidence.",
        "- No new ablation model was trained in this stage.",
        "- Future ablation training requires explicit approval.",
        "",
    ]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines), encoding="utf-8")
    print(inventory[["artifact_name", "status"]].to_string(index=False))
    print(f"Wrote {args.out}")
    print(f"Wrote {args.report}")


if __name__ == "__main__":
    main()
