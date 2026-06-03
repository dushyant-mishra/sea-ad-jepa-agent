from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import h5py
import numpy as np
import pandas as pd
from scipy import sparse


STRICT_FILTER = (
    "disease == 'normal' and "
    "cell_type == 'microglial cell' and "
    "tissue_general == 'brain' and "
    "is_primary_data == True and "
    "suspension_type == 'nucleus' and "
    "assay == \"10x 3' v3 transcription profiling\""
)


def decode_array(values) -> list[str]:
    return [x.decode("utf-8") if isinstance(x, bytes) else str(x) for x in values]


def read_h5ad_var_names(path: Path) -> list[str]:
    with h5py.File(path, "r") as h5:
        var = h5["var"]
        index_key = var.attrs.get("_index", None)
        if isinstance(index_key, bytes):
            index_key = index_key.decode("utf-8")
        if index_key and index_key in var:
            return decode_array(var[index_key][()])
        if "_index" in var:
            return decode_array(var["_index"][()])
    raise KeyError(f"Could not read var names from {path}")


def quote_for_filter(values: list[str]) -> str:
    quoted = []
    for value in values:
        escaped = str(value).replace("\\", "\\\\").replace("'", "\\'")
        quoted.append(f"'{escaped}'")
    return "[" + ", ".join(quoted) + "]"


def add_missing_zero_genes(adata, jepa_genes: list[str]):
    import anndata as ad

    adata.var_names = adata.var["feature_name"].astype(str).to_numpy()
    adata.var_names_make_unique()
    pulled = set(adata.var_names.astype(str))
    matched = [gene for gene in jepa_genes if gene in pulled]
    missing = [gene for gene in jepa_genes if gene not in pulled]

    aligned = adata[:, matched].copy() if matched else adata[:, []].copy()
    if missing:
        zero = sparse.csr_matrix((aligned.n_obs, len(missing)), dtype=np.float32)
        missing_var = pd.DataFrame(index=missing)
        missing_var["feature_name"] = missing
        missing_adata = ad.AnnData(X=zero, obs=aligned.obs.copy(), var=missing_var)
        aligned = ad.concat([aligned, missing_adata], axis=1, join="outer", merge="first")

    aligned = aligned[:, jepa_genes].copy()
    return aligned, matched, missing


def save_qc(adata, matched: list[str], missing: list[str], args: argparse.Namespace) -> None:
    qc_dir = Path(args.qc_dir)
    qc_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        {"metric": "n_cells", "value": int(adata.n_obs)},
        {"metric": "n_genes", "value": int(adata.n_vars)},
        {"metric": "n_matched_jepa_genes", "value": len(matched)},
        {"metric": "n_missing_jepa_genes", "value": len(missing)},
        {"metric": "n_donors", "value": int(adata.obs["donor_id"].nunique()) if "donor_id" in adata.obs else np.nan},
        {"metric": "obs_filter", "value": args.obs_filter},
    ]
    pd.DataFrame(rows).to_csv(qc_dir / "cellxgene_normal_microglia_anchor_qc.csv", index=False)
    pd.DataFrame({"gene": matched}).to_csv(qc_dir / "cellxgene_normal_microglia_matched_genes.csv", index=False)
    pd.DataFrame({"gene": missing}).to_csv(qc_dir / "cellxgene_normal_microglia_missing_genes.csv", index=False)
    for col in ["assay", "tissue", "tissue_general", "disease", "donor_id", "development_stage", "dataset_id", "suspension_type"]:
        if col in adata.obs:
            counts = adata.obs[col].astype(str).value_counts(dropna=False).rename_axis(col).reset_index(name="n_cells")
            counts.to_csv(qc_dir / f"cellxgene_normal_microglia_{col}_counts.csv", index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a strict CELLxGENE normal microglia Stage A anchor aligned to SEA-AD JEPA genes.")
    parser.add_argument("--local-h5ad", default="data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad")
    parser.add_argument("--out", default="data/processed/v2_pretraining/cellxgene_normal_microglia_strict_jepa_aligned.h5ad")
    parser.add_argument("--qc-dir", default="results/tables")
    parser.add_argument("--max-cells", type=int, default=10000)
    parser.add_argument("--obs-filter", default=STRICT_FILTER)
    parser.add_argument("--census-version", default=None)
    args = parser.parse_args()

    try:
        import cellxgene_census
        import scanpy as sc
    except ImportError as exc:
        raise SystemExit("Missing dependency. Install with: python -m pip install cellxgene-census") from exc

    jepa_genes = read_h5ad_var_names(Path(args.local_h5ad))
    print(f"Targeting {len(jepa_genes):,} JEPA genes from {args.local_h5ad}")
    print(f"Strict obs filter:\n{args.obs_filter}")
    print(f"Pilot max cells: {args.max_cells:,}")

    open_kwargs = {}
    if args.census_version:
        open_kwargs["census_version"] = args.census_version

    with cellxgene_census.open_soma(**open_kwargs) as census:
        adata = cellxgene_census.get_anndata(
            census,
            organism="Homo sapiens",
            obs_value_filter=args.obs_filter,
            var_value_filter=f"feature_name in {quote_for_filter(jepa_genes)}",
            column_names={
                "obs": [
                    "assay",
                    "tissue",
                    "tissue_general",
                    "disease",
                    "donor_id",
                    "development_stage",
                    "dataset_id",
                    "suspension_type",
                ],
                "var": ["feature_name", "feature_id"],
            },
        )

    if adata.n_obs == 0:
        raise SystemExit("Strict CELLxGENE query returned 0 cells. Relax assay or suspension_type one step at a time.")
    if args.max_cells and adata.n_obs > args.max_cells:
        rng = np.random.default_rng(42)
        idx = np.sort(rng.choice(adata.n_obs, size=args.max_cells, replace=False))
        adata = adata[idx].copy()

    print(f"Streamed {adata.n_obs:,} normal-labeled microglia nuclei before gene alignment")
    aligned, matched, missing = add_missing_zero_genes(adata, jepa_genes)
    print(f"Matched {len(matched):,} / {len(jepa_genes):,} JEPA genes")
    print(f"Zero-padded {len(missing):,} missing JEPA genes")

    print("Normalizing to 10k total counts and log1p")
    sc.pp.normalize_total(aligned, target_sum=1e4)
    sc.pp.log1p(aligned)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    aligned.write_h5ad(out_path)
    save_qc(aligned, matched, missing, args)

    print(f"Saved aligned Stage A anchor: {out_path}")
    print(f"Cells: {aligned.n_obs:,}")
    print(f"Donors: {aligned.obs['donor_id'].nunique() if 'donor_id' in aligned.obs else 'NA'}")
    if "assay" in aligned.obs:
        print("Assays:")
        print(aligned.obs["assay"].value_counts().to_string())
    if "tissue" in aligned.obs:
        print("Top tissues:")
        print(aligned.obs["tissue"].value_counts().head(10).to_string())


if __name__ == "__main__":
    main()
