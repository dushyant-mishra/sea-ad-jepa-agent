from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pandas as pd


EDGE_CSV = Path("results/tables/ablation_edge_sets/shuffled_graph_edges_v1.csv")
EDGE_MANIFEST = Path(
    "results/tables/ablation_edge_sets/graph_ablation_edge_set_manifest_v1.csv"
)
H5AD = Path(
    "data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad"
)
STAGE_A_SCRIPT = Path("scripts/train_graph_jepa_stage_a_fast.py")
STAGE_B_SCRIPT = Path("scripts/train_graph_jepa_stage_b_adversarial.py")
PROTOCOL = Path("results/reports/discovery_ablation_training_protocol_v1.md")
STAGE_A_DIR = Path("results/models/ablation_shuffled_graph_stage_a_v1")
STAGE_B_DIR = Path("results/models/ablation_shuffled_graph_stage_b_v1")
TABLE_OUT = Path("results/tables/shuffled_graph_ablation_preflight_v1.csv")
REPORT_OUT = Path("results/reports/shuffled_graph_ablation_preflight_v1.md")

REQUIRED_STAGE_A_FLAGS = [
    "--edge-csv",
    "--out-dir",
    "--epochs",
    "--h5ad",
    "--seed",
    "--history-csv",
    "--log-file",
]

STAGE_A_COMMAND = (
    "conda run -n sea-ad-jepa python scripts/train_graph_jepa_stage_a_fast.py "
    "--h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad "
    "--edge-csv results/tables/ablation_edge_sets/shuffled_graph_edges_v1.csv "
    "--out-dir results/models/ablation_shuffled_graph_stage_a_v1 "
    "--epochs 50 --seed 7 "
    "--history-csv results/tables/ablation_shuffled_graph_stage_a_v1_history.csv "
    "--log-file results/logs/ablation_shuffled_graph_stage_a_v1.log"
)
STAGE_B_COMMAND = (
    "conda run -n sea-ad-jepa python "
    "scripts/train_graph_jepa_stage_b_adversarial.py "
    "stage_a_checkpoint=results/models/ablation_shuffled_graph_stage_a_v1/"
    "fast_graph_jepa_epoch_030.pt "
    "edge_csv=results/tables/ablation_edge_sets/shuffled_graph_edges_v1.csv "
    "out_dir=results/models/ablation_shuffled_graph_stage_b_v1 "
    "history_csv=results/tables/ablation_shuffled_graph_stage_b_v1_history.csv "
    "log_file=results/logs/ablation_shuffled_graph_stage_b_v1.log seed=7"
)


def add_check(
    rows: list[dict[str, str]],
    check_name: str,
    passed: bool,
    observed: object,
    expected: object,
    notes: str,
    *,
    warning: bool = False,
) -> None:
    status = "pass" if passed else ("warning" if warning else "fail")
    rows.append(
        {
            "check_name": check_name,
            "status": status,
            "observed": str(observed),
            "expected": str(expected),
            "notes": notes,
        }
    )


def finished_checkpoints(path: Path) -> list[str]:
    if not path.exists():
        return []
    return sorted(
        item.name
        for item in path.glob("*.pt")
        if item.name in {"fast_graph_jepa.pt", "stage_b_adversarial.pt"}
    )


def markdown_table(frame: pd.DataFrame) -> list[str]:
    columns = frame.columns.tolist()
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    lines.extend(
        "| " + " | ".join(str(value).replace("|", "/") for value in row) + " |"
        for row in frame.itertuples(index=False, name=None)
    )
    return lines


def main() -> None:
    rows: list[dict[str, str]] = []
    add_check(
        rows,
        "shuffled_edge_file_exists",
        EDGE_CSV.exists(),
        EDGE_CSV.exists(),
        True,
        str(EDGE_CSV),
    )

    edges = pd.read_csv(EDGE_CSV) if EDGE_CSV.exists() else pd.DataFrame()
    add_check(
        rows,
        "shuffled_edge_count",
        len(edges) == 114029,
        len(edges),
        114029,
        "The source file stores each undirected edge once.",
    )
    required_columns = {"source_idx", "target_idx"}
    columns_present = required_columns.issubset(edges.columns)
    duplicate_count = (
        int(edges.duplicated(["source_idx", "target_idx"]).sum())
        if columns_present
        else -1
    )
    self_loop_count = (
        int((edges["source_idx"] == edges["target_idx"]).sum())
        if columns_present
        else -1
    )
    incident_node_count = (
        len(set(edges["source_idx"]).union(edges["target_idx"]))
        if columns_present
        else 0
    )
    indexed_node_count = (
        int(max(edges["source_idx"].max(), edges["target_idx"].max())) + 1
        if columns_present and not edges.empty
        else 0
    )
    add_check(
        rows,
        "shuffled_zero_duplicate_edges",
        duplicate_count == 0,
        duplicate_count,
        0,
        "Exact stored source-target pairs.",
    )
    add_check(
        rows,
        "shuffled_zero_self_loops",
        self_loop_count == 0,
        self_loop_count,
        0,
        "Self-loops are not part of the shuffled source edge set.",
    )
    add_check(
        rows,
        "shuffled_node_coverage",
        indexed_node_count == 2957,
        (
            f"indexed_node_count={indexed_node_count}; "
            f"incident_nodes={incident_node_count}; "
            f"degree_zero_nodes={indexed_node_count - incident_node_count}"
        ),
        "2,957-node indexed feature space",
        (
            "The CSV spans indices 0-2956. Degree-zero nodes have no inter-gene "
            "rows but remain represented because the loader infers 2,957 nodes "
            "and adds self-loops."
        ),
    )

    manifest = pd.read_csv(EDGE_MANIFEST) if EDGE_MANIFEST.exists() else pd.DataFrame()
    selected = (
        manifest.loc[manifest["edge_set_name"].eq("shuffled_graph_edges_v1")]
        if "edge_set_name" in manifest
        else pd.DataFrame()
    )
    manifest_row = selected.iloc[0] if len(selected) == 1 else None
    degree_preserving = (
        str(manifest_row["degree_preserving"]).lower() == "true"
        if manifest_row is not None
        else False
    )
    shuffle_seed = (
        int(float(manifest_row["shuffle_seed"]))
        if manifest_row is not None and pd.notna(manifest_row["shuffle_seed"])
        else None
    )
    notes = str(manifest_row["notes"]) if manifest_row is not None else ""
    overlap_match = re.search(r"overlap fraction=([0-9]+(?:\.[0-9]+)?)", notes)
    overlap = float(overlap_match.group(1)) if overlap_match else None
    add_check(
        rows,
        "manifest_degree_preserving",
        degree_preserving,
        degree_preserving,
        True,
        str(EDGE_MANIFEST),
    )
    add_check(
        rows,
        "manifest_shuffle_seed",
        shuffle_seed == 20260619,
        shuffle_seed,
        20260619,
        str(EDGE_MANIFEST),
    )
    add_check(
        rows,
        "original_edge_overlap_recorded",
        overlap is not None and abs(overlap - 0.2439) <= 0.001,
        overlap,
        "approximately 0.2439 (24.39%)",
        notes,
    )

    add_check(rows, "h5ad_exists", H5AD.exists(), H5AD.exists(), True, str(H5AD))
    add_check(
        rows,
        "stage_a_training_script_exists",
        STAGE_A_SCRIPT.exists(),
        STAGE_A_SCRIPT.exists(),
        True,
        str(STAGE_A_SCRIPT),
    )
    add_check(
        rows,
        "stage_b_training_script_exists",
        STAGE_B_SCRIPT.exists(),
        STAGE_B_SCRIPT.exists(),
        True,
        str(STAGE_B_SCRIPT),
    )

    help_result = subprocess.run(
        [
            "conda",
            "run",
            "-n",
            "sea-ad-jepa",
            "python",
            str(STAGE_A_SCRIPT),
            "--help",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    help_text = help_result.stdout + help_result.stderr
    missing_flags = [flag for flag in REQUIRED_STAGE_A_FLAGS if flag not in help_text]
    add_check(
        rows,
        "required_stage_a_help_flags_present",
        help_result.returncode == 0 and not missing_flags,
        f"returncode={help_result.returncode}; missing={missing_flags}",
        "all required flags present",
        "Help queried in the sea-ad-jepa Conda environment.",
    )

    stage_a_finished = finished_checkpoints(STAGE_A_DIR)
    stage_b_finished = finished_checkpoints(STAGE_B_DIR)
    add_check(
        rows,
        "stage_a_output_directory_checked",
        not stage_a_finished,
        f"exists={STAGE_A_DIR.exists()}; finished_checkpoints={stage_a_finished}",
        "no finished checkpoint",
        str(STAGE_A_DIR),
    )
    add_check(
        rows,
        "stage_b_output_directory_checked",
        not stage_b_finished,
        f"exists={STAGE_B_DIR.exists()}; finished_checkpoints={stage_b_finished}",
        "no finished checkpoint",
        str(STAGE_B_DIR),
    )
    add_check(
        rows,
        "no_training_run",
        not stage_a_finished and not stage_b_finished,
        f"stage_a_finished={stage_a_finished}; stage_b_finished={stage_b_finished}",
        "no shuffled-graph finished checkpoints",
        "Preflight only. The required approval string was not supplied.",
    )

    checks = pd.DataFrame(rows)
    TABLE_OUT.parent.mkdir(parents=True, exist_ok=True)
    checks.to_csv(TABLE_OUT, index=False)
    counts = checks["status"].value_counts().reindex(
        ["pass", "warning", "fail"], fill_value=0
    )
    lines = [
        "# Shuffled-Graph Ablation Training Preflight v1",
        "",
        "## Outcome",
        "",
        f"- Pass: {counts['pass']}",
        f"- Warning: {counts['warning']}",
        f"- Fail: {counts['fail']}",
        "- Training run: no.",
        "",
        "This preflight checks readiness only. Biological topology has not yet been "
        "compared with the degree-preserving shuffled topology.",
        "",
        "## Checks",
        "",
        *markdown_table(checks),
        "",
        "## Exact Stage A command for a separately approved future run",
        "",
        "```powershell",
        STAGE_A_COMMAND,
        "```",
        "",
        "## Exact Stage B command template",
        "",
        "Run only after Stage A completes and its epoch 30 checkpoint, history, and log "
        "have been verified.",
        "",
        "```powershell",
        STAGE_B_COMMAND,
        "```",
        "",
        "## Frozen run conditions",
        "",
        f"- Edge CSV: `{EDGE_CSV}`",
        f"- Stage A output: `{STAGE_A_DIR}`",
        f"- Stage B output: `{STAGE_B_DIR}`",
        "- Seed: `7`",
        "- Stage A epochs: `50`",
        "- Stage B initialization: Stage A epoch `30`",
        "- No external validation data are part of these commands.",
        "",
        "## Boundary",
        "",
        "- `APPROVED_SHUFFLED_GRAPH_TRAINING` was not present in the request.",
        "- No training command was executed.",
        "- No expression-only autoencoder was trained.",
        "- No external validation was run.",
        "- Evidence levels and the strict Level-2 gliosis criterion are unchanged.",
        "",
    ]
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(checks["status"].value_counts(dropna=False))
    print(checks.loc[checks["status"].ne("pass")].to_string(index=False))
    print(f"Wrote {TABLE_OUT}")
    print(f"Wrote {REPORT_OUT}")
    if checks["status"].eq("fail").any():
        raise SystemExit(1)


if __name__ == "__main__":
    main()
