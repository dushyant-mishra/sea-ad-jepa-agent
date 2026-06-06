from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import KFold, StratifiedKFold
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sea_ad_jepa.baselines import spearman_corr
from sea_ad_jepa.data import load_pathology_targets, normalize_donor_id


FOCUS_TARGETS = [
    "percent AT8 positive area_Grey matter",
    "percent NeuN positive area_Grey matter",
    "percent 6e10 positive area_Grey matter",
    "percent GFAP positive area_Grey matter",
    "percent Iba1 positive area_Grey matter",
]


DEFAULT_RUNS = [
    {"run_id": "sweep_01_base_elastic", "rehearsal": 0.05, "covariance": 0.0},
    {"run_id": "sweep_02_goldilocks", "rehearsal": 0.05, "covariance": 0.001},
    {"run_id": "sweep_03_mod_cov", "rehearsal": 0.05, "covariance": 0.005},
    {"run_id": "sweep_04_loose_anchor", "rehearsal": 0.01, "covariance": 0.001},
    {"run_id": "sweep_05_tight_anchor", "rehearsal": 0.10, "covariance": 0.001},
]


FINE_TIGHT_RUNS = [
    {"run_id": "fine_01_r007_cov0005", "rehearsal": 0.075, "covariance": 0.0005},
    {"run_id": "fine_02_r007_cov001", "rehearsal": 0.075, "covariance": 0.001},
    {"run_id": "fine_03_r010_cov0005", "rehearsal": 0.10, "covariance": 0.0005},
    {"run_id": "fine_04_r010_cov002", "rehearsal": 0.10, "covariance": 0.002},
    {"run_id": "fine_05_r012_cov001", "rehearsal": 0.125, "covariance": 0.001},
    {"run_id": "fine_06_r015_cov001", "rehearsal": 0.15, "covariance": 0.001},
]


FINE_LOOSE_RUNS = [
    {"run_id": "fine_loose_01_r005_cov0005", "rehearsal": 0.005, "covariance": 0.0005},
    {"run_id": "fine_loose_02_r005_cov001", "rehearsal": 0.005, "covariance": 0.001},
    {"run_id": "fine_loose_03_r010_cov0005", "rehearsal": 0.01, "covariance": 0.0005},
    {"run_id": "fine_loose_04_r010_cov002", "rehearsal": 0.01, "covariance": 0.002},
    {"run_id": "fine_loose_05_r020_cov001", "rehearsal": 0.02, "covariance": 0.001},
]


PRESETS = {
    "coarse": DEFAULT_RUNS,
    "fine_tight": FINE_TIGHT_RUNS,
    "fine_loose": FINE_LOOSE_RUNS,
}


def run_command(command: list[str], dry_run: bool, env: dict[str, str]) -> None:
    print("\n$ " + " ".join(command), flush=True)
    if dry_run:
        return
    subprocess.run(command, check=True, env=env)


def make_tertiles(y: np.ndarray) -> np.ndarray:
    try:
        return np.asarray(pd.qcut(y, q=3, labels=False, duplicates="drop"), dtype=np.int32)
    except ValueError:
        return np.asarray(pd.cut(y, bins=3, labels=False, include_lowest=True), dtype=np.int32)


def knn_predict_cosine(x_train: np.ndarray, y_train: np.ndarray, x_test: np.ndarray, k: int) -> np.ndarray:
    train = torch.as_tensor(x_train, dtype=torch.float32)
    test = torch.as_tensor(x_test, dtype=torch.float32)
    train = torch.nn.functional.normalize(train, dim=1)
    test = torch.nn.functional.normalize(test, dim=1)
    distances = (1.0 - test @ train.T).cpu().numpy()
    neighbor_idx = np.argsort(distances, axis=1)[:, :k]
    neighbor_distances = np.take_along_axis(distances, neighbor_idx, axis=1)
    weights = 1.0 / np.maximum(neighbor_distances, 1e-6)
    weights = weights / weights.sum(axis=1, keepdims=True)
    return np.sum(y_train[neighbor_idx] * weights, axis=1).astype(np.float32)


def out_of_fold_cosine_knn(x: np.ndarray, y: np.ndarray, n_neighbors: int, n_splits: int, seed: int) -> np.ndarray:
    y_bins = make_tertiles(y)
    if np.unique(y_bins).size >= 2 and min(np.bincount(y_bins)) >= 2:
        splitter = StratifiedKFold(n_splits=min(n_splits, min(np.bincount(y_bins))), shuffle=True, random_state=seed)
        splits = splitter.split(x, y_bins)
    else:
        splitter = KFold(n_splits=min(n_splits, x.shape[0]), shuffle=True, random_state=seed)
        splits = splitter.split(x)
    pred = np.full(y.shape, np.nan, dtype=np.float32)
    for train_idx, test_idx in splits:
        k = min(n_neighbors, train_idx.size)
        pred[test_idx] = knn_predict_cosine(x[train_idx], y[train_idx], x[test_idx], k)
    return pred


def cosine_knn_metrics(features_path: Path, targets: pd.DataFrame, n_neighbors: int, n_splits: int, seed: int) -> pd.DataFrame:
    features = pd.read_csv(features_path)
    features["Donor ID"] = normalize_donor_id(features["Donor ID"])
    merged = features.merge(targets, on="Donor ID", how="inner")
    feature_cols = [col for col in features.columns if col != "Donor ID"]
    x_all = merged[feature_cols].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=np.float32)
    keep_cols = np.isfinite(x_all).all(axis=0) & (np.std(x_all, axis=0) > 0)
    x_all = StandardScaler().fit_transform(x_all[:, keep_cols]).astype(np.float32)

    rows = []
    for target in FOCUS_TARGETS:
        y_all = pd.to_numeric(merged[target], errors="coerce").to_numpy(dtype=np.float32)
        keep = np.isfinite(y_all) & np.isfinite(x_all).all(axis=1)
        if keep.sum() < max(6, n_splits):
            continue
        pred = out_of_fold_cosine_knn(x_all[keep], y_all[keep], n_neighbors=n_neighbors, n_splits=n_splits, seed=seed)
        rows.append(
            {
                "target": target,
                "n_donors": int(keep.sum()),
                "cosine_knn_spearman": spearman_corr(y_all[keep], pred),
            }
        )
    return pd.DataFrame(rows)


def metric_lookup(df: pd.DataFrame, target: str, column: str, default: float = 0.0) -> float:
    if df is None or df.empty:
        return default
    sub = df[df["target"].eq(target)]
    if sub.empty or column not in sub:
        return default
    value = pd.to_numeric(sub[column], errors="coerce").iloc[0]
    return float(value) if np.isfinite(value) else default


def score_row(
    ridge: pd.DataFrame,
    euclidean_knn: pd.DataFrame,
    cosine_knn: pd.DataFrame,
    history_row: pd.Series,
) -> tuple[float, dict[str, float]]:
    at8 = "percent AT8 positive area_Grey matter"
    neun = "percent NeuN positive area_Grey matter"
    gfap = "percent GFAP positive area_Grey matter"
    iba1 = "percent Iba1 positive area_Grey matter"

    jepa_euclidean = euclidean_knn[euclidean_knn["representation"].eq("jepa_latent_128")]
    parts = {
        "at8_ridge": metric_lookup(ridge, at8, "spearman"),
        "neun_ridge": metric_lookup(ridge, neun, "spearman"),
        "at8_euclidean_knn": metric_lookup(jepa_euclidean, at8, "knn_spearman"),
        "neun_euclidean_knn": metric_lookup(jepa_euclidean, neun, "knn_spearman"),
        "at8_cosine_knn": metric_lookup(cosine_knn, at8, "cosine_knn_spearman"),
        "neun_cosine_knn": metric_lookup(cosine_knn, neun, "cosine_knn_spearman"),
        "gfap_cosine_knn": metric_lookup(cosine_knn, gfap, "cosine_knn_spearman"),
        "iba1_cosine_knn": metric_lookup(cosine_knn, iba1, "cosine_knn_spearman"),
        "effective_dims": float(history_row.get("disease_effective_dims", 0.0)),
        "top_sv_ratio": float(history_row.get("disease_top_sv_ratio", 1.0)),
        "sea_anchor_cosine": float(history_row.get("sea_anchor_cosine", 1.0)),
        "cellxgene_anchor_cosine": float(history_row.get("cellxgene_anchor_cosine", 1.0)),
    }
    anchor_penalty = 0.0
    if parts["sea_anchor_cosine"] < 0.95:
        anchor_penalty += 5.0 * (0.95 - parts["sea_anchor_cosine"])
    if parts["cellxgene_anchor_cosine"] < 0.95:
        anchor_penalty += 5.0 * (0.95 - parts["cellxgene_anchor_cosine"])

    score = (
        parts["at8_ridge"]
        + parts["neun_ridge"]
        + parts["at8_euclidean_knn"]
        + parts["neun_euclidean_knn"]
        + 0.5 * parts["at8_cosine_knn"]
        + 0.5 * parts["neun_cosine_knn"]
        + 0.1 * parts["effective_dims"]
        - 0.5 * parts["top_sv_ratio"]
        - anchor_penalty
    )
    parts["anchor_penalty"] = anchor_penalty
    return float(score), parts


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a targeted Stage C fine-tuning sweep and build a leaderboard.")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--checkpoint-epochs", nargs="+", default=["005", "010"])
    parser.add_argument("--preset", choices=sorted(PRESETS), default="coarse")
    parser.add_argument("--max-runs", type=int, default=0, help="0 means run all configured runs.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--n-neighbors", type=int, default=5)
    parser.add_argument("--n-splits", type=int, default=5)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--out", default="results/tables/stage_c_finetuning_sweep_summary.csv")
    args = parser.parse_args()

    env = os.environ.copy()
    env["PYTHONPATH"] = "src" + os.pathsep + env.get("PYTHONPATH", "")
    configured_runs = PRESETS[args.preset]
    runs = configured_runs[: args.max_runs] if args.max_runs else configured_runs
    targets, _ = load_pathology_targets()
    targets["Donor ID"] = normalize_donor_id(targets["Donor ID"])
    rows = []

    for run in runs:
        run_id = run["run_id"]
        print(f"\n=== {run_id} rehearsal={run['rehearsal']} covariance={run['covariance']} ===", flush=True)
        model_dir = Path("results/models") / f"stage_c_{run_id}"
        log_dir = Path("runs") / f"stage_c_{run_id}"
        history = Path("results/tables") / f"stage_c_{run_id}_history.csv"
        final_model = model_dir / "graph_jepa_stage_c.pt"

        if not (args.skip_existing and final_model.exists()):
            run_command(
                [
                    sys.executable,
                    "scripts/train_graph_jepa_stage_c_disease.py",
                    "--epochs",
                    str(args.epochs),
                    "--sea-rehearsal-weight",
                    str(run["rehearsal"]),
                    "--cellxgene-rehearsal-weight",
                    str(run["rehearsal"]),
                    "--rehearsal-loss-mode",
                    "cosine_softplus_margin",
                    "--rehearsal-margin",
                    "0.95",
                    "--rehearsal-temperature",
                    "100",
                    "--disease-covariance-weight",
                    str(run["covariance"]),
                    "--checkpoint-every",
                    "5",
                    "--out-dir",
                    str(model_dir),
                    "--log-dir",
                    str(log_dir),
                    "--history-out",
                    str(history),
                    "--device",
                    args.device,
                ],
                dry_run=args.dry_run,
                env=env,
            )

        for epoch in args.checkpoint_epochs:
            checkpoint = model_dir / f"graph_jepa_stage_c_epoch_{epoch}.pt"
            if epoch == f"{args.epochs:03d}" and not checkpoint.exists():
                checkpoint = final_model
            coord = Path("results/tables") / f"stage_c_{run_id}_epoch_{epoch}_coordinates.csv"
            donor = Path("results/tables") / f"stage_c_{run_id}_epoch_{epoch}_donor_embeddings.csv"
            ridge_out = Path("results/tables") / f"stage_c_{run_id}_epoch_{epoch}_ridge_pathology.csv"
            metrics_out = Path("results/tables") / f"stage_c_{run_id}_epoch_{epoch}_latent_metrics.csv"
            embed_out = Path("results/tables") / f"stage_c_{run_id}_epoch_{epoch}_umap_coordinates.csv"
            fig_out = Path("results/figures") / f"stage_c_{run_id}_epoch_{epoch}_umap.svg"
            html_out = Path("results/figures") / f"stage_c_{run_id}_epoch_{epoch}_umap.html"
            cosine_out = Path("results/tables") / f"stage_c_{run_id}_epoch_{epoch}_cosine_knn_metrics.csv"

            commands = [
                [
                    sys.executable,
                    "scripts/extract_stage_a_frozen_anchors.py",
                    "--checkpoint",
                    str(checkpoint),
                    "--h5ad",
                    "data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad",
                    "--anchor-type",
                    f"sea_ad_microglia_pvm_{run_id}_epoch_{epoch}",
                    "--out-csv",
                    str(coord),
                    "--edge-csv",
                    "results/tables/v2_graph_string_edges_t700.csv",
                    "--batch-size",
                    "64",
                    "--device",
                    args.device,
                ],
                [sys.executable, "scripts/aggregate_latent_coordinates_by_donor.py", "--coordinates", str(coord), "--out", str(donor)],
                [
                    sys.executable,
                    "scripts/run_pseudobulk_baseline.py",
                    "--features",
                    str(donor),
                    "--out",
                    str(ridge_out),
                    "--max-genes",
                    "0",
                    "--device",
                    args.device,
                ],
                [
                    sys.executable,
                    "scripts/evaluate_latent_spaces.py",
                    "--jepa",
                    str(donor),
                    "--metrics-out",
                    str(metrics_out),
                    "--embedding-out",
                    str(embed_out),
                    "--figure-out",
                    str(fig_out),
                    "--html-out",
                    str(html_out),
                ],
            ]
            for command in commands:
                if args.skip_existing and command[-1] and Path(command[-1]).exists():
                    continue
                run_command(command, dry_run=args.dry_run, env=env)

            if args.dry_run:
                continue
            cosine = cosine_knn_metrics(donor, targets, args.n_neighbors, args.n_splits, args.seed)
            cosine.to_csv(cosine_out, index=False)
            ridge = pd.read_csv(ridge_out)
            euclidean = pd.read_csv(metrics_out)
            hist = pd.read_csv(history)
            hist_epoch = hist[hist["epoch"].eq(int(epoch))]
            history_row = hist_epoch.iloc[0] if not hist_epoch.empty else hist.iloc[-1]
            composite, parts = score_row(ridge, euclidean, cosine, history_row)
            rows.append(
                {
                    "run_id": run_id,
                    "checkpoint_epoch": epoch,
                    "rehearsal_weight": run["rehearsal"],
                    "disease_covariance_weight": run["covariance"],
                    "composite_score": composite,
                    **parts,
                }
            )

    if args.dry_run:
        print("\nDry run complete; no leaderboard written.")
        return

    out = pd.DataFrame(rows).sort_values("composite_score", ascending=False)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)
    print("\nLeaderboard")
    print(out.to_string(index=False))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
