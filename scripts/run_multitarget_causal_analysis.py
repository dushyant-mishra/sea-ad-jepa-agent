from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def slugify(name: str) -> str:
    return name.replace(" ", "_").replace("%", "percent").replace("/", "_").replace("+", "_plus_")


def run_command(cmd: list[str]) -> None:
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False, text=True)
    if result.returncode != 0:
        print(f"Warning: Command failed with exit code {result.returncode}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline runner for multitarget causal discovery.")
    parser.add_argument("--test-run", action="store_true", help="Run a fast smoke test with low epochs and splits.")
    parser.add_argument("--load-pretrained", action="store_true", help="Load saved fold-specific heads to bypass training.")
    parser.add_argument("--device", default="auto")
    args = parser.parse_args()
    
    # Define targets
    targets = [
        "percent AT8 positive area_Grey matter",
        "percent 6e10 positive area_Grey matter",
        "percent GFAP positive area_Grey matter",
        "percent Iba1 positive area_Grey matter",
        "percent NeuN positive area_Grey matter",
        "guhcl pTau_Grey matter",
        "guhcl abeta42_Grey matter",
        "ripa pTau_Grey matter",
        "ripa abeta42_Grey matter"
    ]
    
    # Establish run parameters based on test-run setting
    if args.test_run:
        epochs = 2
        samples_per_epoch = 2000
        n_splits = 3
        print("--- RUNNING FAST INTEGRATION TEST MODE ---")
    else:
        epochs = 8
        samples_per_epoch = 15000
        n_splits = 5
        print("--- RUNNING PRODUCTION CAUSAL DISCOVERY MODE ---")
        
    out_dir = Path("results/tables/multitarget_causal")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    python_exe = sys.executable
    
    # Run loop
    for target in targets:
        target_slug = slugify(target)
        print(f"\n==================================================")
        print(f"Processing Target: {target}")
        print(f"==================================================")
        
        # 1. Run Confounder-Adjusted Effects (Module Mode)
        conf_out = out_dir / f"confounder_adjusted_module_effects_{target_slug}.csv"
        conf_cmd = [
            python_exe, "scripts/causal_confounder_adjusted_effects.py",
            "--pseudobulk", "data/processed/sea_ad_mtg_microglia_pvm_pseudobulk_expanded_modules.csv",
            "--embeddings", "results/tables/microglia_pvm_jepa_ema_var_expanded_balanced_e30_donor_embeddings.csv",
            "--target", target,
            "--mode", "module",
            "--out", str(conf_out),
            "--device", args.device
        ]
        run_command(conf_cmd)
        
        # 2. Run Fold-Specific Knockout (Two-Pass Mode)
        ko_out = out_dir / f"causal_fold_specific_two_pass_{target_slug}.csv"
        ko_donor_out = out_dir / f"causal_fold_specific_two_pass_{target_slug}_by_donor.csv"
        ko_fold_out = out_dir / f"causal_fold_specific_two_pass_{target_slug}_by_fold.csv"
        save_heads_dir = f"results/models/fold_heads/{target_slug}"
        
        ko_cmd = [
            python_exe, "scripts/causal_fold_specific_knockout.py",
            "--h5ad", "data/processed/sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad",
            "--checkpoint", "results/models/microglia_pvm_jepa_ema_var_expanded_balanced_e40/gene_jepa_epoch_030.pt",
            "--target", target,
            "--target-transform", "log1p",
            "--splitter", "stratified_groupkfold",
            "--target-bins", "5",
            "--n-splits", str(n_splits),
            "--mode", "two-pass",
            "--epochs", str(epochs),
            "--samples-per-epoch", str(samples_per_epoch),
            "--out", str(ko_out),
            "--donor-out", str(ko_donor_out),
            "--fold-out", str(ko_fold_out),
            "--device", args.device
        ]
        
        if args.load_pretrained:
            ko_cmd.extend(["--load-fold-heads-dir", save_heads_dir])
        else:
            ko_cmd.extend(["--save-fold-heads-dir", save_heads_dir])
            
        run_command(ko_cmd)
        
    print(f"\nMultitarget Causal Analysis Complete! Output tables saved to: {out_dir}")


if __name__ == "__main__":
    main()
