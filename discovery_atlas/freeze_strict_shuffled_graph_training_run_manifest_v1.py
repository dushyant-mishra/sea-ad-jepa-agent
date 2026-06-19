from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


EDGE_CSV = Path("results/tables/ablation_edge_sets/strict_shuffled_graph_edges_v1.csv")
ORIGINAL_EDGES = Path("results/tables/v2_graph_consensus_edges.csv")
STAGE_A_CHECKPOINT = Path(
    "results/models/ablation_strict_shuffled_graph_stage_a_v1/"
    "fast_graph_jepa_epoch_030.pt"
)
STAGE_A_FINAL = Path(
    "results/models/ablation_strict_shuffled_graph_stage_a_v1/fast_graph_jepa.pt"
)
STAGE_B_CHECKPOINT = Path(
    "results/models/ablation_strict_shuffled_graph_stage_b_v1/"
    "stage_b_adversarial.pt"
)
STAGE_A_HISTORY = Path(
    "results/tables/ablation_strict_shuffled_graph_stage_a_v1_history.csv"
)
STAGE_B_HISTORY = Path(
    "results/tables/ablation_strict_shuffled_graph_stage_b_v1_history.csv"
)
STAGE_A_LOG = Path("results/logs/ablation_strict_shuffled_graph_stage_a_v1.log")
STAGE_B_LOG = Path("results/logs/ablation_strict_shuffled_graph_stage_b_v1.log")
OLD_PARTIAL_LOG = Path("results/logs/ablation_shuffled_graph_stage_a_v1.log")
TABLE_OUT = Path(
    "results/tables/strict_shuffled_graph_ablation_training_run_manifest_v1.csv"
)
REPORT_OUT = Path(
    "results/reports/strict_shuffled_graph_ablation_training_run_manifest_v1.md"
)

STAGE_A_COMMAND = (
    "conda run -n sea-ad-jepa python scripts/train_graph_jepa_stage_a_fast.py "
    "--h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad "
    "--edge-csv results/tables/ablation_edge_sets/strict_shuffled_graph_edges_v1.csv "
    "--out-dir results/models/ablation_strict_shuffled_graph_stage_a_v1 "
    "--epochs 50 --seed 7 "
    "--history-csv results/tables/"
    "ablation_strict_shuffled_graph_stage_a_v1_history.csv "
    "--log-file results/logs/ablation_strict_shuffled_graph_stage_a_v1.log"
)
STAGE_B_COMMAND = (
    "conda run -n sea-ad-jepa python "
    "scripts/train_graph_jepa_stage_b_adversarial.py "
    "stage_a_checkpoint=results/models/"
    "ablation_strict_shuffled_graph_stage_a_v1/fast_graph_jepa_epoch_030.pt "
    "edge_csv=results/tables/ablation_edge_sets/strict_shuffled_graph_edges_v1.csv "
    "out_dir=results/models/ablation_strict_shuffled_graph_stage_b_v1 "
    "history_csv=results/tables/"
    "ablation_strict_shuffled_graph_stage_b_v1_history.csv "
    "log_file=results/logs/ablation_strict_shuffled_graph_stage_b_v1.log seed=7"
)


def canonical_set(frame: pd.DataFrame) -> set[tuple[int, int]]:
    return set(
        zip(
            np.minimum(frame["source_idx"], frame["target_idx"]).astype(int),
            np.maximum(frame["source_idx"], frame["target_idx"]).astype(int),
        )
    )


def degree(frame: pd.DataFrame, n_nodes: int = 2957) -> np.ndarray:
    values = np.zeros(n_nodes, dtype=np.int64)
    np.add.at(values, frame["source_idx"].to_numpy(dtype=np.int64), 1)
    np.add.at(values, frame["target_idx"].to_numpy(dtype=np.int64), 1)
    return values


def size_mb(path: Path) -> float:
    return round(path.stat().st_size / (1024 * 1024), 3) if path.exists() else 0.0


def completed_from_log(path: Path, needle: str) -> bool:
    return path.exists() and needle in path.read_text(
        encoding="utf-8", errors="replace"
    )


def markdown_table(frame: pd.DataFrame, columns: list[str]) -> list[str]:
    data = frame[columns].copy()
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    lines.extend(
        "| " + " | ".join(str(value).replace("|", "/") for value in row) + " |"
        for row in data.itertuples(index=False, name=None)
    )
    return lines


def main() -> None:
    required = [
        EDGE_CSV,
        ORIGINAL_EDGES,
        STAGE_A_CHECKPOINT,
        STAGE_A_FINAL,
        STAGE_B_CHECKPOINT,
        STAGE_A_HISTORY,
        STAGE_B_HISTORY,
        STAGE_A_LOG,
        STAGE_B_LOG,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing strict-shuffled artifacts: {missing}")

    stage_a_history = pd.read_csv(STAGE_A_HISTORY)
    stage_b_history = pd.read_csv(STAGE_B_HISTORY)
    if len(stage_a_history) != 50 or int(stage_a_history["epoch"].max()) != 50:
        raise ValueError("Stage A history does not contain exactly 50 epochs")
    if len(stage_b_history) != 20 or int(stage_b_history["epoch"].max()) != 20:
        raise ValueError("Stage B history does not contain exactly 20 epochs")

    strict = pd.read_csv(EDGE_CSV)
    original = pd.read_csv(ORIGINAL_EDGES)
    strict_set = canonical_set(strict)
    original_set = canonical_set(original)
    overlap_count = len(strict_set & original_set)
    overlap_fraction = overlap_count / len(original_set)
    degree_preserving = bool(np.array_equal(degree(strict), degree(original)))
    self_loop_count = int((strict["source_idx"] == strict["target_idx"]).sum())
    duplicate_count = len(strict) - len(strict_set)
    if len(strict) != 114029:
        raise ValueError("Strict shuffled graph edge count changed")
    if overlap_count != 0:
        raise ValueError("Strict shuffled graph is no longer zero-overlap")
    if not degree_preserving:
        raise ValueError("Strict shuffled graph does not preserve degree sequence")
    if self_loop_count or duplicate_count:
        raise ValueError("Strict shuffled graph has self-loops or duplicate edges")

    stage_a_clean = completed_from_log(
        STAGE_A_LOG,
        "Wrote results\\models\\ablation_strict_shuffled_graph_stage_a_v1\\fast_graph_jepa.pt",
    )
    stage_b_clean = completed_from_log(
        STAGE_B_LOG,
        "Wrote results\\models\\ablation_strict_shuffled_graph_stage_b_v1\\stage_b_adversarial.pt",
    )
    rows = [
        {
            "run_name": "strict_shuffled_graph_ablation_v1",
            "stage": "stage_a",
            "status": "completed_cleanly" if stage_a_clean else "completed_log_not_confirmed",
            "checkpoint_path": str(STAGE_A_CHECKPOINT),
            "checkpoint_exists": STAGE_A_CHECKPOINT.exists(),
            "checkpoint_size_mb": size_mb(STAGE_A_CHECKPOINT),
            "history_csv": str(STAGE_A_HISTORY),
            "history_exists": STAGE_A_HISTORY.exists(),
            "log_file": str(STAGE_A_LOG),
            "log_exists": STAGE_A_LOG.exists(),
            "edge_csv": str(EDGE_CSV),
            "seed": 7,
            "epochs_requested": 50,
            "checkpoint_epoch_used_for_stage_b": 30,
            "command_used": STAGE_A_COMMAND,
            "output_dir": str(STAGE_A_CHECKPOINT.parent),
            "original_edge_overlap_fraction": overlap_fraction,
            "degree_preserving": degree_preserving,
            "notes": "Stage A completed; epoch 30 was used as the Stage B initialization.",
        },
        {
            "run_name": "strict_shuffled_graph_ablation_v1",
            "stage": "stage_b_adversarial",
            "status": "completed_cleanly" if stage_b_clean else "completed_log_not_confirmed",
            "checkpoint_path": str(STAGE_B_CHECKPOINT),
            "checkpoint_exists": STAGE_B_CHECKPOINT.exists(),
            "checkpoint_size_mb": size_mb(STAGE_B_CHECKPOINT),
            "history_csv": str(STAGE_B_HISTORY),
            "history_exists": STAGE_B_HISTORY.exists(),
            "log_file": str(STAGE_B_LOG),
            "log_exists": STAGE_B_LOG.exists(),
            "edge_csv": str(EDGE_CSV),
            "seed": 7,
            "epochs_requested": 20,
            "checkpoint_epoch_used_for_stage_b": 30,
            "command_used": STAGE_B_COMMAND,
            "output_dir": str(STAGE_B_CHECKPOINT.parent),
            "original_edge_overlap_fraction": overlap_fraction,
            "degree_preserving": degree_preserving,
            "notes": "Stage B adversarial calibration completed from the strict-shuffled Stage A epoch 30 checkpoint.",
        },
    ]
    manifest = pd.DataFrame(rows)
    TABLE_OUT.parent.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(TABLE_OUT, index=False)

    lines = [
        "# Strict-Shuffled Graph Ablation Training Run Manifest v1",
        "",
        "## Run status",
        "",
        *markdown_table(
            manifest,
            [
                "stage",
                "status",
                "checkpoint_path",
                "checkpoint_exists",
                "checkpoint_size_mb",
                "history_exists",
                "log_exists",
            ],
        ),
        "",
        "Stage A completed. Stage B completed.",
        "",
        "## Graph invariant checks",
        "",
        f"- Edge CSV: `{EDGE_CSV}`",
        f"- Edge count: {len(strict):,}",
        f"- Original-edge overlap: {overlap_count} ({overlap_fraction:.1%})",
        f"- Degree preserving: `{degree_preserving}`",
        f"- Self-loops: {self_loop_count}",
        f"- Duplicate undirected edges: {duplicate_count}",
        "",
        "## Commands used",
        "",
        "### Stage A",
        "",
        f"`{STAGE_A_COMMAND}`",
        "",
        "### Stage B",
        "",
        f"`{STAGE_B_COMMAND}`",
        "",
        "## Checkpoint tracking policy",
        "",
        "Checkpoint files remain untracked. Repository policy ignores `results/` by "
        "default and selectively tracks lightweight tables, reports, histories, and "
        "logs; no `.pt` checkpoint files were staged.",
        "",
        "## Boundary",
        "",
        f"- The old partial non-strict log `{OLD_PARTIAL_LOG}` was not reused.",
        "- No external validation was run.",
        "- No downstream strict-shuffled evaluation was run yet.",
        "- Evidence levels and the strict Level-2 gliosis criterion are unchanged.",
        "",
    ]
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(manifest[["stage", "status", "checkpoint_exists", "history_exists"]])
    print(f"Wrote {TABLE_OUT}")
    print(f"Wrote {REPORT_OUT}")


if __name__ == "__main__":
    main()
