from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import argparse
import numpy as np
import pandas as pd
import torch

from sea_ad_jepa.baselines import spearman_corr
from sea_ad_jepa.data import load_pathology_targets, normalize_donor_id
from sea_ad_jepa.gene_sets import MICROGLIA_GENE_MODULES


def choose_device(requested: str) -> torch.device:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(requested)


def standardize_train_apply(train: np.ndarray, full: np.ndarray) -> np.ndarray:
    mean = np.nanmean(train, axis=0, keepdims=True)
    std = np.nanstd(train, axis=0, keepdims=True)
    std[std == 0] = 1.0
    return (full - mean) / std


def ridge_residualize(y: np.ndarray, confounders: np.ndarray, alpha: float, device: torch.device) -> np.ndarray:
    keep = np.isfinite(y) & np.isfinite(confounders).all(axis=1)
    if keep.sum() < 3:
        return np.full_like(y, np.nan, dtype=np.float32)
    x = standardize_train_apply(confounders[keep], confounders)
    x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)
    y_keep = y[keep].astype(np.float32)
    x_keep = x[keep]

    x_t = torch.as_tensor(x_keep, dtype=torch.float32, device=device)
    y_t = torch.as_tensor(y_keep, dtype=torch.float32, device=device)
    x_all_t = torch.as_tensor(x, dtype=torch.float32, device=device)
    x_t = torch.cat([torch.ones((x_t.shape[0], 1), dtype=torch.float32, device=device), x_t], dim=1)
    x_all_t = torch.cat([torch.ones((x_all_t.shape[0], 1), dtype=torch.float32, device=device), x_all_t], dim=1)
    identity = torch.eye(x_t.shape[1], dtype=torch.float32, device=device)
    identity[0, 0] = 0.0
    weights = torch.linalg.solve(x_t.T @ x_t + alpha * identity, x_t.T @ y_t)
    pred = (x_all_t @ weights).detach().cpu().numpy()
    residual = y.astype(np.float32) - pred.astype(np.float32)
    residual[~keep] = np.nan
    return residual


def bootstrap_ci(values: np.ndarray, n_bootstrap: int, seed: int, ci: float) -> tuple[float, float]:
    clean = np.asarray(values, dtype=np.float32)
    clean = clean[np.isfinite(clean)]
    if clean.size == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    boot = np.empty(n_bootstrap, dtype=np.float32)
    for i in range(n_bootstrap):
        sample = rng.choice(clean, size=clean.size, replace=True)
        boot[i] = float(np.mean(sample))
    alpha = (100.0 - ci) / 2.0
    return float(np.percentile(boot, alpha)), float(np.percentile(boot, 100.0 - alpha))


def build_confounders(metadata: pd.DataFrame, embeddings: pd.DataFrame, covariates: list[str]) -> pd.DataFrame:
    conf = metadata[["Donor ID", *[c for c in covariates if c in metadata.columns]]].copy()
    numeric_cols = []
    categorical_cols = []
    for col in conf.columns:
        if col == "Donor ID":
            continue
        converted = pd.to_numeric(conf[col], errors="coerce")
        if converted.notna().sum() >= max(5, int(0.5 * len(converted))):
            conf[col] = converted
            numeric_cols.append(col)
        else:
            categorical_cols.append(col)
    if categorical_cols:
        conf = pd.get_dummies(conf, columns=categorical_cols, dummy_na=True, dtype=np.float32)
    embedding_cols = [col for col in embeddings.columns if col != "Donor ID"]
    return conf.merge(embeddings[["Donor ID", *embedding_cols]], on="Donor ID", how="left")


def module_treatments(pseudobulk: pd.DataFrame, modules: list[str] | None) -> pd.DataFrame:
    gene_columns = {col.upper(): col for col in pseudobulk.columns if col != "Donor ID"}
    selected_modules = modules or sorted(MICROGLIA_GENE_MODULES)
    rows = {"Donor ID": pseudobulk["Donor ID"]}
    for module in selected_modules:
        if module not in MICROGLIA_GENE_MODULES:
            raise KeyError(f"Unknown module: {module}")
        genes = [gene_columns[gene.upper()] for gene in MICROGLIA_GENE_MODULES[module] if gene.upper() in gene_columns]
        if genes:
            rows[module] = pseudobulk[genes].mean(axis=1)
    return pd.DataFrame(rows)


def gene_treatments(pseudobulk: pd.DataFrame, genes: list[str] | None) -> pd.DataFrame:
    if not genes:
        raise ValueError("--genes is required when --mode gene")
    gene_columns = {col.upper(): col for col in pseudobulk.columns if col != "Donor ID"}
    rows = {"Donor ID": pseudobulk["Donor ID"]}
    for gene in genes:
        if gene.upper() in gene_columns:
            rows[gene.upper()] = pseudobulk[gene_columns[gene.upper()]]
    return pd.DataFrame(rows)


def estimate_effects(
    treatments: pd.DataFrame,
    targets: pd.DataFrame,
    confounders: pd.DataFrame,
    target: str,
    alpha: float,
    device: torch.device,
    n_bootstrap: int,
    seed: int,
    ci: float,
) -> pd.DataFrame:
    merged = treatments.merge(targets[["Donor ID", target]], on="Donor ID", how="inner")
    merged = merged.merge(confounders, on="Donor ID", how="inner")
    treatment_cols = [col for col in treatments.columns if col != "Donor ID"]
    confounder_cols = [col for col in merged.columns if col not in {"Donor ID", target, *treatment_cols}]
    y = pd.to_numeric(merged[target], errors="coerce").to_numpy(dtype=np.float32)
    w = merged[confounder_cols].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=np.float32)
    y_resid = ridge_residualize(y, w, alpha=alpha, device=device)

    rows = []
    for treatment in treatment_cols:
        t = pd.to_numeric(merged[treatment], errors="coerce").to_numpy(dtype=np.float32)
        t_resid = ridge_residualize(t, w, alpha=alpha, device=device)
        keep = np.isfinite(y_resid) & np.isfinite(t_resid)
        if keep.sum() < 5 or float(np.sum(t_resid[keep] ** 2)) == 0.0:
            continue
        slope = float(np.sum(t_resid[keep] * y_resid[keep]) / np.sum(t_resid[keep] ** 2))
        partial_spearman = spearman_corr(y_resid[keep], t_resid[keep])
        contribution = slope * t_resid[keep]
        ci_low, ci_high = bootstrap_ci(contribution, n_bootstrap=n_bootstrap, seed=seed, ci=ci)
        rows.append(
            {
                "treatment": treatment,
                "target": target,
                "n_donors": int(keep.sum()),
                "adjusted_slope": slope,
                "partial_spearman": partial_spearman,
                "mean_adjusted_contribution": float(np.mean(contribution)),
                "bootstrap_ci_low": ci_low,
                "bootstrap_ci_high": ci_high,
                "abs_partial_spearman": abs(partial_spearman),
            }
        )
    return pd.DataFrame(rows).sort_values("abs_partial_spearman", ascending=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Estimate confounder-adjusted donor-level gene/module effects.")
    parser.add_argument("--pseudobulk", required=True)
    parser.add_argument("--embeddings", required=True)
    parser.add_argument("--target", default="percent AT8 positive area_Grey matter")
    parser.add_argument("--mode", choices=["module", "gene"], default="module")
    parser.add_argument("--modules", nargs="*", default=None)
    parser.add_argument("--genes", nargs="*", default=None)
    parser.add_argument("--covariates", nargs="*", default=["Age at Death", "Sex", "APOE Genotype"])
    parser.add_argument("--alpha", type=float, default=10.0)
    parser.add_argument("--n-bootstrap", type=int, default=2000)
    parser.add_argument("--ci", type=float, default=95.0)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--out", default="results/tables/confounder_adjusted_module_effects.csv")
    args = parser.parse_args()

    device = choose_device(args.device)
    pseudobulk = pd.read_csv(args.pseudobulk)
    pseudobulk["Donor ID"] = normalize_donor_id(pseudobulk["Donor ID"])
    embeddings = pd.read_csv(args.embeddings)
    embeddings["Donor ID"] = normalize_donor_id(embeddings["Donor ID"])
    targets, _ = load_pathology_targets()
    targets["Donor ID"] = normalize_donor_id(targets["Donor ID"])
    targets[args.target] = pd.to_numeric(targets[args.target], errors="coerce")

    treatments = module_treatments(pseudobulk, args.modules) if args.mode == "module" else gene_treatments(pseudobulk, args.genes)
    confounders = build_confounders(targets, embeddings, args.covariates)
    result = estimate_effects(
        treatments=treatments,
        targets=targets,
        confounders=confounders,
        target=args.target,
        alpha=args.alpha,
        device=device,
        n_bootstrap=args.n_bootstrap,
        seed=args.seed,
        ci=args.ci,
    )
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(out_path, index=False)
    print(result.to_string(index=False))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
