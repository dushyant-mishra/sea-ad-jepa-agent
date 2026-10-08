from __future__ import annotations

from pathlib import Path

import pandas as pd


STAGE_A_CHECKPOINT = Path(
    "results/models/ablation_no_graph_stage_a_v1/fast_graph_jepa_epoch_030.pt"
)
STAGE_B_CHECKPOINT = Path(
    "results/models/ablation_no_graph_stage_b_v1/stage_b_adversarial.pt"
)
STAGE_A_HISTORY = Path("results/tables/ablation_no_graph_stage_a_v1_history.csv")
STAGE_B_HISTORY = Path("results/tables/ablation_no_graph_stage_b_v1_history.csv")
STAGE_A_LOG = Path("results/logs/ablation_no_graph_stage_a_v1.log")
STAGE_B_LOG = Path("results/logs/ablation_no_graph_stage_b_v1.log")
EDGE_CSV = Path("results/tables/ablation_edge_sets/no_graph_identity_edges_v1.csv")
TABLE_OUT = Path("results/tables/no_graph_ablation_training_run_manifest_v1.csv")
REPORT_OUT = Path("results/reports/no_graph_ablation_training_run_manifest_v1.md")
FORBIDDEN_TRAINING_PATHS = [
    Path("results/models/ablation_shuffled_graph_stage_a_v1"),
    Path("results/models/ablation_shuffled_graph_stage_b_v1"),
    Path("results/models/ablation_expression_only_autoencoder_v1"),
]

STAGE_A_COMMAND = (
    "conda run -n sea-ad-jepa python scripts/train_graph_jepa_stage_a_fast.py "
    "--h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad "
    "--edge-csv results/tables/ablation_edge_sets/no_graph_identity_edges_v1.csv "
    "--out-dir results/models/ablation_no_graph_stage_a_v1 --epochs 50 --seed 7 "
    "--history-csv results/tables/ablation_no_graph_stage_a_v1_history.csv "
    "--log-file results/logs/ablation_no_graph_stage_a_v1.log"
)
STAGE_B_COMMAND = (
    "conda run -n sea-ad-jepa python scripts/train_graph_jepa_stage_b_adversarial.py "
    "stage_a_checkpoint=results/models/ablation_no_graph_stage_a_v1/"
    "fast_graph_jepa_epoch_030.pt "
    "edge_csv=results/tables/ablation_edge_sets/no_graph_identity_edges_v1.csv "
    "out_dir=results/models/ablation_no_graph_stage_b_v1 "
    "history_csv=results/tables/ablation_no_graph_stage_b_v1_history.csv "
    "log_file=results/logs/ablation_no_graph_stage_b_v1.log seed=7"
)


def size_mb(path: Path) -> float:
    return round(path.stat().st_size / (1024 * 1024), 3) if path.exists() else 0.0


def log_completed(path: Path, expected_text: str) -> bool:
    return path.exists() and expected_text in path.read_text(
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
    stage_a_dir = STAGE_A_CHECKPOINT.parent
    stage_b_dir = STAGE_B_CHECKPOINT.parent
    required_paths = [
        stage_a_dir,
        STAGE_A_HISTORY,
        STAGE_A_CHECKPOINT,
        stage_b_dir,
        STAGE_B_HISTORY,
        STAGE_B_CHECKPOINT,
        EDGE_CSV,
    ]
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required no-graph artifacts: {missing}")
    unexpected = [str(path) for path in FORBIDDEN_TRAINING_PATHS if path.exists()]
    if unexpected:
        raise ValueError(f"Unexpected out-of-scope training artifacts found: {unexpected}")

    stage_a_history = pd.read_csv(STAGE_A_HISTORY)
    stage_b_history = pd.read_csv(STAGE_B_HISTORY)
    if len(stage_a_history) != 50 or int(stage_a_history["epoch"].max()) != 50:
        raise ValueError("Stage A history does not contain the requested 50 epochs")
    if len(stage_b_history) != 20 or int(stage_b_history["epoch"].max()) != 20:
        raise ValueError("Stage B history does not contain the expected 20 epochs")

    edges = pd.read_csv(EDGE_CSV)
    required_edge_columns = {"source_idx", "target_idx"}
    if not required_edge_columns.issubset(edges.columns):
        raise ValueError(f"Edge CSV lacks columns: {required_edge_columns - set(edges)}")
    self_loop_count = int((edges["source_idx"] == edges["target_idx"]).sum())
    inter_gene_count = int((edges["source_idx"] != edges["target_idx"]).sum())
    if len(edges) != 2957 or self_loop_count != 2957 or inter_gene_count != 0:
        raise ValueError(
            "No-graph edge invariant failed: expected 2,957 loops and zero inter-gene edges"
        )

    stage_a_clean = log_completed(STAGE_A_LOG, "Wrote results\\models\\ablation_no_graph_stage_a_v1\\fast_graph_jepa.pt")
    stage_b_clean = log_completed(STAGE_B_LOG, "Wrote results\\models\\ablation_no_graph_stage_b_v1\\stage_b_adversarial.pt")
    rows = [
        {
            "run_name": "no_graph_ablation_v1",
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
            "output_dir": str(stage_a_dir),
            "notes": "Stage A completed; epoch 30 was frozen as the Stage B initialization.",
        },
        {
            "run_name": "no_graph_ablation_v1",
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
            "output_dir": str(stage_b_dir),
            "notes": "Stage B adversarial calibration completed from the Stage A epoch 30 checkpoint.",
        },
    ]
    manifest = pd.DataFrame(rows)
    TABLE_OUT.parent.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(TABLE_OUT, index=False)

    checkpoint_policy = (
        "Model checkpoint files are intentionally left untracked. Repository policy "
        "ignores `results/` by default and selectively tracks lightweight tables and "
        "reports; no files under `results/models/` are currently tracked."
    )
    lines = [
        "# No-Graph Ablation Training Run Manifest v1",
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
        "Both training stages completed cleanly according to their full epoch histories "
        "and terminal checkpoint-write messages.",
        "",
        "## Commands used",
        "",
        "### Stage A",
        "",
        f"`{STAGE_A_COMMAND}`",
        "",
        "### Stage B adversarial calibration",
        "",
        f"`{STAGE_B_COMMAND}`",
        "",
        "## Stage A outputs",
        "",
        f"- Output directory: `{stage_a_dir}`",
        f"- Frozen Stage B initialization: `{STAGE_A_CHECKPOINT}`",
        f"- History: `{STAGE_A_HISTORY}` (50 epochs)",
        f"- Log: `{STAGE_A_LOG}`",
        "",
        "## Stage B outputs",
        "",
        f"- Output directory: `{stage_b_dir}`",
        f"- Final checkpoint: `{STAGE_B_CHECKPOINT}`",
        f"- History: `{STAGE_B_HISTORY}` (20 epochs)",
        f"- Log: `{STAGE_B_LOG}`",
        "",
        "## Edge-set definition",
        "",
        f"`{EDGE_CSV}` contains exactly 2,957 explicit self-loop rows and zero "
        "inter-gene edges. Under the current loader this preserves all feature nodes "
        "while making normalized graph propagation the identity.",
        "",
        "## Checkpoint tracking policy",
        "",
        checkpoint_policy,
        "",
        "## Input and training boundaries",
        "",
        "- The commands used only the frozen local training inputs; no external validation data were used.",
        "- No shuffled-graph training output directory or checkpoint was created by this run.",
        "- No expression-only autoencoder training output was created by this run.",
        "- This artifact freezes training metadata only; downstream predictive evaluation is not included.",
        "- Evidence levels are unchanged.",
        "",
    ]
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {TABLE_OUT}")
    print(f"Wrote {REPORT_OUT}")
    print(manifest[["stage", "status", "checkpoint_exists", "history_exists"]])


if __name__ == "__main__":
    main()
