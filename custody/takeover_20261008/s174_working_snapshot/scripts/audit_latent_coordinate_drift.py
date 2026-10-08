from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def latent_columns(df: pd.DataFrame) -> list[str]:
    cols = [col for col in df.columns if str(col).startswith("z_")]
    if not cols:
        raise ValueError("No latent coordinate columns named z_* were found.")
    return cols


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    numerator = np.sum(a * b, axis=1)
    denominator = np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1)
    return numerator / np.clip(denominator, 1e-8, None)


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit drift between frozen and calibrated JEPA latent coordinates.")
    parser.add_argument("--before", required=True, help="Frozen/reference coordinate CSV.")
    parser.add_argument("--after", required=True, help="Calibrated coordinate CSV.")
    parser.add_argument("--label", required=True, help="Short label for the comparison.")
    parser.add_argument("--summary-out", required=True)
    parser.add_argument("--cell-out", default="")
    args = parser.parse_args()

    before = pd.read_csv(args.before)
    after = pd.read_csv(args.after)
    z_cols = latent_columns(before)
    if z_cols != latent_columns(after):
        raise ValueError("Before/after coordinate files do not have the same z_* columns.")

    if "cell_id" in before and "cell_id" in after:
        merged = before[["cell_id", "donor_id", *z_cols]].merge(
            after[["cell_id", *z_cols]],
            on="cell_id",
            how="inner",
            suffixes=("_before", "_after"),
        )
    else:
        if len(before) != len(after):
            raise ValueError("No cell_id columns were found, and row counts differ.")
        merged = before[["donor_id", *z_cols]].copy()
        for col in z_cols:
            merged[f"{col}_after"] = after[col].to_numpy()
            merged.rename(columns={col: f"{col}_before"}, inplace=True)
        merged.insert(0, "cell_id", np.arange(len(merged)).astype(str))

    if merged.empty:
        raise ValueError("No matching coordinate rows were found.")

    before_z = merged[[f"{col}_before" for col in z_cols]].to_numpy(dtype=np.float32)
    after_z = merged[[f"{col}_after" for col in z_cols]].to_numpy(dtype=np.float32)
    delta = after_z - before_z

    cell_metrics = pd.DataFrame(
        {
            "label": args.label,
            "cell_id": merged["cell_id"].astype(str).to_numpy(),
            "donor_id": merged["donor_id"].astype(str).to_numpy() if "donor_id" in merged else "NA",
            "cosine_before_after": cosine_similarity(before_z, after_z),
            "l2_delta": np.linalg.norm(delta, axis=1),
            "mean_abs_delta": np.mean(np.abs(delta), axis=1),
        }
    )

    summary = {
        "label": args.label,
        "n_cells": int(len(cell_metrics)),
        "latent_dim": int(len(z_cols)),
        "mean_cosine_before_after": float(cell_metrics["cosine_before_after"].mean()),
        "median_cosine_before_after": float(cell_metrics["cosine_before_after"].median()),
        "mean_l2_delta": float(cell_metrics["l2_delta"].mean()),
        "median_l2_delta": float(cell_metrics["l2_delta"].median()),
        "mean_abs_coordinate_delta": float(cell_metrics["mean_abs_delta"].mean()),
        "median_abs_coordinate_delta": float(cell_metrics["mean_abs_delta"].median()),
    }
    summary_df = pd.DataFrame([summary])

    summary_path = Path(args.summary_out)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    if summary_path.exists():
        existing = pd.read_csv(summary_path)
        existing = existing[existing["label"].astype(str) != args.label]
        summary_df = pd.concat([existing, summary_df], ignore_index=True)
    summary_df.to_csv(summary_path, index=False)

    if args.cell_out:
        cell_path = Path(args.cell_out)
        cell_path.parent.mkdir(parents=True, exist_ok=True)
        cell_metrics.to_csv(cell_path, index=False)

    print(summary_df[summary_df["label"].astype(str) == args.label].to_string(index=False))
    print(f"Wrote summary: {summary_path}")
    if args.cell_out:
        print(f"Wrote per-cell drift metrics: {args.cell_out}")


if __name__ == "__main__":
    main()
