from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import argparse
import time
import fsspec
import h5py
import numpy as np
import pandas as pd
import torch
import anndata as ad
from scipy import sparse

from sea_ad_jepa.jepa import GeneJEPA
from sea_ad_jepa.evaluation_utils import choose_device, load_jepa


def retry_call(label: str, fn, max_retries: int, retry_wait_seconds: float):
    for attempt in range(1, max_retries + 1):
        try:
            return fn()
        except Exception:
            if attempt >= max_retries:
                raise
            wait = retry_wait_seconds * attempt
            print(f"Retrying {label} after transient read failure ({attempt}/{max_retries}); waiting {wait:.1f}s...")
            time.sleep(wait)


def read_obs_column(h5: h5py.File, col_name: str) -> list[str | None]:
    if f"obs/{col_name}" not in h5:
        raise KeyError(f"Column '{col_name}' not found in obs group.")
    
    col_ds = h5[f"obs/{col_name}"]
    
    if isinstance(col_ds, h5py.Group):
        # New AnnData categorical format (Group containing codes and categories datasets)
        if "codes" in col_ds:
            codes = col_ds["codes"][()]
            categories = col_ds["categories"][()] if "categories" in col_ds else []
            categories = [c.decode("utf-8") if isinstance(c, bytes) else str(c) for c in categories]
            return [categories[code] if code >= 0 and code < len(categories) else None for code in codes]
        raise TypeError(f"obs/{col_name} is a group but does not contain codes/categories datasets.")
    else:
        # col_ds is a Dataset
        categories_path = f"obs/__categories/{col_name}"
        if categories_path in h5:
            # Old AnnData categorical format (Dataset of codes + separate categories dataset)
            codes = col_ds[()]
            categories = h5[categories_path][()]
            categories = [c.decode("utf-8") if isinstance(c, bytes) else str(c) for c in categories]
            return [categories[code] if code >= 0 and code < len(categories) else None for code in codes]
        else:
            # Direct string or numerical dataset
            data = col_ds[()]
            return [d.decode("utf-8") if isinstance(d, bytes) else str(d) for d in data]


def read_var_names(h5: h5py.File) -> list[str]:
    for key in ["var/_index", "var/index", "var/gene_symbols", "var/gene_name"]:
        if key in h5:
            data = h5[key][()]
            return [d.decode("utf-8") if isinstance(d, bytes) else str(d) for d in data]
    raise KeyError("Could not locate var index (gene names) in the remote H5AD file.")


def stream_rows(
    h5: h5py.File,
    row_indices: list[int],
    n_vars: int,
    indptr_local: np.ndarray | None = None,
    max_retries: int = 3,
    retry_wait_seconds: float = 2.0,
) -> np.ndarray:
    x_obj = h5["X"]
    
    if isinstance(x_obj, h5py.Dataset):
        # Dense matrix
        dense_rows = np.zeros((len(row_indices), n_vars), dtype=np.float32)
        for i, r_idx in enumerate(row_indices):
            dense_rows[i] = retry_call(
                f"dense row {r_idx}",
                lambda r_idx=r_idx: x_obj[r_idx],
                max_retries=max_retries,
                retry_wait_seconds=retry_wait_seconds,
            )
        return dense_rows
    else:
        # Sparse CSR group
        indices = x_obj["indices"]
        data = x_obj["data"]
        
        dense_rows = np.zeros((len(row_indices), n_vars), dtype=np.float32)
        if indptr_local is not None:
            for i, r_idx in enumerate(row_indices):
                start = indptr_local[r_idx]
                end = indptr_local[r_idx + 1]
                row_indices_local = retry_call(
                    f"sparse row indices {r_idx}",
                    lambda start=start, end=end: indices[start:end],
                    max_retries=max_retries,
                    retry_wait_seconds=retry_wait_seconds,
                )
                row_data = retry_call(
                    f"sparse row data {r_idx}",
                    lambda start=start, end=end: data[start:end],
                    max_retries=max_retries,
                    retry_wait_seconds=retry_wait_seconds,
                )
                dense_rows[i, row_indices_local] = row_data
        else:
            indptr = x_obj["indptr"]
            for i, r_idx in enumerate(row_indices):
                start = retry_call(
                    f"sparse row start {r_idx}",
                    lambda r_idx=r_idx: indptr[r_idx],
                    max_retries=max_retries,
                    retry_wait_seconds=retry_wait_seconds,
                )
                end = retry_call(
                    f"sparse row end {r_idx}",
                    lambda r_idx=r_idx: indptr[r_idx + 1],
                    max_retries=max_retries,
                    retry_wait_seconds=retry_wait_seconds,
                )
                row_indices_local = retry_call(
                    f"sparse row indices {r_idx}",
                    lambda start=start, end=end: indices[start:end],
                    max_retries=max_retries,
                    retry_wait_seconds=retry_wait_seconds,
                )
                row_data = retry_call(
                    f"sparse row data {r_idx}",
                    lambda start=start, end=end: data[start:end],
                    max_retries=max_retries,
                    retry_wait_seconds=retry_wait_seconds,
                )
                dense_rows[i, row_indices_local] = row_data
        return dense_rows


def project_cells(model: GeneJEPA, x: torch.Tensor, mode: str) -> np.ndarray:
    with torch.no_grad():
        z = model.context_encoder(x)
        if mode == "predictive":
            z = model.predictor(z)
        return z.cpu().numpy()


def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return float(np.dot(v1, v2) / (norm1 * norm2))


def spearman_correlation(v1: np.ndarray, v2: np.ndarray) -> float:
    r1 = pd.Series(v1).rank(method="average").to_numpy(dtype=np.float32)
    r2 = pd.Series(v2).rank(method="average").to_numpy(dtype=np.float32)
    r1 = r1 - r1.mean()
    r2 = r2 - r2.mean()
    denom = float(np.sqrt(np.sum(r1**2) * np.sum(r2**2)))
    if denom == 0.0:
        return float("nan")
    return float(np.sum(r1 * r2) / denom)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stream remote Perturb-seq data to validate local causal knockouts."
    )
    # Default is the Replogle K562 essential dataset from scPerturb/Zenodo
    parser.add_argument(
        "--url", 
        default="https://zenodo.org/record/7041538/files/Replogle2022_K562_essential.h5ad",
        help="URL of the remote H5AD file to stream."
    )
    parser.add_argument(
        "--local-h5ad", 
        default="data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad",
        help="Local reference H5AD file containing the 3000 HVGs used in JEPA training."
    )
    parser.add_argument(
        "--checkpoint", 
        default="results/models/microglia_pvm_jepa_ema_var_expanded_balanced_e40/gene_jepa_epoch_030.pt",
        help="Local GeneJEPA model checkpoint."
    )
    parser.add_argument(
        "--perturbation-col", 
        default="perturbation",
        help="Column name in obs containing the guide perturbation target."
    )
    parser.add_argument(
        "--control-label", 
        default="control",
        help="Value in perturbation-col corresponding to Non-Targeting Controls."
    )
    parser.add_argument(
        "--target-genes", 
        nargs="+", 
        default=["P2RY12", "CX3CR1"],
        help="CRISPR perturbation genes to stream and validate."
    )
    parser.add_argument(
        "--n-shuffles", 
        type=int, 
        default=100,
        help="Number of random guide shuffles to compute empirical p-values."
    )
    parser.add_argument("--max-ntc", type=int, default=500, help="Maximum control cells to stream.")
    parser.add_argument("--max-ko-cells", type=int, default=0, help="Maximum KO cells per target. Use 0 for all.")
    parser.add_argument("--shuffle-cells", type=int, default=50, help="Maximum cells to stream per shuffle guide.")
    parser.add_argument("--out", default="results/tables/perturbseq_streaming_validation.csv")
    parser.add_argument(
        "--counterfactual-mode",
        choices=["input_erasure", "predictive"],
        default="input_erasure",
        help=(
            "input_erasure compares context-encoder shifts after mean-replacing the target gene; "
            "predictive compares true CRISPR context-encoder shifts against predictor-space shifts "
            "from masked controls."
        ),
    )
    parser.add_argument("--max-retries", type=int, default=3, help="Maximum retries for H5 row reads.")
    parser.add_argument("--retry-wait-seconds", type=float, default=2.0, help="Base backoff wait between retries.")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--batch-size", type=int, default=128)
    args = parser.parse_args()
    
    device = choose_device(args.device)
    
    # 1. Load Local Gene Names (to align feature spaces)
    print(f"Loading local reference H5AD for gene alignment: {args.local_h5ad}")
    local_adata = ad.read_h5ad(args.local_h5ad, backed="r")
    jepa_genes = local_adata.var_names.astype(str).tolist()
    jepa_gene_to_idx = {gene.upper(): idx for idx, gene in enumerate(jepa_genes)}
    print(f"Aligned model expects {len(jepa_genes)} input genes.")
    
    # 2. Connect to File (Local or Remote)
    if args.url.startswith("http://") or args.url.startswith("https://"):
        print(f"\nConnecting to remote Perturb-seq file:\n{args.url}")
        fs = fsspec.filesystem("http")
        try:
            remote_file = retry_call(
                "open remote file",
                lambda: fs.open(args.url, "rb"),
                max_retries=args.max_retries,
                retry_wait_seconds=args.retry_wait_seconds,
            )
            h5 = retry_call(
                "open remote H5",
                lambda: h5py.File(remote_file, "r"),
                max_retries=args.max_retries,
                retry_wait_seconds=args.retry_wait_seconds,
            )
        except Exception as e:
            print(f"Error opening remote file: {e}")
            sys.exit(1)
    else:
        print(f"\nOpening local Perturb-seq file:\n{args.url}")
        try:
            h5 = h5py.File(args.url, "r")
        except Exception as e:
            print(f"Error opening local file: {e}")
            sys.exit(1)
        
    print("Connected successfully! Loading metadata...")
    
    # Read remote obs columns and var names
    perturbations = read_obs_column(h5, args.perturbation_col)
    remote_genes = read_var_names(h5)
    n_cells = len(perturbations)
    n_vars = len(remote_genes)
    print(f"Remote dataset shape: {n_cells:,} cells x {n_vars:,} genes")
    
    indptr_local = None
    if "X/indptr" in h5:
        print("Caching indptr in memory for fast row streaming...")
        indptr_local = h5["X/indptr"][()]
    
    # Map remote genes to JEPA model gene indices
    # We will build an alignment mask to easily transform raw streamed rows to JEPA-compatible inputs
    remote_gene_to_jepa_idx = []
    for remote_idx, r_gene in enumerate(remote_genes):
        u_gene = r_gene.upper()
        if u_gene in jepa_gene_to_idx:
            remote_gene_to_jepa_idx.append((remote_idx, jepa_gene_to_idx[u_gene]))
            
    print(f"Aligned {len(remote_gene_to_jepa_idx)} genes between Remote Perturb-seq and JEPA Model.")
    remote_idxs = np.array([x[0] for x in remote_gene_to_jepa_idx])
    jepa_idxs = np.array([x[1] for x in remote_gene_to_jepa_idx])
    
    # 3. Locate Indices for Controls and Targets
    perturbation_series = pd.Series(perturbations)
    control_indices = perturbation_series[perturbation_series == args.control_label].index.tolist()
    print(f"Found {len(control_indices)} Non-Targeting Control (NTC) cells.")
    
    target_indices = {}
    for target in args.target_genes:
        idx = perturbation_series[perturbation_series == target].index.tolist()
        # Fallback to case-insensitive check if exact match is empty
        if not idx:
            idx = perturbation_series[perturbation_series.str.upper() == target.upper()].index.tolist()
        target_indices[target] = idx
        print(f"Found {len(idx)} CRISPR cells targeting '{target}'.")
        
    # Gather other valid guide names for empirical permutation shuffles
    other_guides = perturbation_series[
        (perturbation_series != args.control_label) & 
        (~perturbation_series.isin(args.target_genes))
    ].dropna().unique().tolist()
    
    # 4. Stream and Align NTC Expression Data
    print("\nStreaming NTC expression matrix chunks...")
    # Limit NTC size to speed up inference if too large
    max_ntc = min(args.max_ntc, len(control_indices))
    selected_ntc_idx = np.random.choice(control_indices, size=max_ntc, replace=False).tolist()
    
    ntc_raw_streamed = stream_rows(
        h5,
        selected_ntc_idx,
        n_vars,
        indptr_local,
        max_retries=args.max_retries,
        retry_wait_seconds=args.retry_wait_seconds,
    )
    # Align to JEPA 3000 feature space (vectorized)
    ntc_aligned = np.zeros((len(selected_ntc_idx), len(jepa_genes)), dtype=np.float32)
    ntc_aligned[:, jepa_idxs] = ntc_raw_streamed[:, remote_idxs]
        
    # 5. Load JEPA Model
    print(f"\nLoading JEPA model from: {args.checkpoint}")
    model, checkpoint = load_jepa(args.checkpoint, device)
    model.eval()
    
    # Convert NTC to PyTorch tensor
    ntc_tensor = torch.from_numpy(ntc_aligned).to(device)
    
    # Project NTC cells to observed latent space. The observed CRISPR shift is always
    # measured in context-encoder space; predictive mode only changes the model-implied
    # counterfactual shift.
    z_ntc = project_cells(model, ntc_tensor, mode="input_erasure")
    z_ntc_mean = z_ntc.mean(axis=0)
    z_ntc_pred_mean = project_cells(model, ntc_tensor, mode="predictive").mean(axis=0)
    
    results = []
    
    # Precompute background shuffle latent shifts once to speed up target benchmarking
    shuffle_obs_shifts = []
    if len(other_guides) > 0:
        print("\nPrecomputing background shuffle latent shifts...")
        np.random.seed(42)
        shuffled_guides = np.random.choice(other_guides, size=min(args.n_shuffles, len(other_guides)), replace=False)
        
        for idx_sh, sh_guide in enumerate(shuffled_guides):
            sh_indices = perturbation_series[perturbation_series == sh_guide].index.tolist()
            if not sh_indices:
                continue
            
            if idx_sh % 20 == 0:
                print(f"  Streaming and projecting shuffle {idx_sh}/{len(shuffled_guides)}: '{sh_guide}'...")
                
            sh_raw = stream_rows(
                h5,
                sh_indices[: args.shuffle_cells],
                n_vars,
                indptr_local,
                max_retries=args.max_retries,
                retry_wait_seconds=args.retry_wait_seconds,
            )
            sh_aligned = np.zeros((sh_raw.shape[0], len(jepa_genes)), dtype=np.float32)
            sh_aligned[:, jepa_idxs] = sh_raw[:, remote_idxs]
            
            sh_tensor = torch.from_numpy(sh_aligned).to(device)
            z_sh = project_cells(model, sh_tensor, mode="input_erasure")
            z_sh_mean = z_sh.mean(axis=0)
            
            v_obs_sh = z_sh_mean - z_ntc_mean
            shuffle_obs_shifts.append(v_obs_sh)
        print(f"Precomputed {len(shuffle_obs_shifts)} background shuffle shifts successfully.")
    else:
        print("\nNo background guides available for shuffle precomputation.")
    
    # 6. Run Causal Knockout Benchmarking Loop
    for target in args.target_genes:
        ko_indices = target_indices[target]
        if not ko_indices:
            print(f"\nSkipping '{target}': No cells found in the dataset.")
            continue
            
        print(f"\n--------------------------------------------------")
        print(f"Benchmarking Target: {target}")
        print(f"--------------------------------------------------")
        
        # A. Stream real CRISPR KO cells
        print(f"Streaming {len(ko_indices)} real CRISPR cells...")
        if args.max_ko_cells and len(ko_indices) > args.max_ko_cells:
            ko_indices = np.random.choice(ko_indices, size=args.max_ko_cells, replace=False).tolist()
            print(f"Capped target stream to {len(ko_indices)} cells.")
        ko_raw_streamed = stream_rows(
            h5,
            ko_indices,
            n_vars,
            indptr_local,
            max_retries=args.max_retries,
            retry_wait_seconds=args.retry_wait_seconds,
        )
        ko_aligned = np.zeros((len(ko_indices), len(jepa_genes)), dtype=np.float32)
        ko_aligned[:, jepa_idxs] = ko_raw_streamed[:, remote_idxs]
            
        # Project real CRISPR KO to Latent Space
        ko_tensor = torch.from_numpy(ko_aligned).to(device)
        z_ko_real = project_cells(model, ko_tensor, mode="input_erasure")
        z_ko_real_mean = z_ko_real.mean(axis=0)
        
        # Observed Latent Vector (CRISPR KO - NTC)
        v_obs = z_ko_real_mean - z_ntc_mean
        
        # B. Run JEPA Counterfactual Knockout
        # In input space: set target gene expression to global mean (or 0)
        ntc_perturbed = ntc_aligned.copy()
        if target.upper() in jepa_gene_to_idx:
            t_idx = jepa_gene_to_idx[target.upper()]
            # Set to global mean of NTC
            ntc_perturbed[:, t_idx] = ntc_aligned[:, t_idx].mean()
        else:
            print(f"Warning: Target '{target}' is not in JEPA's 3000 gene list. Knocking out via embedding space only.")
            
        # Project perturbed NTC cells.
        ntc_perturbed_tensor = torch.from_numpy(ntc_perturbed).to(device)
        z_ko_pred = project_cells(model, ntc_perturbed_tensor, mode=args.counterfactual_mode)
        z_ko_pred_mean = z_ko_pred.mean(axis=0)
        
        # Predicted Latent Vector (JEPA Counterfactual KO - NTC)
        if args.counterfactual_mode == "predictive":
            v_pred = z_ko_pred_mean - z_ntc_pred_mean
        else:
            v_pred = z_ko_pred_mean - z_ntc_mean
        
        # C. Compute Congruence
        cos_sim = cosine_similarity(v_obs, v_pred)
        spearman_r = spearman_correlation(v_obs, v_pred)
        print(f"Cosine Similarity (V_obs, V_pred): {cos_sim:.4f}")
        print(f"Spearman Correlation (V_obs, V_pred): {spearman_r:.4f}")
        
        # D. Empirical Null Shuffle (Permutation Test)
        print("Running permutation shuffle for empirical significance...")
        shuffle_cosines = []
        for v_obs_sh in shuffle_obs_shifts:
            shuffle_cosines.append(cosine_similarity(v_obs_sh, v_pred))
            
        shuffle_cosines = np.array(shuffle_cosines)
        if len(shuffle_cosines) > 0:
            empirical_p = float(np.mean(np.abs(shuffle_cosines) >= abs(cos_sim)))
            print(f"Background Cosine Mean: {shuffle_cosines.mean():.4f} +/- {shuffle_cosines.std():.4f}")
            print(f"Empirical p-value: {empirical_p:.4f}")
        else:
            empirical_p = float('nan')
            print("No precomputed shuffles available to run permutation test.")
        
        results.append({
            "target_gene": target,
            "counterfactual_mode": args.counterfactual_mode,
            "cosine_similarity": cos_sim,
            "spearman_r": spearman_r,
            "empirical_p": empirical_p,
            "cells_streamed": len(ko_indices)
        })
        partial_df = pd.DataFrame(results)
        partial_out = Path(args.out)
        partial_out.parent.mkdir(parents=True, exist_ok=True)
        partial_df.to_csv(partial_out, index=False)
        print(f"Updated partial results at: {partial_out}")
        
    h5.close()
    
    # 7. Print Results Table
    print("\n==================================================")
    print("Cloud-Streaming Validation Complete!")
    print("==================================================")
    res_df = pd.DataFrame(results)
    print(res_df.to_string(index=False))
    
    # Save output
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    res_df.to_csv(out_path, index=False)
    print(f"\nWrote validation summary results to: {out_path}")


if __name__ == "__main__":
    main()
