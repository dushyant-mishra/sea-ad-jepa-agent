#!/usr/bin/env python3
"""Fail-closed validation of physical FULL104 dimension metric receipts.

This does not compute metrics or select D_shared/D_private/D_obs. It only proves that
metric rows came from the declared physical FULL104 stream under the declared
prospective precision authority and required holdout/null mechanics.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Mapping

SCHEMA = "V5_FULL104_DIMENSION_METRIC_RECEIPT_V1"
PASS = "PASS_FULL104_DIMENSION_METRIC_RECEIPT_MECHANICS__NO_DIMENSION_AUTHORITY"
STOP = "STOP_FULL104_DIMENSION_METRIC_RECEIPT_NOT_LAWFUL"
BINDING_PASS = "PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE"
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _fail(reason: str) -> dict[str, Any]:
    return {
        "terminal": STOP,
        "lawful": False,
        "reason": reason,
        "dimension_selected": False,
        "training_authorized": False,
    }


def validate_metric_receipt(rec: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(rec, Mapping) or rec.get("schema") != SCHEMA:
        return _fail("schema_mismatch")
    if rec.get("physical_binding_terminal") != BINDING_PASS:
        return _fail("physical_binding_not_closed")
    binding_sha = rec.get("physical_binding_sha256")
    precision_sha = rec.get("precision_authority_sha256")
    if not isinstance(binding_sha, str) or HEX64.fullmatch(binding_sha) is None:
        return _fail("physical_binding_sha256_invalid")
    if not isinstance(precision_sha, str) or HEX64.fullmatch(precision_sha) is None:
        return _fail("precision_authority_sha256_invalid")
    replicates = rec.get("precision_replicates")
    if isinstance(replicates, bool) or not isinstance(replicates, int) or replicates <= 0:
        return _fail("precision_replicates_invalid")
    if rec.get("training_authorized") is not False:
        return _fail("receipt_cannot_grant_training_authority")
    if rec.get("test_fixture_mode") is not False:
        return _fail("fixture_metrics_forbidden")
    if rec.get("synthetic_data_used") is not False:
        return _fail("synthetic_metrics_forbidden")

    rows = rec.get("rank_rows")
    if not isinstance(rows, list) or not rows:
        return _fail("rank_rows_missing")
    for expected_rank, row in enumerate(rows, start=1):
        if not isinstance(row, Mapping) or row.get("rank") != expected_rank:
            return _fail("rank_rows_must_be_consecutive_from_one")
        if row.get("replicates") != replicates:
            return _fail("replicate_count_not_bound_to_precision_authority")
        if row.get("physical_binding_sha256") != binding_sha:
            return _fail("rank_row_physical_binding_hash_mismatch")
        if row.get("precision_authority_sha256") != precision_sha:
            return _fail("rank_row_precision_authority_hash_mismatch")
        for key in ("full_stream", "matched_null_full_refit", "held_donor", "held_operator"):
            if row.get(key) is not True:
                return _fail(f"required_metric_mechanic_missing:{key}")

    return {
        "terminal": PASS,
        "lawful": True,
        "n_ranks": len(rows),
        "replicates": replicates,
        "physical_binding_sha256": binding_sha,
        "precision_authority_sha256": precision_sha,
        "dimension_selected": False,
        "training_authorized": False,
        "next_required_stage": "APPLY_FROZEN_DIMENSION_SELECTOR_TO_AUTHENTICATED_METRIC_ROWS",
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--receipt", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    out = validate_metric_receipt(json.loads(a.receipt.read_text(encoding="utf-8")))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if out["lawful"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
