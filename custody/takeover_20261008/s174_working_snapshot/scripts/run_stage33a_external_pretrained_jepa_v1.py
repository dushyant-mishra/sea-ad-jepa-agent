from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "results" / "tables"
REPORT_DIR = ROOT / "results" / "reports"

PASS_FAIL_OUT = TABLE_DIR / "stage33a_external_pretrained_pass_fail_v1.csv"
REPORT_OUT = REPORT_DIR / "stage33a_external_pretrained_jepa_report_v1.md"


def load_cfg(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def resolve(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def update_status(pf: pd.DataFrame) -> None:
    row = pf.iloc[0]
    score_path = TABLE_DIR / "v3_scorecard_status_v1.csv"
    score = pd.read_csv(score_path)
    new = {
        "scorecard_item": "stage33a_external_pretrained_jepa",
        "status": "skipped" if bool(row.stage33a_skipped) else "complete",
        "stage": "Stage 33A",
        "metric": "external-pretrained representation benchmark",
        "threshold_or_gate": "run only if Stage 32B approved matrix exists; full pass requires > Stage 27C and graph controls if claimed",
        "current_value": "skipped_no_approved_matrix" if bool(row.stage33a_skipped) else f"{row.best_mean_pooled_oof_spearman:.4f}",
        "pass_fail": "pass" if bool(row.stage33a_full_pass) else "fail",
        "datasets_allowed": "Stage 32B approved external pretraining matrix only",
        "datasets_forbidden": "clean holdouts; SEA-AD in pretraining; external labels/model selection",
        "allowed_claim": row.controlled_interpretation,
        "notes": "No external validation claim; no graph-specific claim unless real graph beats no-graph and strict-shuffled.",
    }
    score = score[score["scorecard_item"] != "stage33a_external_pretrained_jepa"]
    pd.concat([score, pd.DataFrame([new])], ignore_index=True).to_csv(score_path, index=False)

    active_path = ROOT / "docs" / "ACTIVE_V3_STATUS.md"
    text = active_path.read_text(encoding="utf-8")
    marker = "\n\n## Stage 33A external-pretrained benchmark status\n"
    addition = (
        marker
        + f"\nStage 33A status: `{'skipped' if bool(row.stage33a_skipped) else 'complete'}`. "
        + f"Stage 33A full pass: `{bool(row.stage33a_full_pass)}`. "
        + f"Interpretation: `{row.controlled_interpretation}`. "
        + "External validation remains not run, manuscript claims are unchanged, and in silico ablation remains unvalidated.\n"
    )
    active_path.write_text(text.split(marker)[0].rstrip() + addition, encoding="utf-8")

    score_doc = ROOT / "docs" / "V3_SCORECARD.md"
    text = score_doc.read_text(encoding="utf-8")
    marker = "\n\n## Stage 33A external-pretrained JEPA result\n"
    addition = (
        marker
        + f"\nStage 33A skipped: `{bool(row.stage33a_skipped)}`; full pass: `{bool(row.stage33a_full_pass)}`; "
        + f"graph-specific pass: `{bool(row.graph_specific_pass)}`. "
        + f"Interpretation: `{row.controlled_interpretation}`.\n"
    )
    score_doc.write_text(text.split(marker)[0].rstrip() + addition, encoding="utf-8")


def write_skipped_report(cfg: dict[str, Any], stage32b: pd.DataFrame, pf: pd.DataFrame) -> None:
    row = pf.iloc[0]
    lines = [
        "# Stage 33A external-pretrained JEPA report v1",
        "",
        "## Executive summary",
        "",
        "Stage 33A was skipped because Stage 32B did not produce an approved aligned external pretraining matrix.",
        "",
        "## Gate check",
        "",
        "```csv",
        stage32b.to_csv(index=False).strip(),
        "```",
        "",
        "## Pass/fail",
        "",
        "```csv",
        pf.to_csv(index=False).strip(),
        "```",
        "",
        "## What was not run",
        "",
        "- No JEPA or Graph-JEPA model was trained.",
        "- No downstream predictor was trained.",
        "- No external labels, clean holdouts, or SEA-AD pathology targets were used for pretraining.",
        "- No manuscript or benchmark claim was updated.",
        "",
        "## Required next action",
        "",
        "Manually approve/download/build one registry-approved external pretraining matrix via Stage 32B, then rerun Stage 33A.",
        "",
        "## Interpretation boundary",
        "",
        f"{row.controlled_interpretation}. This is not external validation, graph topology validation, causal evidence, therapeutic evidence, or in silico ablation validation.",
    ]
    REPORT_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/train/stage33a_external_pretrained_jepa_v1.yaml")
    args = parser.parse_args()
    cfg = load_cfg(resolve(args.config))
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    stage32b_path = resolve(cfg["stage32b_pass_fail_path"])
    if not stage32b_path.exists():
        raise FileNotFoundError(f"Missing Stage 32B pass/fail gate: {stage32b_path}")
    stage32b = pd.read_csv(stage32b_path)
    ready = bool(stage32b.iloc[0].get("stage32b_ready_for_stage33a", False))
    matrix_path = resolve(cfg["stage32b_matrix_path"])

    if not ready or not matrix_path.exists():
        pf = pd.DataFrame(
            [
                {
                    "stage33a_run": False,
                    "stage33a_skipped": True,
                    "skip_reason": "stage32b_ready_for_stage33a_false_or_matrix_missing",
                    "stage32b_ready_for_stage33a": ready,
                    "stage32b_matrix_path_exists": matrix_path.exists(),
                    "best_stage33a_condition": "",
                    "best_mean_pooled_oof_spearman": float("nan"),
                    "stage27c_reference_mean": float(cfg["stage27c_reference_mean"]),
                    "stage31_best_reference_mean": float(cfg["stage31_best_reference_mean"]),
                    "best_minus_stage27c_reference": float("nan"),
                    "best_minus_stage31_reference": float("nan"),
                    "graph_specific_pass": False,
                    "stage33a_full_pass": False,
                    "controlled_interpretation": "Stage 33A skipped because no approved external pretraining matrix was available",
                    "external_validation_claim": False,
                    "manuscript_claim_update": False,
                    "clean_holdout_used": False,
                    "external_labels_used_for_supervision": False,
                }
            ]
        )
        pf.to_csv(PASS_FAIL_OUT, index=False)
        write_skipped_report(cfg, stage32b, pf)
        update_status(pf)
        print("stage33a_run=False")
        print("stage33a_skipped=True")
        print("best_stage33a_condition=")
        print("mean_pooled_oof_spearman=")
        print("comparison_vs_stage27c=")
        print("comparison_vs_stage31=")
        print("graph_specific_pass=False")
        print("stage33a_full_pass=False")
        return

    raise NotImplementedError(
        "Stage 33A training path is intentionally guarded and was not reached. "
        "Implement frozen external-pretrained encoder benchmark only after Stage 32B builds an approved matrix."
    )


if __name__ == "__main__":
    main()
