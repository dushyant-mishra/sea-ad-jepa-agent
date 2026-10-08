#!/usr/bin/env python3
"""Stage76/F9 signed TF-target and perturbation-direction audit.

Uses the frozen F8 evidence outputs as the regulatory source of truth. Edge
signs are labeled as predicted response signs from coactivity only; no activation,
repression, causal, or therapeutic direction is inferred.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
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
APPROVED_WORDING = "Model-based, enhancer-informed perturbation hypotheses requiring experimental validation."
TRUE_VALUES = {"true", "1", "yes", "y", "t"}


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"YAML is not a mapping: {path}")
    return data


def read_csv(project: Path, rel_path: str, label: str) -> pd.DataFrame:
    path = project / rel_path
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")
    return pd.read_csv(path)


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
        raise ValueError(f"{label} has none of the claim-boundary columns")
    for column in present:
        values = as_bool(frame[column])
        if values.any():
            raise RuntimeError(f"{label} has true {column}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_head(project: Path) -> str:
    from_env = os.environ.get("STAGE76_GIT_COMMIT", "").strip()
    if from_env:
        return from_env
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=project,
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


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


def response_sign(value: float) -> str:
    if pd.isna(value):
        return "unresolved"
    if value > 0:
        return "positive"
    if value < 0:
        return "negative"
    return "zero"


def scenario_pair(desired: str) -> str:
    if desired in {"increase", "decrease"}:
        return desired
    return "up_and_down_preserved_for_future_simulation"


def build_signed_edges(targets: pd.DataFrame, cfg: dict[str, Any]) -> pd.DataFrame:
    required = {
        "tf", "target_gene", "evidence_tier", "motif_support_class",
        "edge_bootstrap_median_rho", "edge_bootstrap_sign_stability",
        "edge_spearman_rho", *FALSE_CLAIM_COLUMNS,
    }
    require(targets, required, "F8 integrated TF-target summary")
    assert_false_claims(targets, "F8 integrated TF-target summary")
    if targets.duplicated(["tf", "target_gene"]).any():
        dup = targets.loc[targets.duplicated(["tf", "target_gene"], keep=False), ["tf", "target_gene"]]
        raise RuntimeError(f"Duplicate F8 tf,target_gene rows: {dup.to_dict('records')}")

    out = targets.copy()
    median = pd.to_numeric(out["edge_bootstrap_median_rho"], errors="coerce")
    stability = pd.to_numeric(out["edge_bootstrap_sign_stability"], errors="coerce")
    spearman = pd.to_numeric(out["edge_spearman_rho"], errors="coerce")

    out["candidate_coactivity_sign"] = median.map(response_sign)
    out["predicted_response_sign_from_coactivity"] = out["candidate_coactivity_sign"]
    out["edge_sign_rule"] = "sign(edge_bootstrap_median_rho); coactivity only, not activation/repression"
    out["direction_confidence_basis"] = "fails_existing_stage72b_sign_threshold"
    pass_mask = (
        median.abs().ge(float(cfg["min_abs_spearman"]))
        & stability.ge(float(cfg["min_bootstrap_sign_stability"]))
        & spearman.notna()
        & out["candidate_coactivity_sign"].isin(["positive", "negative"])
    )
    out.loc[pass_mask, "direction_confidence_basis"] = "passes_existing_stage72b_abs_rho_and_sign_stability_thresholds"
    out["relevant_state_association"] = "absent_tf_level_state_association_evidence"
    out["desired_tf_change"] = "unresolved"
    out["future_simulation_directions_to_preserve"] = out["desired_tf_change"].map(scenario_pair)
    out["expected_target_expression_direction"] = "unresolved_without_desired_tf_change"
    out["direction_resolved"] = False
    out["unresolved_reason"] = (
        "No existing TF-level rare-high/background or disease-state association result "
        "was found for assigning desired_tf_change; coactivity sign is retained only "
        "as predicted_response_sign_from_coactivity."
    )
    for column in FALSE_CLAIM_COLUMNS:
        out[column] = False

    if out["desired_tf_change"].isna().any() or out["unresolved_reason"].eq("").any():
        raise RuntimeError("Silent missing direction value detected in signed edges")
    return out.sort_values(["evidence_tier", "tf", "target_gene"]).reset_index(drop=True)


def build_regulator_summary(regulators: pd.DataFrame, signed_edges: pd.DataFrame, cfg: dict[str, Any]) -> pd.DataFrame:
    required = {"tf", "evidence_tier", "regulator_role", "stage75_integrated_gate", *FALSE_CLAIM_COLUMNS}
    require(regulators, required, "F8 integrated regulator summary")
    assert_false_claims(regulators, "F8 integrated regulator summary")
    if regulators["tf"].duplicated().any():
        raise RuntimeError("Duplicate regulators in F8 regulator summary")

    rows = []
    edge_counts = signed_edges.groupby("tf").size().to_dict()
    pass_counts = signed_edges.groupby("tf")["direction_confidence_basis"].apply(
        lambda s: int(s.eq("passes_existing_stage72b_abs_rho_and_sign_stability_thresholds").sum())
    ).to_dict()
    positive_counts = signed_edges.groupby("tf")["candidate_coactivity_sign"].apply(lambda s: int(s.eq("positive").sum())).to_dict()
    negative_counts = signed_edges.groupby("tf")["candidate_coactivity_sign"].apply(lambda s: int(s.eq("negative").sum())).to_dict()

    for row in regulators.sort_values(["evidence_tier", "tf"]).itertuples(index=False):
        tf = str(row.tf)
        is_supported = str(row.evidence_tier) in {"Tier A", "Tier B"}
        if is_supported:
            unresolved_reason = (
                "No existing TF-level state-direction evidence establishes whether higher "
                "or lower TF activity is associated with the undesired state."
            )
        else:
            unresolved_reason = "Tier C negative motif-support gate; excluded from perturbation graph assembly."
        rows.append({
            "tf": tf,
            "evidence_tier": row.evidence_tier,
            "regulator_role": row.regulator_role,
            "stage75_integrated_gate": row.stage75_integrated_gate,
            "n_supported_tf_target_rows": int(edge_counts.get(tf, 0)),
            "n_edges_passing_existing_sign_thresholds": int(pass_counts.get(tf, 0)),
            "n_positive_predicted_response_sign_from_coactivity": int(positive_counts.get(tf, 0)),
            "n_negative_predicted_response_sign_from_coactivity": int(negative_counts.get(tf, 0)),
            "desired_tf_change": "unresolved",
            "future_simulation_directions_to_preserve": "up_and_down_preserved_for_future_simulation" if is_supported else "none_excluded_negative_gate",
            "direction_resolved": False,
            "direction_confidence_basis": "state_direction_unresolved",
            "unresolved_reason": unresolved_reason,
            "excluded_from_perturbation_graph_assembly": not is_supported,
            "validated_regulation": False,
            "validated_grn_claim": False,
            "causal_validation_pass": False,
            "therapeutic_target_claim": False,
        })
    out = pd.DataFrame(rows)
    if len(out) != 10:
        raise RuntimeError(f"Expected all 10 regulators represented, observed {len(out)}")
    if out["tf"].duplicated().any():
        raise RuntimeError("Duplicate rows in regulator directionality summary")
    return out.reset_index(drop=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    args = parser.parse_args()

    project = args.project_dir.resolve()
    cfg = load_yaml(args.config.resolve())
    f9 = cfg["stage76_directionality_audit"]
    sources = f9["sources"]
    thresholds = f9["sign_thresholds"]
    outputs = f9["outputs"]

    regulators = read_csv(project, sources["integrated_regulator_summary"], "F8 regulator summary")
    targets = read_csv(project, sources["integrated_tf_target_summary"], "F8 TF-target summary")
    negative = read_csv(project, sources["integrated_negative_regulator_gate"], "F8 negative regulator gate")
    manifest_path = project / sources["integrated_manifest"]
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing F8 manifest: {manifest_path}")

    signed_edges = build_signed_edges(targets, thresholds)
    regulator_summary = build_regulator_summary(regulators, signed_edges, thresholds)
    unresolved = regulator_summary.loc[~regulator_summary["direction_resolved"]].copy()

    if len(signed_edges) != 96:
        raise RuntimeError(f"Expected 96 supported TF-target rows, observed {len(signed_edges)}")
    if set(negative["tf"].astype(str)) != set(regulator_summary.loc[regulator_summary["evidence_tier"].eq("Tier C"), "tf"].astype(str)):
        raise RuntimeError("Tier C negative gate mismatch between F8 and F9")
    if signed_edges["tf"].isin(negative["tf"].astype(str)).any():
        raise RuntimeError("Tier C regulator appears in signed TF-target hypotheses")
    if unresolved["unresolved_reason"].isna().any() or unresolved["unresolved_reason"].eq("").any():
        raise RuntimeError("Every unresolved row must have an explicit reason")

    output_paths = {name: project / rel for name, rel in outputs.items()}
    atomic_write_csv(signed_edges, output_paths["signed_tf_target_csv"])
    atomic_write_csv(regulator_summary, output_paths["regulator_directionality_csv"])
    atomic_write_csv(unresolved, output_paths["unresolved_directionality_csv"])

    source_hashes = {
        name: {"path": rel, "sha256": sha256_file(project / rel)}
        for name, rel in sources.items()
        if name != "integrated_manifest"
    }
    source_hashes["integrated_manifest"] = {
        "path": sources["integrated_manifest"],
        "sha256": sha256_file(manifest_path),
    }
    report = {
        "stage": "stage76_directionality_audit_v1",
        "purpose": "signed coactivity and perturbation-direction audit without activation/repression claims",
        "git_commit": git_head(project),
        "source_tables": source_hashes,
        "inspection_findings": {
            "stage72b_sign_thresholds_reused": True,
            "min_abs_spearman": float(thresholds["min_abs_spearman"]),
            "min_bootstrap_sign_stability": float(thresholds["min_bootstrap_sign_stability"]),
            "tf_level_state_direction_source_found": False,
            "desired_tf_change_policy": "unresolved unless existing TF-level state-association evidence is available",
        },
        "row_counts": {
            "signed_tf_target_hypotheses": int(len(signed_edges)),
            "regulator_directionality_summary": int(len(regulator_summary)),
            "unresolved_directionality": int(len(unresolved)),
            "negative_gate_regulators": int(regulator_summary["evidence_tier"].eq("Tier C").sum()),
        },
        "resolved_direction_counts": regulator_summary["direction_resolved"].value_counts(dropna=False).astype(int).to_dict(),
        "outputs": outputs,
        "claim_boundaries": {
            "validated_regulation": False,
            "validated_grn_claim": False,
            "causal_validation_pass": False,
            "therapeutic_target_claim": False,
            "activation_or_repression_claim": False,
            "approved_wording": APPROVED_WORDING,
        },
    }
    atomic_write_json(report, output_paths["report_json"])

    print(f"Wrote: {output_paths['signed_tf_target_csv']}")
    print(f"Wrote: {output_paths['regulator_directionality_csv']}")
    print(f"Wrote: {output_paths['unresolved_directionality_csv']}")
    print(f"Wrote: {output_paths['report_json']}")
    print(json.dumps({
        "stage": report["stage"],
        "signed_tf_target_rows": len(signed_edges),
        "regulators_represented": len(regulator_summary),
        "direction_resolved_rows": int(regulator_summary["direction_resolved"].sum()),
        "unresolved_rows": len(unresolved),
        "tier_c_excluded_regulators": int(regulator_summary["evidence_tier"].eq("Tier C").sum()),
        "validated_regulation": False,
        "validated_grn_claim": False,
        "causal_validation_pass": False,
        "therapeutic_target_claim": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())