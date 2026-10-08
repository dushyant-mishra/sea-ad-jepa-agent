"""Preflight checks for formal no-graph ablation training.

Outputs:
  results/tables/no_graph_ablation_preflight_v1.csv
  results/reports/no_graph_ablation_preflight_v1.md
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
import re

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

def run_preflight() -> pd.DataFrame:
    checks = []

    def add_check(name: str, status: str, observed: str, expected: str, notes: str = ""):
        checks.append({
            "check_name": name,
            "status": status,
            "observed": str(observed),
            "expected": str(expected),
            "notes": notes
        })

    # 1. Edge CSV exists
    edge_csv_path = PROJECT_ROOT / "results" / "tables" / "ablation_edge_sets" / "no_graph_identity_edges_v1.csv"
    edge_csv_exists = edge_csv_path.exists()
    add_check(
        "no_graph_edge_file_exists",
        "pass" if edge_csv_exists else "fail",
        "exists" if edge_csv_exists else "missing",
        "exists",
        f"Path: {edge_csv_path.relative_to(PROJECT_ROOT) if edge_csv_exists else edge_csv_path}"
    )

    if edge_csv_exists:
        try:
            edges = pd.read_csv(edge_csv_path)
            # 2. 2,957 rows
            n_rows = len(edges)
            add_check(
                "no_graph_edge_row_count",
                "pass" if n_rows == 2957 else "fail",
                str(n_rows),
                "2957"
            )

            # 3 & 4. All self loops, zero inter-gene edges
            if "source" in edges.columns and "target" in edges.columns:
                self_loops = (edges["source"] == edges["target"]).sum()
                inter_gene = n_rows - self_loops
                
                add_check(
                    "no_graph_all_self_loops",
                    "pass" if self_loops == n_rows else "fail",
                    str(self_loops),
                    str(n_rows)
                )
                
                add_check(
                    "no_graph_zero_inter_gene_edges",
                    "pass" if inter_gene == 0 else "fail",
                    str(inter_gene),
                    "0"
                )
            else:
                add_check("no_graph_all_self_loops", "fail", "missing columns", "source and target columns")
                add_check("no_graph_zero_inter_gene_edges", "fail", "missing columns", "source and target columns")

            # 5. Zero duplicate source-target pairs
            if "source" in edges.columns and "target" in edges.columns:
                duplicates = edges.duplicated(subset=["source", "target"]).sum()
                add_check(
                    "no_graph_zero_duplicate_edges",
                    "pass" if duplicates == 0 else "fail",
                    str(duplicates),
                    "0"
                )
            else:
                add_check("no_graph_zero_duplicate_edges", "fail", "missing columns", "source and target columns")

        except Exception as e:
            add_check("no_graph_edge_row_count", "fail", f"error: {e}", "2957")
            add_check("no_graph_all_self_loops", "fail", "error", "all self loops")
            add_check("no_graph_zero_inter_gene_edges", "fail", "error", "0")
            add_check("no_graph_zero_duplicate_edges", "fail", "error", "0")
    else:
        add_check("no_graph_edge_row_count", "fail", "file missing", "2957")
        add_check("no_graph_all_self_loops", "fail", "file missing", "all self loops")
        add_check("no_graph_zero_inter_gene_edges", "fail", "file missing", "0")
        add_check("no_graph_zero_duplicate_edges", "fail", "file missing", "0")

    # 6. H5AD exists
    h5ad_path = PROJECT_ROOT / "data" / "processed" / "sea_ad_mtg_microglia_pvm_all_hvg3k_expanded_modules.h5ad"
    h5ad_exists = h5ad_path.exists()
    add_check(
        "h5ad_exists",
        "pass" if h5ad_exists else "fail",
        "exists" if h5ad_exists else "missing",
        "exists",
        f"Path: {h5ad_path.relative_to(PROJECT_ROOT) if h5ad_exists else h5ad_path}"
    )

    # 7. Training script exists
    script_path = PROJECT_ROOT / "scripts" / "train_graph_jepa_stage_a_fast.py"
    script_exists = script_path.exists()
    add_check(
        "training_script_exists",
        "pass" if script_exists else "fail",
        "exists" if script_exists else "missing",
        "exists"
    )

    # 8. Training script help confirms required flags
    if script_exists:
        try:
            result = subprocess.run(
                [sys.executable, str(script_path), "--help"],
                capture_output=True,
                text=True,
                check=True
            )
            help_text = result.stdout
            required_flags = ["--edge-csv", "--out-dir", "--epochs", "--h5ad", "--seed"]
            missing_flags = [flag for flag in required_flags if flag not in help_text]
            
            add_check(
                "required_help_flags_present",
                "pass" if not missing_flags else "fail",
                "all present" if not missing_flags else f"missing: {missing_flags}",
                "all present",
                f"Checked for: {', '.join(required_flags)}"
            )
        except Exception as e:
            add_check("required_help_flags_present", "fail", f"error running help: {e}", "all present")
    else:
        add_check("required_help_flags_present", "fail", "script missing", "all present")

    # 9 & 10. Expected output directory
    out_dir = PROJECT_ROOT / "results" / "models" / "ablations" / "no_graph_jepa_v1"
    
    add_check(
        "output_directory_checked",
        "pass",
        "checked",
        "checked",
        f"Target dir: {out_dir.relative_to(PROJECT_ROOT) if out_dir.is_relative_to(PROJECT_ROOT) else out_dir}"
    )
    
    checkpoint_exists = (out_dir / "fast_graph_jepa.pt").exists() or (out_dir / "graph_jepa.pt").exists()
    add_check(
        "no_existing_checkpoint_in_out_dir",
        "pass" if not checkpoint_exists else "warning",
        "checkpoint found" if checkpoint_exists else "empty/no checkpoint",
        "empty/no checkpoint",
        "Warning if checkpoint already exists"
    )

    # 11. Frozen command template
    protocol_path = PROJECT_ROOT / "results" / "reports" / "discovery_ablation_training_protocol_v1.md"
    protocol_exists = protocol_path.exists()
    add_check(
        "protocol_exists",
        "pass" if protocol_exists else "fail",
        "exists" if protocol_exists else "missing",
        "exists"
    )
    
    if protocol_exists:
        content = protocol_path.read_text()
        # Find the no_graph_jepa section
        matches = re.search(r"### no_graph_jepa\n.*?\n```text\n(.*?)\n```", content, re.DOTALL)
        if matches:
            cmd_template = matches.group(1).strip()
            add_check(
                "frozen_command_template_extracted",
                "pass",
                "extracted",
                "extracted",
                f"Command: {cmd_template}"
            )
        else:
            add_check(
                "frozen_command_template_extracted",
                "fail",
                "not found in protocol",
                "extracted"
            )
    else:
        add_check(
            "frozen_command_template_extracted",
            "fail",
            "protocol missing",
            "extracted"
        )

    # 12. No training was run
    add_check(
        "no_training_run",
        "pass",
        "true",
        "true",
        "Preflight script only inspects files and metadata"
    )

    return pd.DataFrame(checks)

def generate_report(df: pd.DataFrame, out_path: Path):
    lines = ["# No-Graph Ablation Training Preflight v1\n"]
    
    status_counts = df["status"].value_counts()
    lines.append(f"**Total Checks**: {len(df)}")
    lines.append(f"**Pass**: {status_counts.get('pass', 0)}")
    lines.append(f"**Warning**: {status_counts.get('warning', 0)}")
    lines.append(f"**Fail**: {status_counts.get('fail', 0)}\n")
    
    if "fail" in status_counts and status_counts["fail"] > 0:
        lines.append("## ❌ PREFLIGHT FAILED\n")
        lines.append("One or more critical checks failed. Training must not proceed until these are resolved.\n")
    else:
        lines.append("## ✅ PREFLIGHT PASSED\n")
        lines.append("All critical checks passed. Training is approved to proceed once placeholders are resolved.\n")
        
    lines.append("## Check Details\n")
    lines.append("| Check Name | Status | Observed | Expected | Notes |")
    lines.append("|---|---|---|---|---|")
    for _, row in df.iterrows():
        status_emoji = "✅" if row["status"] == "pass" else ("⚠️" if row["status"] == "warning" else "❌")
        lines.append(f"| {row['check_name']} | {status_emoji} {row['status']} | {row['observed']} | {row['expected']} | {row['notes']} |")
        
    lines.append("\n## Extracted Command Template\n")
    cmd_row = df[df["check_name"] == "frozen_command_template_extracted"]
    if not cmd_row.empty and cmd_row.iloc[0]["status"] == "pass":
        cmd = cmd_row.iloc[0]["notes"].replace("Command: ", "")
        lines.append("```bash")
        lines.append(cmd)
        lines.append("```\n")
        lines.append("**Note**: Placeholders `<MATCHED_EPOCHS>` and `<FROZEN_SEED>` must be resolved before execution.\n")
        
    lines.append("## Boundary\n")
    lines.append("- No training was run.\n")
    
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--table-out", default="results/tables/no_graph_ablation_preflight_v1.csv")
    parser.add_argument("--report-out", default="results/reports/no_graph_ablation_preflight_v1.md")
    args = parser.parse_args()

    print("Running no-graph ablation preflight checks...")
    df = run_preflight()
    
    table_path = PROJECT_ROOT / args.table_out
    table_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(table_path, index=False)
    print(f"Wrote preflight table: {table_path}")
    
    report_path = PROJECT_ROOT / args.report_out
    generate_report(df, report_path)
    print(f"Wrote preflight report: {report_path}")
    
    if (df["status"] == "fail").any():
        print("\n[FAIL] Preflight failed. See report for details.")
        sys.exit(1)
    else:
        print("\n[PASS] Preflight passed.")

if __name__ == "__main__":
    main()
