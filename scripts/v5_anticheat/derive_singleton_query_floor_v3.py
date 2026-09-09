#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def family_geometry(path: Path) -> dict[int, dict[str, tuple[int, float]]]:
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    out: dict[int, dict[str, tuple[int, float]]] = {}
    for row in rows:
        op = int(row["operator_index"])
        family = str(row["family"])
        out.setdefault(op, {})[family] = (
            int(row["target_count"]),
            float(row["family_loss_weight"]),
        )
    if not out or any(set(x) != {"COMMON_CORE", "OPERATOR_NATIVE"} for x in out.values()):
        raise ValueError("every operator must contain exactly the two frozen support families")
    return out


def exact_bound(N: int, q: int, weight: float) -> float:
    if not 1 <= q <= N or N <= 1:
        raise ValueError("invalid finite-population query geometry")
    return weight * weight * (N - q) / (q * (N - 1))


def optimal_allocation(families: dict[str, tuple[int, float]], total_queries: int) -> tuple[float,int,int]:
    Nc, wc = families["COMMON_CORE"]
    Nn, wn = families["OPERATOR_NATIVE"]
    best = None
    for qc in range(1, total_queries):
        qn = total_queries - qc
        if qc > Nc or qn > Nn:
            continue
        value = exact_bound(Nc, qc, wc) + exact_bound(Nn, qn, wn)
        candidate = (value, qc, qn)
        if best is None or candidate < best:
            best = candidate
    if best is None:
        raise ValueError("no positive two-family query allocation exists")
    return best


def derive(*, geometry: Path, expected_geometry_sha256: str, max_variance_ratio: float) -> dict:
    if sha256_file(geometry) != expected_geometry_sha256:
        raise RuntimeError("operator-family geometry SHA mismatch")
    if not 0 < max_variance_ratio < 1:
        raise ValueError("max_variance_ratio must be an explicit probability-like risk bound")
    groups = family_geometry(geometry)
    Q = 2
    previous = None
    while True:
        rows = []
        for op, families in sorted(groups.items()):
            value, qc, qn = optimal_allocation(families, Q)
            rows.append({"operator_index":op,"ratio":value,"common_queries":qc,"native_queries":qn})
        worst = max(rows, key=lambda x:x["ratio"])
        if worst["ratio"] <= max_variance_ratio:
            return {
                "schema":"JEPA_V5_SINGLETON_QUERY_PRECISION_DERIVATION_V1",
                "geometry_sha256":expected_geometry_sha256,
                "max_variance_ratio":max_variance_ratio,
                "minimum_total_queries":Q,
                "worst_ratio_at_minimum":worst["ratio"],
                "worst_operator_at_minimum":worst["operator_index"],
                "minimum_allocation":{
                    "common_queries":worst["common_queries"],
                    "native_queries":worst["native_queries"]
                },
                "previous_total_queries":previous["Q"] if previous else None,
                "worst_ratio_at_previous":previous["worst"] if previous else None,
                "synthetic_data_used":False,
                "training_authorized":False
            }
        previous={"Q":Q,"worst":worst["ratio"]}
        Q += 1


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--geometry",type=Path,required=True)
    p.add_argument("--expected-geometry-sha256",required=True)
    p.add_argument("--max-variance-ratio",type=float,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    result=derive(
        geometry=a.geometry,
        expected_geometry_sha256=a.expected_geometry_sha256,
        max_variance_ratio=a.max_variance_ratio,
    )
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
