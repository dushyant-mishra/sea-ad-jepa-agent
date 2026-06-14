from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import anndata as ad
import numpy as np
import pandas as pd
import scanpy as sc
from scipy import sparse
from scipy.stats import hypergeom


LU_EARLY_PIG_SEED_GENES = [
    "C1QB",
    "APOC1",
    "TYROBP",
    "S100A8",
]

LU_LATE_PIG_SEED_GENES = [
    "SPP1",
    "CCL3",
    "CH25H",
    "RGS1",
]

CANONICAL_DAM_GENES = [
    "APOE",
    "TREM2",
    "TYROBP",
    "LPL",
    "SPP1",
    "CST7",
    "CTSD",
    "C1QA",
    "C1QB",
    "C1QC",
    "CD9",
]


def hypergeom_overlap(discovered: set[str], reference: set[str], universe: set[str]) -> tuple[int, float, str]:
    discovered = {gene.upper() for gene in discovered if gene.upper() in universe}
    reference = {gene.upper() for gene in reference if gene.upper() in universe}
    overlap_genes = sorted(discovered & reference)
    overlap = len(overlap_genes)
    pval = hypergeom.sf(overlap - 1, len(universe), len(reference), len(discovered)) if discovered and reference else float("nan")
    return overlap, float(pval), ";".join(overlap_genes)


def load_reference_sets(path: str | None) -> dict[str, list[str]]:
    refs = {
        "lu_early_pig_seed": LU_EARLY_PIG_SEED_GENES,
        "lu_late_pig_seed": LU_LATE_PIG_SEED_GENES,
        "canonical_dam": CANONICAL_DAM_GENES,
    }
    if path is None:
        return refs
    ref_path = Path(path)
    if not ref_path.exists():
        raise FileNotFoundError(path)
    table = pd.read_csv(ref_path)
    if not {"signature", "gene"}.issubset(table.columns):
        raise ValueError("Reference signature CSV must contain columns: signature,gene")
    for signature, group in table.groupby("signature"):
        refs[str(signature)] = group["gene"].astype(str).str.upper().dropna().unique().tolist()
    return refs


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate high-attention MIL cells against DGE and PIG/DAM signatures.")
    parser.add_argument("--h5ad", default="data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad")
    parser.add_argument("--attention", default="results/tables/v2_2_abeta_mil_head_attention.csv")
    parser.add_argument("--top-quantile", type=float, default=0.95)
    parser.add_argument(
        "--signature-csv",
        default=None,
        help="Optional CSV with columns signature,gene, e.g. Lu Supplementary Table 3-derived gene sets.",
    )
    parser.add_argument("--out-prefix", default="results/tables/v2_2_abeta_mil_attention")
    args = parser.parse_args()

    adata = ad.read_h5ad(args.h5ad)
    if sparse.issparse(adata.X):
        pass
    attention = pd.read_csv(args.attention)
    if "cell_id" not in attention.columns or "attention_weight" not in attention.columns:
        raise ValueError("Attention CSV must contain cell_id and attention_weight")
    # A cell appears once, because each donor belongs to exactly one held-out fold.
    cell_attention = (
        attention.dropna(subset=["cell_id"])
        .groupby("cell_id", as_index=False)["attention_weight"]
        .mean()
    )
    cell_attention["cell_id"] = cell_attention["cell_id"].astype(str)
    common = adata.obs_names.astype(str).intersection(pd.Index(cell_attention["cell_id"]))
    if len(common) == 0:
        raise ValueError("No overlapping cell IDs between AnnData and attention table")
    adata = adata[common].copy()
    cell_attention = cell_attention.set_index("cell_id").loc[adata.obs_names.astype(str)]
    adata.obs["mil_attention_weight"] = cell_attention["attention_weight"].to_numpy(dtype=np.float32)
    threshold = float(np.quantile(adata.obs["mil_attention_weight"], args.top_quantile))
    adata.obs["mil_attention_group"] = np.where(
        adata.obs["mil_attention_weight"] >= threshold,
        "high_attention",
        "background",
    )
    n_high = int((adata.obs["mil_attention_group"] == "high_attention").sum())
    print(f"High-attention cells: {n_high:,} / {adata.n_obs:,}")

    sc.tl.rank_genes_groups(
        adata,
        groupby="mil_attention_group",
        groups=["high_attention"],
        reference="background",
        method="wilcoxon",
    )
    dge = sc.get.rank_genes_groups_df(adata, group="high_attention")
    dge = dge.sort_values(["pvals_adj", "logfoldchanges"], ascending=[True, False])
    up = dge[(dge["pvals_adj"] < 0.05) & (dge["logfoldchanges"] > 0)].copy()

    universe = {gene.upper() for gene in adata.var_names.astype(str)}
    top_up_50 = set(up.head(50)["names"].astype(str).str.upper())
    refs = load_reference_sets(args.signature_csv)
    overlap_rows = []
    for signature, genes in refs.items():
        overlap, pval, overlap_genes = hypergeom_overlap(top_up_50, set(genes), universe)
        overlap_rows.append(
            {
                "signature": signature,
                "n_reference_genes_present": len({gene.upper() for gene in genes if gene.upper() in universe}),
                "n_top50_upregulated_overlap": overlap,
                "hypergeom_p": pval,
                "overlap_genes": overlap_genes,
            }
        )
    overlap_df = pd.DataFrame(overlap_rows).sort_values("hypergeom_p", na_position="last")
    summary = pd.DataFrame(
        [
            {
                "n_cells": int(adata.n_obs),
                "n_high_attention_cells": n_high,
                "top_quantile": args.top_quantile,
                "attention_threshold": threshold,
                "top_upregulated_genes": ";".join(up.head(20)["names"].astype(str).tolist()),
            }
        ]
    )

    out_prefix = Path(args.out_prefix)
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    dge.to_csv(f"{out_prefix}_dge_all_summary.csv", index=False)
    up.to_csv(f"{out_prefix}_dge_upregulated_summary.csv", index=False)
    overlap_df.to_csv(f"{out_prefix}_signature_overlap_summary.csv", index=False)
    summary.to_csv(f"{out_prefix}_summary.csv", index=False)
    print("\nSignature overlaps")
    print(overlap_df.to_string(index=False))
    print("\nTop upregulated genes")
    print(up.head(20)[["names", "scores", "logfoldchanges", "pvals_adj"]].to_string(index=False))
    print(f"\nWrote outputs with prefix: {out_prefix}")


if __name__ == "__main__":
    main()
