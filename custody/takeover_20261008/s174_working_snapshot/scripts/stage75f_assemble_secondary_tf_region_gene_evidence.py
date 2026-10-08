#!/usr/bin/env python3
"""Stage75F/F7 secondary TF-region-gene evidence assembly.

Reuses the validated F5c assembler with a temporary secondary-specific config,
then creates an explicit eight-TF gate audit. Only F6-supported secondary TFs
advance; negative motif-support results remain visible and are not forced into
empty evidence tables.
"""

from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

TRUE_VALUES = {"true", "1", "yes", "y", "t"}


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"YAML is not a mapping: {path}")
    return data


def as_bool(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)
    return series.astype(str).str.strip().str.lower().isin(TRUE_VALUES)


def require(frame: pd.DataFrame, columns: set[str], label: str) -> None:
    missing = columns - set(frame.columns)
    if missing:
        raise ValueError(f"{label} missing columns: {sorted(missing)}")


def load_f6_gate(path: Path, configured_tfs: list[str]) -> tuple[pd.DataFrame, list[str], list[str]]:
    gate = pd.read_csv(path)
    require(
        gate,
        {
            "batch_id", "tf", "batch_tf_direct_motif_support",
            "batch_tf_extended_motif_support", "motif_enrichment_completed",
        },
        "F6 support summary",
    )
    for column in [
        "batch_tf_direct_motif_support",
        "batch_tf_extended_motif_support",
        "motif_enrichment_completed",
    ]:
        gate[column] = as_bool(gate[column])
    gate["tf"] = gate["tf"].astype(str)
    if gate["tf"].duplicated().any():
        raise RuntimeError("F6 support summary contains duplicate TF rows")

    configured = list(map(str, configured_tfs))
    observed = gate["tf"].tolist()
    if set(observed) != set(configured):
        raise RuntimeError(
            f"F6/config mismatch: missing={sorted(set(configured)-set(observed))} "
            f"unexpected={sorted(set(observed)-set(configured))}"
        )
    if not gate["motif_enrichment_completed"].all():
        incomplete = gate.loc[~gate["motif_enrichment_completed"], "tf"].tolist()
        raise RuntimeError(f"Incomplete F6 TF batches: {incomplete}")

    supported = gate.loc[gate["batch_tf_extended_motif_support"], "tf"].tolist()
    negative = gate.loc[~gate["batch_tf_extended_motif_support"], "tf"].tolist()
    if not supported:
        raise RuntimeError("No secondary TF passed the F6 motif-support gate")
    return gate, supported, negative


def run_reused_f5c(project: Path, cfg: dict[str, Any], supported_tfs: list[str]) -> None:
    runtime_cfg = copy.deepcopy(cfg)
    runtime_cfg["cistarget_primary_pilot"] = copy.deepcopy(
        cfg["cistarget_secondary_pilot"]
    )
    runtime_cfg["primary_tf_region_gene_evidence"] = copy.deepcopy(
        cfg["secondary_tf_region_gene_evidence"]
    )
    runtime_cfg["regulators"]["primary_passed_all_stage74_gates"] = list(
        supported_tfs
    )

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".yaml",
        prefix="stage75f_f7_runtime_",
        dir=project / "results",
        delete=False,
        encoding="utf-8",
    ) as handle:
        yaml.safe_dump(runtime_cfg, handle, sort_keys=False, width=1000)
        runtime_path = Path(handle.name)

    try:
        command = [
            sys.executable,
            "-u",
            str(project / "scripts/stage75f_assemble_primary_tf_region_gene_evidence.py"),
            "--config",
            str(runtime_path),
            "--project-dir",
            str(project),
        ]
        print("Running validated F5c assembler for supported secondary TFs", flush=True)
        subprocess.run(command, check=True)
    finally:
        runtime_path.unlink(missing_ok=True)


def build_gate_table(
    f6_gate: pd.DataFrame,
    tf_summary: pd.DataFrame,
) -> pd.DataFrame:
    require(
        tf_summary,
        {
            "tf", "n_supported_motifs", "n_supported_target_genes",
            "n_supported_query_peaks", "n_supported_screen_regions",
            "n_evidence_rows", "motif_support_interpretation",
        },
        "F7 TF summary",
    )
    compact = f6_gate.merge(
        tf_summary[
            [
                "tf", "n_supported_motifs", "n_supported_target_genes",
                "n_supported_query_peaks", "n_supported_screen_regions",
                "n_evidence_rows", "motif_support_interpretation",
            ]
        ],
        on="tf",
        how="left",
        validate="one_to_one",
    )
    supported = compact["batch_tf_extended_motif_support"]
    compact["f7_evidence_gate"] = supported.map(
        {True: "advance_supported", False: "stop_no_tf_annotated_enriched_motif"}
    )
    compact["f7_exclusion_reason"] = ""
    compact.loc[
        ~supported,
        "f7_exclusion_reason",
    ] = "no enriched motif annotated to batch TF at configured F6 thresholds"
    for column in [
        "n_supported_motifs", "n_supported_target_genes",
        "n_supported_query_peaks", "n_supported_screen_regions",
        "n_evidence_rows",
    ]:
        compact[column] = pd.to_numeric(
            compact[column], errors="coerce"
        ).fillna(0).astype(int)
    compact["motif_support_interpretation"] = compact[
        "motif_support_interpretation"
    ].fillna("none_at_configured_thresholds")
    compact["validated_regulation"] = False
    compact["validated_grn_claim"] = False
    compact["causal_validation_pass"] = False
    compact["therapeutic_target_claim"] = False
    return compact.sort_values("batch_id").reset_index(drop=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    args = parser.parse_args()

    project = args.project_dir.resolve()
    cfg = load_yaml(args.config.resolve())
    f6 = cfg["cistarget_secondary_pilot"]
    f7 = cfg["secondary_tf_region_gene_evidence"]

    f6_gate, supported_tfs, negative_tfs = load_f6_gate(
        project / f6["outputs"]["tf_support_summary_csv"],
        list(f6["tfs"]),
    )
    print(f"F7 supported secondary TFs: {', '.join(supported_tfs)}", flush=True)
    print(f"F7 negative gate TFs: {', '.join(negative_tfs)}", flush=True)

    run_reused_f5c(project, cfg, supported_tfs)

    outputs = f7["outputs"]
    tf_summary_path = project / outputs["tf_summary_csv"]
    report_path = project / outputs["report_json"]
    gate_path = project / outputs["gate_csv"]

    tf_summary = pd.read_csv(tf_summary_path)
    tf_summary.insert(1, "regulator_role", "descriptive_secondary_hypothesis")
    tf_summary.insert(2, "evidence_gate", "advance_supported")
    tf_summary.to_csv(tf_summary_path, index=False)

    observed_supported = set(tf_summary["tf"].astype(str))
    missing_supported = sorted(set(supported_tfs) - observed_supported)
    unexpected_supported = sorted(observed_supported - set(supported_tfs))

    gate_table = build_gate_table(f6_gate, tf_summary)
    gate_path.parent.mkdir(parents=True, exist_ok=True)
    gate_table.to_csv(gate_path, index=False)

    observed_negative = set(
        gate_table.loc[
            gate_table["f7_evidence_gate"].eq(
                "stop_no_tf_annotated_enriched_motif"
            ),
            "tf",
        ].astype(str)
    )
    negative_gate_mismatch = sorted(set(negative_tfs) ^ observed_negative)

    report = json.loads(report_path.read_text(encoding="utf-8"))
    base_pass = bool(report.get("assembly_integrity_pass"))
    final_pass = bool(
        base_pass
        and not missing_supported
        and not unexpected_supported
        and not negative_gate_mismatch
    )
    report.update(
        {
            "stage": "stage75f_secondary_tf_region_gene_evidence_v1",
            "purpose": (
                "assemble descriptive secondary TF-region-gene candidate "
                "evidence with an explicit negative motif-support gate"
            ),
            "assembly_integrity_pass": final_pass,
            "supported_secondary_tfs": supported_tfs,
            "negative_gate_secondary_tfs": negative_tfs,
            "n_supported_secondary_tfs": len(supported_tfs),
            "n_negative_gate_secondary_tfs": len(negative_tfs),
            "missing_supported_tfs": missing_supported,
            "unexpected_evidence_tfs": unexpected_supported,
            "negative_gate_mismatch": negative_gate_mismatch,
        }
    )
    report.pop("n_primary_tfs", None)
    report.pop("missing_primary_tfs", None)
    report["outputs"] = outputs
    report["claim_boundaries"].update(
        {
            "descriptive_secondary_candidate_evidence": True,
            "negative_motif_support_results_retained": True,
            "validated_regulation": False,
            "validated_grn_claim": False,
            "causal_validation_pass": False,
            "therapeutic_target_claim": False,
        }
    )
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Wrote: {gate_path}", flush=True)
    print(json.dumps(report, indent=2), flush=True)
    return 0 if final_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
