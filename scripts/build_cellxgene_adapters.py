from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse

from sea_ad_jepa.graph_data import read_h5ad_var_names


MICROGLIA_ONTOLOGY_ID = "CL:0000129"


def obs_column(obs: pd.DataFrame, candidates: list[str]) -> str | None:
    for col in candidates:
        if col in obs.columns:
            return col
    return None


def gene_symbols(adata: ad.AnnData) -> list[str]:
    if "feature_name" in adata.var.columns:
        return adata.var["feature_name"].astype(str).tolist()
    if "gene_name" in adata.var.columns:
        return adata.var["gene_name"].astype(str).tolist()
    if "gene_symbols" in adata.var.columns:
        return adata.var["gene_symbols"].astype(str).tolist()
    return adata.var_names.astype(str).tolist()


def microglia_mask(obs: pd.DataFrame) -> pd.Series:
    mask = pd.Series(False, index=obs.index)
    if "cell_type_ontology_term_id" in obs.columns:
        mask = mask | obs["cell_type_ontology_term_id"].astype(str).eq(MICROGLIA_ONTOLOGY_ID)
    if "cell_type" in obs.columns:
        mask = mask | obs["cell_type"].astype(str).str.lower().eq("microglial cell")
    return mask


def select_obs_columns(obs: pd.DataFrame) -> pd.DataFrame:
    keep = [
        "donor_id",
        "suspension_type",
        "assay",
        "disease",
        "disease_ontology_term_id",
        "tissue",
        "tissue_ontology_term_id",
        "cell_type",
        "cell_type_ontology_term_id",
        "development_stage",
        "sex",
        "self_reported_ethnicity",
    ]
    return obs[[col for col in keep if col in obs.columns]].copy()


def count_unique(obs: pd.DataFrame, candidates: list[str]) -> int:
    col = obs_column(obs, candidates)
    if col is None:
        return 0
    return int(obs[col].nunique(dropna=True))


def value_counts(obs: pd.DataFrame, col: str, max_items: int = 12) -> str:
    if col not in obs.columns:
        return "not available"
    counts = obs[col].astype(str).value_counts(dropna=False).head(max_items)
    return "; ".join(f"{idx}: {value}" for idx, value in counts.items())


def align_h5ad(
    label: str,
    input_h5ad: Path,
    jepa_genes: list[str],
    out_dir: Path,
    max_cells: int,
    seed: int,
) -> dict[str, object]:
    if not input_h5ad.exists():
        raise FileNotFoundError(input_h5ad)

    print(f"\n[{label}] Reading {input_h5ad}")
    source = ad.read_h5ad(input_h5ad, backed="r")
    obs = source.obs.copy()
    keep = microglia_mask(obs)
    if not keep.any():
        raise ValueError(f"{label}: no microglia found using cell_type == 'microglial cell' or {MICROGLIA_ONTOLOGY_ID}")
    selected_idx = np.flatnonzero(keep.to_numpy())
    if max_cells > 0 and len(selected_idx) > max_cells:
        rng = np.random.default_rng(seed)
        selected_idx = np.sort(rng.choice(selected_idx, size=max_cells, replace=False))
    selected_obs = select_obs_columns(obs.iloc[selected_idx]).reset_index(drop=True)

    symbols = gene_symbols(source)
    symbol_to_source: dict[str, int] = {}
    for idx, gene in enumerate(symbols):
        symbol_to_source.setdefault(str(gene).upper(), idx)

    present_pairs: list[tuple[int, int]] = []
    missing_genes: list[str] = []
    for out_idx, gene in enumerate(jepa_genes):
        src_idx = symbol_to_source.get(str(gene).upper())
        if src_idx is None:
            missing_genes.append(gene)
        else:
            present_pairs.append((out_idx, src_idx))

    source_order = [src for _, src in present_pairs]
    output_order = [out for out, _ in present_pairs]
    x_present = source[selected_idx, source_order].X
    if not sparse.issparse(x_present):
        x_present = sparse.csr_matrix(np.asarray(x_present, dtype=np.float32))
    else:
        x_present = x_present.tocsr().astype(np.float32)

    columns = []
    present_lookup = {out_idx: pos for pos, out_idx in enumerate(output_order)}
    zero_col = sparse.csr_matrix((len(selected_idx), 1), dtype=np.float32)
    for out_idx in range(len(jepa_genes)):
        pos = present_lookup.get(out_idx)
        if pos is None:
            columns.append(zero_col.copy())
        else:
            columns.append(x_present[:, pos])
    aligned_x = sparse.hstack(columns, format="csr", dtype=np.float32)

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{label}_microglia_jepa_aligned.h5ad"
    out = ad.AnnData(
        X=aligned_x,
        obs=selected_obs,
        var=pd.DataFrame(index=pd.Index(jepa_genes, name="gene")),
        uns={
            "source_h5ad": str(input_h5ad),
            "adapter": "scripts/build_cellxgene_adapters.py",
            "missing_gene_policy": "zero_fill",
            "cell_type_filter": f"cell_type == microglial cell or cell_type_ontology_term_id == {MICROGLIA_ONTOLOGY_ID}",
        },
    )
    out.write_h5ad(out_path, compression="gzip")
    source.file.close()

    stats: dict[str, object] = {
        "dataset": label,
        "input_h5ad": str(input_h5ad),
        "output_h5ad": str(out_path),
        "source_cells": int(source.n_obs),
        "source_genes": int(source.n_vars),
        "microglia_cells": int(len(selected_idx)),
        "donors": count_unique(selected_obs, ["donor_id", "Donor ID", "SampleID", "sample_id"]),
        "jepa_genes": int(len(jepa_genes)),
        "matched_genes": int(len(present_pairs)),
        "missing_genes": int(len(missing_genes)),
        "gene_overlap_fraction": float(len(present_pairs) / max(len(jepa_genes), 1)),
        "disease_counts": value_counts(selected_obs, "disease"),
        "tissue_counts": value_counts(selected_obs, "tissue"),
        "assay_counts": value_counts(selected_obs, "assay"),
    }

    missing_path = out_dir / f"{label}_missing_genes.txt"
    missing_path.write_text("\n".join(missing_genes) + ("\n" if missing_genes else ""), encoding="utf-8")
    stats["missing_gene_file"] = str(missing_path)

    print(
        f"[{label}] microglia={stats['microglia_cells']} donors={stats['donors']} "
        f"matched={stats['matched_genes']}/{stats['jepa_genes']} -> {out_path}"
    )
    return stats


def markdown_report(stats: list[dict[str, object]]) -> str:
    lines = [
        "# v2.2 CELLxGENE Alignment Stats",
        "",
        "This report summarizes public CELLxGENE cohorts filtered to microglia and aligned to the fixed 2,957-gene Graph-JEPA topology.",
        "",
        "Missing genes are zero-filled. The master Graph-JEPA gene order and graph topology are not modified.",
        "",
        "| Dataset | Microglia | Donors | Matched Genes | Overlap | Disease Counts | Tissue Counts | Assay Counts |",
        "| --- | ---: | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for row in stats:
        lines.append(
            "| {dataset} | {microglia_cells} | {donors} | {matched_genes}/{jepa_genes} | {gene_overlap_fraction:.3f} | {disease_counts} | {tissue_counts} | {assay_counts} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Outputs",
            "",
        ]
    )
    for row in stats:
        lines.extend(
            [
                f"### {row['dataset']}",
                "",
                f"- input: `{row['input_h5ad']}`",
                f"- aligned output: `{row['output_h5ad']}`",
                f"- missing genes: `{row['missing_gene_file']}`",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Graph-JEPA-aligned public CELLxGENE microglia adapters.")
    parser.add_argument("--local-h5ad", default="data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad")
    parser.add_argument("--rexach-h5ad", default="")
    parser.add_argument("--olah-h5ad", default="")
    parser.add_argument("--out-dir", default="data/processed/v2_alignment")
    parser.add_argument("--report-out", default="results/reports/v2_2_cellxgene_alignment_stats.md")
    parser.add_argument("--summary-out", default="results/tables/v2_2_cellxgene_alignment_stats.csv")
    parser.add_argument("--max-cells", type=int, default=0)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    jepa_genes = read_h5ad_var_names(args.local_h5ad)
    stats = []
    if args.rexach_h5ad:
        stats.append(align_h5ad("rexach_cross_dementia", Path(args.rexach_h5ad), jepa_genes, Path(args.out_dir), args.max_cells, args.seed))
    if args.olah_h5ad:
        stats.append(align_h5ad("olah_live_microglia", Path(args.olah_h5ad), jepa_genes, Path(args.out_dir), args.max_cells, args.seed))
    if not stats:
        raise SystemExit("Provide at least one of --rexach-h5ad or --olah-h5ad")

    summary_path = Path(args.summary_out)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(stats).to_csv(summary_path, index=False)
    report_path = Path(args.report_out)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(markdown_report(stats), encoding="utf-8")
    print(f"Wrote {summary_path}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
