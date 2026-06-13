from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd

from sea_ad_jepa.graph_data import read_h5ad_var_names


def genes_from_10x_h5(path: Path) -> set[str]:
    import scanpy as sc

    adata = sc.read_10x_h5(path)
    return {str(gene).upper() for gene in adata.var_names}


def genes_from_counts_csv(path: Path, chunksize: int) -> set[str]:
    genes: set[str] = set()
    first_col = pd.read_csv(path, nrows=0).columns[0]
    for chunk in pd.read_csv(path, usecols=[first_col], chunksize=chunksize):
        genes.update(chunk[first_col].astype(str).str.upper().tolist())
    return genes


def write_missing(name: str, external_genes: set[str], jepa_genes: list[str], out_dir: Path) -> Path:
    missing = [gene for gene in jepa_genes if gene.upper() not in external_genes]
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{name}_missing_genes.txt"
    path.write_text("\n".join(missing) + ("\n" if missing else ""), encoding="utf-8")
    print(f"{name}: matched={len(jepa_genes) - len(missing)} missing={len(missing)} total={len(jepa_genes)} -> {path}")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build missing-gene masks for external cohorts against Graph-JEPA gene order.")
    parser.add_argument("--local-h5ad", default="data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad")
    parser.add_argument("--out-dir", default="results/tables/external_gene_masks")
    parser.add_argument("--gse174367-h5", default="data/external/gse174367/GSE174367_snRNA-seq_filtered_feature_bc_matrix.h5")
    parser.add_argument("--gse138852-counts", default="data/external/grubman_gse138852/GSE138852_counts.csv.gz")
    parser.add_argument("--counts-chunksize", type=int, default=4096)
    args = parser.parse_args()

    jepa_genes = read_h5ad_var_names(args.local_h5ad)
    out_dir = Path(args.out_dir)
    summary = []

    gse174367 = Path(args.gse174367_h5)
    if gse174367.exists():
        path = write_missing("gse174367_morabito", genes_from_10x_h5(gse174367), jepa_genes, out_dir)
        summary.append({"cohort": "gse174367_morabito", "mask_file": str(path)})
    else:
        print(f"Skipping missing file: {gse174367}")

    gse138852 = Path(args.gse138852_counts)
    if gse138852.exists():
        path = write_missing("gse138852_grubman", genes_from_counts_csv(gse138852, args.counts_chunksize), jepa_genes, out_dir)
        summary.append({"cohort": "gse138852_grubman", "mask_file": str(path)})
    else:
        print(f"Skipping missing file: {gse138852}")

    if summary:
        pd.DataFrame(summary).to_csv(out_dir / "external_gene_masks_manifest.csv", index=False)


if __name__ == "__main__":
    main()
