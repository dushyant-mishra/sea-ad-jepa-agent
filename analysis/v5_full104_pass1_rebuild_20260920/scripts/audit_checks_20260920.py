"""Independent audit checks for the FULL104 pass1 rebuild.

Run with the canonical interpreter from the scientific worktree root:

    python analysis/v5_full104_pass1_rebuild_20260920/scripts/audit_checks_20260920.py --check all

Checks
------
``parser``     adversarial cases for the exact-decimal ``source_library`` parser
``alignment``  necessary-condition diagnostic on metadata/matrix row correspondence
``indexing``   reproduces the September-17 block-position defect (needs that artifact)
``donors``     derives the canonical donor registry and compares to September-17

Result states
-------------
``PASS``            the check ran and satisfied its requirement
``FAIL``            the check ran and did not
``NOT_MEASURABLE``  required evidence was absent, so the check did not run

**A required check that is NOT_MEASURABLE makes the overall audit non-PASS.**
Missing evidence is never reported as success.

Nothing here opens a terminal masking outcome, target-panel ladder, margin,
D_shared, protected/pathology/DEV/SEALED data, or training.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

import numpy as np
import scipy.sparse as sp

PASS = "PASS"
FAIL = "FAIL"
NOT_MEASURABLE = "NOT_MEASURABLE"

L4_DEFAULT = Path(r"C:/jepa_full104_ssd/expression_level4")

#: Content-addressed September-17 artifact, retained ONLY so the indexing and
#: donor-comparison checks stay measurable. Status INVALID_FOR_CURRENT_ROLE; it
#: must never be used as a current input to anything.
SEPT17_PASS1_SHA256 = "0e99d12b9b74e3cc6ae95ab436effa84c9e71c461496258653022ae56d396811"
SEPT17_PASS1_DEFAULT = Path(
    r"D:/jepa_full104_preterminal_20260919_a51cdbe8_outputs/"
    r"historical_invalid_pass1_20260917/pass1_SEPT17_INVALID_FOR_CURRENT_ROLE.npz"
)

#: Authenticated materialization lineage. THIS is the primary reason metadata row
#: order corresponds to sparse matrix row order: both materializers construct the
#: matrix row and the metadata row from the same ordered ``take`` selection.
MATERIALIZER_LINEAGE = {
    "full104_block_manifest_sha256":
        "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29",
    "python_materializer_sha256":
        "575d02a4e7f7c5c6f3187eeed691a2eac7d3f1df9510621bc497b283806c270b",
    "nph_r_materializer_sha256":
        "ca595536f6144a1f6fb2570fe24f58c5335ba31e43a1f9a4b660e18db58e7529",
}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def _resolve_sept17(path: Path) -> tuple[Path | None, str]:
    if not path.is_file():
        return None, f"September-17 artifact absent at {path}"
    observed = _sha256(path)
    if observed != SEPT17_PASS1_SHA256:
        return None, f"September-17 artifact digest mismatch: {observed}"
    return path, ""


def check_parser() -> tuple[str, str]:
    """Accept integral decimals and scientific notation; reject everything else."""
    from sea_ad_jepa.v5.full104_physical_shakedown_v1 import _parse_source_library as P

    cases = [
        ("61129", 61129), ("61129.0", 61129), ("  61129.0  ", 61129),
        ("6.1129E4", 61129), ("6.1129E+4", 61129), ("61129.00000", 61129),
        ("1_000", None), ("0x10", None), ("0", None), ("0.0", None),
        ("-5", None), ("-61129.0", None), ("0.5", None), ("61129.5", None),
        ("1e-3", None), ("nan", None), ("NaN", None), ("inf", None),
        ("Infinity", None), ("-inf", None), ("", None), ("abc", None), (None, None),
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
    print("\n  mismatches:", bad)
    return (PASS, "") if bad == 0 else (FAIL, f"{bad} parser mismatches")


def check_alignment(level4_root: Path, blocks: int = 8) -> tuple[str, str]:
    """Necessary-condition diagnostic on metadata/matrix row correspondence.

    This is NOT a proof of row identity. The primary provenance is construction
    lineage: both authenticated materializers build the sparse matrix row and the
    metadata row from the same ordered ``take`` selection. The Python/H5 path
    writes sparse row ``local`` and metadata row ``local``; the NPH R path builds
    matrix rows from ``columns[take]`` and metadata from ``requested[take]``. The
    authenticated materialization manifest binds those code hashes to the Level-4
    package.

    What this adds is an adversarial consistency test: a row's summed raw counts
    cannot exceed that row's ``source_library``. As-built data satisfies it; a
    deliberate shuffle violates it. Satisfying a necessary condition does not
    establish identity -- but failing it would refute the correspondence, and the
    shuffle control shows the test has power to detect misalignment.
    """
    print("  primary provenance (construction lineage):")
    for key, value in MATERIALIZER_LINEAGE.items():
        print("    %-34s %s" % (key, value))
    print("  the runtime check below is a NECESSARY-CONDITION diagnostic, not a proof\n")

    from sea_ad_jepa.v5.full104_physical_shakedown_v1 import _parse_source_library

    manifest = level4_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv"
    if not manifest.is_file():
        return NOT_MEASURABLE, f"Level-4 manifest absent at {manifest}"

    rows = list(csv.DictReader(manifest.open(newline="")))
    aligned = shuffled = 0
    for row in rows[:blocks]:
        matrix = sp.load_npz(level4_root / row["counts_path"]).tocsr()
        meta = list(csv.DictReader((level4_root / row["meta_path"]).open(newline="")))
        # exact positive-integral parser, never loose float()
        library = np.array(
            [_parse_source_library(m["source_library"], row["block_key"]) for m in meta],
            dtype=np.int64,
        )
        row_sums = np.asarray(matrix.sum(axis=1)).ravel()
        perm = np.random.default_rng(0).permutation(library.size)
        a = int((row_sums > library).sum())
        s = int((row_sums > library[perm]).sum())
        aligned += a
        shuffled += s
        print("  %-20s rows=%-6d aligned_violations=%-4d shuffled_violations=%d"
              % (row["block_key"], matrix.shape[0], a, s))
    print("\n  TOTAL aligned=%d  shuffled=%d" % (aligned, shuffled))
    if aligned != 0:
        return FAIL, f"{aligned} violations under the as-built correspondence"
    if shuffled == 0:
        return NOT_MEASURABLE, "shuffle control produced no violations; test lacks power here"
    return PASS, ""


def check_indexing(level4_root: Path, sept17: Path, blocks: int = 12) -> tuple[str, str]:
    """Reproduce the September-17 defect: cells keyed to block iteration position."""
    path, why = _resolve_sept17(sept17)
    if path is None:
        print("  " + why)
        return NOT_MEASURABLE, why

    data = np.load(path, allow_pickle=True)
    cell_donor = data["cell_donor"]
    duniq = [str(x) for x in data["duniq"]]
    code_of = {name: index for index, name in enumerate(duniq)}
    rows = list(
        csv.DictReader((level4_root / "PHASE2_EXPRESSION_BLOCK_MANIFEST.csv").open(newline=""))
    )
    by_selection = by_position = 0
    position = 0
    for row in rows[:blocks]:
        meta = list(csv.DictReader((level4_root / row["meta_path"]).open(newline="")))
        selection = np.array([int(m["selection_row"]) for m in meta])
        donor_codes = np.array([code_of[str(m["donor_id"])] for m in meta])
        n = len(meta)
        by_selection += int(np.array_equal(cell_donor[selection], donor_codes))
        by_position += int(np.array_equal(cell_donor[position:position + n], donor_codes))
        position += n
    first = list(csv.DictReader((level4_root / rows[0]["meta_path"]).open(newline="")))
    print("  blocks checked                      :", blocks)
    print("  match when indexed by selection_row :", by_selection)
    print("  match when indexed by block position:", by_position)
    print("  block 0 first selection_rows        :", [int(m["selection_row"]) for m in first[:6]])
    if by_selection == 0 and by_position == blocks:
        return PASS, ""
    return FAIL, f"expected 0/{blocks} by selection_row and {blocks}/{blocks} by position"


def check_donors(level4_root: Path, sept17: Path) -> tuple[str, str]:
    """Canonical donor registry, and comparison to the September-17 ordering."""
    from sea_ad_jepa.v5.full104_pass1_builder_v1 import (
        DONOR_ORDER_RULE,
        derive_canonical_donor_registry,
    )

    duniq, donor_src = derive_canonical_donor_registry(level4_root, expect_hashes=True)
    duniq = [str(x) for x in duniq]
    print("  rule                  :", DONOR_ORDER_RULE)
    print("  donors                :", len(duniq), " unique:", len(set(duniq)))
    print("  equals sorted(unique) :", duniq == sorted(set(duniq)))
    print("  source counts         :",
          {int(c): int((donor_src == c).sum()) for c in np.unique(donor_src)})
    if duniq != sorted(set(duniq)) or len(set(duniq)) != len(duniq):
        return FAIL, "derived registry is not a sorted unique donor list"

    path, why = _resolve_sept17(sept17)
    if path is None:
        print("  " + why)
        return NOT_MEASURABLE, "September-17 comparison not performed: " + why

    old = np.load(path, allow_pickle=True)
    old_duniq = [str(x) for x in old["duniq"]]
    old_src = np.asarray(old["donor_src"], dtype=np.int64)
    same_order = old_duniq == duniq
    same_source = bool(np.array_equal(old_src, donor_src))
    print("  IDENTICAL order to Sept-17:", same_order)
    print("  donor_src identical       :", same_source)
    return (PASS, "") if (same_order and same_source) else (FAIL, "donor registry drifted")


REQUIRED = ("parser", "alignment", "indexing", "donors")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", choices=(*REQUIRED, "all"), default="all")
    parser.add_argument("--level4-root", type=Path, default=L4_DEFAULT)
    parser.add_argument("--sept17-pass1", type=Path, default=SEPT17_PASS1_DEFAULT)
    args = parser.parse_args()

    selected = REQUIRED if args.check == "all" else (args.check,)
    results: dict[str, tuple[str, str]] = {}
    for name in selected:
        print("=" * 78)
        print(name.upper())
        print("=" * 78)
        if name == "parser":
            results[name] = check_parser()
        elif name == "alignment":
            results[name] = check_alignment(args.level4_root)
        elif name == "indexing":
            results[name] = check_indexing(args.level4_root, args.sept17_pass1)
        else:
            results[name] = check_donors(args.level4_root, args.sept17_pass1)
        print()

    print("=" * 78)
    print("SUMMARY")
    print("=" * 78)
    for name in selected:
        state, detail = results[name]
        print("  %-12s %-16s %s" % (name, state, detail))

    failed = [n for n, (s, _) in results.items() if s == FAIL]
    unmeasured = [n for n, (s, _) in results.items() if s == NOT_MEASURABLE]
    overall = PASS if not failed and not unmeasured else "NON_PASS"
    print("\n  failed         :", failed or "none")
    print("  not measurable :", unmeasured or "none")
    print("  OVERALL        :", overall)
    if unmeasured and not failed:
        print("\n  A required check could not run. Missing evidence is NOT a pass.")
    return 0 if overall == PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
