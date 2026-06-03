from __future__ import annotations

import argparse
import urllib.request
from pathlib import Path

import h5py
import numpy as np
import pandas as pd


HPA_QUERIES = {
    "hpa_fda_drug_target": "protein_class:FDA+approved+drug+targets",
    "hpa_predicted_secreted": "protein_class:Predicted+secreted+proteins",
    "hpa_predicted_membrane": "protein_class:Predicted+membrane+proteins",
}


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


def load_jepa_genes(local_h5ad: Path, fallback_gene_csv: Path | None) -> list[str]:
    if local_h5ad.exists():
        return read_h5ad_var_names(local_h5ad)
    if fallback_gene_csv and fallback_gene_csv.exists():
        df = pd.read_csv(fallback_gene_csv)
        gene_col = find_col(df, ["gene", "Gene", "feature_name"])
        return df[gene_col].astype(str).tolist()
    raise FileNotFoundError(f"Could not find {local_h5ad} or fallback gene CSV {fallback_gene_csv}")


def find_col(df: pd.DataFrame, candidates: list[str]) -> str:
    for col in candidates:
        if col in df.columns:
            return col
    raise KeyError(f"None of {candidates} found in columns: {list(df.columns)}")


def hpa_url(query: str) -> str:
    return (
        "https://www.proteinatlas.org/api/search_download.php?"
        f"search={query}&format=tsv&columns=g,gs&compress=no"
    )


def download_hpa_table(name: str, query: str, out_dir: Path, refresh: bool) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{name}.tsv"
    if path.exists() and not refresh:
        return path
    req = urllib.request.Request(hpa_url(query), headers={"User-Agent": "sea-ad-jepa-translational-audit/1.0"})
    with urllib.request.urlopen(req, timeout=120) as response:
        path.write_bytes(response.read())
    return path


def read_hpa_genes(path: Path) -> set[str]:
    df = pd.read_csv(path, sep="\t")
    gene_col = find_col(df, ["Gene", "gene", "Gene name", "gene_name"])
    return set(df[gene_col].dropna().astype(str).str.upper())


def minmax(values: pd.Series) -> pd.Series:
    values = pd.to_numeric(values, errors="coerce")
    if values.notna().sum() == 0:
        return pd.Series(np.zeros(len(values)), index=values.index)
    lo = values.min()
    hi = values.max()
    if not np.isfinite(lo) or not np.isfinite(hi) or hi == lo:
        return pd.Series(np.zeros(len(values)), index=values.index)
    return (values - lo) / (hi - lo)


def load_optional_csv(path: Path, label: str) -> pd.DataFrame | None:
    if not path.exists():
        print(f"[WARN] Missing {label}: {path}")
        return None
    return pd.read_csv(path)


def build_master_table(args: argparse.Namespace, hpa_sets: dict[str, set[str]]) -> pd.DataFrame:
    jepa_genes = load_jepa_genes(Path(args.local_h5ad), Path(args.fallback_gene_csv) if args.fallback_gene_csv else None)
    master = pd.DataFrame({"gene": jepa_genes})
    master["gene_upper"] = master["gene"].astype(str).str.upper()

    v1 = load_optional_csv(Path(args.v1_candidates), "v1 candidate genes")
    if v1 is not None:
        gene_col = find_col(v1, ["gene", "Gene"])
        v1 = v1.rename(columns={gene_col: "gene"})
        v1["gene_upper"] = v1["gene"].astype(str).str.upper()
        keep = [
            "gene_upper",
            "module",
            "mean_donor_delta",
            "bootstrap_ci_low",
            "bootstrap_ci_high",
            "adjusted_slope",
            "partial_spearman",
            "model_implied_at8_reducing_knockout",
            "confounder_adjusted_abs_partial_spearman",
        ]
        keep = [col for col in keep if col in v1.columns]
        master = master.merge(v1[keep].drop_duplicates("gene_upper"), on="gene_upper", how="left")

    at8 = load_optional_csv(Path(args.at8_rankings), "AT8 gene rankings")
    if at8 is not None:
        gene_col = find_col(at8, ["gene", "Gene"])
        at8 = at8.rename(columns={gene_col: "gene"})
        at8["gene_upper"] = at8["gene"].astype(str).str.upper()
        score_col = find_col(at8, ["score", "abs_score"])
        at8 = at8[["gene_upper", score_col]].drop_duplicates("gene_upper").rename(columns={score_col: "at8_pseudobulk_score"})
        master = master.merge(at8, on="gene_upper", how="left")

    for name, genes in hpa_sets.items():
        master[f"is_{name}"] = master["gene_upper"].isin(genes).astype(int)

    master["biology_score"] = 0.0
    if "confounder_adjusted_abs_partial_spearman" in master:
        master["biology_score"] += minmax(master["confounder_adjusted_abs_partial_spearman"]).fillna(0) * 0.45
    if "mean_donor_delta" in master:
        knockout_strength = pd.to_numeric(master["mean_donor_delta"], errors="coerce").abs()
        master["biology_score"] += minmax(knockout_strength).fillna(0) * 0.35
    if "at8_pseudobulk_score" in master:
        master["biology_score"] += minmax(pd.to_numeric(master["at8_pseudobulk_score"], errors="coerce").abs()).fillna(0) * 0.20

    master["translational_bonus"] = (
        master["is_hpa_fda_drug_target"] * 0.25
        + master["is_hpa_predicted_membrane"] * 0.20
        + master["is_hpa_predicted_secreted"] * 0.15
    )
    master["translational_priority_score"] = master["biology_score"] + master["translational_bonus"]

    def category(row: pd.Series) -> str:
        if row["is_hpa_fda_drug_target"] and row["is_hpa_predicted_membrane"]:
            return "actionable_surface_drug_target"
        if row["is_hpa_fda_drug_target"]:
            return "known_drug_target"
        if row["is_hpa_predicted_membrane"]:
            return "surface_target_candidate"
        if row["is_hpa_predicted_secreted"]:
            return "secreted_biomarker_candidate"
        return "biology_first_hard_target"

    master["translational_category"] = master.apply(category, axis=1)
    master = master.sort_values(
        ["translational_priority_score", "biology_score", "gene"],
        ascending=[False, False, True],
    )
    return master.drop(columns=["gene_upper"])


def write_summary(master: pd.DataFrame, out_path: Path, summary_path: Path) -> None:
    rows = [
        {"metric": "n_jepa_genes", "value": int(len(master))},
        {"metric": "n_hpa_fda_drug_targets", "value": int(master["is_hpa_fda_drug_target"].sum())},
        {"metric": "n_hpa_predicted_secreted", "value": int(master["is_hpa_predicted_secreted"].sum())},
        {"metric": "n_hpa_predicted_membrane", "value": int(master["is_hpa_predicted_membrane"].sum())},
        {
            "metric": "n_fda_and_membrane",
            "value": int(((master["is_hpa_fda_drug_target"] == 1) & (master["is_hpa_predicted_membrane"] == 1)).sum()),
        },
    ]
    category_counts = master["translational_category"].value_counts()
    for category, value in category_counts.items():
        rows.append({"metric": f"category_{category}", "value": int(value)})
    pd.DataFrame(rows).to_csv(summary_path, index=False)
    master.to_csv(out_path, index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit JEPA genes for translational actionability annotations.")
    parser.add_argument("--local-h5ad", default="data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad")
    parser.add_argument("--fallback-gene-csv", default="")
    parser.add_argument("--v1-candidates", default="results/tables/v1_hypothesis_candidate_genes.csv")
    parser.add_argument("--at8-rankings", default="results/tables/microglia_pvm_percent_AT8_gene_rankings.csv")
    parser.add_argument("--hpa-dir", default="data/external/hpa")
    parser.add_argument("--out", default="results/tables/jepa_v2_translational_actionability_matrix.csv")
    parser.add_argument("--summary-out", default="results/tables/jepa_v2_translational_actionability_summary.csv")
    parser.add_argument("--refresh-hpa", action="store_true")
    args = parser.parse_args()

    hpa_dir = Path(args.hpa_dir)
    hpa_sets = {}
    for name, query in HPA_QUERIES.items():
        print(f"Loading HPA annotation: {name}")
        path = download_hpa_table(name, query, hpa_dir, args.refresh_hpa)
        hpa_sets[name] = read_hpa_genes(path)
        print(f"  {len(hpa_sets[name]):,} genes")

    master = build_master_table(args, hpa_sets)
    out_path = Path(args.out)
    summary_path = Path(args.summary_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    write_summary(master, out_path, summary_path)

    print("\nTranslational audit summary")
    print(pd.read_csv(summary_path).to_string(index=False))
    print("\nTop 20 prioritized genes")
    top_cols = [
        "gene",
        "module",
        "biology_score",
        "translational_bonus",
        "translational_priority_score",
        "translational_category",
        "is_hpa_fda_drug_target",
        "is_hpa_predicted_membrane",
        "is_hpa_predicted_secreted",
    ]
    top_cols = [col for col in top_cols if col in master.columns]
    print(master[top_cols].head(20).to_string(index=False))
    print(f"\nWrote matrix: {out_path}")
    print(f"Wrote summary: {summary_path}")


if __name__ == "__main__":
    main()
