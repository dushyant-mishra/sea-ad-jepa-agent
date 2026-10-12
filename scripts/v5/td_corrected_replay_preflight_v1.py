"""Metadata/hash-only authentication of corrected-replay predecessors."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any


class PreflightError(ValueError):
    pass


@dataclass(frozen=True)
class PreflightInputs:
    g6_acceptance: Path
    g6_receipt: Path
    g7_marker: Path
    g7_receipt: Path
    diagnostic: Path
    diagnostic_commit: str


def _sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _load_json(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise PreflightError(f"missing {label}: {path}")
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise PreflightError(f"invalid {label} JSON: {path}") from exc
    if not isinstance(obj, dict):
        raise PreflightError(f"{label} must be a JSON object")
    return obj


def _require_hash(path: Path, expected: str, label: str) -> None:
    if not path.is_file():
        raise PreflightError(f"missing {label}: {path}")
    observed = _sha256_path(path)
    if observed != expected:
        raise PreflightError(f"{label} hash mismatch: expected {expected}, got {observed}")


def authenticate_predecessors(contract: dict[str, Any], inputs: PreflightInputs) -> dict[str, Any]:
    """Authenticate accepted G6, executed G7, and namespace diagnostic.

    This function never opens corrected value arrays. It reads only small receipts,
    marker/acceptance bytes, and the metadata-only diagnostic.
    """
    p = contract.get("predecessors") or {}
    g6c = p.get("g6") or {}
    g7c = p.get("g7") or {}
    dc = p.get("diagnostic") or {}

    _require_hash(inputs.g6_acceptance, str(g6c.get("external_acceptance_sha256")), "G6 acceptance")
    _require_hash(inputs.g6_receipt, str(g6c.get("receipt_sha256")), "G6 receipt")
    _require_hash(inputs.g7_marker, str(g7c.get("marker_sha256")), "G7 marker")
    _require_hash(inputs.g7_receipt, str(g7c.get("receipt_sha256")), "G7 receipt")

    g7 = _load_json(inputs.g7_receipt, "G7 receipt")
    expected_terminal = g7c.get("terminal")
    if g7.get("terminal") != expected_terminal:
        raise PreflightError(
            f"G7 terminal mismatch: expected {expected_terminal!r}, got {g7.get('terminal')!r}"
        )
    if expected_terminal != "NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP":
        raise PreflightError("G7 terminal contract may not be relabeled as PASS")
    if g7.get("spent_authority") is not True:
        raise PreflightError("G7 spent authority must be recorded before replay predecessor closure")
    if g7.get("biological_replay_authorized") is True:
        raise PreflightError("G7 receipt may not itself authorize biological replay")

    if inputs.diagnostic_commit != dc.get("commit"):
        raise PreflightError(
            f"diagnostic commit mismatch: expected {dc.get('commit')!r}, got {inputs.diagnostic_commit!r}"
        )
    diagnostic = _load_json(inputs.diagnostic, "diagnostic")
    expected_classification = dc.get("classification")
    if diagnostic.get("classification") != expected_classification:
        raise PreflightError(
            "diagnostic classification mismatch: "
            f"expected {expected_classification!r}, got {diagnostic.get('classification')!r}"
        )
    if diagnostic.get("claims_value_agreement") is not False:
        raise PreflightError("diagnostic must not claim value agreement")
    if diagnostic.get("biological_replay_authorized") is True:
        raise PreflightError("diagnostic may not authorize biological replay")

    return {
        "schema": "JEPA_TD_CORRECTED_REPLAY_PREFLIGHT_RECEIPT_V1",
        "technical_prerequisite_closed": True,
        "g7_pass": False,
        "g7_terminal": expected_terminal,
        "diagnostic_classification": expected_classification,
        "closure_reason": "G7_NOT_ESTIMABLE__GENUINELY_DISJOINT_NATURAL_CELL_SETS",
        "g6_acceptance_sha256": g6c.get("external_acceptance_sha256"),
        "g6_receipt_sha256": g6c.get("receipt_sha256"),
        "g7_marker_sha256": g7c.get("marker_sha256"),
        "g7_receipt_sha256": g7c.get("receipt_sha256"),
        "diagnostic_commit": inputs.diagnostic_commit,
        "corrected_replay_authorized": False,
        "biological_replay_authorized": False,
        "target_selected": False,
        "td60_authorized": False,
        "stage4_authorized": False,
        "training_authorized": False
    }
