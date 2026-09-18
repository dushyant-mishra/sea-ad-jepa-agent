"""Outcome-blind target-panel selector for FULL104 qualification.

The selector consumes only the already-qualified eligible target columns and a
required explicit target count. It never inspects masking scores, expression
values, discovery rankings, or historical target lists.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Iterable, Mapping, Any

import numpy as np

SELECTOR_ID = "DETERMINISTIC_HASH_RANKED_ELIGIBLE_TARGET_PANEL_V2"
SELECTION_NAMESPACE = "JEPA_V5_FULL104_TARGET_PANEL_V2"


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value != value.lower():
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest") from exc
    return value


def _digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    ).hexdigest()


def select_target_cols(
    eligible_cols: Iterable[int],
    *,
    target_count: int,
    eligibility_receipt_sha256: str,
    namespace: str = SELECTION_NAMESPACE,
) -> tuple[int, ...]:
    cols = np.asarray(list(eligible_cols))
    if cols.ndim != 1 or cols.size == 0 or not np.issubdtype(cols.dtype, np.integer):
        raise ValueError("eligible_cols must be a nonempty one-dimensional integer sequence")
    cols = cols.astype(np.int64, copy=False)
    if np.unique(cols).size != cols.size:
        raise ValueError("eligible_cols must be unique")
    if isinstance(target_count, bool) or not isinstance(target_count, int) or target_count < 1:
        raise ValueError("target_count must be a positive integer")
    if target_count > cols.size:
        raise ValueError("target_count cannot exceed eligible target count")
    _sha(eligibility_receipt_sha256, "eligibility_receipt_sha256")
    if not isinstance(namespace, str) or not namespace.strip():
        raise ValueError("namespace must be nonempty")

    ranked = sorted(
        map(int, cols),
        key=lambda col: (
            hashlib.sha256(
                f"{namespace}|{eligibility_receipt_sha256}|{col}".encode("utf-8")
            ).digest(),
            col,
        ),
    )
    return tuple(ranked[:target_count])


@dataclass(frozen=True)
class TargetPanelSelectionReceiptV2:
    eligibility_receipt_sha256: str
    target_count: int
    selected_target_cols: tuple[int, ...]
    selector_id: str = SELECTOR_ID
    namespace: str = SELECTION_NAMESPACE
    terminal_masking_outcomes_inspected: bool = False
    training_authorized: bool = False

    def validate(self) -> None:
        _sha(self.eligibility_receipt_sha256, "eligibility_receipt_sha256")
        if self.selector_id != SELECTOR_ID:
            raise ValueError("selector_id mismatch")
        if self.namespace != SELECTION_NAMESPACE:
            raise ValueError("namespace mismatch")
        if isinstance(self.target_count, bool) or not isinstance(self.target_count, int) or self.target_count < 1:
            raise ValueError("target_count must be positive")
        if len(self.selected_target_cols) != self.target_count:
            raise ValueError("selected target list length must equal target_count")
        if len(set(self.selected_target_cols)) != len(self.selected_target_cols):
            raise ValueError("selected targets must be unique")
        if self.terminal_masking_outcomes_inspected is not False:
            raise ValueError("target panel must freeze before terminal masking outcomes")
        if self.training_authorized is not False:
            raise ValueError("target panel selection cannot authorize training")

    def canonical_digest(self) -> str:
        self.validate()
        payload = asdict(self)
        payload["selected_target_cols"] = list(self.selected_target_cols)
        return _digest({"schema": "V5_TARGET_PANEL_SELECTION_RECEIPT_V2", **payload})
