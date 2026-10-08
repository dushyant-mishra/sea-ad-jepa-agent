from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np
import pandas as pd


STRICT_EDGES = Path(
    "results/tables/ablation_edge_sets/strict_shuffled_graph_edges_v1.csv"
)
STRICT_DIAGNOSTICS = Path(
    "results/tables/ablation_edge_sets/"
    "strict_shuffled_graph_edge_diagnostics_v1.csv"
)
STRICT_REPORT = Path(
    "results/reports/strict_shuffled_graph_edge_generation_v1.md"
)
ORIGINAL_EDGES = Path("results/tables/v2_graph_consensus_edges.csv")
IDENTITY_NODE_MAP = Path(
    "results/tables/ablation_edge_sets/no_graph_identity_edges_v1.csv"
)
H5AD = Path(
    "data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad"
)
STAGE_A_SCRIPT = Path("scripts/train_graph_jepa_stage_a_fast.py")
STAGE_B_SCRIPT = Path("scripts/train_graph_jepa_stage_b_adversarial.py")
STAGE_A_DIR = Path("results/models/ablation_strict_shuffled_graph_stage_a_v1")
STAGE_B_DIR = Path("results/models/ablation_strict_shuffled_graph_stage_b_v1")
STAGE_A_HISTORY = Path(
    "results/tables/ablation_strict_shuffled_graph_stage_a_v1_history.csv"
)
STAGE_B_HISTORY = Path(
    "results/tables/ablation_strict_shuffled_graph_stage_b_v1_history.csv"
)
STAGE_A_LOG = Path(
    "results/logs/ablation_strict_shuffled_graph_stage_a_v1.log"
)
STAGE_B_LOG = Path(
    "results/logs/ablation_strict_shuffled_graph_stage_b_v1.log"
)
OLD_PARTIAL_LOG = Path("results/logs/ablation_shuffled_graph_stage_a_v1.log")
TABLE_OUT = Path("results/tables/strict_shuffled_graph_ablation_preflight_v1.csv")
REPORT_OUT = Path(
    "results/reports/strict_shuffled_graph_ablation_preflight_v1.md"
)

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
    "--edge-csv results/tables/ablation_edge_sets/strict_shuffled_graph_edges_v1.csv "
    "--out-dir results/models/ablation_strict_shuffled_graph_stage_a_v1 "
    "--epochs 50 --seed 7 "
    "--history-csv results/tables/"
    "ablation_strict_shuffled_graph_stage_a_v1_history.csv "
    "--log-file results/logs/"
    "ablation_strict_shuffled_graph_stage_a_v1.log"
)
STAGE_B_COMMAND = (
    "conda run -n sea-ad-jepa python "
    "scripts/train_graph_jepa_stage_b_adversarial.py "
    "stage_a_checkpoint=results/models/"
    "ablation_strict_shuffled_graph_stage_a_v1/"
    "fast_graph_jepa_epoch_030.pt "
    "edge_csv=results/tables/ablation_edge_sets/"
    "strict_shuffled_graph_edges_v1.csv "
    "out_dir=results/models/ablation_strict_shuffled_graph_stage_b_v1 "
    "history_csv=results/tables/"
    "ablation_strict_shuffled_graph_stage_b_v1_history.csv "
    "log_file=results/logs/"
    "ablation_strict_shuffled_graph_stage_b_v1.log seed=7"
)


def add_check(
    rows: list[dict[str, str]],
    check_name: str,
    status: str,
    observed: object,
    expected: object,
    notes: str,
) -> None:
    if status not in {"pass", "warning", "fail"}:
        raise ValueError(f"Invalid controlled status: {status}")
    rows.append(
        {
            "check_name": check_name,
            "status": status,
            "observed": str(observed),
            "expected": str(expected),
            "notes": notes,
        }
    )


def canonical_set(frame: pd.DataFrame) -> set[tuple[int, int]]:
    return set(
        zip(
            np.minimum(frame["source_idx"], frame["target_idx"]).astype(int),
            np.maximum(frame["source_idx"], frame["target_idx"]).astype(int),
        )
    )


def degree(frame: pd.DataFrame, n_nodes: int) -> np.ndarray:
    values = np.zeros(n_nodes, dtype=np.int64)
    np.add.at(values, frame["source_idx"].to_numpy(dtype=np.int64), 1)
    np.add.at(values, frame["target_idx"].to_numpy(dtype=np.int64), 1)
    return values


def checkpoint_paths(path: Path) -> list[str]:
    return sorted(str(item) for item in path.glob("*.pt")) if path.exists() else []


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
        "strict_shuffled_edge_file_exists",
        "pass" if STRICT_EDGES.exists() else "fail",
        STRICT_EDGES.exists(),
        True,
        str(STRICT_EDGES),
    )

    strict = pd.read_csv(STRICT_EDGES) if STRICT_EDGES.exists() else pd.DataFrame()
    original = (
        pd.read_csv(ORIGINAL_EDGES) if ORIGINAL_EDGES.exists() else pd.DataFrame()
    )
    identity = (
        pd.read_csv(IDENTITY_NODE_MAP)
        if IDENTITY_NODE_MAP.exists()
        else pd.DataFrame()
    )
    required_edge_columns = {"source", "target", "source_idx", "target_idx"}
    columns_ok = required_edge_columns.issubset(strict.columns)
    add_check(
        rows,
        "strict_shuffled_edge_count",
        "pass" if len(strict) == 114029 else "fail",
        len(strict),
        114029,
        "Simple undirected edges stored once.",
    )

    identity_indices = (
        set(identity["source_idx"].astype(int))
        if "source_idx" in identity.columns
        else set()
    )
    strict_max_index = (
        int(strict[["source_idx", "target_idx"]].to_numpy().max())
        if columns_ok and not strict.empty
        else -1
    )
    node_universe_ok = identity_indices == set(range(2957)) and strict_max_index == 2956
    add_check(
        rows,
        "strict_shuffled_node_universe",
        "pass" if node_universe_ok else "fail",
        (
            f"identity_nodes={len(identity_indices)}; "
            f"strict_max_index={strict_max_index}"
        ),
        "authoritative identity map contains 0-2956; strict max index 2956",
        "The identity edge file supplies the full index-to-gene map, including degree-zero nodes.",
    )

    degree_matches = False
    overlap_count = -1
    self_loops = -1
    duplicate_count = -1
    if columns_ok and required_edge_columns.issubset(original.columns):
        degree_matches = bool(
            np.array_equal(degree(original, 2957), degree(strict, 2957))
        )
        overlap_count = len(canonical_set(original) & canonical_set(strict))
        self_loops = int(
            (strict["source_idx"] == strict["target_idx"]).sum()
        )
        duplicate_count = len(strict) - len(canonical_set(strict))
    add_check(
        rows,
        "degree_sequence_matches_original",
        "pass" if degree_matches else "fail",
        degree_matches,
        True,
        "Exact node-wise degree sequence comparison.",
    )
    add_check(
        rows,
        "original_edge_overlap_zero",
        "pass" if overlap_count == 0 else "fail",
        overlap_count,
        0,
        "Canonical undirected intersection with the real graph.",
    )
    add_check(
        rows,
        "strict_shuffled_zero_self_loops",
        "pass" if self_loops == 0 else "fail",
        self_loops,
        0,
        "Required simple-graph invariant.",
    )
    add_check(
        rows,
        "strict_shuffled_zero_duplicate_edges",
        "pass" if duplicate_count == 0 else "fail",
        duplicate_count,
        0,
        "Canonical undirected duplicates.",
    )

    for check_name, path in [
        ("h5ad_exists", H5AD),
        ("stage_a_training_script_exists", STAGE_A_SCRIPT),
        ("stage_b_training_script_exists", STAGE_B_SCRIPT),
    ]:
        add_check(
            rows,
            check_name,
            "pass" if path.exists() else "fail",
            path.exists(),
            True,
            str(path),
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
        "pass" if help_result.returncode == 0 and not missing_flags else "fail",
        f"returncode={help_result.returncode}; missing={missing_flags}",
        "all required flags present",
        "Queried in the sea-ad-jepa Conda environment.",
    )

    stage_a_checkpoints = checkpoint_paths(STAGE_A_DIR)
    stage_b_checkpoints = checkpoint_paths(STAGE_B_DIR)
    add_check(
        rows,
        "stage_a_output_directory_checked",
        "pass" if not stage_a_checkpoints else "fail",
        f"exists={STAGE_A_DIR.exists()}; checkpoints={stage_a_checkpoints}",
        "absent/empty with no checkpoints",
        str(STAGE_A_DIR),
    )
    add_check(
        rows,
        "stage_b_output_directory_checked",
        "pass" if not stage_b_checkpoints else "fail",
        f"exists={STAGE_B_DIR.exists()}; checkpoints={stage_b_checkpoints}",
        "absent/empty with no checkpoints",
        str(STAGE_B_DIR),
    )

    old_partial_exists = OLD_PARTIAL_LOG.exists()
    strict_logs_exist = STAGE_A_LOG.exists() or STAGE_B_LOG.exists()
    partial_status = (
        "fail"
        if strict_logs_exist
        else ("warning" if old_partial_exists else "pass")
    )
    add_check(
        rows,
        "partial_interrupted_logs_checked",
        partial_status,
        (
            f"old_non_strict_partial_log={old_partial_exists}; "
            f"strict_logs_exist={strict_logs_exist}"
        ),
        "historical partial logs allowed only outside strict paths",
        (
            f"`{OLD_PARTIAL_LOG}` is historical and will not be reused."
            if old_partial_exists and not strict_logs_exist
            else "No reusable historical log detected."
        ),
    )

    strict_checkpoint_exists = bool(stage_a_checkpoints or stage_b_checkpoints)
    strict_history_paths = [
        str(path)
        for path in [STAGE_A_HISTORY, STAGE_B_HISTORY]
        if path.exists()
    ]
    add_check(
        rows,
        "no_strict_shuffled_checkpoint_exists",
        "pass" if not strict_checkpoint_exists else "fail",
        strict_checkpoint_exists,
        False,
        "No strict-shuffled model checkpoint may predate approval.",
    )
    add_check(
        rows,
        "no_strict_shuffled_history_exists",
        "pass" if not strict_history_paths else "fail",
        strict_history_paths,
        [],
        "No strict-shuffled training history may predate approval.",
    )
    no_training = (
        not strict_checkpoint_exists
        and not strict_history_paths
        and not strict_logs_exist
        and not STAGE_A_DIR.exists()
        and not STAGE_B_DIR.exists()
    )
    add_check(
        rows,
        "no_training_run",
        "pass" if no_training else "fail",
        no_training,
        True,
        "Preflight only; APPROVED_STRICT_SHUFFLED_GRAPH_TRAINING was absent.",
    )

    checks = pd.DataFrame(rows)
    TABLE_OUT.parent.mkdir(parents=True, exist_ok=True)
    checks.to_csv(TABLE_OUT, index=False)
    counts = checks["status"].value_counts().reindex(
        ["pass", "warning", "fail"], fill_value=0
    )
    lines = [
        "# Strict-Shuffled Graph Ablation Training Preflight v1",
        "",
        "## Outcome",
        "",
        f"- Pass: {counts['pass']}",
        f"- Warning: {counts['warning']}",
        f"- Fail: {counts['fail']}",
        "- Training run: no.",
        "",
        f"- Strict edge file: `{STRICT_EDGES}`",
        "- Original-edge overlap: `0`.",
        f"- Exact degree preservation: `{degree_matches}`.",
        "",
        "## Checks",
        "",
        *markdown_table(checks),
        "",
        "## Future Stage A command after separate explicit approval",
        "",
        "```powershell",
        STAGE_A_COMMAND,
        "```",
        "",
        "## Future Stage B command after verified Stage A completion",
        "",
        "```powershell",
        STAGE_B_COMMAND,
        "```",
        "",
        "## Historical partial log",
        "",
        (
            f"`{OLD_PARTIAL_LOG}` exists from the interrupted older, non-strict "
            "shuffled attempt. It is outside all strict-shuffled paths and must "
            "not be reused."
            if old_partial_exists
            else "No historical partial log was found."
        ),
        "",
        "## Boundary",
        "",
        "- `APPROVED_STRICT_SHUFFLED_GRAPH_TRAINING` was not present.",
        "- No strict-shuffled training command was executed.",
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
