"""Mandatory falsifier engine emitting raw case- and donor-level evidence."""
from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict
from math import fsum
from typing import Mapping, Sequence

import td_real_tournament_contract_v1 as C


class FalsifierError(ValueError):
    pass


@dataclass(frozen=True)
class RawFalsifierEvidence:
    falsifier_id: str
    per_case_delta: dict[str, float]
    per_donor_delta: dict[str, float]
    estimable_cases: int
    not_estimable_cases: int


def _vec(values) -> tuple[float, ...]:
    if isinstance(values, (int, float)):
        return (float(values),)
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)) or not values:
        raise FalsifierError("prediction/target must be a nonempty numeric sequence")
    try:
        return tuple(float(v) for v in values)
    except Exception as exc:
        raise FalsifierError("prediction/target contains nonnumeric value") from exc


def _concat(parts) -> tuple[float, ...]:
    out = []
    for part in parts:
        out.extend(_vec(part))
    return tuple(out)


def _target_student(record) -> tuple[tuple[float, ...], tuple[float, ...]]:
    v = record.values
    if "shared_target" in v and "query_target" in v and "relational_target" in v:
        return _concat([v["shared_target"], v["relational_target"], v["query_target"]]), _concat([v["shared_student"], v["relational_student"], v["query_student"]])
    if "shared_target" in v and "relational_target" in v:
        return _concat([v["shared_target"], v["relational_target"]]), _concat([v["shared_student"], v["relational_student"]])
    if "shared_target" in v and "query_target" in v:
        return _concat([v["shared_target"], v["query_target"]]), _concat([v["shared_student"], v["query_student"]])
    if "shared_target" in v:
        return _vec(v["shared_target"]), _vec(v["shared_student"])
    if "query_target" in v:
        return _vec(v["query_target"]), _vec(v["query_student"])
    if "regulatory_target" in v:
        return _vec(v["regulatory_target"]), _vec(v["regulatory_student"])
    raise FalsifierError(f"cannot identify target/student fields for {record.cell_id}")


def _mse(target: tuple[float, ...], prediction: tuple[float, ...]) -> float:
    if len(target) != len(prediction):
        raise FalsifierError("prediction length differs from target length")
    return fsum((a - b) ** 2 for a, b in zip(target, prediction)) / len(target)


def _donor_means(case_rows, per_case: dict[str, float]) -> dict[str, float]:
    grouped = defaultdict(list)
    for row in case_rows:
        if row.cell_id in per_case:
            grouped[row.donor_id].append(per_case[row.cell_id])
    return {donor: fsum(vals) / len(vals) for donor, vals in sorted(grouped.items())}


def _partner_prediction(record, payload_by_case, ledger_by_case, attr: str):
    ledger_row = ledger_by_case[record.case_id]
    partner_case_id = getattr(ledger_row, attr)
    if partner_case_id is None:
        return None
    partner = payload_by_case.get(partner_case_id)
    if partner is None:
        raise FalsifierError("ledger partner missing from candidate payload")
    _, student = _target_student(partner)
    return student


def run_falsifiers(payload, case_ledger, baseline_predictions: Mapping[str, Mapping[str, Sequence[float]]]) -> dict[str, RawFalsifierEvidence]:
    contract = C.load_real_tournament_contract()
    registry = C.validate_candidate_registry(contract)
    if payload.candidate_id not in registry:
        raise FalsifierError("candidate absent from real tournament registry")
    required = registry[payload.candidate_id]["mandatory_falsifiers"]
    provided = set(baseline_predictions)
    derived = {"matched_wrong_cell", "fine_neighborhood_wrong_cell"}
    missing = [f for f in required if f not in provided and f not in derived]
    if missing:
        raise FalsifierError(f"missing mandatory falsifier baselines: {missing}")

    payload_by_case = {r.case_id: r for r in payload.records}
    ledger_by_case = {r.case_id: r for r in case_ledger.rows}
    out = {}
    for falsifier_id in required:
        per_case: dict[str, float] = {}
        not_estimable = 0
        for record in payload.records:
            if record.support_state == "STRUCTURALLY_UNSUPPORTED":
                continue
            target, student = _target_student(record)
            student_loss = _mse(target, student)
            if falsifier_id == "matched_wrong_cell":
                baseline = _partner_prediction(record, payload_by_case, ledger_by_case, "matched_wrong_cell_case_id")
            elif falsifier_id == "fine_neighborhood_wrong_cell":
                baseline = _partner_prediction(record, payload_by_case, ledger_by_case, "fine_neighborhood_wrong_cell_case_id")
            else:
                by_cell = baseline_predictions.get(falsifier_id)
                if not isinstance(by_cell, Mapping) or record.cell_id not in by_cell:
                    raise FalsifierError(f"missing baseline prediction for {falsifier_id}:{record.cell_id}")
                baseline = _vec(by_cell[record.cell_id])
            if baseline is None:
                not_estimable += 1
                continue
            baseline_loss = _mse(target, _vec(baseline))
            per_case[record.cell_id] = baseline_loss - student_loss
        out[falsifier_id] = RawFalsifierEvidence(
            falsifier_id=falsifier_id,
            per_case_delta=per_case,
            per_donor_delta=_donor_means(payload.records, per_case),
            estimable_cases=len(per_case),
            not_estimable_cases=not_estimable,
        )
    return out
