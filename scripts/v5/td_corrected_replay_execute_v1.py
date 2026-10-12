"""Thin orchestration for the frozen corrected TD56/57B/57C/59 replay."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Callable

from td_corrected_replay_authority_v1 import BoundReplayAuthority


ALLOWED_STATUS = {"PASS", "FAIL", "NOT_ESTIMABLE"}
MARKER = "TD_CORRECTED_REPLAY_EXECUTION_START.json"
FINAL_RECEIPT = "TD_CORRECTED_REPLAY_RECEIPT_V1.json"


@dataclass(frozen=True)
class StageOutcome:
    status: str
    terminal: str
    artifacts: tuple[Path, ...] = ()


def _sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _base(bound: BoundReplayAuthority) -> dict:
    return {
        "schema": "JEPA_TD_CORRECTED_REPLAY_RECEIPT_V1",
        "contract_sha256": bound.contract_sha256,
        "qualification_receipt_sha256": bound.qualification_receipt_sha256,
        "implementation_commit": bound.implementation_commit,
        "authority_ids": list(bound.authority_ids),
        "spent_authority": True,
        "target_selected": False,
        "representation_selected": False,
        "td60_authorized": False,
        "stage4_authorized": False,
        "training_authorized": False,
    }


def _validate_outcome(stage: str, outcome: StageOutcome) -> None:
    if not isinstance(outcome, StageOutcome):
        raise TypeError(f"{stage} runner must return StageOutcome")
    if outcome.status not in ALLOWED_STATUS:
        raise ValueError(f"{stage} returned invalid status {outcome.status!r}")
    if not outcome.terminal:
        raise ValueError(f"{stage} returned empty terminal")
    for artifact in outcome.artifacts:
        if not artifact.is_file():
            raise ValueError(f"{stage} declared missing artifact {artifact}")


def _stage_receipt(stage: str, outcome: StageOutcome) -> dict:
    return {
        "stage": stage,
        "status": outcome.status,
        "terminal": outcome.terminal,
        "artifacts": [
            {"path": str(path), "sha256": _sha256_path(path), "bytes": path.stat().st_size}
            for path in outcome.artifacts
        ],
        "target_selected": False,
        "td60_authorized": False,
        "stage4_authorized": False,
        "training_authorized": False,
    }


def _terminal_for_statuses(statuses: dict[str, str]) -> str:
    if statuses.get("TD56") == "NOT_ESTIMABLE":
        return "CORRECTED_REPLAY_EARLY_STOP__TD56_NOT_ESTIMABLE__NO_BIOLOGICAL_PASS"
    if statuses.get("TD56") == "FAIL":
        return "CORRECTED_REPLAY_EARLY_STOP__TD56_FAIL__RELATIONAL_PROMOTION_STOPPED"
    if statuses.get("TD57B") == "NOT_ESTIMABLE":
        return "CORRECTED_REPLAY_EARLY_STOP__TD57B_NOT_ESTIMABLE__NO_BIOLOGICAL_PASS"
    if statuses.get("TD57B") == "FAIL":
        return "CORRECTED_REPLAY_EARLY_STOP__TD57B_FAIL__DONOR_RECURRENCE_NOT_CONFIRMED"
    if statuses.get("TD57C") == "NOT_ESTIMABLE":
        return "CORRECTED_REPLAY_EARLY_STOP__TD57C_NOT_ESTIMABLE__NO_BIOLOGICAL_PASS"
    if statuses.get("TD57C") == "PASS":
        return "CORRECTED_TD57C_PASS_DIVERGENCE__PROSPECTIVE_LOCALITY_EXPERIMENT_REQUIRED__NO_TARGET_AUTHORITY"
    if "TD59" in statuses:
        return "CORRECTED_REPLAY_COMPLETE__ROUTING_PROJECTION_REQUIRED__NO_TARGET_AUTHORITY"
    raise RuntimeError("unrecognized corrected replay state")


def execute_replay(
    bound: BoundReplayAuthority,
    namespace: Path,
    run_stage: Callable[[str], StageOutcome],
) -> dict:
    """Execute frozen stages in order after an existing one-shot start marker.

    ``run_stage`` is the only statistics-bearing seam. This controller never
    recomputes a biological statistic and never mutates a stage threshold.
    """
    if namespace != bound.namespace:
        raise ValueError("namespace does not match bound authority")
    marker = namespace / MARKER
    if not marker.is_file():
        raise ValueError("corrected replay start marker is required before execution")

    receipt = _base(bound)
    statuses: dict[str, str] = {}
    stage_receipts: list[dict] = []
    try:
        for stage in ("TD56", "TD57B", "TD57C", "TD59"):
            if stage == "TD57B" and statuses.get("TD56") != "PASS":
                break
            if stage == "TD57C" and not (statuses.get("TD56") == "PASS" and statuses.get("TD57B") == "PASS"):
                break
            if stage == "TD59" and not (
                statuses.get("TD56") == "PASS"
                and statuses.get("TD57B") == "PASS"
                and statuses.get("TD57C") == "FAIL"
            ):
                break
            outcome = run_stage(stage)
            _validate_outcome(stage, outcome)
            statuses[stage] = outcome.status
            sr = _stage_receipt(stage, outcome)
            stage_receipts.append(sr)
            _write_json(namespace / f"{stage}_STAGE_RECEIPT.json", sr)
            if outcome.status in {"FAIL", "NOT_ESTIMABLE"} and stage in {"TD56", "TD57B"}:
                break
            if stage == "TD57C" and outcome.status != "FAIL":
                break

        receipt.update(
            {
                "stage_statuses": statuses,
                "stage_receipts": stage_receipts,
                "terminal": _terminal_for_statuses(statuses),
                "failure": None,
            }
        )
    except Exception as exc:
        receipt.update(
            {
                "stage_statuses": statuses,
                "stage_receipts": stage_receipts,
                "terminal": "POST_MARKER_EXECUTION_FAILURE__AUTHORITY_SPENT__NO_RERUN",
                "failure": f"{type(exc).__name__}: {exc}",
            }
        )
    _write_json(namespace / FINAL_RECEIPT, receipt)
    return receipt
