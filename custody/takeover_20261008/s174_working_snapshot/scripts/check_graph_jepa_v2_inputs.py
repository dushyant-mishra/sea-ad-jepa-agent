from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd

from sea_ad_jepa.graph_data import (
    DEFAULT_NODE_ANNOTATION_COLS,
    load_consensus_edge_index,
    load_node_annotations,
    read_h5ad_var_names,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Graph-JEPA v2 graph, annotation, and anchor inputs.")
    parser.add_argument("--local-h5ad", default="data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad")
    parser.add_argument("--edge-csv", default="results/tables/v2_graph_consensus_edge_index.csv")
    parser.add_argument("--annotation-csv", default="results/tables/jepa_v2_translational_actionability_matrix.csv")
    parser.add_argument("--anchor-h5ad", default="")
    parser.add_argument("--out", default="results/tables/graph_jepa_v2_input_check.csv")
    args = parser.parse_args()

    genes = read_h5ad_var_names(args.local_h5ad)
    edge_index = load_consensus_edge_index(args.edge_csv)
    annotations = load_node_annotations(args.annotation_csv, genes)
    rows = [
        {"metric": "n_genes", "value": len(genes)},
        {"metric": "n_edge_index_columns", "value": int(edge_index.shape[1])},
        {"metric": "max_edge_node_idx", "value": int(edge_index.max().item())},
        {"metric": "n_annotation_rows", "value": int(annotations.shape[0])},
    ]
    for col in DEFAULT_NODE_ANNOTATION_COLS:
        rows.append({"metric": f"annotation_sum_{col}", "value": int(annotations[col].sum())})

    if args.anchor_h5ad:
        anchor_genes = read_h5ad_var_names(args.anchor_h5ad)
        rows.extend(
            [
                {"metric": "anchor_n_genes", "value": len(anchor_genes)},
                {"metric": "anchor_exact_gene_order_match", "value": int(anchor_genes == genes)},
            ]
        )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out_path, index=False)
    print(pd.DataFrame(rows).to_string(index=False))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
