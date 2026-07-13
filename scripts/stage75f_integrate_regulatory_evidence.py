#!/usr/bin/env python3
"""Stage75/F8 integrated regulatory evidence freeze.

Combines the compact Stage75 primary and secondary evidence summaries into a
single deterministic freeze. This preserves raw evidence columns and adds
explicit evidence tiers without creating causal, validated-GRN, or therapeutic
claims.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

FALSE_CLAIM_COLUMNS = [
    "validated_regulation",
    "validated_grn_claim",
    "causal_validation_pass",
    "therapeutic_target_claim",
]
TRUE_VALUES = {"true", "1", "yes", "y", "t"}
APPROVED_WORDING = (
    "Model-based, enhancer-informed perturbation hypotheses requiring "
    "experimental validation."
)


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"YAML is not a mapping: {path}")
    return data


def require(frame: pd.DataFrame, columns: set[str], label: str) -> None:
    missing = columns - set(frame.columns)
    if missing:
        raise ValueError(f"{label} missing columns: {sorted(missing)}")


def as_bool(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)
    return series.astype(str).str.strip().str.lower().isin(TRUE_VALUES)


def assert_false_claims(frame: pd.DataFrame, label: str) -> None:
    present = [column for column in FALSE_CLAIM_COLUMNS if column in frame.columns]
    if not present:
        raise ValueError(f"{label} has none of the required claim-boundary columns")
    for column in present:
        values = as_bool(frame[column])
        if values.any():
            bad = frame.loc[values, [c for c in ["tf", "target_gene", column] if c in frame.columns]]
            raise RuntimeError(f"{label} has true {column}: {bad.to_dict('records')}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(project: Path, rel_path: str, label: str) -> pd.DataFrame:
    path = project / rel_path
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")
    return pd.read_csv(path)


def atomic_write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        suffix=".tmp",
        prefix=f".{path.name}.",
        dir=path.parent,
        delete=False,
    ) as handle:
        tmp_path = Path(handle.name)
        frame.to_csv(handle, index=False)
    tmp_path.replace(path)


def atomic_write_json(payload: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".tmp",
        prefix=f".{path.name}.",
        dir=path.parent,
        delete=False,
    ) as handle:
        tmp_path = Path(handle.name)
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    tmp_path.replace(path)


def git_head(project: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=project,
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def tier_for(tf: str, tiers: dict[str, list[str]]) -> str:
    for tier, tfs in tiers.items():
        if tf in set(map(str, tfs)):
            return tier
    raise RuntimeError(f"No configured evidence tier for TF: {tf}")


def build_regulator_table(
    primary_reg: pd.DataFrame,
    primary_motif: pd.DataFrame,
    secondary_reg: pd.DataFrame,
    secondary_gate: pd.DataFrame,
    tiers: dict[str, list[str]],
) -> pd.DataFrame:
    supported_required = {
        "tf", "n_supported_motifs", "n_direct_supported_motifs",
        "n_extended_only_supported_motifs", "n_supported_target_genes",
        "n_supported_query_peaks", "n_supported_screen_regions", "n_evidence_rows",
        "motif_support_interpretation", *FALSE_CLAIM_COLUMNS,
    }
    motif_required = {
        "batch_id", "tf", "n_query_regions", "n_mapped_query_regions",
        "query_coverage_fraction", "n_selected_db_regions", "n_motifs_tested",
        "n_enriched_motifs", "n_direct_batch_tf_enriched_motifs",
        "n_extended_batch_tf_enriched_motifs", "batch_tf_direct_motif_support",
        "batch_tf_extended_motif_support", "motif_enrichment_completed",
        *FALSE_CLAIM_COLUMNS,
    }
    require(primary_reg, supported_required, "primary regulator summary")
    require(secondary_reg, supported_required | {"regulator_role", "evidence_gate"}, "secondary regulator summary")
    require(primary_motif, motif_required, "primary motif support summary")
    require(secondary_gate, motif_required | {"regulator_role", "f7_evidence_gate"}, "secondary evidence gate")

    assert_false_claims(primary_reg, "primary regulator summary")
    assert_false_claims(secondary_reg, "secondary regulator summary")
    assert_false_claims(primary_motif, "primary motif support summary")
    assert_false_claims(secondary_gate, "secondary evidence gate")

    primary = primary_motif.merge(
        primary_reg,
        on="tf",
        how="left",
        validate="one_to_one",
        suffixes=("", "_evidence"),
    )
    primary["regulator_role"] = "primary_stage74_gate_pass"
    primary["evidence_gate"] = "advance_supported"

    secondary = secondary_gate.merge(
        secondary_reg.drop(columns=["regulator_role", "evidence_gate"], errors="ignore"),
        on="tf",
        how="left",
        validate="one_to_one",
        suffixes=("", "_evidence"),
    )
    secondary["evidence_gate"] = secondary["f7_evidence_gate"]

    combined = pd.concat([primary, secondary], ignore_index=True, sort=False)
    combined["evidence_tier"] = combined["tf"].map(lambda value: tier_for(str(value), tiers))
    combined["evidence_tier_label"] = combined["evidence_tier"].map(
        {
            "Tier A": "direct motif support",
            "Tier B": "extended-only motif support",
            "Tier C": "no TF-annotated enriched motif at configured thresholds",
        }
    )
    combined["stage75_integrated_gate"] = combined["evidence_tier"].map(
        {"Tier A": "advance_supported", "Tier B": "advance_supported", "Tier C": "stop_no_tf_annotated_enriched_motif"}
    )

    for column in [
        "n_supported_motifs", "n_direct_supported_motifs",
        "n_extended_only_supported_motifs", "n_supported_target_genes",
        "n_supported_query_peaks", "n_supported_screen_regions", "n_evidence_rows",
    ]:
        evidence_column = f"{column}_evidence"
        if evidence_column in combined.columns:
            combined[column] = combined[evidence_column].where(combined[evidence_column].notna(), combined[column])
            combined = combined.drop(columns=[evidence_column])
        combined[column] = pd.to_numeric(combined[column], errors="coerce").fillna(0).astype(int)

    for column in ["n_direct_batch_tf_enriched_motifs", "n_extended_batch_tf_enriched_motifs"]:
        combined[column] = pd.to_numeric(combined[column], errors="raise").astype(int)

    if combined["tf"].duplicated().any():
        raise RuntimeError("Duplicate regulator rows in integrated table")

    tier_order = {"Tier A": 0, "Tier B": 1, "Tier C": 2}
    combined["_tier_order"] = combined["evidence_tier"].map(tier_order)
    combined = combined.sort_values(["_tier_order", "tf"]).drop(columns=["_tier_order"]).reset_index(drop=True)

    if len(combined) != 10:
        raise RuntimeError(f"Expected exactly 10 regulators, observed {len(combined)}")
    if int(combined["evidence_tier"].isin(["Tier A", "Tier B"]).sum()) != 7:
        raise RuntimeError("Expected exactly 7 supported Tier A/B regulators")
    if int(combined["evidence_tier"].eq("Tier C").sum()) != 3:
        raise RuntimeError("Expected exactly 3 Tier C negative-gate regulators")

    for tier, expected in tiers.items():
        observed = combined.loc[combined["evidence_tier"].eq(tier), "tf"].tolist()
        if observed != sorted(expected):
            raise RuntimeError(f"{tier} mismatch: observed={observed} expected={sorted(expected)}")

    assert_false_claims(combined, "integrated regulator summary")
    return combined


def build_target_table(primary_targets: pd.DataFrame, secondary_targets: pd.DataFrame, tiers: dict[str, list[str]]) -> pd.DataFrame:
    required = {"tf", "target_gene", "motif_support_class", *FALSE_CLAIM_COLUMNS}
    require(primary_targets, required, "primary TF-target summary")
    require(secondary_targets, required, "secondary TF-target summary")
    assert_false_claims(primary_targets, "primary TF-target summary")
    assert_false_claims(secondary_targets, "secondary TF-target summary")

    primary = primary_targets.copy()
    primary["regulator_role"] = "primary_stage74_gate_pass"
    secondary = secondary_targets.copy()
    if "regulator_role" not in secondary.columns:
        secondary["regulator_role"] = "descriptive_secondary_hypothesis"

    combined = pd.concat([primary, secondary], ignore_index=True, sort=False)
    combined["evidence_tier"] = combined["tf"].map(lambda value: tier_for(str(value), tiers))
    combined["stage75_integrated_gate"] = "advance_supported"

    if combined["evidence_tier"].eq("Tier C").any():
        bad = sorted(combined.loc[combined["evidence_tier"].eq("Tier C"), "tf"].unique())
        raise RuntimeError(f"Tier C regulator appears in supported TF-target table: {bad}")
    if not combined["evidence_tier"].isin(["Tier A", "Tier B"]).all():
        raise RuntimeError("Every supported TF-target row must belong to Tier A or Tier B")
    if combined.duplicated(["tf", "target_gene"]).any():
        dup = combined.loc[combined.duplicated(["tf", "target_gene"], keep=False), ["tf", "target_gene"]]
        raise RuntimeError(f"Duplicate tf,target_gene rows: {dup.to_dict('records')}")

    assert_false_claims(combined, "integrated TF-target summary")
    return combined.sort_values(["evidence_tier", "tf", "target_gene"]).reset_index(drop=True)


def validate_counts(regulators: pd.DataFrame, targets: pd.DataFrame) -> None:
    target_counts = targets.groupby("tf")["target_gene"].nunique().to_dict()
    supported = regulators.loc[regulators["evidence_tier"].isin(["Tier A", "Tier B"])]
    for row in supported.itertuples(index=False):
        observed = int(target_counts.get(row.tf, 0))
        expected = int(row.n_supported_target_genes)
        if observed != expected:
            raise RuntimeError(f"Target-gene count mismatch for {row.tf}: source={expected} integrated={observed}")

    # Keep both motif-count definitions. The batch-level extended count comes
    # from the motif gate and may include motifs that also have direct support;
    # n_extended_only_supported_motifs comes from the assembled evidence table.
    for column in [
        "n_direct_supported_motifs",
        "n_extended_only_supported_motifs",
        "n_direct_batch_tf_enriched_motifs",
        "n_extended_batch_tf_enriched_motifs",
    ]:
        if regulators[column].isna().any():
            missing = regulators.loc[regulators[column].isna(), "tf"].tolist()
            raise RuntimeError(f"Missing motif count values in {column}: {missing}")
        if (pd.to_numeric(regulators[column], errors="raise") < 0).any():
            raise RuntimeError(f"Negative motif count values in {column}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    args = parser.parse_args()

    project = args.project_dir.resolve()
    cfg = load_yaml(args.config.resolve())
    f8 = cfg["integrated_stage75_evidence_freeze"]
    sources = f8["sources"]
    outputs = f8["outputs"]
    tiers = {str(k): [str(v) for v in values] for k, values in f8["tiers"].items()}

    expected_tiers = {
        "Tier A": ["ELF1", "SPI1", "STAT1"],
        "Tier B": ["BACH1", "CEBPA", "IRF8", "RELA"],
        "Tier C": ["MITF", "NRF1", "STAT3"],
    }
    if {k: sorted(v) for k, v in tiers.items()} != expected_tiers:
        raise RuntimeError(f"F8 tier config drift: {tiers}")

    frames = {
        name: read_csv(project, rel_path, name)
        for name, rel_path in sources.items()
    }

    regulators = build_regulator_table(
        frames["primary_regulator_summary"],
        frames["primary_motif_support_summary"],
        frames["secondary_regulator_summary"],
        frames["secondary_evidence_gate"],
        tiers,
    )
    targets = build_target_table(
        frames["primary_tf_target_summary"],
        frames["secondary_tf_target_summary"],
        tiers,
    )
    validate_counts(regulators, targets)

    negative = regulators.loc[regulators["evidence_tier"].eq("Tier C")].copy()
    negative = negative.sort_values(["tf"]).reset_index(drop=True)

    output_paths = {name: project / rel_path for name, rel_path in outputs.items()}
    atomic_write_csv(regulators, output_paths["regulator_summary_csv"])
    atomic_write_csv(targets, output_paths["tf_target_summary_csv"])
    atomic_write_csv(negative, output_paths["negative_regulator_gate_csv"])

    source_hashes = {
        name: {
            "path": rel_path,
            "sha256": sha256_file(project / rel_path),
            "rows": int(len(frames[name])),
            "columns": list(frames[name].columns),
        }
        for name, rel_path in sources.items()
    }
    counts_by_tier = regulators.groupby("evidence_tier").size().to_dict()
    manifest = {
        "stage": "stage75_integrated_evidence_freeze_v1",
        "purpose": "integrated Stage75 regulatory evidence freeze",
        "git_commit": git_head(project),
        "source_tables": source_hashes,
        "parameters": {
            "cistarget_global_region_count": int(f8["parameters"]["cistarget_global_region_count"]),
            "motif_count_per_batch": int(f8["parameters"]["motif_count_per_batch"]),
            "overlap_threshold": float(f8["parameters"]["overlap_threshold"]),
            "auc_threshold": float(f8["parameters"]["auc_threshold"]),
            "nes_threshold": float(f8["parameters"]["nes_threshold"]),
            "recovery_rank_fraction": float(f8["parameters"]["recovery_rank_fraction"]),
        },
        "tiers": tiers,
        "counts_by_tier": {key: int(value) for key, value in counts_by_tier.items()},
        "input_row_counts": {name: int(len(frame)) for name, frame in frames.items()},
        "output_row_counts": {
            "regulator_summary": int(len(regulators)),
            "tf_target_summary": int(len(targets)),
            "negative_regulator_gate": int(len(negative)),
        },
        "validation": {
            "exactly_10_regulators": len(regulators) == 10,
            "exactly_7_supported_regulators": int(regulators["evidence_tier"].isin(["Tier A", "Tier B"]).sum()) == 7,
            "exactly_3_negative_gate_regulators": len(negative) == 3,
            "duplicate_regulator_rows": bool(regulators["tf"].duplicated().any()),
            "duplicate_tf_target_rows": bool(targets.duplicated(["tf", "target_gene"]).any()),
            "tier_c_in_supported_targets": bool(targets["evidence_tier"].eq("Tier C").any()),
            "claim_boundaries_false": True,
        },
        "outputs": outputs,
        "claim_boundaries": {
            "validated_regulation": False,
            "validated_grn_claim": False,
            "causal_validation_pass": False,
            "therapeutic_target_claim": False,
            "integrated_evidence_freeze": True,
            "approved_wording": APPROVED_WORDING,
        },
    }
    atomic_write_json(manifest, output_paths["manifest_json"])

    print(f"Wrote: {output_paths['regulator_summary_csv']}")
    print(f"Wrote: {output_paths['tf_target_summary_csv']}")
    print(f"Wrote: {output_paths['negative_regulator_gate_csv']}")
    print(f"Wrote: {output_paths['manifest_json']}")
    print(json.dumps({
        "stage": manifest["stage"],
        "regulators": len(regulators),
        "supported_regulators": int(regulators["evidence_tier"].isin(["Tier A", "Tier B"]).sum()),
        "negative_gate_regulators": len(negative),
        "tf_target_rows": len(targets),
        "counts_by_tier": manifest["counts_by_tier"],
        "validated_regulation": False,
        "validated_grn_claim": False,
        "causal_validation_pass": False,
        "therapeutic_target_claim": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())