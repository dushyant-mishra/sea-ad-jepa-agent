"""Deterministic donor-primary metadata ledger for real target-tournament execution."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable, Mapping


class CaseLedgerError(ValueError):
    pass


SUPPORT_STATES = {"MEASURED_POSITIVE", "MEASURED_ZERO", "STRUCTURALLY_UNSUPPORTED"}
SPLITS = {"TRAIN", "EVAL", "TEST"}
_REQUIRED = {"cell_id", "donor_id", "source", "operator", "split", "support_state"}


def _sha(value) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class CaseRow:
    case_id: str
    cell_id: str
    donor_id: str
    source: str
    operator: str
    split: str
    support_state: str
    query_id: str | None
    neighborhood_id: str | None
    eligible_for_value: bool
    matched_wrong_cell_case_id: str | None
    matched_wrong_cell_status: str
    fine_neighborhood_wrong_cell_case_id: str | None
    fine_neighborhood_wrong_cell_status: str


@dataclass(frozen=True)
class CaseLedger:
    rows: tuple[CaseRow, ...]
    sha256: str


def _normalize(rows: Iterable[Mapping]) -> list[dict]:
    out = []
    seen_cells = set()
    donor_splits: dict[str, set[str]] = {}
    for raw in rows:
        if not isinstance(raw, Mapping) or not _REQUIRED <= set(raw):
            raise CaseLedgerError("case row missing required metadata fields")
        row = {k: raw.get(k) for k in _REQUIRED | {"query_id", "neighborhood_id"}}
        for key in ("cell_id", "donor_id", "source", "operator", "split", "support_state"):
            if not isinstance(row[key], str) or not row[key]:
                raise CaseLedgerError(f"{key} must be a nonempty string")
        if row["cell_id"] in seen_cells:
            raise CaseLedgerError(f"duplicate cell_id: {row['cell_id']}")
        seen_cells.add(row["cell_id"])
        if row["split"] not in SPLITS:
            raise CaseLedgerError(f"invalid split: {row['split']}")
        if row["support_state"] not in SUPPORT_STATES:
            raise CaseLedgerError(f"invalid support_state: {row['support_state']}")
        for key in ("query_id", "neighborhood_id"):
            if row[key] is not None and (not isinstance(row[key], str) or not row[key]):
                raise CaseLedgerError(f"{key} must be null or nonempty string")
        donor_splits.setdefault(row["donor_id"], set()).add(row["split"])
        out.append(row)
    offenders = sorted(d for d, splits in donor_splits.items() if len(splits) > 1)
    if offenders:
        raise CaseLedgerError(f"donor appears in multiple splits: {offenders}")
    return sorted(out, key=lambda r: (r["source"], r["operator"], r["split"], r["donor_id"], r["cell_id"], r.get("query_id") or ""))


def _identity(row: dict) -> dict:
    return {
        "cell_id": row["cell_id"], "donor_id": row["donor_id"], "source": row["source"],
        "operator": row["operator"], "split": row["split"], "support_state": row["support_state"],
        "query_id": row.get("query_id"), "neighborhood_id": row.get("neighborhood_id"),
    }


def _eligible(row: dict) -> bool:
    return row["support_state"] in {"MEASURED_POSITIVE", "MEASURED_ZERO"}


def _partner(row: dict, rows: list[dict], case_ids: dict[str, str], *, fine: bool) -> tuple[str | None, str]:
    if not _eligible(row):
        return None, "NOT_ESTIMABLE"
    candidates = []
    for other in rows:
        if other["cell_id"] == row["cell_id"] or other["donor_id"] == row["donor_id"] or not _eligible(other):
            continue
        if (other["source"], other["operator"], other["split"], other.get("query_id")) != (
            row["source"], row["operator"], row["split"], row.get("query_id")
        ):
            continue
        if fine and other.get("neighborhood_id") != row.get("neighborhood_id"):
            continue
        candidates.append(other)
    if not candidates:
        return None, "NOT_ESTIMABLE"
    chosen = min(candidates, key=lambda r: (r["donor_id"], r["cell_id"]))
    return case_ids[chosen["cell_id"]], "ESTIMABLE"


def build_case_ledger(metadata_rows: Iterable[Mapping]) -> CaseLedger:
    rows = _normalize(metadata_rows)
    case_ids = {row["cell_id"]: _sha(_identity(row)) for row in rows}
    built = []
    for row in rows:
        matched_id, matched_status = _partner(row, rows, case_ids, fine=False)
        fine_id, fine_status = _partner(row, rows, case_ids, fine=True)
        built.append(CaseRow(
            case_id=case_ids[row["cell_id"]], cell_id=row["cell_id"], donor_id=row["donor_id"],
            source=row["source"], operator=row["operator"], split=row["split"], support_state=row["support_state"],
            query_id=row.get("query_id"), neighborhood_id=row.get("neighborhood_id"), eligible_for_value=_eligible(row),
            matched_wrong_cell_case_id=matched_id, matched_wrong_cell_status=matched_status,
            fine_neighborhood_wrong_cell_case_id=fine_id, fine_neighborhood_wrong_cell_status=fine_status,
        ))
    ledger_payload = [r.__dict__ for r in built]
    return CaseLedger(rows=tuple(built), sha256=_sha(ledger_payload))
