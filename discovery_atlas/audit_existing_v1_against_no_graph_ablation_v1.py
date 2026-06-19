"""Audit existing v1 artifacts against the planned no-graph ablation.

Searches results/models, results/, configs/, scripts/ and paths matching
v1/stage_a/jepa/no_graph/identity/autoencoder/expression for any model
checkpoint that could serve as a no-graph / expression-only control.

Outputs:
  results/tables/existing_v1_no_graph_ablation_compatibility_v1.csv
  results/reports/existing_v1_no_graph_ablation_compatibility_v1.md
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import torch

# ---------------------------------------------------------------------------
# Planned no-graph ablation reference (from ablation protocol v1)
# ---------------------------------------------------------------------------
PLANNED_ABLATION = {
    "h5ad": "data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad",
    "edge_csv": "results/tables/ablation_edge_sets/no_graph_identity_edges_v1.csv",
    "edge_type": "identity_self_loop",
    "architecture": "FastGraphGeneJEPA",
    "hidden_dim": 128,
    "latent_dim": 128,
    "n_layers": 2,
    "n_genes": 2957,
    "seed": 7,
    "training_script": "scripts/train_graph_jepa_stage_a_fast.py",
    "stage_b_script": "scripts/train_graph_jepa_stage_b_adversarial.py",
    "evaluation": "pathology-head on frozen Stage B encoder",
    "first_five_genes": ["ISG15", "GNB1", "SKI", "CAMTA1", "SLC2A5"],
}

VALID_LABELS = [
    "compatible_as_no_graph_ablation",
    "partially_compatible_historical_context_only",
    "not_compatible_due_to_feature_or_preprocessing_mismatch",
    "not_enough_metadata_to_use_as_ablation",
    "not_a_no_graph_model",
]

# Patterns to search for candidate artifacts
SEARCH_ROOTS = [
    "results/models",
    "results",
    "configs",
    "configs/train",
    "scripts",
]
KEYWORD_PATTERNS = ["v1", "stage_a", "stage_b", "jepa", "no_graph",
                     "identity", "autoencoder", "expression"]

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def find_candidate_checkpoints() -> list[dict]:
    """Find .pt checkpoint files and YAML configs that could be v1 or no-graph artifacts."""
    candidates: list[dict] = []
    seen_paths: set[str] = set()

    # 1. Scan results/models for .pt files
    models_dir = PROJECT_ROOT / "results" / "models"
    if models_dir.exists():
        for pt_file in models_dir.rglob("*.pt"):
            rel = str(pt_file.relative_to(PROJECT_ROOT)).replace("\\", "/")
            if rel not in seen_paths:
                seen_paths.add(rel)
                candidates.append({"artifact_path": rel, "type": "checkpoint"})

    # 2. Scan configs for YAML files
    for cfg_root in ["configs", "configs/train"]:
        cfg_dir = PROJECT_ROOT / cfg_root
        if cfg_dir.exists():
            for yml in cfg_dir.rglob("*.yaml"):
                rel = str(yml.relative_to(PROJECT_ROOT)).replace("\\", "/")
                if rel not in seen_paths:
                    seen_paths.add(rel)
                    candidates.append({"artifact_path": rel, "type": "config"})
            for yml in cfg_dir.rglob("*.yml"):
                rel = str(yml.relative_to(PROJECT_ROOT)).replace("\\", "/")
                if rel not in seen_paths:
                    seen_paths.add(rel)
                    candidates.append({"artifact_path": rel, "type": "config"})

    return candidates


def is_keyword_match(path: str) -> bool:
    """Check if a path matches any keyword pattern."""
    path_lower = path.lower()
    for pattern in KEYWORD_PATTERNS:
        if pattern in path_lower:
            return True
    return False


def is_v1_candidate(path: str) -> bool:
    """Determine if a checkpoint is a v1-era (non-graph) model."""
    # v1 models use GeneJEPA / MLPEncoder (no graph convolutions)
    # v2 models use GraphGeneJEPA or FastGraphGeneJEPA
    # v1 models are in directories like microglia_pvm_jepa_*
    v1_patterns = [
        r"microglia_pvm_jepa",
        r"jepa_snrna",
        r"gene_jepa\.pt",
    ]
    v2_patterns = [
        r"v2_2_",
        r"graph_jepa",
        r"fast_graph_jepa",
        r"stage_b_adversarial",
        r"stage_c_",
        r"ablation_",
        r"abeta_mil",
    ]
    path_lower = path.lower()
    for p in v2_patterns:
        if re.search(p, path_lower):
            return False
    for p in v1_patterns:
        if re.search(p, path_lower):
            return True
    return False


def extract_checkpoint_metadata(artifact_path: str) -> dict:
    """Load a .pt checkpoint and extract metadata for compatibility audit."""
    full_path = PROJECT_ROOT / artifact_path
    info: dict = {
        "candidate_name": "",
        "artifact_path": artifact_path,
        "config_path": "not_available",
        "checkpoint_path": artifact_path,
        "training_script": "unknown",
        "input_h5ad": "unknown",
        "feature_count": "unknown",
        "feature_order_status": "unknown",
        "edge_csv": "not_applicable",
        "edge_status": "unknown",
        "latent_dim": "unknown",
        "hidden_dim": "unknown",
        "n_layers": "unknown",
        "seed": "unknown",
        "training_epochs": "unknown",
        "stage_a_b_comparable": "unknown",
        "pathology_head_comparable": "unknown",
        "donor_fold_comparable": "unknown",
        "evaluation_status": "unknown",
        "architecture_status": "unknown",
        "input_data_status": "unknown",
        "compatibility_status": "not_enough_metadata_to_use_as_ablation",
        "recommendation": "cannot_assess",
        "mismatch_details": "",
    }

    if not full_path.exists():
        info["mismatch_details"] = "checkpoint file not found"
        return info

    try:
        ck = torch.load(str(full_path), map_location="cpu", weights_only=False)
    except Exception as e:
        info["mismatch_details"] = f"failed to load checkpoint: {e}"
        return info

    # Extract name from directory
    dir_name = Path(artifact_path).parent.name
    file_name = Path(artifact_path).stem
    info["candidate_name"] = f"{dir_name}/{file_name}" if dir_name != "models" else file_name

    # Extract args
    args = ck.get("args", {})
    model_class = ck.get("model_class", None)

    # Training script inference
    if "h5ad" in args and "edge_csv" not in args:
        info["training_script"] = "scripts/train_jepa_snrna.py"
    elif "edge_csv" in args:
        info["training_script"] = "scripts/train_graph_jepa_stage_a_fast.py"

    # H5AD
    info["input_h5ad"] = args.get("h5ad", "unknown")

    # Feature count and order
    n_genes = ck.get("n_genes", "unknown")
    gene_names = ck.get("gene_names", [])
    info["feature_count"] = str(n_genes) if n_genes != "unknown" else "unknown"

    if gene_names and len(gene_names) >= 5:
        first_five = gene_names[:5]
        if first_five == PLANNED_ABLATION["first_five_genes"]:
            info["feature_order_status"] = "exact_match"
        else:
            info["feature_order_status"] = f"mismatch_first_five={first_five}"
    elif gene_names:
        info["feature_order_status"] = "partial_recoverable"
    else:
        info["feature_order_status"] = "not_recoverable"

    # Edge CSV / status
    edge_csv = args.get("edge_csv", None)
    if edge_csv:
        info["edge_csv"] = edge_csv
        edge_path = str(edge_csv).lower()
        if "identity" in edge_path or "no_graph" in edge_path:
            info["edge_status"] = "identity_self_loop"
        elif "shuffled" in edge_path:
            info["edge_status"] = "shuffled"
        elif "consensus" in edge_path or "string" in edge_path:
            info["edge_status"] = "real_graph"
        else:
            info["edge_status"] = "unknown"
    else:
        info["edge_csv"] = "not_applicable"
        info["edge_status"] = "absent_expression_only"

    # Architecture
    info["hidden_dim"] = str(args.get("hidden_dim", "unknown"))
    info["latent_dim"] = str(args.get("latent_dim", "unknown"))
    info["n_layers"] = str(args.get("n_layers", "not_applicable"))
    info["seed"] = str(args.get("seed", "unknown"))
    info["training_epochs"] = str(args.get("epochs", "unknown"))

    # Determine model class
    if model_class:
        arch_class = str(model_class)
    elif "edge_csv" not in args:
        arch_class = "GeneJEPA_MLPEncoder"
    else:
        arch_class = "GraphGeneJEPA_or_FastGraphGeneJEPA"

    # --- Compatibility assessment ---
    mismatches: list[str] = []

    # 1. Input data match
    if info["input_h5ad"] == PLANNED_ABLATION["h5ad"]:
        info["input_data_status"] = "exact_match"
    elif info["input_h5ad"] == "unknown":
        info["input_data_status"] = "unknown"
        mismatches.append("input H5AD unknown")
    else:
        info["input_data_status"] = "mismatch"
        mismatches.append(f"input H5AD mismatch: {info['input_h5ad']} vs {PLANNED_ABLATION['h5ad']}")

    # 2. Feature count match
    if str(n_genes) == str(PLANNED_ABLATION["n_genes"]):
        pass  # OK
    elif n_genes == "unknown":
        mismatches.append("feature count unknown")
    else:
        mismatches.append(f"feature count mismatch: {n_genes} vs {PLANNED_ABLATION['n_genes']}")

    # 3. Architecture match
    if "MLP" in arch_class or "GeneJEPA" in arch_class and "Graph" not in arch_class:
        info["architecture_status"] = "v1_mlp_no_graph"
        mismatches.append(
            f"architecture mismatch: v1 MLPEncoder (hidden={info['hidden_dim']}) vs "
            f"planned FastGraphGeneJEPA (hidden={PLANNED_ABLATION['hidden_dim']}, "
            f"n_layers={PLANNED_ABLATION['n_layers']})"
        )
    elif "FastGraph" in arch_class or "GraphGene" in arch_class:
        info["architecture_status"] = "v2_graph"
        if info["edge_status"] != "absent_expression_only" and info["edge_status"] != "identity_self_loop":
            mismatches.append("uses real or shuffled graph edges, not expression-only")
    else:
        info["architecture_status"] = "unknown"
        mismatches.append("architecture class unknown")

    # 4. Hidden dim match
    if info["hidden_dim"] != str(PLANNED_ABLATION["hidden_dim"]) and info["hidden_dim"] != "unknown":
        mismatches.append(
            f"hidden_dim mismatch: v1={info['hidden_dim']} vs planned={PLANNED_ABLATION['hidden_dim']}"
        )

    # 5. Stage A/B comparability
    if info["edge_status"] == "absent_expression_only":
        info["stage_a_b_comparable"] = "no_stage_b_not_applicable_to_v1"
        mismatches.append("v1 has no Stage B equivalent; planned ablation requires matched Stage A+B")
    elif info["edge_status"] in ("identity_self_loop", "real_graph", "shuffled"):
        info["stage_a_b_comparable"] = "potentially_yes_if_stage_b_rerun"
    else:
        info["stage_a_b_comparable"] = "unknown"

    # 6. Pathology head comparability
    if info["architecture_status"] == "v1_mlp_no_graph":
        info["pathology_head_comparable"] = "no_different_architecture"
        mismatches.append(
            "pathology head not directly comparable: v1 MLPEncoder output space "
            "differs from v2 GraphGeneEncoder output space"
        )
    else:
        info["pathology_head_comparable"] = "potentially_yes"

    # 7. Donor fold comparability
    if info["input_data_status"] == "exact_match" and info["feature_order_status"] == "exact_match":
        info["donor_fold_comparable"] = "yes_same_h5ad_and_genes"
    else:
        info["donor_fold_comparable"] = "unknown_or_mismatched"

    # 8. Downstream evaluation
    if (info["architecture_status"] == "v1_mlp_no_graph" and
            info["input_data_status"] == "exact_match"):
        info["evaluation_status"] = (
            "can_extract_embeddings_but_not_with_graph_jepa_evaluator"
        )
    elif info["architecture_status"] == "v2_graph":
        info["evaluation_status"] = "can_run_with_current_scripts"
    else:
        info["evaluation_status"] = "unknown"

    # --- Final classification ---
    info["mismatch_details"] = "; ".join(mismatches) if mismatches else "none"

    if info["edge_status"] not in ("absent_expression_only", "identity_self_loop"):
        info["compatibility_status"] = "not_a_no_graph_model"
        info["recommendation"] = "not_applicable_uses_graph_edges"
    elif not mismatches:
        info["compatibility_status"] = "compatible_as_no_graph_ablation"
        info["recommendation"] = "reuse_as_no_graph_ablation"
    elif (info["input_data_status"] == "exact_match" and
          info["feature_order_status"] == "exact_match" and
          info["edge_status"] == "absent_expression_only"):
        # Same data, same features, no graph — but architecture mismatch
        if info["architecture_status"] == "v1_mlp_no_graph":
            info["compatibility_status"] = "partially_compatible_historical_context_only"
            info["recommendation"] = (
                "use_as_historical_context_but_train_fresh_no_graph_ablation_with_matched_architecture"
            )
        else:
            info["compatibility_status"] = "not_enough_metadata_to_use_as_ablation"
            info["recommendation"] = "train_fresh_no_graph_ablation"
    elif info["input_data_status"] != "exact_match" or info["feature_order_status"] != "exact_match":
        if info["input_data_status"] == "unknown" or info["feature_order_status"] == "unknown":
            info["compatibility_status"] = "not_enough_metadata_to_use_as_ablation"
            info["recommendation"] = "train_fresh_no_graph_ablation"
        else:
            info["compatibility_status"] = "not_compatible_due_to_feature_or_preprocessing_mismatch"
            info["recommendation"] = "train_fresh_no_graph_ablation"
    else:
        info["compatibility_status"] = "not_enough_metadata_to_use_as_ablation"
        info["recommendation"] = "train_fresh_no_graph_ablation"

    return info


def generate_report(candidates_df: pd.DataFrame, out_path: Path) -> None:
    """Write the compatibility report as markdown."""
    lines: list[str] = []
    lines.append("# Existing v1 vs Planned No-Graph Ablation Compatibility Audit\n")
    lines.append(f"Audited: {len(candidates_df)} candidate artifact(s)\n")

    # Section 1: Candidates found
    lines.append("## 1. Candidate v1 Artifacts Found\n")
    v1_candidates = candidates_df[
        candidates_df["edge_status"].isin(["absent_expression_only", "identity_self_loop"])
    ]
    non_graph = candidates_df[
        ~candidates_df["edge_status"].isin(["absent_expression_only", "identity_self_loop"])
    ]

    if len(v1_candidates) == 0:
        lines.append("No expression-only or identity-edge artifacts found.\n")
    else:
        lines.append(f"Found {len(v1_candidates)} expression-only / no-graph candidate(s):\n")
        for _, row in v1_candidates.iterrows():
            lines.append(f"- **{row['candidate_name']}**")
            lines.append(f"  - Path: `{row['artifact_path']}`")
            lines.append(f"  - Edge status: `{row['edge_status']}`")
            lines.append(f"  - Architecture: `{row['architecture_status']}`")
            lines.append(f"  - Features: {row['feature_count']} genes")
            lines.append(f"  - Hidden dim: {row['hidden_dim']}, Latent dim: {row['latent_dim']}")
            lines.append(f"  - Epochs: {row['training_epochs']}")
            lines.append(f"  - Seed: {row['seed']}")
            lines.append("")

    lines.append(f"\nSkipped {len(non_graph)} artifact(s) that use real or shuffled graph edges.\n")

    # Section 2: Similarity to planned ablation
    lines.append("## 2. Similarity to Planned No-Graph Ablation\n")
    lines.append("Planned ablation reference:\n")
    lines.append("```text")
    lines.append(f"Architecture: {PLANNED_ABLATION['architecture']}")
    lines.append(f"H5AD: {PLANNED_ABLATION['h5ad']}")
    lines.append(f"Edge set: {PLANNED_ABLATION['edge_csv']} (identity self-loops)")
    lines.append(f"Features: {PLANNED_ABLATION['n_genes']} genes")
    lines.append(f"Hidden dim: {PLANNED_ABLATION['hidden_dim']}")
    lines.append(f"Latent dim: {PLANNED_ABLATION['latent_dim']}")
    lines.append(f"Graph layers: {PLANNED_ABLATION['n_layers']}")
    lines.append(f"Training script: {PLANNED_ABLATION['training_script']}")
    lines.append("```\n")

    for _, row in v1_candidates.iterrows():
        lines.append(f"### {row['candidate_name']}\n")
        matches: list[str] = []
        diffs: list[str] = []
        if row["input_data_status"] == "exact_match":
            matches.append("Input H5AD: exact match")
        else:
            diffs.append(f"Input H5AD: {row['input_data_status']}")
        if row["feature_order_status"] == "exact_match":
            matches.append("Feature order: exact match")
        else:
            diffs.append(f"Feature order: {row['feature_order_status']}")
        if row["architecture_status"] == "v1_mlp_no_graph":
            diffs.append(
                f"Architecture: v1 MLPEncoder (hidden={row['hidden_dim']}) vs "
                f"planned FastGraphGeneJEPA (hidden={PLANNED_ABLATION['hidden_dim']}, "
                f"{PLANNED_ABLATION['n_layers']} GNN layers with identity edges)"
            )
        if row["hidden_dim"] != str(PLANNED_ABLATION["hidden_dim"]):
            diffs.append(f"Hidden dim: {row['hidden_dim']} vs {PLANNED_ABLATION['hidden_dim']}")

        if matches:
            lines.append("Matches:")
            for m in matches:
                lines.append(f"- {m}")
            lines.append("")
        if diffs:
            lines.append("Differences:")
            for d in diffs:
                lines.append(f"- {d}")
            lines.append("")

        lines.append(f"Compatibility: `{row['compatibility_status']}`\n")

    # Section 3: Mismatches
    lines.append("## 3. Mismatch Summary\n")
    for _, row in v1_candidates.iterrows():
        lines.append(f"**{row['candidate_name']}**: {row['mismatch_details']}\n")

    # Section 4: Whether retraining is recommended
    lines.append("## 4. Whether Retraining Is Still Recommended\n")

    any_compatible = (v1_candidates["compatibility_status"] == "compatible_as_no_graph_ablation").any()
    any_partial = (v1_candidates["compatibility_status"] == "partially_compatible_historical_context_only").any()

    if any_compatible:
        lines.append(
            "At least one v1 artifact is fully compatible as the no-graph ablation. "
            "Fresh training is not required.\n"
        )
    elif any_partial:
        lines.append(
            "Existing v1 artifacts share the same input data and feature order but differ in "
            "architecture (MLPEncoder vs FastGraphGeneJEPA with identity edges). These provide "
            "useful historical context but are not a matched no-graph ablation.\n"
        )
        lines.append(
            "**Fresh no-graph ablation training is still recommended** using the frozen protocol "
            "(FastGraphGeneJEPA with identity self-loop edges) for a fair apples-to-apples comparison.\n"
        )
        lines.append("Key architectural differences that prevent reuse:\n")
        lines.append(
            "- v1 uses a 2-layer MLP (Linear → LayerNorm → GELU → Dropout → Linear) with "
            "hidden_dim=512\n"
        )
        lines.append(
            "- Planned ablation uses FastGraphGeneJEPA with 2 SAGEConv layers, "
            "gene identity embeddings, node annotation features, and hidden_dim=128\n"
        )
        lines.append(
            "- Even with identity self-loop edges (no message passing), the FastGraphGeneJEPA "
            "architecture includes input projection, residual connections, and graph-pooling "
            "operations that differ from the v1 MLP\n"
        )
        lines.append(
            "- The pathology head and downstream evaluation pipeline are designed for "
            "FastGraphGeneJEPA encoder outputs, not v1 MLPEncoder outputs\n"
        )
    else:
        lines.append("No compatible v1 artifacts found. Fresh no-graph ablation training is required.\n")

    # Section 5: Final recommendation
    lines.append("## 5. Final Recommendation\n")
    if any_compatible:
        compat_rows = v1_candidates[v1_candidates["compatibility_status"] == "compatible_as_no_graph_ablation"]
        lines.append("**Reuse the following v1 artifact(s) as the no-graph ablation:**\n")
        for _, row in compat_rows.iterrows():
            lines.append(f"- `{row['artifact_path']}`\n")
    else:
        lines.append(
            "**Train a fresh no-graph ablation** using the frozen protocol in "
            "`results/reports/discovery_ablation_training_protocol_v1.md`.\n"
        )
        lines.append("Command template:\n")
        lines.append("```text")
        lines.append(
            "python scripts/train_graph_jepa_stage_a_fast.py "
            "--h5ad data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad "
            "--edge-csv results/tables/ablation_edge_sets/no_graph_identity_edges_v1.csv "
            "--out-dir results/models/ablation_no_graph_stage_a_v1 "
            "--epochs <MATCHED_EPOCHS> "
            "--seed <FROZEN_SEED> "
            "--history-csv results/tables/ablation_no_graph_stage_a_v1_history.csv "
            "--log-file results/logs/ablation_no_graph_stage_a_v1.log"
        )
        lines.append("```\n")
        if any_partial:
            lines.append(
                "The existing v1 checkpoints remain useful as historical context for comparing "
                "the v1 MLP approach against the v2 Graph-JEPA approach. They should be cited "
                "as prior work, not as matched ablation controls.\n"
            )

    lines.append("## Boundary\n")
    lines.append("- No training was run.")
    lines.append("- No evidence levels were modified.")
    lines.append("- No external validation was performed.")
    lines.append("- No manuscript text was generated.")
    lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote report: {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit existing v1 artifacts against planned no-graph ablation."
    )
    parser.add_argument(
        "--table-out",
        default="results/tables/existing_v1_no_graph_ablation_compatibility_v1.csv",
    )
    parser.add_argument(
        "--report-out",
        default="results/reports/existing_v1_no_graph_ablation_compatibility_v1.md",
    )
    args = parser.parse_args()

    print("Scanning for candidate artifacts...")
    all_candidates = find_candidate_checkpoints()
    print(f"Found {len(all_candidates)} total artifact(s)")

    # Filter to checkpoints only (configs don't contain model weights)
    checkpoints = [c for c in all_candidates if c["type"] == "checkpoint"]
    print(f"Found {len(checkpoints)} checkpoint(s)")

    # Filter to keyword-matching or v1-candidate checkpoints
    relevant = [c for c in checkpoints
                 if is_keyword_match(c["artifact_path"]) or is_v1_candidate(c["artifact_path"])]
    print(f"Found {len(relevant)} keyword-matching or v1-candidate checkpoint(s)")

    # Deduplicate to final checkpoints only (not interim epoch checkpoints)
    final_models: list[dict] = []
    seen_dirs: set[str] = set()
    for c in relevant:
        model_dir = str(Path(c["artifact_path"]).parent)
        file_name = Path(c["artifact_path"]).name
        # Prefer the final checkpoint (no epoch number) per directory
        if "epoch" not in file_name:
            final_models.append(c)
            seen_dirs.add(model_dir)

    # Add directories that only have epoch checkpoints
    for c in relevant:
        model_dir = str(Path(c["artifact_path"]).parent)
        if model_dir not in seen_dirs:
            final_models.append(c)
            seen_dirs.add(model_dir)

    print(f"Auditing {len(final_models)} final checkpoint(s)")

    # Extract metadata and classify
    rows: list[dict] = []
    for candidate in final_models:
        info = extract_checkpoint_metadata(candidate["artifact_path"])
        rows.append(info)

    # Build dataframe with required columns
    columns = [
        "candidate_name",
        "artifact_path",
        "config_path",
        "checkpoint_path",
        "training_script",
        "input_h5ad",
        "feature_count",
        "feature_order_status",
        "edge_csv",
        "edge_status",
        "latent_dim",
        "hidden_dim",
        "n_layers",
        "seed",
        "training_epochs",
        "stage_a_b_comparable",
        "pathology_head_comparable",
        "donor_fold_comparable",
        "evaluation_status",
        "architecture_status",
        "input_data_status",
        "compatibility_status",
        "recommendation",
        "mismatch_details",
    ]
    df = pd.DataFrame(rows, columns=columns)

    # Validate labels
    for status in df["compatibility_status"]:
        if status not in VALID_LABELS:
            raise ValueError(f"Invalid compatibility_status: {status}")

    # Sort: expression-only first, then by name
    sort_order = {
        "compatible_as_no_graph_ablation": 0,
        "partially_compatible_historical_context_only": 1,
        "not_compatible_due_to_feature_or_preprocessing_mismatch": 2,
        "not_enough_metadata_to_use_as_ablation": 3,
        "not_a_no_graph_model": 4,
    }
    df["_sort"] = df["compatibility_status"].map(sort_order)
    df = df.sort_values(["_sort", "candidate_name"]).drop(columns=["_sort"])

    # Write outputs
    table_path = Path(args.table_out)
    table_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(table_path, index=False)
    print(f"Wrote table: {table_path} ({len(df)} rows)")

    report_path = Path(args.report_out)
    generate_report(df, report_path)


if __name__ == "__main__":
    main()
