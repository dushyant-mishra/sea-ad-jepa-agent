"""Outcome-blind qualification for the corrected relational replay stage."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any

from td_corrected_replay_contract_v1 import validate_contract


class QualificationError(ValueError):
    pass


@dataclass(frozen=True)
class QualificationInputs:
    external_executors: dict[str, Path]
    comparison_population_n: dict[str, int]
    namespace_probe: Path


def _sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _require_predecessor_receipt(receipt: dict[str, Any]) -> None:
    if receipt.get("schema") != "JEPA_TD_CORRECTED_REPLAY_PREFLIGHT_RECEIPT_V1":
        raise QualificationError("invalid predecessor receipt schema")
    if receipt.get("technical_prerequisite_closed") is not True:
        raise QualificationError("technical predecessor prerequisite is not closed")
    if receipt.get("g7_pass") is not False:
        raise QualificationError("G7 PASS relabeling is forbidden")
    if receipt.get("g7_terminal") != "NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP":
        raise QualificationError("unexpected G7 terminal")
    if receipt.get("diagnostic_classification") != "GENUINELY_DISJOINT_NATURAL_CELL_SETS":
        raise QualificationError("unexpected diagnostic classification")
    if receipt.get("closure_reason") != "G7_NOT_ESTIMABLE__GENUINELY_DISJOINT_NATURAL_CELL_SETS":
        raise QualificationError("unexpected predecessor closure reason")
    if receipt.get("biological_replay_authorized") is not False:
        raise QualificationError("predecessor receipt must not authorize biological replay")


def _expected_external(contract: dict[str, Any]) -> dict[str, str]:
    td56 = contract["executors"]["TD56"]["selected_artifacts"]
    by_source = {row["source"]: row["sha256"] for row in td56}
    return {
        "TD56:HVS": by_source["HVS"],
        "TD56:NPH52": by_source["NPH52"],
        "TD56:SEA_AD": by_source["SEA_AD"],
        "TD57C": contract["executors"]["TD57C"]["sha256"],
    }


def qualify_replay(
    contract: dict[str, Any],
    predecessor_receipt: dict[str, Any],
    repo_root: Path,
    metadata_inputs: QualificationInputs,
) -> dict[str, Any]:
    """Bind exact executors and cheap estimability without creating outcomes."""
    _require_predecessor_receipt(predecessor_receipt)
    validated = validate_contract(contract, repo_root)

    if metadata_inputs.namespace_probe.exists():
        raise QualificationError("future replay namespace must not already exist")

    expected = _expected_external(validated)
    if set(metadata_inputs.external_executors) != set(expected):
        raise QualificationError(
            "external executor bindings must contain exactly " + ", ".join(sorted(expected))
        )
    external_receipt: dict[str, Any] = {}
    for key, expected_sha in expected.items():
        path = metadata_inputs.external_executors[key]
        if not path.is_file():
            raise QualificationError(f"missing external executor for {key}: {path}")
        observed = _sha256_path(path)
        if observed != expected_sha:
            raise QualificationError(
                f"{key} executor hash mismatch: expected {expected_sha}, got {observed}"
            )
        external_receipt[key] = {"path": str(path), "sha256": observed}

    populations = metadata_inputs.comparison_population_n
    required_stages = {"TD56", "TD57B", "TD57C", "TD59"}
    if set(populations) != required_stages:
        raise QualificationError("comparison_population_n must contain exactly TD56, TD57B, TD57C, TD59")
    for stage, n in populations.items():
        if not isinstance(n, int) or isinstance(n, bool) or n < 0:
            raise QualificationError(f"invalid comparison_population_n for {stage}")
        if n == 0:
            raise QualificationError(f"zero comparison population for {stage}; stop before start marker")

    stage_receipts = []
    for stage in validated["stages"]:
        sid = stage["id"]
        stage_receipts.append({
            "id": sid,
            "comparison_population_n": populations[sid],
            "kernel_invoked": False,
            "protected_values_opened": False,
        })

    return {
        "schema": "JEPA_TD_CORRECTED_REPLAY_QUALIFICATION_RECEIPT_V1",
        "terminal": "PASS_TD_CORRECTED_REPLAY_TURNKEY_QUALIFICATION__NO_BIOLOGICAL_REPLAY_RUN__LAUNCH_AUDIT_REQUIRED",
        "predecessor_closure_reason": predecessor_receipt["closure_reason"],
        "g7_pass": False,
        "stages": stage_receipts,
        "external_executor_bindings": external_receipt,
        "repository_executor_bindings": {
            sid: {
                "path": validated["executors"][sid]["repository_path"],
                "sha256": validated["executors"][sid]["sha256"],
            }
            for sid in ("TD57B", "TD59")
        },
        "namespace_probe": str(metadata_inputs.namespace_probe),
        "biological_replay_run": False,
        "start_marker_created": False,
        "target_selected": False,
        "representation_selected": False,
        "td60_authorized": False,
        "stage4_authorized": False,
        "training_authorized": False
    }
