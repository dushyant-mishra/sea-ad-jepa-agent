"""Mechanical structural controls for FULL104 masking qualification."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Sequence

import numpy as np

from . import full104_masking_streaming_executor_v1 as streaming


EXPECTED_META_COLUMNS = (
    "selection_row",
    "canonical_cell_id",
    "donor_id",
    "expression_row",
    "primary_row_weight",
    "source_library",
)
EXPECTED_MANIFEST_COLUMNS = (
    "block_key",
    "source",
    "operator_index",
    "matrix_id",
    "rows",
    "nnz",
    "counts_path",
    "counts_sha256",
    "meta_path",
    "meta_sha256",
)


def _normalize(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Mapping):
        return {str(k): _normalize(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (list, tuple)):
        return [_normalize(v) for v in value]
    if isinstance(value, set):
        return sorted(_normalize(v) for v in value)
    return value


def canonical_rows_digest(rows: Sequence[Mapping[str, Any]]) -> str:
    raw = json.dumps(
        _normalize(list(rows)),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class StructuralControlReceiptV1:
    primary_rows_sha256: str
    replay_rows_sha256: str
    replay_exact: bool
    untreated_identity_exact: bool
    no_privileged_metadata: bool
    uniform_row_count: int
    schema_policy_id: str = "FULL104_MASKING_ALLOWED_METADATA_SCHEMA_ONLY_V1"

    def validate(self) -> None:
        if self.replay_exact is not True:
            raise ValueError("deterministic replay control failed")
        if self.untreated_identity_exact is not True:
            raise ValueError("untreated mask identity control failed")
        if self.no_privileged_metadata is not True:
            raise ValueError("no-privileged-metadata control failed")
        if self.uniform_row_count < 1:
            raise ValueError("uniform identity control requires at least one row")
        if self.schema_policy_id != "FULL104_MASKING_ALLOWED_METADATA_SCHEMA_ONLY_V1":
            raise ValueError("schema_policy_id mismatch")
        for name, value in (
            ("primary_rows_sha256", self.primary_rows_sha256),
            ("replay_rows_sha256", self.replay_rows_sha256),
        ):
            if not isinstance(value, str) or len(value) != 64:
                raise ValueError(f"{name} must be a SHA-256 digest")

    def canonical_digest(self) -> str:
        self.validate()
        raw = json.dumps(
            {"schema": "V5_MASKING_STRUCTURAL_CONTROL_RECEIPT_V1", **asdict(self)},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()


def build_structural_control_receipt(
    primary_rows: Sequence[Mapping[str, Any]],
    replay_rows: Sequence[Mapping[str, Any]],
) -> StructuralControlReceiptV1:
    primary_sha = canonical_rows_digest(primary_rows)
    replay_sha = canonical_rows_digest(replay_rows)

    uniform = [row for row in primary_rows if row.get("method") == "UNIFORM_RANDOM"]
    identity = bool(uniform)
    for row in uniform:
        identity = identity and (
            float(row["score"]) == float(row["uniform_score"])
            and int(row["mask_cardinality"]) == int(row["uniform_mask_cardinality"])
            and int(row.get("targeted_n", 0)) == 0
            and int(row.get("effective_targeted_n", 0)) == 0
            and tuple(row.get("targeted_cols", ())) == ()
        )

    no_privileged = (
        tuple(streaming._META_COLUMNS) == EXPECTED_META_COLUMNS
        and tuple(streaming._MANIFEST_COLUMNS) == EXPECTED_MANIFEST_COLUMNS
    )

    receipt = StructuralControlReceiptV1(
        primary_rows_sha256=primary_sha,
        replay_rows_sha256=replay_sha,
        replay_exact=(primary_sha == replay_sha),
        untreated_identity_exact=identity,
        no_privileged_metadata=no_privileged,
        uniform_row_count=len(uniform),
    )
    receipt.validate()
    return receipt
