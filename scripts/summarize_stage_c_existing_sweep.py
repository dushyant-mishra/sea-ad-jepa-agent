from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def load_sweep_module():
    path = Path(__file__).resolve().parent / "sweep_stage_c_finetuning.py"
    spec = importlib.util.spec_from_file_location("sweep_stage_c_finetuning", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    sweep = load_sweep_module()
    parser = argparse.ArgumentParser(description="Summarize an already-completed Stage C sweep from existing output files.")
    parser.add_argument("--preset", choices=sorted(sweep.PRESETS), required=True)
    parser.add_argument("--checkpoint-epoch", default="005")
    parser.add_argument("--n-neighbors", type=int, default=5)
    parser.add_argument("--n-splits", type=int, default=5)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    targets, _ = sweep.load_pathology_targets()
    targets["Donor ID"] = sweep.normalize_donor_id(targets["Donor ID"])
    rows = []

    for run in sweep.PRESETS[args.preset]:
        run_id = run["run_id"]
        epoch = args.checkpoint_epoch
        history_path = Path("results/tables") / f"stage_c_{run_id}_history.csv"
        donor_path = Path("results/tables") / f"stage_c_{run_id}_epoch_{epoch}_donor_embeddings.csv"
        ridge_path = Path("results/tables") / f"stage_c_{run_id}_epoch_{epoch}_ridge_pathology.csv"
        metrics_path = Path("results/tables") / f"stage_c_{run_id}_epoch_{epoch}_latent_metrics.csv"
        cosine_path = Path("results/tables") / f"stage_c_{run_id}_epoch_{epoch}_cosine_knn_metrics.csv"

        required = [history_path, donor_path, ridge_path, metrics_path]
        missing = [str(path) for path in required if not path.exists()]
        if missing:
            print(f"Skipping {run_id}; missing {missing}")
            continue

        if cosine_path.exists():
            cosine = pd.read_csv(cosine_path)
        else:
            cosine = sweep.cosine_knn_metrics(donor_path, targets, args.n_neighbors, args.n_splits, args.seed)
            cosine.to_csv(cosine_path, index=False)

        ridge = pd.read_csv(ridge_path)
        euclidean = pd.read_csv(metrics_path)
        history = pd.read_csv(history_path)
        history_epoch = history[history["epoch"].eq(int(epoch))]
        history_row = history_epoch.iloc[0] if not history_epoch.empty else history.iloc[-1]
        composite, parts = sweep.score_row(ridge, euclidean, cosine, history_row)
        rows.append(
            {
                "run_id": run_id,
                "checkpoint_epoch": int(epoch),
                "rehearsal_weight": run["rehearsal"],
                "disease_covariance_weight": run["covariance"],
                "composite_score": composite,
                **parts,
            }
        )

    out = pd.DataFrame(rows).sort_values("composite_score", ascending=False)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)
    print(out.to_string(index=False))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
