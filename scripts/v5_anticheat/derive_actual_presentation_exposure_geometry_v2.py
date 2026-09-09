#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sqlite3
from pathlib import Path

import numpy as np


LEDGER_DTYPE = np.dtype([("stable_key", "<i8"), ("multiplicity", "u1")])


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _summary(sequence: np.ndarray, names: list[object], horizon: int) -> tuple[list[dict], dict]:
    rows = []
    for index, name in enumerate(names):
        positions = np.flatnonzero(sequence == index).astype(np.int64)
        if len(positions) == 0:
            raise RuntimeError(f"missing exposure for {name}")
        linear = np.diff(positions)
        circular = np.r_[linear, positions[0] + horizon - positions[-1]]
        rows.append({
            "id": str(name),
            "presentations": int(len(positions)),
            "max_gap": int(circular.max()),
            "max_absence_run": int(circular.max() - 1),
            "p99_gap": float(np.quantile(circular, 0.99)),
            "median_gap": float(np.median(circular)),
        })
    return rows, max(rows, key=lambda x: x["max_gap"])


def derive(
    *,
    metadata_sqlite: Path,
    expected_metadata_sha256: str,
    ledger: Path,
    expected_ledger_sha256: str,
    horizon: int,
    affine_a: int,
    affine_b: int,
    partition: str,
) -> dict:
    if sha256_file(metadata_sqlite) != expected_metadata_sha256:
        raise RuntimeError("metadata SHA mismatch")
    if sha256_file(ledger) != expected_ledger_sha256:
        raise RuntimeError("multiplicity ledger SHA mismatch")
    if horizon < 1 or math.gcd(affine_a, horizon) != 1:
        raise ValueError("scientific presentation permutation is not bijective")
    inverse = pow(affine_a, -1, horizon)
    table = np.memmap(ledger, dtype=LEDGER_DTYPE, mode="r")

    con = sqlite3.connect(f"file:{metadata_sqlite}?mode=ro&immutable=1", uri=True)
    cur = con.cursor()
    donors = [str(r[0]) for r in cur.execute(
        "select distinct donor_id from cells where partition=? order by donor_id",
        (partition,),
    )]
    operators = [int(r[0]) for r in cur.execute(
        "select distinct operator_index from cells where partition=? order by operator_index",
        (partition,),
    )]
    sources = [str(r[0]) for r in cur.execute(
        "select distinct source from cells where partition=? order by source",
        (partition,),
    )]
    donor_map = {name: i for i, name in enumerate(donors)}
    operator_map = {name: i for i, name in enumerate(operators)}
    source_map = {name: i for i, name in enumerate(sources)}

    donor_sequence = np.empty(horizon, dtype=np.uint16)
    operator_sequence = np.empty(horizon, dtype=np.uint16)
    source_sequence = np.empty(horizon, dtype=np.uint16)

    query = cur.execute(
        "select stable_key,donor_id,operator_index,source from cells "
        "where partition=? order by stable_key",
        (partition,),
    )
    row_offset = 0
    slot_offset = 0
    while True:
        rows = query.fetchmany(100_000)
        if not rows:
            break
        n = len(rows)
        ledger_keys = table["stable_key"][row_offset:row_offset+n]
        ledger_mult = table["multiplicity"][row_offset:row_offset+n].astype(np.int64)
        row_keys = np.fromiter((int(r[0]) for r in rows), np.int64, count=n)
        if not np.array_equal(ledger_keys, row_keys):
            raise RuntimeError("stable-key alignment mismatch")
        donor = np.fromiter((donor_map[str(r[1])] for r in rows), np.uint16, count=n)
        operator = np.fromiter((operator_map[int(r[2])] for r in rows), np.uint16, count=n)
        source = np.fromiter((source_map[str(r[3])] for r in rows), np.uint16, count=n)
        expanded_donor = np.repeat(donor, ledger_mult)
        expanded_operator = np.repeat(operator, ledger_mult)
        expanded_source = np.repeat(source, ledger_mult)
        slots = np.arange(slot_offset, slot_offset + len(expanded_donor), dtype=np.int64)
        presentation = ((slots - affine_b) * inverse) % horizon
        donor_sequence[presentation] = expanded_donor
        operator_sequence[presentation] = expanded_operator
        source_sequence[presentation] = expanded_source
        row_offset += n
        slot_offset += len(expanded_donor)
    con.close()
    if row_offset != len(table) or slot_offset != horizon:
        raise RuntimeError("ledger/population/horizon closure mismatch")

    donor_rows, donor_worst = _summary(donor_sequence, donors, horizon)
    operator_rows, operator_worst = _summary(operator_sequence, operators, horizon)
    source_rows, source_worst = _summary(source_sequence, sources, horizon)
    return {
        "schema": "JEPA_V5_ACTUAL_PRESENTATION_EXPOSURE_GEOMETRY_V2",
        "status": "REAL_DETERMINISTIC_SCHEDULE_EXPOSURE_DERIVED__NO_EMA_AUTHORITY",
        "schedule": {
            "H": horizon,
            "a": affine_a,
            "b": affine_b,
            "ledger_raw_sha256": expected_ledger_sha256,
            "metadata_sha256": expected_metadata_sha256,
        },
        "donor": {"worst": donor_worst, "rows": donor_rows},
        "operator": {"worst": operator_worst, "rows": operator_rows},
        "source": {"worst": source_worst, "rows": source_rows},
        "synthetic_data_used": False,
        "pathology_used": False,
        "checkpoint_outcomes_used": False,
        "training_authorized": False,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--metadata-sqlite", type=Path, required=True)
    p.add_argument("--expected-metadata-sha256", required=True)
    p.add_argument("--ledger", type=Path, required=True)
    p.add_argument("--expected-ledger-sha256", required=True)
    p.add_argument("--horizon", type=int, required=True)
    p.add_argument("--affine-a", type=int, required=True)
    p.add_argument("--affine-b", type=int, required=True)
    p.add_argument("--partition", required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    result = derive(
        metadata_sqlite=a.metadata_sqlite,
        expected_metadata_sha256=a.expected_metadata_sha256,
        ledger=a.ledger,
        expected_ledger_sha256=a.expected_ledger_sha256,
        horizon=a.horizon,
        affine_a=a.affine_a,
        affine_b=a.affine_b,
        partition=a.partition,
    )
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "donor_worst": result["donor"]["worst"],
        "operator_worst": result["operator"]["worst"],
        "source_worst": result["source"]["worst"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
