"""Independent audit checks run during the 2026-09-20 pass1 rebuild.

Each check is standalone and read-only. Run with the canonical `sea-ad-jepa`
interpreter from the scientific worktree root:

    python analysis/v5_full104_pass1_rebuild_20260920/scripts/audit_checks_20260920.py --check all

Checks
------
``parser``     adversarial cases for the PR #29 exact-decimal source_library parser
``alignment``  proves metadata CSV row order equals sparse matrix row order
``indexing``   proves the September-17 pass1 was keyed to block position
``donors``     derives the canonical donor registry and compares to September-17

Nothing here opens a terminal masking outcome, D_shared, protected/pathology/
DEV/SEALED data, or training.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
import scipy.sparse as sp

L4_DEFAULT = Path(r"C:/jepa_full104_ssd/expression_level4")
SEPT17_PASS1 = Path(
    r"C:/Users/dushy/AppData/Local/Temp/claude/d--Jepa-project/"
    r"cdf819f6-5db4-4119-9a97-37fef1d27909/scratchpad/census/pass1.npz"
)


def check_parser() -> int:
    """PR #29 _parse_source_library: accept integral decimals, reject the rest."""
    from sea_ad_jepa.v5.full104_physical_shakedown_v1 import _parse_source_library as P

    cases = [
        ("61129", 61129), ("61129.0", 61129), ("  61129.0  ", 61129),
        ("6.1129E+4", 61129), ("61129.00000", 61129),
        ("0", None), ("0.0", None), ("-5", None), ("-61129.0", None),
        ("0.5", None), ("61129.5", None), ("1e-3", None),
        ("nan", None), ("NaN", None), ("inf", None), ("Infinity", None),
        ("-inf", None), ("", None), ("abc", None), ("0x10", None), (None, None),
    ]
    bad = 0
    for raw, expected in cases:
        try:
            got = P(raw, "blk")
        except ValueError:
            got = None
        ok = got == expected
        bad += 0 if ok else 1
        print("  %-16r expected=%-8s got=%-8s %s"
              % (raw, expected, got, "" if ok else "*** MISMATCH ***"))
    # Decimal accepts Python underscore separators; a correct integer reading.
    print("  %-16r -> %s  (underscore separators; benign)" % ("1_000", P("1_000", "blk")))
    print("\n  mismatches:", bad)
    return bad


def check_alignment(level4_root: Path, blocks: int = 8) -> int:
    """Metadata CSV row order must equal sparse matrix row order.

    Invariant: a cell's summed raw counts cannot exceed its source_library.
    Aligned -> 0 violations; deliberately shuffled -> many.
    """
    rows = list(csv.DictReader((level4_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv").open(newline="")))
    aligned = shuffled = 0
    for r in rows[:blocks]:
        m = sp.load_npz(level4_root / r["counts_path"]).tocsr()
        md = list(csv.DictReader((level4_root / r["meta_path"]).open(newline="")))
        lib = np.array([float(x["source_library"]) for x in md], dtype=np.float64)
        rs = np.asarray(m.sum(axis=1)).ravel()
        perm = np.random.default_rng(0).permutation(lib.size)
        a, s = int((rs > lib).sum()), int((rs > lib[perm]).sum())
        aligned += a
        shuffled += s
        print("  %-20s rows=%-6d aligned_violations=%-4d shuffled_violations=%d"
              % (r["block_key"], m.shape[0], a, s))
    print("\n  TOTAL aligned=%d  shuffled=%d" % (aligned, shuffled))
    print("  -> aligned==0 and shuffled>0 means CSV order IS matrix row order")
    return 0 if (aligned == 0 and shuffled > 0) else 1


def check_indexing(level4_root: Path, pass1: Path, blocks: int = 12) -> int:
    """Show the September-17 pass1 was keyed to block position, not selection_row."""
    if not pass1.is_file():
        print("  September-17 pass1 not present at", pass1)
        return 0
    d = np.load(pass1, allow_pickle=True)
    cell_donor = d["cell_donor"]
    duniq = [str(x) for x in d["duniq"]]
    d2c = {x: i for i, x in enumerate(duniq)}
    rows = list(csv.DictReader((level4_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv").open(newline="")))
    by_selection = by_position = 0
    pos = 0
    for r in rows[:blocks]:
        md = list(csv.DictReader((level4_root / r["meta_path"]).open(newline="")))
        sel = np.array([int(m["selection_row"]) for m in md])
        dc = np.array([d2c[str(m["donor_id"])] for m in md])
        n = len(md)
        by_selection += int(np.array_equal(cell_donor[sel], dc))
        by_position += int(np.array_equal(cell_donor[pos:pos + n], dc))
        pos += n
    print("  blocks checked                      :", blocks)
    print("  match when indexed by selection_row :", by_selection)
    print("  match when indexed by block position:", by_position)
    md0 = list(csv.DictReader((level4_root / rows[0]["meta_path"]).open(newline="")))
    print("  block 0 first selection_rows        :", [int(m["selection_row"]) for m in md0[:6]])
    return 0 if (by_selection == 0 and by_position == blocks) else 1


def check_donors(level4_root: Path, pass1: Path) -> int:
    """Canonical donor registry, and comparison to the September-17 ordering."""
    from sea_ad_jepa.v5.full104_pass1_builder_v1 import (
        DONOR_ORDER_RULE, derive_canonical_donor_registry,
    )

    duniq, donor_src = derive_canonical_donor_registry(level4_root, expect_hashes=True)
    duniq = [str(x) for x in duniq]
    print("  rule                  :", DONOR_ORDER_RULE)
    print("  donors                :", len(duniq), " unique:", len(set(duniq)))
    print("  equals sorted(unique) :", duniq == sorted(set(duniq)))
    print("  source counts         :", {int(c): int((donor_src == c).sum()) for c in np.unique(donor_src)})
    if not pass1.is_file():
        print("  September-17 pass1 not present; skipping comparison")
        return 0
    old = np.load(pass1, allow_pickle=True)
    old_duniq = [str(x) for x in old["duniq"]]
    old_src = np.asarray(old["donor_src"], dtype=np.int64)
    print("  IDENTICAL order to Sept-17:", old_duniq == duniq)
    print("  donor_src identical       :", bool(np.array_equal(old_src, donor_src)))
    return 0 if (old_duniq == duniq and np.array_equal(old_src, donor_src)) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", choices=("parser", "alignment", "indexing", "donors", "all"),
                    default="all")
    ap.add_argument("--level4-root", type=Path, default=L4_DEFAULT)
    ap.add_argument("--sept17-pass1", type=Path, default=SEPT17_PASS1)
    args = ap.parse_args()

    failures = 0
    order = ("parser", "alignment", "indexing", "donors")
    for name in (order if args.check == "all" else (args.check,)):
        print("=" * 78)
        print(name.upper())
        print("=" * 78)
        if name == "parser":
            failures += check_parser()
        elif name == "alignment":
            failures += check_alignment(args.level4_root)
        elif name == "indexing":
            failures += check_indexing(args.level4_root, args.sept17_pass1)
        else:
            failures += check_donors(args.level4_root, args.sept17_pass1)
        print()
    print("FAILURES:", failures)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
