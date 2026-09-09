#!/usr/bin/env python3
from __future__ import annotations

import argparse
import heapq
import json
import math
import sqlite3
from fractions import Fraction
from pathlib import Path


def load_donor_sizes(path: Path, partition: str) -> dict[str, int]:
    con = sqlite3.connect(f"file:{path}?mode=ro&immutable=1", uri=True)
    rows = con.execute(
        "select donor_id,count(*) from cells where partition=? group by donor_id",
        (partition,),
    ).fetchall()
    con.close()
    if not rows:
        raise RuntimeError("empty reader-fit donor geometry")
    return {str(d): int(n) for d, n in rows}


def marginal_reduction(*, donors: int, donor_cells: int, multiplicity: int) -> Fraction:
    return Fraction(
        1,
        donors * donors * donor_cells * donor_cells
        * multiplicity * (multiplicity + 1),
    )


def exact_product(H: int, A: Fraction, k: int, reduction: Fraction) -> Fraction:
    return Fraction(H + k, 1) * (A - k * reduction)


def first_crossing(
    *, H: int, A: Fraction, count: int, reduction: Fraction, threshold: Fraction
) -> int | None:
    if Fraction(H, 1) * A <= threshold:
        return 0
    # Float root gives a candidate only; exact Fraction comparisons below decide.
    h = float(H)
    a = float(A)
    b = float(reduction)
    target = float(threshold)
    c = h * a - target
    disc = (a - b * h) ** 2 + 4.0 * b * c
    root = ((a - b * h) + math.sqrt(max(0.0, disc))) / (2.0 * b)
    k = max(1, math.ceil(root - 1e-12))
    while k <= count and exact_product(H, A, k, reduction) > threshold:
        k += 1
    while k > 1 and exact_product(H, A, k - 1, reduction) <= threshold:
        k -= 1
    return k if k <= count else None


def ratio_optimal_point(
    donor_sizes: dict[str, int], *, cap: int, ess_floor: Fraction
) -> dict | None:
    if cap < 1:
        raise ValueError("cap must be positive")
    D = len(donor_sizes)
    nmin = min(donor_sizes.values())
    nmax = max(donor_sizes.values())
    pmin = nmin * cap
    pmax = nmax
    bounds = {
        d: (max(1, math.ceil(pmin / n)), min(cap, pmax // n))
        for d, n in donor_sizes.items()
    }
    if any(lo > hi for lo, hi in bounds.values()):
        return None

    H = sum(donor_sizes[d] * lo for d, (lo, _) in bounds.items())
    A = sum(
        Fraction(1, D * D * donor_sizes[d] * lo)
        for d, (lo, _) in bounds.items()
    )
    threshold = Fraction(1, 1) / ess_floor
    if Fraction(H, 1) * A <= threshold:
        crossing = H
        product = Fraction(H, 1) * A
    else:
        heap = []
        for d, n in donor_sizes.items():
            lo, hi = bounds[d]
            if lo < hi:
                red = marginal_reduction(
                    donors=D, donor_cells=n, multiplicity=lo
                )
                heapq.heappush(heap, (-float(red), d, lo, n, red))
        crossing = None
        product = None
        while heap:
            _, d, m, count, reduction = heapq.heappop(heap)
            k = first_crossing(
                H=H, A=A, count=count, reduction=reduction,
                threshold=threshold,
            )
            if k is not None:
                crossing = H + k
                product = exact_product(H, A, k, reduction)
                break
            H += count
            A -= count * reduction
            if m + 1 < bounds[d][1]:
                next_red = marginal_reduction(
                    donors=D, donor_cells=donor_sizes[d],
                    multiplicity=m + 1,
                )
                heapq.heappush(
                    heap, (-float(next_red), d, m + 1, count, next_red)
                )
        if crossing is None:
            return None

    ratio = Fraction(nmax, nmin * cap)
    return {
        "cell_repeat_cap": cap,
        "minimum_ratio_optimal_presentations_for_ess_floor": crossing,
        "population_equivalents": crossing / sum(donor_sizes.values()),
        "importance_ess_fraction": float(1 / product),
        "ratio_lower_bound_numerator": ratio.numerator,
        "ratio_lower_bound_denominator": ratio.denominator,
        "ratio_lower_bound_float": float(ratio),
    }


def unrestricted_minimum_cap(
    donor_sizes: dict[str, int], *, max_cap: int, ess_floor: Fraction
) -> int | None:
    # Exact fixed-H optimality follows from separable, diminishing marginal
    # reductions in A. This search does not impose the ratio-optimal interval.
    D = len(donor_sizes)
    total = sum(donor_sizes.values())
    threshold = Fraction(1, 1) / ess_floor
    for cap in range(1, max_cap + 1):
        H = total
        A = sum(Fraction(1, D * D * n) for n in donor_sizes.values())
        heap = []
        for d, n in donor_sizes.items():
            if cap > 1:
                red = marginal_reduction(donors=D, donor_cells=n, multiplicity=1)
                heapq.heappush(heap, (-float(red), d, 1, n, red))
        if Fraction(H, 1) * A <= threshold:
            return cap
        while heap:
            _, d, m, count, reduction = heapq.heappop(heap)
            k = first_crossing(
                H=H, A=A, count=count, reduction=reduction,
                threshold=threshold,
            )
            if k is not None:
                return cap
            H += count
            A -= count * reduction
            if m + 1 < cap:
                next_red = marginal_reduction(
                    donors=D, donor_cells=donor_sizes[d], multiplicity=m + 1
                )
                heapq.heappush(
                    heap, (-float(next_red), d, m + 1, count, next_red)
                )
    return None


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--metadata-sqlite", type=Path, required=True)
    p.add_argument("--partition", required=True)
    p.add_argument("--ess-floor-numerator", type=int, required=True)
    p.add_argument("--ess-floor-denominator", type=int, required=True)
    p.add_argument("--minimum-cap", type=int, required=True)
    p.add_argument("--maximum-cap", type=int, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    floor = Fraction(a.ess_floor_numerator, a.ess_floor_denominator)
    if not 0 < floor <= 1:
        raise ValueError("ESS floor must lie in (0,1]")
    if a.minimum_cap < 1 or a.maximum_cap < a.minimum_cap:
        raise ValueError("invalid cap range")
    donor_sizes = load_donor_sizes(a.metadata_sqlite, a.partition)
    rows = []
    for cap in range(a.minimum_cap, a.maximum_cap + 1):
        point = ratio_optimal_point(donor_sizes, cap=cap, ess_floor=floor)
        if point is not None:
            rows.append(point)
    result = {
        "schema": "JEPA_V5_REPEAT_CAP_CONDITIONING_PARETO_V1",
        "status": "REAL_DONOR_GEOMETRY_DIAGNOSTIC__NO_REPEAT_CAP_AUTHORITY",
        "population_cells": sum(donor_sizes.values()),
        "donors": len(donor_sizes),
        "minimum_donor_cells": min(donor_sizes.values()),
        "maximum_donor_cells": max(donor_sizes.values()),
        "ess_floor": {
            "numerator": floor.numerator,
            "denominator": floor.denominator,
            "float": float(floor),
        },
        "minimum_cap_that_can_achieve_ess_floor_without_ratio_constraint":
            unrestricted_minimum_cap(
                donor_sizes, max_cap=a.maximum_cap, ess_floor=floor
            ),
        "ratio_optimal_frontier": rows,
        "interpretation": (
            "The dataset determines this frontier conditional on the declared ESS "
            "risk floor. Choosing a repeat cap remains a prospective anti-concentration/"
            "conditioning decision and cannot be selected from training outcomes."
        ),
        "synthetic_data_used": False,
        "training_authorized": False,
    }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
