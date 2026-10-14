"""Outcome-blind population/support audit for the TD real lane (metadata only).

Reads only hash-pinned metadata, split and operator-address observation-state
artifacts.  No expression value, candidate output, pathology field or
DEV/SEALED object is opened.  Every table is a count/occupancy summary.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

PINNED = {
    "metadata_sqlite": ("metadata/foundation_metadata_rows.sqlite",
                        "a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913"),
    "reader_split": ("splits/reader_donor_split.csv",
                     "efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511"),
    "operator_address_state": ("support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz",
                               "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537"),
}
EXPECTED = {"rows": 6_351_753, "donors": 149, "operators": 42, "sources": 3,
            "donor_operator_strata": 2_028, "partitions": {"reader_fit": 104,
            "reader_validation": 22, "reader_oracle": 23}}
FAMILY_ALPHA = 0.01  # td_real_directional_gate_executors_v2.py default family alpha
STATE_NAMES = {0: "STRUCTURALLY_UNMEASURED", 1: "MEASURED_SCALAR", 2: "MEASURED_COLLISION_UNRESOLVED"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def min_sign_test_donors(alpha_eff: float) -> int:
    """Smallest n with 0.5**n <= alpha_eff (exact one-sided sign test, all n donors positive)."""
    return max(1, math.ceil(math.log2(1.0 / alpha_eff) - 1e-12))


def max_resolvable_family(n: int, alpha: float = FAMILY_ALPHA) -> int:
    """Largest Bonferroni family size m with 0.5**n <= alpha/m."""
    return int(math.floor(alpha * (2 ** n) + 1e-12)) if n > 0 else 0


def write_csv(path: Path, header: list[str], rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def quantiles(values: list[int]) -> list:
    if not values:
        return ["", "", "", ""]
    a = np.asarray(sorted(values))
    return [int(a.min()), float(np.quantile(a, 0.1)), float(np.median(a)), int(a.max())]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    bundle, out = Path(args.bundle), Path(args.out)
    inputs = {}
    for key, (rel, expected) in PINNED.items():
        got = sha256(bundle / rel)
        if got != expected:
            raise SystemExit(f"input hash mismatch: {key}")
        inputs[key] = {"path": rel, "sha256": got, "bytes": (bundle / rel).stat().st_size}

    split = {}
    with (bundle / PINNED["reader_split"][0]).open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["donor_id"] in split:
                raise SystemExit("duplicate split donor")
            split[row["donor_id"]] = row["reader_partition"]

    con = sqlite3.connect(f"file:{(bundle / PINNED['metadata_sqlite'][0]).as_posix()}?mode=ro&immutable=1", uri=True)
    q = ("select donor_id, partition, source, operator_index, matrix_id, broad_class, native_class, count(*) "
         "from cells group by donor_id, partition, source, operator_index, matrix_id, broad_class, native_class")
    agg = con.execute(q).fetchall()
    con.close()

    total = sum(r[-1] for r in agg)
    donor_part, donor_src = defaultdict(set), defaultdict(set)
    dxo = Counter()
    op_meta = {}
    cls = {"broad_class": Counter(), "native_class": Counter()}
    for donor, part, src, op, mid, broad, native, n in agg:
        donor_part[donor].add(part)
        donor_src[donor].add(src)
        dxo[(donor, part, src, op, mid)] += n
        prev = op_meta.setdefault(op, (mid, src))
        if prev != (mid, src):
            raise SystemExit("operator identity not unique")
        cls["broad_class"][(donor, part, src, broad)] += n
        cls["native_class"][(donor, part, src, native)] += n

    # identity closure checks against the frozen split and expected population
    if any(len(v) != 1 for v in donor_part.values()) or any(len(v) != 1 for v in donor_src.values()):
        raise SystemExit("donor spans multiple partitions or sources")
    donor_partition = {d: next(iter(v)) for d, v in donor_part.items()}
    donor_source = {d: next(iter(v)) for d, v in donor_src.items()}
    if donor_partition != split:
        raise SystemExit("sqlite partition disagrees with frozen split")
    part_counts = Counter(donor_partition.values())
    checks = {
        "rows": total == EXPECTED["rows"],
        "donors": len(donor_partition) == EXPECTED["donors"],
        "operators": len(op_meta) == EXPECTED["operators"],
        "sources": len(set(donor_source.values())) == EXPECTED["sources"],
        "donor_operator_strata": len(dxo) == EXPECTED["donor_operator_strata"],
        "partitions": dict(part_counts) == EXPECTED["partitions"],
    }
    if not all(checks.values()):
        raise SystemExit(f"population drift: {checks}")

    # donor table
    donor_cells, donor_ops = Counter(), defaultdict(set)
    for (donor, part, src, op, mid), n in dxo.items():
        donor_cells[donor] += n
        donor_ops[donor].add(op)
    write_csv(out / "population/DONOR.csv",
              ["donor_id", "reader_partition", "source", "n_operators", "n_cells"],
              sorted([d, donor_partition[d], donor_source[d], len(donor_ops[d]), donor_cells[d]] for d in donor_cells))
    write_csv(out / "population/DONOR_X_OPERATOR.csv",
              ["donor_id", "reader_partition", "source", "operator_index", "matrix_id", "n_cells"],
              sorted([*k, n] for k, n in dxo.items()))

    # operator table
    op_rows = []
    op_part_donors = defaultdict(lambda: defaultdict(set))
    op_part_cells = defaultdict(Counter)
    for (donor, part, src, op, mid), n in dxo.items():
        op_part_donors[op][part].add(donor)
        op_part_cells[op][part] += n
    parts = ["reader_fit", "reader_validation", "reader_oracle"]
    for op in sorted(op_meta):
        mid, src = op_meta[op]
        nd = [len(op_part_donors[op][p]) for p in parts]
        nc = [op_part_cells[op][p] for p in parts]
        op_rows.append([op, mid, src, *nd, *nc, sum(1 for x in nd if x), sum(nd)])
    write_csv(out / "population/OPERATOR.csv",
              ["operator_index", "matrix_id", "source", *[f"donors_{p}" for p in parts],
               *[f"cells_{p}" for p in parts], "partitions_spanned", "donors_total"], op_rows)

    # source x partition
    sp_rows = []
    for src in sorted(set(donor_source.values())):
        for p in parts:
            ds = [d for d in donor_partition if donor_partition[d] == p and donor_source[d] == src]
            ops = {op for (d, pp, s, op, mid) in dxo if pp == p and s == src}
            n = len(ds)
            sp_rows.append([src, p, n, sum(donor_cells[d] for d in ds), len(ops),
                            *quantiles([donor_cells[d] for d in ds]), max_resolvable_family(n)])
    write_csv(out / "population/SOURCE_X_PARTITION.csv",
              ["source", "reader_partition", "n_donors", "n_cells", "n_operators",
               "cells_per_donor_min", "cells_per_donor_q10", "cells_per_donor_median", "cells_per_donor_max",
               "max_bonferroni_family_resolvable_at_alpha_0.01_exact_sign_test"], sp_rows)

    # cell-class strata (rare/sparse); >=3 cells is the structural minimum for an anchored triplet
    for key in ("broad_class", "native_class"):
        per = defaultdict(lambda: defaultdict(list))
        for (donor, part, src, c), n in cls[key].items():
            per[(c, part, src)]["cells"].append(n)
        rows = []
        for (c, part, src), v in sorted(per.items(), key=lambda kv: tuple(str(x) for x in kv[0])):
            cells = v["cells"]
            n1 = len(cells)
            n3 = sum(1 for x in cells if x >= 3)
            rows.append([c, part, src, n1, n3, sum(cells), *quantiles(cells),
                         max_resolvable_family(n1), max_resolvable_family(n3)])
        write_csv(out / f"population/{key.upper()}_X_PARTITION_X_SOURCE.csv",
                  [key, "reader_partition", "source", "n_donors_ge1_cell", "n_donors_ge3_cells", "n_cells",
                   "cells_per_present_donor_min", "q10", "median", "max",
                   "max_family_resolvable_donors_ge1", "max_family_resolvable_donors_ge3"], rows)

    # operator-address structural support
    z = np.load(bundle / PINNED["operator_address_state"][0], allow_pickle=False)
    states, mids, opidx = z["states"], [str(x) for x in z["matrix_id"]], z["operator_index"].tolist()
    if states.shape != (42, 41238) or any(op_meta[o][0] != m for o, m in zip(opidx, mids)):
        raise SystemExit("observation-state operator identity mismatch")
    st_rows = []
    for i, op in enumerate(opidx):
        c = Counter(states[i].tolist())
        st_rows.append([op, mids[i], op_meta[op][1], c.get(1, 0), c.get(0, 0), c.get(2, 0)])
    write_csv(out / "support/OPERATOR_ADDRESS_STATE_COUNTS.csv",
              ["operator_index", "matrix_id", "source", "MEASURED_SCALAR", "STRUCTURALLY_UNMEASURED",
               "MEASURED_COLLISION_UNRESOLVED"], st_rows)
    scalar = states == 1
    support_summary = {}
    groups = {"all_operators": list(range(42))}
    for src in sorted(set(donor_source.values())):
        groups[f"source={src}"] = [i for i, op in enumerate(opidx) if op_meta[op][1] == src]
    for p in parts:
        groups[f"partition={p}"] = [i for i, op in enumerate(opidx) if op_part_donors[op][p]]
    for g, idx in groups.items():
        sub = scalar[idx]
        support_summary[g] = {
            "n_operators": len(idx),
            "addresses_scalar_in_any": int(sub.any(0).sum()),
            "addresses_scalar_in_all": int(sub.all(0).sum()),
            "addresses_never_scalar": int((~sub.any(0)).sum()),
        }
    src_any = {s: scalar[[i for i, op in enumerate(opidx) if op_meta[op][1] == s]].any(0)
               for s in sorted(set(donor_source.values()))}
    stack = np.vstack(list(src_any.values()))
    support_summary["addresses_scalar_in_exactly_k_sources"] = {
        str(k): int((stack.sum(0) == k).sum()) for k in range(len(src_any) + 1)}
    for s in src_any:
        others = np.vstack([v for t, v in src_any.items() if t != s]).any(0)
        support_summary[f"addresses_scalar_only_in_source={s}"] = int((src_any[s] & ~others).sum())
    fit_any = scalar[groups["partition=reader_fit"]].any(0)
    for p in ("reader_validation", "reader_oracle"):
        held_any = scalar[groups[f"partition={p}"]].any(0)
        support_summary[f"addresses_scalar_in_reader_fit_but_never_in_{p}"] = int((fit_any & ~held_any).sum())
        support_summary[f"addresses_scalar_in_{p}_but_never_in_reader_fit"] = int((held_any & ~fit_any).sum())
    per_addr_ops = scalar.sum(0)
    support_summary["operators_measuring_address_histogram"] = {
        str(k): int((per_addr_ops == k).sum()) for k in range(43) if (per_addr_ops == k).any()}

    # crossing structure
    op_donors = defaultdict(set)
    for (donor, part, src, op, mid) in dxo:
        op_donors[op].add(donor)
    crossing = {
        "donors_spanning_multiple_sources": sum(1 for v in donor_src.values() if len(v) > 1),
        "donors_spanning_multiple_partitions": sum(1 for v in donor_part.values() if len(v) > 1),
        "operators_spanning_multiple_partitions": sum(1 for r in op_rows if r[-2] > 1),
        "operators_single_partition": sum(1 for r in op_rows if r[-2] == 1),
        "operators_with_single_donor": sum(1 for v in op_donors.values() if len(v) == 1),
        "operators_donor_count_histogram": dict(sorted(Counter(len(v) for v in op_donors.values()).items())),
        "donors_with_single_operator": sum(1 for v in donor_ops.values() if len(v) == 1),
        "donor_operator_count_histogram": dict(sorted(Counter(len(v) for v in donor_ops.values()).items())),
    }

    resolution = {
        "family_alpha": FAMILY_ALPHA,
        "test": "exact one-sided donor sign test; minimum n with 0.5**n <= alpha/m",
        "min_donors_by_bonferroni_family_size": {str(m): min_sign_test_donors(FAMILY_ALPHA / m) for m in (1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 30)},
        "note": "gate-specific family sizes are not all frozen; this table is the resolution function, not a gate decision",
    }
    receipt = {
        "schema": "JEPA_TD_REAL_POPULATION_SUPPORT_AUDIT_V1",
        "scope": "OUTCOME_BLIND_SUPPORT_MAPPING__METADATA_ONLY",
        "inputs": inputs,
        "identity_checks": checks,
        "partition_donor_counts": dict(part_counts),
        "crossing": crossing,
        "structural_support": support_summary,
        "inferential_resolution": resolution,
        "expression_values_opened": False,
        "candidate_outcomes_opened": False,
        "pathology_opened": False,
        "dev_sealed_opened": False,
        "authority": "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED",
    }
    (out / "POPULATION_SUPPORT_AUDIT_RECEIPT_V1.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
