from __future__ import annotations

import argparse
import gzip
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import h5py
import numpy as np
import pandas as pd
import torch
from scipy import sparse
from scipy.io import mmread

from sea_ad_jepa.jepa import GeneJEPA


DEFAULT_LATENTS = ["jepa_63", "jepa_34", "jepa_46", "jepa_108"]


def choose_device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(requested)


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
        if "gene_ids" in var:
            return decode_array(var["gene_ids"][()])
    raise KeyError(f"Could not find var names in {path}")


def load_jepa(checkpoint_path: Path, device: torch.device) -> tuple[GeneJEPA, dict]:
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    model_args = checkpoint.get("args", {})
    model = GeneJEPA(
        input_dim=int(checkpoint["n_genes"]),
        hidden_dim=int(model_args.get("hidden_dim", 512)),
        latent_dim=int(model_args.get("latent_dim", 128)),
        dropout=float(model_args.get("dropout", 0.1)),
        ema_decay=float(model_args.get("ema_decay", 0.996)),
    ).to(device)
    model.load_state_dict(checkpoint["model_state"])
    model.eval()
    return model, checkpoint


def open_text(path: Path):
    return gzip.open(path, "rt", encoding="utf-8") if path.suffix == ".gz" else path.open("r", encoding="utf-8")


def read_tsv_first_column(path: Path) -> list[str]:
    values = []
    with open_text(path) as handle:
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            if parts:
                values.append(parts[0])
    return values


def read_gene_names(path: Path) -> list[str]:
    genes = []
    with open_text(path) as handle:
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 2:
                genes.append(parts[1])
            elif parts:
                genes.append(parts[0])
    return genes


def discover_mex_samples(root: Path) -> list[dict[str, Path | str]]:
    matrix_files = sorted(root.glob("*.matrix.mtx*")) + sorted(root.glob("*matrix.mtx*"))
    seen = set()
    samples = []
    for matrix in matrix_files:
        if matrix in seen:
            continue
        seen.add(matrix)
        prefix = re.sub(r"\.matrix\.mtx(\.gz)?$", "", matrix.name)
        gene_candidates = [
            root / f"{prefix}.genes.tsv.gz",
            root / f"{prefix}.genes.tsv",
            root / f"{prefix}.features.tsv.gz",
            root / f"{prefix}.features.tsv",
        ]
        barcode_candidates = [
            root / f"{prefix}.barcodes.tsv.gz",
            root / f"{prefix}.barcodes.tsv",
        ]
        genes = next((p for p in gene_candidates if p.exists()), None)
        barcodes = next((p for p in barcode_candidates if p.exists()), None)
        if genes is None or barcodes is None:
            continue
        samples.append({"sample_id": prefix, "matrix": matrix, "genes": genes, "barcodes": barcodes})
    return samples


def infer_condition(sample_id: str) -> str:
    lower = sample_id.lower()
    if re.search(r"(^|[_\-.])(ad|alz|braak6|late)([_\-.]|$)", lower):
        return "AD"
    if "healthy" in lower or "control" in lower or re.search(r"(^|[_\-.])(ct|ctrl|con|braak0)([_\-.]|$)", lower):
        return "Control"
    return "Unknown"


def read_metadata(path: Path | None) -> pd.DataFrame | None:
    if path is None:
        return None
    sep = "\t" if path.suffix.lower() in {".tsv", ".txt"} else ","
    return pd.read_csv(path, sep=sep)


def metadata_index(metadata: pd.DataFrame, barcode_col: str | None) -> pd.DataFrame:
    if barcode_col and barcode_col in metadata:
        return metadata.set_index(barcode_col, drop=False)
    for candidate in ["cell_id", "cell", "barcode", "Cell", "Barcode", "CellID", "cellID"]:
        if candidate in metadata:
            return metadata.set_index(candidate, drop=False)
    return metadata


def sample_condition_map(sample_metadata: pd.DataFrame | None, sample_col: str, condition_col: str) -> dict[str, str]:
    if sample_metadata is None:
        return {}
    if sample_col not in sample_metadata or condition_col not in sample_metadata:
        return {}
    return {
        str(row[sample_col]): str(row[condition_col])
        for _, row in sample_metadata[[sample_col, condition_col]].dropna().iterrows()
    }


def normalize_log_to_jepa_space(matrix_genes_by_cells: sparse.spmatrix, source_genes: list[str], jepa_genes: list[str]) -> tuple[np.ndarray, int]:
    gene_to_source: dict[str, int] = {}
    for idx, gene in enumerate(source_genes):
        key = str(gene).upper()
        if key not in gene_to_source:
            gene_to_source[key] = idx

    source_indices: list[int] = []
    jepa_indices: list[int] = []
    for jepa_idx, gene in enumerate(jepa_genes):
        source_idx = gene_to_source.get(str(gene).upper())
        if source_idx is not None:
            source_indices.append(source_idx)
            jepa_indices.append(jepa_idx)

    if not source_indices:
        raise ValueError("No source genes overlapped the SEA-AD JEPA gene list.")

    counts = matrix_genes_by_cells.tocsc().astype(np.float32)
    cell_totals = np.asarray(counts.sum(axis=0)).ravel().astype(np.float32)
    cell_totals[cell_totals <= 0] = 1.0
    subset = counts[source_indices, :].T.tocsr()
    subset = subset.multiply((10000.0 / cell_totals)[:, None])
    subset.data = np.log1p(subset.data)

    x = np.zeros((subset.shape[0], len(jepa_genes)), dtype=np.float32)
    subset = subset.tocoo()
    mapped_cols = np.asarray(jepa_indices, dtype=np.int64)
    x[subset.row, mapped_cols[subset.col]] = subset.data
    return x, len(jepa_indices)


def load_mex_dataset(
    mex_root: Path,
    jepa_genes: list[str],
    metadata: pd.DataFrame | None,
    sample_metadata: pd.DataFrame | None,
    barcode_col: str | None,
    donor_col: str,
    condition_col: str,
    sample_col: str,
    cell_type_col: str | None,
    microglia_pattern: str,
    allow_all_cells: bool,
) -> tuple[np.ndarray, pd.DataFrame, int]:
    samples = discover_mex_samples(mex_root)
    if not samples:
        raise FileNotFoundError(f"No GEO-style MEX samples were found in {mex_root}")

    meta_by_barcode = metadata_index(metadata, barcode_col) if metadata is not None else None
    condition_by_sample = sample_condition_map(sample_metadata, sample_col, condition_col)
    chunks = []
    obs_chunks = []
    overlaps = []
    pattern = re.compile(microglia_pattern, re.IGNORECASE)

    for sample in samples:
        sample_id = str(sample["sample_id"])
        print(f"Loading {sample_id}")
        matrix = mmread(sample["matrix"]).tocsr()
        genes = read_gene_names(Path(sample["genes"]))
        barcodes = read_tsv_first_column(Path(sample["barcodes"]))
        if matrix.shape[0] != len(genes) and matrix.shape[1] == len(genes):
            matrix = matrix.T
        if matrix.shape[0] != len(genes) or matrix.shape[1] != len(barcodes):
            raise ValueError(f"MEX dimensions do not match genes/barcodes for {sample_id}: {matrix.shape}")

        x, overlap = normalize_log_to_jepa_space(matrix, genes, jepa_genes)
        overlaps.append(overlap)
        obs = pd.DataFrame({"barcode": barcodes})
        obs["sample_id"] = sample_id
        obs["cell_id"] = [f"{sample_id}:{barcode}" for barcode in barcodes]
        obs[donor_col] = sample_id
        obs[condition_col] = condition_by_sample.get(sample_id, infer_condition(sample_id))

        if meta_by_barcode is not None:
            joined = obs.join(meta_by_barcode, on="barcode", rsuffix="_meta")
            joined_full = obs.set_index("cell_id").join(meta_by_barcode, how="left", rsuffix="_meta").reset_index(drop=True)
            obs = joined if joined.notna().sum().sum() >= joined_full.notna().sum().sum() else joined_full
            if donor_col not in obs and f"{donor_col}_meta" in obs:
                obs[donor_col] = obs[f"{donor_col}_meta"]
            if condition_col not in obs and f"{condition_col}_meta" in obs:
                obs[condition_col] = obs[f"{condition_col}_meta"]

        if cell_type_col and cell_type_col in obs:
            keep = obs[cell_type_col].astype(str).str.contains(pattern, na=False).to_numpy()
            x = x[keep]
            obs = obs.loc[keep].reset_index(drop=True)
        elif not allow_all_cells:
            raise KeyError(
                f"Cell-type column '{cell_type_col}' was not found. Provide --cell-type-col or pass --allow-all-cells."
            )

        chunks.append(x)
        obs_chunks.append(obs)

    x_all = np.vstack(chunks).astype(np.float32)
    obs_all = pd.concat(obs_chunks, ignore_index=True)
    return x_all, obs_all, int(min(overlaps))


def infer_sample_pool(cell_id: str) -> str:
    match = re.search(r"_([^_]+_[^_]+)$", str(cell_id))
    return match.group(1) if match else str(cell_id)


def read_counts_csv_aligned(path: Path, jepa_genes: list[str], chunksize: int) -> tuple[np.ndarray, list[str], int]:
    gene_to_jepa = {gene.upper(): idx for idx, gene in enumerate(jepa_genes)}
    cell_ids: list[str] | None = None
    cell_totals: np.ndarray | None = None
    matched_rows: list[tuple[int, np.ndarray]] = []
    matched_seen: set[int] = set()

    for chunk in pd.read_csv(path, chunksize=chunksize):
        gene_col = chunk.columns[0]
        if cell_ids is None:
            cell_ids = [str(c) for c in chunk.columns[1:]]
            cell_totals = np.zeros(len(cell_ids), dtype=np.float64)
        values = chunk.iloc[:, 1:].to_numpy(dtype=np.float32, copy=False)
        cell_totals += values.sum(axis=0)
        genes = chunk[gene_col].astype(str).tolist()
        for row_idx, gene in enumerate(genes):
            jepa_idx = gene_to_jepa.get(gene.upper())
            if jepa_idx is None or jepa_idx in matched_seen:
                continue
            matched_seen.add(jepa_idx)
            matched_rows.append((jepa_idx, values[row_idx].astype(np.float32, copy=True)))

    if cell_ids is None or cell_totals is None:
        raise ValueError(f"No data found in {path}")
    if not matched_rows:
        raise ValueError("No genes in the Grubman count matrix overlapped the SEA-AD JEPA gene list.")

    cell_totals[cell_totals <= 0] = 1.0
    x = np.zeros((len(cell_ids), len(jepa_genes)), dtype=np.float32)
    scale = (10000.0 / cell_totals).astype(np.float32)
    for jepa_idx, counts in matched_rows:
        x[:, jepa_idx] = np.log1p(counts * scale)
    return x, cell_ids, len(matched_rows)


def load_counts_csv_dataset(
    counts_csv: Path,
    covariates_csv: Path,
    jepa_genes: list[str],
    donor_col: str,
    condition_col: str,
    cell_type_col: str | None,
    microglia_pattern: str,
    allow_all_cells: bool,
    chunksize: int,
) -> tuple[np.ndarray, pd.DataFrame, int]:
    print(f"Loading count CSV: {counts_csv}")
    x, cell_ids, n_overlap = read_counts_csv_aligned(counts_csv, jepa_genes, chunksize)
    cov = pd.read_csv(covariates_csv)
    if cov.columns[0] != "cell_id":
        cov = cov.rename(columns={cov.columns[0]: "cell_id"})
    cov["cell_id"] = cov["cell_id"].astype(str)
    obs = pd.DataFrame({"cell_id": cell_ids})
    obs = obs.merge(cov, on="cell_id", how="left")

    if donor_col not in obs:
        obs[donor_col] = obs["cell_id"].map(infer_sample_pool)
    if condition_col not in obs:
        if "oupSample.batchCond" in obs:
            obs[condition_col] = obs["oupSample.batchCond"].map(lambda x: "Control" if str(x).lower() in {"ct", "ctrl", "control"} else str(x))
        else:
            obs[condition_col] = obs[donor_col].map(infer_condition)

    if cell_type_col and cell_type_col in obs:
        keep = obs[cell_type_col].astype(str).str.contains(microglia_pattern, case=False, na=False).to_numpy()
        x = x[keep]
        obs = obs.loc[keep].reset_index(drop=True)
    elif not allow_all_cells:
        raise KeyError(
            f"Cell-type column '{cell_type_col}' was not found in covariates. Provide --cell-type-col or pass --allow-all-cells."
        )

    return x.astype(np.float32), obs, n_overlap


def encode_cells(model: GeneJEPA, x: np.ndarray, device: torch.device, batch_size: int) -> np.ndarray:
    latents = []
    with torch.no_grad():
        for start in range(0, x.shape[0], batch_size):
            batch = torch.from_numpy(x[start : start + batch_size]).to(device)
            latents.append(model.encode(batch).cpu().numpy())
    return np.vstack(latents).astype(np.float32)


def rank_biserial(x: np.ndarray, y: np.ndarray) -> float:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.size == 0 or y.size == 0:
        return float("nan")
    combined = pd.Series(np.concatenate([x, y])).rank(method="average").to_numpy(dtype=float)
    r_x = combined[: x.size].sum()
    u_x = r_x - x.size * (x.size + 1) / 2.0
    return float((2.0 * u_x / (x.size * y.size)) - 1.0)


def mann_whitney_p(x: np.ndarray, y: np.ndarray) -> float:
    try:
        from scipy.stats import mannwhitneyu

        return float(mannwhitneyu(x, y, alternative="two-sided").pvalue)
    except Exception:
        return float("nan")


def summarize_donors(df: pd.DataFrame, donor_col: str, condition_col: str, latent_cols: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    donor = df.groupby([donor_col, condition_col], as_index=False)[latent_cols].mean()
    rows = []
    conditions = sorted([c for c in donor[condition_col].dropna().astype(str).unique() if c != "Unknown"])
    if len(conditions) >= 2:
        control_label = next((c for c in conditions if c.lower() in {"control", "ctrl", "ct", "healthy"}), conditions[0])
        disease_label = next((c for c in conditions if c != control_label), conditions[-1])
    else:
        control_label = "Control"
        disease_label = "AD"

    ctrl = donor[donor[condition_col].astype(str).eq(control_label)]
    dis = donor[donor[condition_col].astype(str).eq(disease_label)]
    for latent in latent_cols:
        x = dis[latent].to_numpy(dtype=float)
        y = ctrl[latent].to_numpy(dtype=float)
        rows.append(
            {
                "latent_factor": latent,
                "disease_label": disease_label,
                "control_label": control_label,
                "n_disease_donors": int(x.size),
                "n_control_donors": int(y.size),
                "disease_mean": float(np.nanmean(x)) if x.size else float("nan"),
                "control_mean": float(np.nanmean(y)) if y.size else float("nan"),
                "mean_difference_disease_minus_control": float(np.nanmean(x) - np.nanmean(y)) if x.size and y.size else float("nan"),
                "rank_biserial_effect": rank_biserial(x, y),
                "mannwhitney_p": mann_whitney_p(x, y),
            }
        )
    return donor, pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Zero-shot project public Grubman/GSE138852 cells through the frozen SEA-AD JEPA encoder.")
    parser.add_argument("--mex-root", default="data/external/grubman_gse138852")
    parser.add_argument("--counts-csv", default="data/external/grubman_gse138852/GSE138852_counts.csv.gz")
    parser.add_argument("--covariates-csv", default="data/external/grubman_gse138852/GSE138852_covariates.csv.gz")
    parser.add_argument("--metadata", default="")
    parser.add_argument("--sample-metadata", default="")
    parser.add_argument("--local-h5ad", default="data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad")
    parser.add_argument("--checkpoint", default="results/models/microglia_pvm_jepa_ema_var_expanded_balanced_e40/gene_jepa_epoch_030.pt")
    parser.add_argument("--donor-col", default="patient_id")
    parser.add_argument("--condition-col", default="condition")
    parser.add_argument("--sample-col", default="sample_id")
    parser.add_argument("--barcode-col", default="")
    parser.add_argument("--cell-type-col", default="cell_type")
    parser.add_argument("--microglia-pattern", default="micro|myeloid")
    parser.add_argument("--allow-all-cells", action="store_true")
    parser.add_argument("--counts-chunksize", type=int, default=250)
    parser.add_argument("--latents", nargs="+", default=DEFAULT_LATENTS)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--out-donor", default="results/tables/grubman_zero_shot_donor_embeddings.csv")
    parser.add_argument("--out-summary", default="results/tables/grubman_zero_shot_generalization.csv")
    parser.add_argument("--device", default="auto")
    args = parser.parse_args()

    device = choose_device(args.device)
    jepa_genes = read_h5ad_var_names(Path(args.local_h5ad))
    model, checkpoint = load_jepa(Path(args.checkpoint), device)
    if int(checkpoint["n_genes"]) != len(jepa_genes):
        raise ValueError(f"Checkpoint expects {checkpoint['n_genes']} genes, but local H5AD has {len(jepa_genes)} genes.")

    metadata = read_metadata(Path(args.metadata)) if args.metadata else None
    sample_metadata = read_metadata(Path(args.sample_metadata)) if args.sample_metadata else None
    counts_csv = Path(args.counts_csv)
    covariates_csv = Path(args.covariates_csv)
    if counts_csv.exists() and covariates_csv.exists():
        x, obs, n_overlap = load_counts_csv_dataset(
            counts_csv=counts_csv,
            covariates_csv=covariates_csv,
            jepa_genes=jepa_genes,
            donor_col=args.donor_col,
            condition_col=args.condition_col,
            cell_type_col=args.cell_type_col or None,
            microglia_pattern=args.microglia_pattern,
            allow_all_cells=args.allow_all_cells,
            chunksize=args.counts_chunksize,
        )
    else:
        x, obs, n_overlap = load_mex_dataset(
            mex_root=Path(args.mex_root),
            jepa_genes=jepa_genes,
            metadata=metadata,
            sample_metadata=sample_metadata,
            barcode_col=args.barcode_col or None,
            donor_col=args.donor_col,
            condition_col=args.condition_col,
            sample_col=args.sample_col,
            cell_type_col=args.cell_type_col or None,
            microglia_pattern=args.microglia_pattern,
            allow_all_cells=args.allow_all_cells,
        )

    print(f"Cells projected: {x.shape[0]:,}")
    print(f"JEPA genes matched: {n_overlap:,} / {len(jepa_genes):,}")
    z = encode_cells(model, x, device, args.batch_size)
    latent_cols = [f"jepa_{i}" for i in range(z.shape[1])]
    for col in args.latents:
        if col not in latent_cols:
            raise KeyError(f"Requested latent {col} is not available; model returned {len(latent_cols)} dimensions.")
    latent_df = pd.DataFrame(z, columns=latent_cols)
    full = pd.concat([obs.reset_index(drop=True), latent_df], axis=1)
    donor, summary = summarize_donors(full, args.donor_col, args.condition_col, args.latents)
    summary.insert(0, "dataset", "GSE138852_Grubman")
    summary.insert(1, "cell_filter", args.microglia_pattern if args.cell_type_col else "all_cells")
    summary.insert(2, "n_projected_cells", int(x.shape[0]))
    summary.insert(3, "n_jepa_genes_matched", int(n_overlap))

    out_donor = Path(args.out_donor)
    out_summary = Path(args.out_summary)
    out_donor.parent.mkdir(parents=True, exist_ok=True)
    out_summary.parent.mkdir(parents=True, exist_ok=True)
    donor.to_csv(out_donor, index=False)
    summary.to_csv(out_summary, index=False)

    print(summary.to_string(index=False))
    print(f"Wrote {out_donor}")
    print(f"Wrote {out_summary}")
    print("Interpretation boundary: this is zero-shot observational cohort validation, not perturbational causal proof.")


if __name__ == "__main__":
    main()
