from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pandas as pd


INVENTORY_OUT = Path("results/tables/v3_reusable_asset_inventory_v1.csv")
MISSING_OUT = Path("results/tables/v3_missing_or_deferred_assets_v1.csv")
REPORT_OUT = Path("results/reports/v3_reusable_asset_inventory_v1.md")


def exists(path: str | Path) -> bool:
    return Path(path).exists()


def size_or_count(path: str | Path) -> str:
    path = Path(path)
    if not path.exists():
        return "missing"
    if path.is_dir():
        return f"{len(list(path.rglob('*')))} files"
    if path.suffix.lower() == ".csv":
        try:
            with path.open("r", encoding="utf-8", errors="ignore") as handle:
                rows = max(sum(1 for _ in handle) - 1, 0)
            return f"{rows} rows; {path.stat().st_size} bytes"
        except OSError:
            pass
    return f"{path.stat().st_size} bytes"


def import_available(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def add_asset(
    rows: list[dict[str, object]],
    asset_id: str,
    category: str,
    asset_name: str,
    expected_path_or_package: str,
    exists_or_available: bool,
    asset_type: str,
    v3_role: str,
    immediately_usable: bool,
    needed_for_minimum_v3: bool,
    blocking_if_missing: bool,
    notes: str,
    *,
    size_count: str | None = None,
) -> None:
    rows.append(
        {
            "asset_id": asset_id,
            "category": category,
            "asset_name": asset_name,
            "expected_path_or_package": expected_path_or_package,
            "exists_or_available": bool(exists_or_available),
            "asset_type": asset_type,
            "size_or_count": size_count
            if size_count is not None
            else (
                "available"
                if exists_or_available and asset_type == "python_package"
                else size_or_count(expected_path_or_package)
            ),
            "v3_role": v3_role,
            "immediately_usable": bool(immediately_usable),
            "needed_for_minimum_v3": bool(needed_for_minimum_v3),
            "blocking_if_missing": bool(blocking_if_missing),
            "notes": notes,
        }
    )


def add_path_asset(
    rows: list[dict[str, object]],
    asset_id: str,
    category: str,
    asset_name: str,
    path: str,
    asset_type: str,
    v3_role: str,
    needed_for_minimum_v3: bool,
    blocking_if_missing: bool,
    notes: str,
    *,
    immediately_usable: bool | None = None,
) -> None:
    present = exists(path)
    add_asset(
        rows,
        asset_id,
        category,
        asset_name,
        path,
        present,
        asset_type,
        v3_role,
        present if immediately_usable is None else immediately_usable and present,
        needed_for_minimum_v3,
        blocking_if_missing,
        notes,
    )


def markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int = 30) -> list[str]:
    data = frame[columns].head(max_rows).copy()
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    lines.extend(
        "| " + " | ".join(str(value).replace("|", "/") for value in row) + " |"
        for row in data.itertuples(index=False, name=None)
    )
    if len(frame) > max_rows:
        lines.append(f"| ... | ... | ... | ... | ... | ... |")
    return lines


def metadata_columns(path: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        return set(pd.read_csv(path, nrows=1).columns)
    except Exception:
        return set()


def main() -> None:
    rows: list[dict[str, object]] = []
    metadata_path = Path("data/processed/metadata/sea_ad_mtg_donor_pathology_targets.csv")
    metadata_cols = metadata_columns(metadata_path)

    # Core v2 assets.
    add_path_asset(rows, "CORE-001", "core_v2_asset", "SEA-AD H5AD file", "data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad", "h5ad", "primary v3 expression input", True, True, "Frozen v2 single-cell input.")
    add_path_asset(rows, "CORE-002", "core_v2_asset", "2,957-gene feature universe", "results/tables/ablation_edge_sets/no_graph_identity_edges_v1.csv", "csv", "canonical gene universe and node order", True, True, "Identity edge file has one self-loop per feature.")
    add_path_asset(rows, "CORE-003", "core_v2_asset", "identity edge file / canonical gene-index map", "results/tables/ablation_edge_sets/no_graph_identity_edges_v1.csv", "csv", "no-graph control and node map", True, True, "Required to align all graph sources.")
    add_path_asset(rows, "CORE-004", "core_v2_asset", "real graph edge file", "results/tables/v2_graph_consensus_edges.csv", "csv", "v3 first typed graph source", True, True, "Consensus graph with STRING/WGCNA support labels.")
    add_path_asset(rows, "CORE-005", "core_v2_asset", "real graph edge index", "results/tables/v2_graph_consensus_edge_index.csv", "csv", "legacy loader-compatible edge index", True, False, "Used by v2 model checkpoint evaluation.")
    add_path_asset(rows, "CORE-006", "core_v2_asset", "no-graph identity edge file", "results/tables/ablation_edge_sets/no_graph_identity_edges_v1.csv", "csv", "matched no-message-passing control", True, True, "Reusable for v3 no-graph control.")
    add_path_asset(rows, "CORE-007", "core_v2_asset", "strict shuffled graph edge file", "results/tables/ablation_edge_sets/strict_shuffled_graph_edges_v1.csv", "csv", "zero-overlap degree-preserving graph control", True, True, "Reusable strict shuffled topology.")
    add_path_asset(rows, "CORE-008", "core_v2_asset", "strict shuffled diagnostics", "results/tables/ablation_edge_sets/strict_shuffled_graph_edge_diagnostics_v1.csv", "csv", "strict shuffled provenance", True, False, "Confirms zero overlap and degree preservation.")
    add_path_asset(rows, "CORE-009", "core_v2_asset", "donor-level fold definitions if saved", "results/tables/donor_groupkfold_validation.csv", "csv", "prior donor fold artifact/reference", False, False, "Existing fold outputs found; Stage 24 should lock explicit v3 folds.")
    add_path_asset(rows, "CORE-010", "core_v2_asset", "pathology target table", str(metadata_path), "csv", "donor pathology targets and environment covariates", True, True, "Contains AT8, 6e10/Aβ, GFAP, Iba1, NeuN plus covariates.")
    add_path_asset(rows, "CORE-011", "core_v2_asset", "baseline comparison table", "results/tables/discovery_baseline_predictive_representation_comparison.csv", "csv", "v2 baseline reference", True, True, "Includes module mean, PCA, raw expression baselines.")
    add_path_asset(rows, "CORE-012", "core_v2_asset", "final ablation comparison table", "results/tables/strict_shuffled_graph_ablation_predictive_representation_comparison_v1.csv", "csv", "v2 final graph-control benchmark", True, True, "Real graph, no-graph, strict shuffled, and simple baselines.")
    add_path_asset(rows, "CORE-013", "core_v2_asset", "v2 scorecard table", "results/tables/discovery_scorecard_v2_graph_connected_feature_wide.csv", "csv", "Discovery Atlas scorecard seed", True, False, "Model-implied hypotheses only.")
    add_path_asset(rows, "CORE-014", "core_v2_asset", "v2 final candidate shortlist", "results/tables/discovery_final_candidate_shortlist_v3.csv", "csv", "Discovery Atlas candidate reference", True, False, "Evidence gates remain conservative.")
    add_path_asset(rows, "CORE-015", "core_v2_asset", "targeted manifold QC table", "results/tables/discovery_targeted_manifold_audit_results_v1.csv", "csv", "manifold QC reuse", True, False, "Targeted v2 manifold audit output.")
    add_path_asset(rows, "CORE-016", "core_v2_asset", "internal evidence scorecard", "results/tables/discovery_internal_evidence_scorecard_v1_annotated.csv", "csv", "evidence-level discipline reference", True, False, "Annotated internal evidence table.")

    # Module assets.
    add_path_asset(rows, "MOD-001", "module_asset", "module membership definitions", "src/sea_ad_jepa/gene_sets.py", "python_module", "module branch and module baselines", True, True, "Contains MICROGLIA_GENE_MODULES definitions.")
    add_path_asset(rows, "MOD-002", "module_asset", "module-mean baseline table", "results/tables/discovery_baseline_predictive_representation_comparison.csv", "csv", "module mean benchmark reference", True, True, "Module mean was v2 best absolute predictor.")
    add_path_asset(rows, "MOD-003", "module_asset", "WGCNA module eigengenes", "results/tables/wgcna_module_eigengenes.csv", "csv", "WGCNA module baseline", False, False, "Not found; generate or defer.")
    add_path_asset(rows, "MOD-004", "module_asset", "WGCNA/TOM adjacency table", "results/tables/v2_graph_wgcna_edges.csv", "csv", "typed WGCNA/TOM graph source", True, True, "Available according to input availability report/path scan.")
    add_path_asset(rows, "MOD-005", "module_asset", "module-to-gene mapping file", "results/tables/module_to_gene_mapping.csv", "csv", "module branch input", False, False, "Can be generated from src/sea_ad_jepa/gene_sets.py.")
    add_path_asset(rows, "MOD-006", "module_asset", "module summary feature table", "data/processed/sea_ad_mtg_microglia_pvm_pseudobulk_expanded_modules.csv", "csv", "module feature reuse", True, False, "Pseudobulk/module-preserved processed table.")

    # Graph source assets.
    add_path_asset(rows, "GRAPH-001", "graph_source_asset", "STRING external links", "data/external/string/9606.protein.links.v12.0.txt.gz", "gz", "STRING graph source", True, True, "Raw STRING data available.")
    add_path_asset(rows, "GRAPH-002", "graph_source_asset", "STRING external protein info", "data/external/string/9606.protein.info.v12.0.txt.gz", "gz", "STRING graph source mapping", True, True, "Raw STRING mapping available.")
    add_path_asset(rows, "GRAPH-003", "graph_source_asset", "STRING graph build script", "scripts/build_string_graph.py", "python_script", "STRING graph regeneration", True, False, "Reusable builder.")
    add_path_asset(rows, "GRAPH-004", "graph_source_asset", "WGCNA/TOM graph file", "results/tables/v2_graph_wgcna_edges.csv", "csv", "WGCNA/TOM typed graph source", True, True, "Available graph source.")
    add_path_asset(rows, "GRAPH-005", "graph_source_asset", "WGCNA/TOM graph build script", "scripts/build_wgcna_tom_graph.py", "python_script", "WGCNA/TOM graph regeneration", True, False, "Reusable builder.")
    add_path_asset(rows, "GRAPH-006", "graph_source_asset", "pathway graph file", "results/tables/pathway_graph_edges.csv", "csv", "pathway typed graph source", False, False, "Missing/deferred; Reactome/KEGG/GO source can be generated later.")
    add_path_asset(rows, "GRAPH-007", "graph_source_asset", "Reactome/KEGG/GO membership files", "data/external/pathways", "directory", "pathway memberships", False, False, "Missing/deferred.")
    add_path_asset(rows, "GRAPH-008", "graph_source_asset", "coexpression graph file", "results/tables/v2_graph_wgcna_edges.csv", "csv", "coexpression source via WGCNA/TOM", True, False, "WGCNA/TOM serves as current coexpression graph.")
    add_path_asset(rows, "GRAPH-009", "graph_source_asset", "GRN / TF-target file", "results/tables/grn_tf_target_edges.csv", "csv", "causal-prior graph source", False, False, "Missing/deferred.")
    add_path_asset(rows, "GRAPH-010", "graph_source_asset", "edge source/type labels", "results/tables/v2_graph_consensus_edges.csv", "csv", "typed graph branch labels", True, True, "Columns include in_string, in_wgcna, support, string_score, wgcna_tom.")
    add_path_asset(rows, "GRAPH-011", "graph_source_asset", "graph node-name mapping file", "results/tables/ablation_edge_sets/no_graph_identity_edges_v1.csv", "csv", "canonical node map", True, True, "One row per gene index.")

    packages = {
        "sklearn": ("sklearn", "PCA, TSNE, ridge, ElasticNet, tree baselines"),
        "umap": ("umap", "UMAP baseline"),
        "openTSNE": ("openTSNE", "alternative t-SNE baseline"),
        "phate": ("phate", "PHATE baseline"),
        "pydiffmap": ("pydiffmap", "diffusion maps baseline"),
        "torch": ("torch", "MLP, autoencoder, Graph-JEPA"),
        "torch_geometric": ("torch_geometric", "graph-only GNN feasibility"),
        "scanpy": ("scanpy", "single-cell preprocessing and diffusion alternatives"),
        "scvi": ("scvi", "VAE/scVI-style latent"),
        "xgboost": ("xgboost", "tree/boosting baseline"),
        "lightgbm": ("lightgbm", "tree/boosting baseline"),
        "econml": ("econml", "observational causal effect estimation"),
        "dowhy": ("dowhy", "observational causal effect estimation and refutation"),
        "networkx": ("networkx", "graph utilities and strict shuffles"),
    }
    package_available: dict[str, bool] = {}
    for idx, (module, role) in enumerate(packages.values(), start=1):
        available = import_available(module)
        package_available[module] = available
        add_asset(rows, f"PKG-{idx:03d}", "benchmark_package", module, module, available, "python_package", role, available, module in {"sklearn", "torch", "networkx"}, module in {"sklearn", "torch", "networkx"}, "Import availability in the current Python environment.")

    has_sklearn = package_available.get("sklearn", False)
    has_torch = package_available.get("torch", False)
    has_umap = package_available.get("umap", False)
    has_phate = package_available.get("phate", False)
    has_diffusion = package_available.get("pydiffmap", False) or package_available.get("scanpy", False)
    has_boost = package_available.get("xgboost", False) or package_available.get("lightgbm", False) or has_sklearn
    has_scvi = package_available.get("scvi", False)
    has_torch_geo = package_available.get("torch_geometric", False)
    baselines = [
        ("BASE-001", "PCA + ridge", has_sklearn, True, "PCA and Ridge available through sklearn."),
        ("BASE-002", "t-SNE + ridge/kNN", has_sklearn or package_available.get("openTSNE", False), False, "Runnable if fold-safe embedding harness is added."),
        ("BASE-003", "UMAP + ridge/kNN", has_umap, True, "Requires umap package and fold-safe harness."),
        ("BASE-004", "supervised UMAP if leakage-safe", has_umap, False, "Must be blocked until leakage-safe fit protocol is written."),
        ("BASE-005", "PHATE + ridge/kNN", has_phate, False, "Package-dependent; do not install here."),
        ("BASE-006", "diffusion maps + ridge/kNN", has_diffusion, False, "Requires pydiffmap or scanpy diffusion-map equivalent."),
        ("BASE-007", "raw expression ridge", has_sklearn, True, "Already implemented in v2 baseline harness."),
        ("BASE-008", "raw expression ElasticNet", has_sklearn, True, "Available through sklearn; needs locked harness extension."),
        ("BASE-009", "raw expression tree/boosting", has_boost, False, "Can use sklearn tree ensemble immediately if boosting packages are absent."),
        ("BASE-010", "expression-only MLP", has_torch, True, "Requires a locked no-graph neural baseline."),
        ("BASE-011", "module-only MLP", has_torch and exists("src/sea_ad_jepa/gene_sets.py"), False, "Needs module feature extraction harness."),
        ("BASE-012", "autoencoder latent", has_torch, True, "Can be implemented without graph inputs."),
        ("BASE-013", "VAE/scVI-style latent", has_scvi, False, "Future extension if scvi available/installed later."),
        ("BASE-014", "graph-only GNN", has_torch and has_torch_geo, False, "Requires torch_geometric and locked GNN baseline."),
        ("BASE-015", "v3 no-graph", has_torch and exists("results/tables/ablation_edge_sets/no_graph_identity_edges_v1.csv"), True, "Minimum v3 control."),
        ("BASE-016", "v3 strict shuffled", has_torch and exists("results/tables/ablation_edge_sets/strict_shuffled_graph_edges_v1.csv"), True, "Minimum graph-specific control."),
        ("BASE-017", "v3 real graph", has_torch and exists("results/tables/v2_graph_consensus_edges.csv"), True, "Minimum real graph model."),
    ]
    for asset_id, name, available, minimum, note in baselines:
        add_asset(rows, asset_id, "benchmark_baseline", name, "benchmark_harness", available, "baseline", "v3 benchmark suite", available and ("supervised" not in name), minimum, minimum and not available, note)

    env_specs = [
        ("CAUSAL-001", "donor metadata usable as environments", metadata_path, {"Donor ID"}),
        ("CAUSAL-002", "batch labels", metadata_path, {"Batch", "batch", "library_prep", "Specimen ID"}),
        ("CAUSAL-003", "sex", metadata_path, {"Sex"}),
        ("CAUSAL-004", "diagnosis", metadata_path, {"Cognitive Status", "Overall AD neuropathological Change"}),
        ("CAUSAL-005", "pathology strata", metadata_path, {"Braak", "Thal", "CERAD score", "Overall AD neuropathological Change"}),
        ("CAUSAL-006", "cell-state cluster labels", Path("data/processed/cell_state_cluster_labels.csv"), {"cell_state", "cluster"}),
        ("CAUSAL-007", "microglia/PVM labels", Path("data/processed/microglia_pvm_state_labels.csv"), {"microglia_state", "PVM"}),
        ("CAUSAL-008", "adjustment covariates", metadata_path, {"Age at Death", "Sex", "APOE Genotype", "Braak", "Thal"}),
    ]
    for asset_id, name, path, cols in env_specs:
        if path == metadata_path:
            present_cols = sorted(cols & metadata_cols)
            available = bool(present_cols)
            notes = f"Available columns: {present_cols}" if available else f"Missing expected columns among {sorted(cols)}"
        else:
            available = path.exists()
            notes = "Dedicated table found." if available else "Dedicated table not found; may be derivable from H5AD obs in Stage 24."
        add_asset(rows, asset_id, "causal_inference_asset", name, str(path), available, "metadata_or_schema", "environment invariance / causal adjustment", available, name in {"donor metadata usable as environments", "sex", "diagnosis", "pathology strata", "adjustment covariates"}, name in {"donor metadata usable as environments", "pathology strata"} and not available, notes)
    add_path_asset(rows, "CAUSAL-009", "causal_inference_asset", "candidate treatment/exposure definitions", "results/tables/discovery_final_candidate_shortlist_v3.csv", "csv", "shortlisted gene exposure candidates", True, False, "Shortlist can seed causal-hypothesis candidates.")
    add_path_asset(rows, "CAUSAL-010", "causal_inference_asset", "causal evidence schema", "results/tables/graph_jepa_v3_causal_evidence_schema_v1.csv", "csv", "causal evidence reporting schema", True, True, "Created in Stage 22B.")
    add_path_asset(rows, "CAUSAL-011", "causal_inference_asset", "causal inference layer spec", "results/reports/graph_jepa_v3_causal_inference_layer_spec_v1.md", "md", "causal anti-overclaiming spec", True, True, "Created in Stage 22B.")

    perturb_paths = [
        ("PERT-001", "Perturb-seq files", "data/processed/perturbseq"),
        ("PERT-002", "CRISPRi/CRISPRa files", "data/processed/crispr"),
        ("PERT-003", "public perturbation dataset references", "results/tables/perturbseq_streaming_validation.csv"),
        ("PERT-004", "fake perturbseq generator", "scripts/generate_fake_perturbseq.py"),
        ("PERT-005", "perturbation benchmark script", "scripts/benchmark_perturbseq_streaming.py"),
    ]
    for asset_id, name, path in perturb_paths:
        present = exists(path)
        usable = asset_id in {"PERT-001", "PERT-002"} and present
        add_asset(rows, asset_id, "perturbation_asset", name, path, present, "file_or_directory", "perturbation-supervised calibration", usable, False, False, "Future extension unless real perturbation dataset is present and overlap is audited.")

    inventory = pd.DataFrame(rows)
    missing_rows = []
    for row in inventory.itertuples(index=False):
        if not bool(row.exists_or_available) or not bool(row.immediately_usable):
            missing_rows.append(
                {
                    "missing_asset": row.asset_name,
                    "category": row.category,
                    "why_needed": row.v3_role,
                    "blocking_level": "minimum_v3_blocker" if bool(row.blocking_if_missing) else ("minimum_v3_needed_not_blocking" if bool(row.needed_for_minimum_v3) else "future_extension"),
                    "suggested_action": (
                        "generate_or_restore_before_stage_24"
                        if bool(row.blocking_if_missing)
                        else ("include_in_stage_24_plan_or_mark_deferred" if bool(row.needed_for_minimum_v3) else "defer_to_future_extension")
                    ),
                    "can_defer_to_future_extension": not bool(row.needed_for_minimum_v3),
                    "notes": row.notes,
                }
            )
    missing = pd.DataFrame(missing_rows)

    INVENTORY_OUT.parent.mkdir(parents=True, exist_ok=True)
    inventory.to_csv(INVENTORY_OUT, index=False)
    missing.to_csv(MISSING_OUT, index=False)

    immediately = inventory[inventory["immediately_usable"].astype(bool)]
    module_available = inventory[inventory["category"].eq("module_asset") & inventory["exists_or_available"].astype(bool)]
    graph_available = inventory[inventory["category"].eq("graph_source_asset") & inventory["exists_or_available"].astype(bool)]
    packages_available = inventory[inventory["category"].eq("benchmark_package") & inventory["exists_or_available"].astype(bool)]
    runnable_baselines = inventory[inventory["category"].eq("benchmark_baseline") & inventory["immediately_usable"].astype(bool)]
    causal_available = inventory[inventory["category"].eq("causal_inference_asset") & inventory["exists_or_available"].astype(bool)]
    perturb_usable = inventory[inventory["category"].eq("perturbation_asset") & inventory["immediately_usable"].astype(bool)]

    lines = [
        "# V3 Reusable Asset Inventory v1",
        "",
        "## 1. Executive summary",
        "",
        f"- Inventory rows: {len(inventory)}",
        f"- Immediately usable assets: {len(immediately)}",
        f"- Missing/deferred assets: {len(missing)}",
        f"- Minimum-v3 blockers: {int(missing['blocking_level'].eq('minimum_v3_blocker').sum()) if not missing.empty else 0}",
        "- No training was run.",
        "- No packages were installed.",
        "",
        "## 2. Assets immediately reusable from v2",
        "",
        *markdown_table(immediately, ["asset_id", "category", "asset_name", "v3_role", "size_or_count"], 25),
        "",
        "## 3. Module/WGCNA availability",
        "",
        *markdown_table(module_available, ["asset_id", "asset_name", "expected_path_or_package", "immediately_usable", "notes"], 20),
        "",
        "## 4. Graph-source availability",
        "",
        *markdown_table(graph_available, ["asset_id", "asset_name", "expected_path_or_package", "immediately_usable", "notes"], 20),
        "",
        "If a source-specific WGCNA/TOM or STRING derivative is missing in a future environment, Stage 24 should not fail automatically; generate it locally or use the current real graph as the first v3 typed-graph source.",
        "",
        "## 5. Benchmark package availability",
        "",
        *markdown_table(packages_available, ["asset_id", "asset_name", "exists_or_available", "v3_role"], 30),
        "",
        "Unavailable PHATE, scVI, DoWhy, EconML, or diffusion packages should be marked unavailable; do not install them in this stage.",
        "This package check used the current `python` executable. Prior model training used the `sea-ad-jepa` Conda environment, so Stage 24 should explicitly choose and record the benchmark runtime environment before treating package gaps as infrastructure blockers.",
        "",
        "## 6. Benchmark baselines immediately runnable",
        "",
        *markdown_table(runnable_baselines, ["asset_id", "asset_name", "immediately_usable", "notes"], 30),
        "",
        "## 7. Causal inference metadata availability",
        "",
        *markdown_table(causal_available, ["asset_id", "asset_name", "immediately_usable", "notes"], 30),
        "",
        "## 8. Perturbation-data availability",
        "",
        *markdown_table(inventory[inventory["category"].eq("perturbation_asset")], ["asset_id", "asset_name", "exists_or_available", "immediately_usable", "notes"], 30),
        "",
        "Perturbation-supervised calibration is future-only unless a real Perturb-seq, CRISPRi, CRISPRa, or related dataset is present and gene overlap with the 2,957-gene universe is audited.",
        "",
        "## 9. Missing/deferred assets",
        "",
        *markdown_table(missing, ["missing_asset", "category", "blocking_level", "suggested_action", "notes"], 40),
        "",
        "## 10. Recommended Stage 24 plan",
        "",
        "1. Lock and materialize explicit v3 donor folds before any benchmark expansion.",
        "2. Build a benchmark harness that first runs immediately available PCA, raw expression ridge/ElasticNet, and module mean baselines in the current environment.",
        "3. Select and record the Stage 24 runtime environment, then enable torch-dependent expression MLP, autoencoder, v3 real graph, v3 no-graph, and v3 strict shuffled controls.",
        "4. Add UMAP/t-SNE only with leakage-safe fold-local fitting; supervised UMAP remains gated until the leakage protocol is explicit.",
        "5. Treat PHATE, diffusion maps, scVI, DoWhy, and EconML as optional/deferred if unavailable.",
        "6. Generate missing module-to-gene and WGCNA eigengene tables from existing module definitions/WGCNA outputs where useful.",
        "7. Keep perturbation-supervised calibration as a future extension unless real perturbation data are added and overlap-audited.",
        "",
    ]
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(inventory.groupby("category")["asset_name"].count().to_string())
    print(f"Immediately usable assets: {len(immediately)}")
    print(f"Missing/deferred assets: {len(missing)}")
    print(f"Wrote {INVENTORY_OUT}")
    print(f"Wrote {MISSING_OUT}")
    print(f"Wrote {REPORT_OUT}")


if __name__ == "__main__":
    main()
