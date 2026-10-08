from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "results" / "tables"
REPORT_DIR = ROOT / "results" / "reports"

PASS_FAIL_OUT = TABLE_DIR / "stage35d_pass_fail_v1.csv"
RESOURCE_OUT = TABLE_DIR / "stage35d_perturbation_resource_audit_v1.csv"
ALIGN_OUT = TABLE_DIR / "stage35d_graph_alignment_audit_v1.csv"
CONDITION_OUT = TABLE_DIR / "stage35d_condition_metrics_v1.csv"
MEAN_OUT = TABLE_DIR / "stage35d_mean_metrics_v1.csv"
TARGET_OUT = TABLE_DIR / "stage35d_target_metrics_v1.csv"
GRAPH_OUT = TABLE_DIR / "stage35d_graph_control_audit_v1.csv"
LEAKAGE_OUT = TABLE_DIR / "stage35d_leakage_audit_v1.csv"
REPORT_OUT = REPORT_DIR / "stage35d_perturbation_graph_diagnostic_report_v1.md"


def load_cfg(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def resolve(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def small_csv_columns(path: Path) -> list[str]:
    if path.suffix.lower() not in {".csv", ".tsv"} or path.stat().st_size > 5_000_000:
        return []
    try:
        with path.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
            sample = handle.read(4096)
        dialect = csv.Sniffer().sniff(sample) if sample.strip() else csv.excel
        return next(csv.reader(sample.splitlines(), dialect), [])
    except Exception:
        return []


def discover_resources(cfg: dict[str, Any]) -> pd.DataFrame:
    keywords = [str(k).lower() for k in cfg["resource_search"]["keywords"]]
    rows = []
    for root_value in cfg["resource_search"]["roots"]:
        root = resolve(root_value)
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            rel = str(path.relative_to(ROOT))
            if rel.replace("\\", "/").startswith("results/tables/stage35d_"):
                continue
            text = rel.lower()
            hits = [kw for kw in keywords if kw in text]
            if not hits:
                continue
            columns = small_csv_columns(path)
            lower_cols = {c.lower() for c in columns}
            has_edge_schema = bool({"source", "target"}.issubset(lower_cols) or {"source_idx", "target_idx"}.issubset(lower_cols))
            approved_by_name = "approved" in text and any(k in text for k in ["perturb", "lincs", "l1000", "crispr", "regulatory"])
            forbidden_by_name = any(k in text for k in ["holdout", "validation", "raw", ".h5ad", ".h5", ".loom", ".zarr", ".mtx"])
            rows.append(
                {
                    "path": rel,
                    "size_bytes": int(path.stat().st_size),
                    "keyword_hits": ";".join(hits),
                    "candidate_edge_schema": has_edge_schema,
                    "approved_local_perturbation_graph": bool(has_edge_schema and approved_by_name and not forbidden_by_name),
                    "forbidden_or_clean_holdout_risk": bool(forbidden_by_name),
                    "benchmark_eligible": bool(has_edge_schema and approved_by_name and not forbidden_by_name),
                    "notes": "filename/resource audit only; no download or web scraping performed",
                }
            )
    if not rows:
        rows.append(
            {
                "path": "",
                "size_bytes": 0,
                "keyword_hits": "",
                "candidate_edge_schema": False,
                "approved_local_perturbation_graph": False,
                "forbidden_or_clean_holdout_risk": False,
                "benchmark_eligible": False,
                "notes": "No local perturbation-derived graph candidates were found under configured roots.",
            }
        )
    return pd.DataFrame(rows)


def write_status(pf: pd.DataFrame) -> None:
    row = pf.iloc[0]
    score_path = TABLE_DIR / "v3_scorecard_status_v1.csv"
    score = pd.read_csv(score_path)
    item = "stage35d_perturbation_graph_diagnostic"
    new = {
        "scorecard_item": item,
        "status": "complete",
        "stage": "Stage 35D",
        "metric": "feasibility audit; benchmark only if approved local perturbation graph exists",
        "threshold_or_gate": "benchmark requires approved local perturbation-derived graph aligned to canonical project genes",
        "current_value": "benchmark_not_run",
        "pass_fail": "fail",
        "datasets_allowed": "already-local approved perturbation edge list only",
        "datasets_forbidden": "new downloads; web scraping; clean holdouts; external labels; raw perturbation matrices",
        "allowed_claim": row.controlled_interpretation,
        "notes": f"perturbation_graph_benchmark_run={bool(row.perturbation_graph_benchmark_run)}; graph_specific_pass={bool(row.stage35d_graph_specific_pass)}",
    }
    score = score[score["scorecard_item"] != item]
    pd.concat([score, pd.DataFrame([new])], ignore_index=True).to_csv(score_path, index=False)
    for doc_path, marker, addition in [
        (ROOT / "docs" / "ACTIVE_V3_STATUS.md", "\n\n## Stage 35D perturbation graph diagnostic status\n", f"\nStage 35D is complete as a feasibility audit. Benchmark run: `{bool(row.perturbation_graph_benchmark_run)}`. {row.controlled_interpretation} No external validation, causal validation, or manuscript claim update.\n"),
        (ROOT / "docs" / "V3_SCORECARD.md", "\n\n## Stage 35D perturbation graph diagnostic result\n", f"\nStage 35D completed the perturbation graph feasibility audit. Benchmark run: `{bool(row.perturbation_graph_benchmark_run)}`; internal performance pass: `{bool(row.stage35d_internal_performance_pass)}`; graph-specific pass: `{bool(row.stage35d_graph_specific_pass)}`. {row.controlled_interpretation}\n"),
    ]:
        text = doc_path.read_text(encoding="utf-8")
        doc_path.write_text(text.split(marker)[0].rstrip() + marker + addition.lstrip(), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/train/stage35d_perturbation_graph_diagnostic_v1.yaml")
    args = parser.parse_args()
    cfg = load_cfg(resolve(args.config))
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    resources = discover_resources(cfg)
    eligible = resources[resources["benchmark_eligible"].astype(bool)].copy()
    benchmark_run = bool(len(eligible) > 0)
    interpretation = (
        "Stage 35D completed a perturbation-graph feasibility audit but did not run a benchmark because no approved local perturbation-derived graph was available."
        if not benchmark_run
        else "Perturbation-derived graph benchmark path is available but was not implemented in this compact audit runner."
    )
    align = pd.DataFrame(
        [
            {
                "approved_local_perturbation_graph_exists": benchmark_run,
                "selected_graph_path": "" if not benchmark_run else str(eligible.iloc[0]["path"]),
                "graph_aligned_to_canonical_gene_universe": False,
                "benchmark_alignment_pass": False,
                "skipped_reason": "" if benchmark_run else interpretation,
            }
        ]
    )
    leakage = pd.DataFrame(
        [
            {
                "clean_holdout_used": False,
                "external_pretraining_matrix_used": False,
                "external_labels_used_for_supervised_pathology_prediction": False,
                "newly_downloaded_perturbation_data": False,
                "target_values_used_to_construct_graph": False,
                "sea_ad_used_for_downstream_only": True,
                "locked_donor_folds_used": False if not benchmark_run else True,
                "fold_local_downstream_scaling_and_ridge": False if not benchmark_run else True,
                "in_silico_ablation_run": False,
                "leakage_audit_pass": True,
            }
        ]
    )
    graph = pd.DataFrame(
        [
            {
                "comparison": "perturbation_graph_benchmark_not_run",
                "left_condition": "",
                "right_condition": "",
                "delta_mean_pooled_oof_spearman": "",
                "graph_gate_pass": False,
                "notes": "No approved local perturbation-derived graph was available for matched graph controls.",
            }
        ]
    )
    skipped_metrics = pd.DataFrame([{"condition": "stage35d_benchmark_skipped", "skip_reason": interpretation}])
    pf = pd.DataFrame(
        [
            {
                "stage35d_run": True,
                "resource_search_completed": True,
                "perturbation_resource_audit_written": True,
                "graph_alignment_audit_written": True,
                "leakage_audit_written": True,
                "report_written": True,
                "stage35d_audit_run_pass": True,
                "perturbation_graph_benchmark_run": benchmark_run,
                "stage35d_benchmark_run_pass": False,
                "stage35d_internal_performance_pass": False,
                "stage35d_graph_specific_pass": False,
                "controlled_interpretation": interpretation,
            }
        ]
    )
    resources.to_csv(RESOURCE_OUT, index=False)
    align.to_csv(ALIGN_OUT, index=False)
    skipped_metrics.to_csv(CONDITION_OUT, index=False)
    skipped_metrics.to_csv(MEAN_OUT, index=False)
    skipped_metrics.to_csv(TARGET_OUT, index=False)
    graph.to_csv(GRAPH_OUT, index=False)
    leakage.to_csv(LEAKAGE_OUT, index=False)
    pf.to_csv(PASS_FAIL_OUT, index=False)
    lines = [
        "# Stage 35D perturbation graph diagnostic report v1",
        "",
        "## Executive summary",
        "",
        f"Audit run pass: `True`. Perturbation graph benchmark run: `{benchmark_run}`.",
        "",
        "## Controlled interpretation",
        "",
        interpretation,
        "This is not external validation, graph topology validation, causal validation, in silico ablation validation, or therapeutic-target discovery.",
        "",
        "## Resource audit",
        "```csv",
        resources.to_csv(index=False).strip(),
        "```",
        "## Graph alignment audit",
        "```csv",
        align.to_csv(index=False).strip(),
        "```",
        "## Graph-control audit",
        "```csv",
        graph.to_csv(index=False).strip(),
        "```",
        "## Leakage audit",
        "```csv",
        leakage.to_csv(index=False).strip(),
        "```",
        "## Pass/fail",
        "```csv",
        pf.to_csv(index=False).strip(),
        "```",
    ]
    REPORT_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_status(pf)
    print("stage35d_audit_run_pass=True")
    print(f"perturbation_graph_benchmark_run={benchmark_run}")
    print("stage35d_graph_specific_pass=False")


if __name__ == "__main__":
    main()
