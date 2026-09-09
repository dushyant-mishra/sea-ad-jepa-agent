#!/usr/bin/env python3
"""Audit guaranteed full-cell coverage against V5 proposal-conditioning constraints.

Dataset-geometry only: no pathology/protected outcome and no optimizer. All
scientific constraints are mandatory arguments. The greedy donor-balanced result
is a deterministic calibration candidate, not claimed globally optimal and not
training authority.

Under donor-uniform cell target mass, per-cell target probability is inversely
proportional to donor size. If every cell must appear at least once and no cell
may appear more than cell_cap times, proposal multiplicities are in [1,cell_cap].
Therefore the smallest possible max/min importance-weight ratio is at least:

    (largest donor / smallest donor) / cell_cap.

Any smaller frozen ratio ceiling is mathematically incompatible with guaranteed
full-cell coverage under that cap.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence


@dataclass(frozen=True)
class Group:
    donor: str
    operator: int
    source: str
    cells: int


@dataclass(frozen=True)
class DonorState:
    donor: str
    base_multiplicity: int
    presentations: int
    a_term: float
    p_over_m_min: float
    p_over_m_max: float
    max_cell_multiplicity: int
    minimum_group_presentations: int
    group_topup_presentations: int
    source_presentations: dict[str, int]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be an explicit positive integer")
    return int(value)


def full_coverage_weight_ratio_lower_bound(
    donor_sizes: Mapping[str, int], *, cell_cap: int
) -> float:
    cap = _positive_int(cell_cap, "cell_cap")
    if not donor_sizes:
        raise ValueError("donor_sizes cannot be empty")
    parsed = []
    for donor, raw_n in donor_sizes.items():
        if not isinstance(donor, str) or not donor:
            raise ValueError("donor IDs must be nonempty strings")
        parsed.append(_positive_int(raw_n, f"donor size for {donor}"))
    return (max(parsed) / min(parsed)) / cap


def minimum_cell_cap_for_weight_ratio_ceiling(
    donor_sizes: Mapping[str, int], *, weight_ratio_ceiling: float
) -> int:
    if isinstance(weight_ratio_ceiling, bool) or not isinstance(
        weight_ratio_ceiling, (int, float)
    ):
        raise ValueError("weight_ratio_ceiling must be explicit numeric")
    ceiling = float(weight_ratio_ceiling)
    if not math.isfinite(ceiling) or ceiling <= 0:
        raise ValueError("weight_ratio_ceiling must be finite and positive")
    if not donor_sizes:
        raise ValueError("donor_sizes cannot be empty")
    sizes = [
        _positive_int(value, f"donor size for {donor}")
        for donor, value in donor_sizes.items()
    ]
    return int(math.ceil((max(sizes) / min(sizes)) / ceiling))


def load_geometry(db: Path, partition: str):
    if not isinstance(partition, str) or not partition:
        raise ValueError("partition must be an explicit nonempty string")
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        cur = con.cursor()
        cols = [row[1] for row in cur.execute("pragma table_info(cells)")]
        needed = {"source", "operator_index", "donor_id", "partition", "stable_key"}
        if not needed.issubset(cols):
            raise RuntimeError(f"cells schema missing {sorted(needed-set(cols))}")
        query = (
            "select donor_id,operator_index,source,count(*) from cells "
            "where partition=? group by donor_id,operator_index,source"
        )
        groups = [
            Group(str(d), int(o), str(s), int(n))
            for d, o, s, n in cur.execute(query, (partition,))
        ]
        donor_n = {
            str(d): int(n)
            for d, n in cur.execute(
                "select donor_id,count(*) from cells where partition=? group by donor_id",
                (partition,),
            )
        }
        source_n = {
            str(s): int(n)
            for s, n in cur.execute(
                "select source,count(*) from cells where partition=? group by source",
                (partition,),
            )
        }
        total = int(
            cur.execute(
                "select count(*) from cells where partition=?", (partition,)
            ).fetchone()[0]
        )
        unique = int(
            cur.execute(
                "select count(distinct stable_key) from cells where partition=?",
                (partition,),
            ).fetchone()[0]
        )
    finally:
        con.close()
    if total < 1 or not donor_n or not groups:
        raise RuntimeError("requested partition has no usable population")
    if total != unique:
        raise RuntimeError("stable_key is not unique across requested population")
    if sum(group.cells for group in groups) != total:
        raise RuntimeError("group counts do not cover population exactly")
    return groups, donor_n, source_n, total


def donor_state(
    donor: str,
    groups: list[Group],
    donor_cells: int,
    donor_count: int,
    base: int,
    group_floor: int,
    cell_cap: int,
) -> DonorState:
    p = 1.0 / (donor_count * donor_cells)
    presentations = 0
    a_term = 0.0
    p_over_m_min = float("inf")
    p_over_m_max = 0.0
    max_multiplicity = 0
    minimum_group = 10**30
    group_topup = 0
    source_presentations: collections.Counter[str] = collections.Counter()
    for group in groups:
        group_total = group.cells * base
        if group_total < group_floor:
            extra = group_floor - group_total
            group_topup += extra
            q, r = divmod(extra, group.cells)
            specs = ((group.cells-r, base+q), (r, base+q+1))
        else:
            specs = ((group.cells, base),)
        realized_group = 0
        for count, multiplicity in specs:
            if count <= 0:
                continue
            if multiplicity > cell_cap:
                raise RuntimeError(f"donor {donor} group top-up exceeds cell cap")
            presentations += count * multiplicity
            realized_group += count * multiplicity
            source_presentations[group.source] += count * multiplicity
            max_multiplicity = max(max_multiplicity, multiplicity)
            a_term += count * (p * p / multiplicity)
            p_over_m = p / multiplicity
            p_over_m_min = min(p_over_m_min, p_over_m)
            p_over_m_max = max(p_over_m_max, p_over_m)
        minimum_group = min(minimum_group, realized_group)
    return DonorState(
        donor,
        base,
        presentations,
        a_term,
        p_over_m_min,
        p_over_m_max,
        max_multiplicity,
        minimum_group,
        group_topup,
        dict(source_presentations),
    )


def compile_states(
    groups: Sequence[Group],
    donor_n: Mapping[str, int],
    *,
    group_floor: int,
    cell_cap: int,
):
    donor_count = len(donor_n)
    by_donor: dict[str, list[Group]] = collections.defaultdict(list)
    for group in groups:
        by_donor[group.donor].append(group)
    return {
        donor: {
            multiplicity: donor_state(
                donor,
                by_donor[donor],
                donor_n[donor],
                donor_count,
                multiplicity,
                group_floor,
                cell_cap,
            )
            for multiplicity in range(1, cell_cap+1)
        }
        for donor in donor_n
    }


def metrics(mult: Mapping[str, int], states, population_cells: int):
    chosen = [states[donor][multiplicity] for donor, multiplicity in mult.items()]
    total = sum(item.presentations for item in chosen)
    a_term = sum(item.a_term for item in chosen)
    source: collections.Counter[str] = collections.Counter()
    for item in chosen:
        source.update(item.source_presentations)
    return {
        "total_presentations": total,
        "extra_presentations": total-population_cells,
        "population_equivalents": total/population_cells,
        "importance_ess_fraction": 1.0/(total*a_term),
        "importance_weight_max_to_min_ratio": (
            max(item.p_over_m_max for item in chosen)
            / min(item.p_over_m_min for item in chosen)
        ),
        "max_cell_multiplicity": max(item.max_cell_multiplicity for item in chosen),
        "minimum_group_presentations": min(
            item.minimum_group_presentations for item in chosen
        ),
        "group_topup_presentations": sum(
            item.group_topup_presentations for item in chosen
        ),
        "source_presentations": dict(sorted(source.items())),
        "source_presentation_fraction": {
            key: source[key]/total for key in sorted(source)
        },
    }


def greedy(states, population_cells: int, ess_floor: float):
    mult = {donor: 1 for donor in states}
    current = metrics(mult, states, population_cells)
    steps = 0
    while current["importance_ess_fraction"] + 1e-15 < ess_floor:
        current_total = current["total_presentations"]
        current_ess = current["importance_ess_fraction"]
        best = None
        for donor in sorted(states):
            multiplicity = mult[donor]
            if multiplicity >= max(states[donor]):
                continue
            trial = dict(mult)
            trial[donor] = multiplicity+1
            candidate = metrics(trial, states, population_cells)
            gain = candidate["importance_ess_fraction"]-current_ess
            if gain <= 0:
                continue
            cost = candidate["total_presentations"]-current_total
            key = (cost/gain, candidate["total_presentations"], donor)
            if best is None or key < best[0]:
                best = (key, donor, candidate)
        if best is None:
            raise RuntimeError(
                "ESS floor infeasible under supplied full-coverage/cap constraints"
            )
        mult[best[1]] += 1
        current = best[2]
        steps += 1
    return mult, current, steps


def build_result(
    *,
    metadata_sqlite_sha256: str,
    partition: str,
    groups: Sequence[Group],
    donor_n: Mapping[str, int],
    source_n: Mapping[str, int],
    population_cells: int,
    group_floor: int,
    cell_cap: int,
    ess_floor: float,
    weight_ratio_ceiling: float,
):
    states = compile_states(
        groups, donor_n, group_floor=group_floor, cell_cap=cell_cap
    )
    base = {donor: 1 for donor in donor_n}
    coverage = metrics(base, states, population_cells)
    smallest = min(donor_n.values())
    largest = max(donor_n.values())
    lower = full_coverage_weight_ratio_lower_bound(donor_n, cell_cap=cell_cap)
    minimum_cap = minimum_cell_cap_for_weight_ratio_ceiling(
        donor_n, weight_ratio_ceiling=weight_ratio_ceiling
    )
    mult, balanced, steps = greedy(states, population_cells, ess_floor)
    return {
        "schema": "JEPA_V5_FULL_POPULATION_COVERAGE_CONDITIONING_AUDIT_V1",
        "status": "DATASET_GEOMETRY_AUDIT__NO_TRAINING_AUTHORITY",
        "metadata_sqlite_sha256": metadata_sqlite_sha256,
        "partition": partition,
        "population_cells": population_cells,
        "donors": len(donor_n),
        "groups": len(groups),
        "sources": len(source_n),
        "constraints": {
            "minimum_group_presentations": group_floor,
            "max_presentations_per_cell": cell_cap,
            "minimum_importance_ess_fraction": ess_floor,
            "maximum_importance_weight_max_to_min_ratio": weight_ratio_ceiling,
        },
        "donor_size_extrema": {
            "minimum": smallest,
            "maximum": largest,
            "target_per_cell_probability_ratio": largest/smallest,
        },
        "full_coverage_feasibility": {
            "importance_weight_ratio_lower_bound_under_cell_cap": lower,
            "requested_weight_ratio_ceiling": weight_ratio_ceiling,
            "requested_ratio_ceiling_is_feasible_under_full_coverage_and_cell_cap": (
                weight_ratio_ceiling + 1e-15 >= lower
            ),
            "minimum_integer_cell_cap_for_requested_ratio_ceiling": minimum_cap,
        },
        "coverage_plus_group_topup_only": coverage,
        "greedy_donor_balanced_full_coverage_candidate": balanced,
        "greedy_steps": steps,
        "donor_multiplicity_histogram": {
            str(k): v
            for k, v in sorted(collections.Counter(mult.values()).items())
        },
        "all_cells_guaranteed_at_least_once": True,
        "interpretation": [
            "A population-equivalent with-replacement horizon is not proof of unique-cell coverage.",
            "Coverage plus rare-group top-up alone preserves target mass but fails the requested ESS conditioning floor.",
            "Any weight-ratio ceiling below the reported mathematical lower bound is incompatible with both guaranteed full coverage and the supplied cell cap.",
            "The greedy donor-balanced schedule is a deterministic dataset-only calibration candidate, not a proof of global optimality and not execution authority.",
        ],
        "training_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata-sqlite", type=Path, required=True)
    parser.add_argument("--expected-sqlite-sha256", required=True)
    parser.add_argument("--partition", required=True)
    parser.add_argument("--group-floor", type=int, required=True)
    parser.add_argument("--cell-cap", type=int, required=True)
    parser.add_argument("--ess-floor", type=float, required=True)
    parser.add_argument("--weight-ratio-ceiling", type=float, required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    args = parser.parse_args()
    if args.group_floor < 1 or args.cell_cap < 1:
        raise SystemExit("invalid explicit integer constraints")
    if not (0 < args.ess_floor <= 1):
        raise SystemExit("invalid explicit ESS floor")
    if not (
        math.isfinite(args.weight_ratio_ceiling)
        and args.weight_ratio_ceiling > 0
    ):
        raise SystemExit("invalid explicit weight-ratio ceiling")
    observed = sha256(args.metadata_sqlite)
    if observed.lower() != args.expected_sqlite_sha256.lower():
        raise SystemExit(f"metadata SHA mismatch: {observed}")
    groups, donor_n, source_n, population_cells = load_geometry(
        args.metadata_sqlite, args.partition
    )
    result = build_result(
        metadata_sqlite_sha256=observed,
        partition=args.partition,
        groups=groups,
        donor_n=donor_n,
        source_n=source_n,
        population_cells=population_cells,
        group_floor=args.group_floor,
        cell_cap=args.cell_cap,
        ess_floor=args.ess_floor,
        weight_ratio_ceiling=args.weight_ratio_ceiling,
    )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(
        json.dumps(result, indent=2, sort_keys=True)+"\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
