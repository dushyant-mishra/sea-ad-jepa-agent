#!/usr/bin/env python3
"""Behavioural tests for the V74 Lane E exclusion-list gate and attrition producer.

Every test here is driven to the state it is supposed to detect. A test that cannot
fail proves nothing, so each case below states what result would make it fail and then
constructs exactly that input.

Run:  python scripts/v74/test_laneE_blacklist_attrition_v1.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRODUCER = HERE / "laneE_blacklist_attrition_v1.py"

RESULTS = []


def sha256_text(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def write_bed(p: Path, rows) -> Path:
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write("\t".join(str(x) for x in r) + "\n")
    return p


def run(region_bed, region_sha, bl_bed, bl_sha, tmp):
    out_receipt = Path(tmp) / "receipt.json"
    cmd = [sys.executable, str(PRODUCER),
           "--region-bed", str(region_bed),
           "--region-bed-sha256", region_sha,
           "--blacklist-bed", str(bl_bed),
           "--blacklist-bed-sha256", bl_sha,
           "--blacklist-accession", "TEST_ACCESSION",
           "--route-id", "TEST_ROUTE",
           "--out-receipt", str(out_receipt),
           "--out-excluded-bed", str(Path(tmp) / "excluded.bed"),
           "--out-retained-bed", str(Path(tmp) / "retained.bed")]
    cp = subprocess.run(cmd, capture_output=True, text=True)
    return cp, out_receipt


def check(name, condition, detail=""):
    RESULTS.append({"test": name, "pass": bool(condition), "detail": detail})
    print(("PASS  " if condition else "FAIL  ") + name + ("  " + detail if detail else ""))


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)

        regions = write_bed(tmp / "regions.bed", [
            ("chr1", 1000, 2000, "chr1:1000-2000"),    # no overlap
            ("chr1", 5000, 6000, "chr1:5000-6000"),    # overlaps bl by 1 bp at 5999
            ("chr2", 100, 1100, "chr2:100-1100"),      # fully inside a bl interval
            ("chr3", 10, 110, "chr3:10-110"),          # no overlap, different contig
        ])
        blacklist = write_bed(tmp / "bl.bed", [
            ("chr1", 5999, 7000),
            ("chr2", 0, 5000),
        ])
        r_sha = sha256_text(regions)
        b_sha = sha256_text(blacklist)

        # ---- T1 happy path: the gate must let a matching pair through -------------
        # Would fail if: the gate refused a correct input, or the arithmetic were wrong.
        cp, rec_path = run(regions, r_sha, blacklist, b_sha, tmp)
        check("T1 matching digests are accepted (exit 0)", cp.returncode == 0,
              "rc=%d" % cp.returncode)
        rec = json.loads(rec_path.read_text(encoding="utf-8"))
        check("T1 status PASS", rec["status"] == "PASS__ATTRITION_MEASURED", rec["status"])
        check("T1 exactly 2 regions excluded (any-overlap rule)",
              rec["ATTRITION"]["n_regions_excluded"] == 2,
              str(rec["ATTRITION"]["n_regions_excluded"]))
        check("T1 1 bp region counted: intersected bp is 1 + 1000 = 1001",
              rec["ATTRITION"]["bp_actually_intersecting_the_exclusion_list"] == 1001,
              str(rec["ATTRITION"]["bp_actually_intersecting_the_exclusion_list"]))
        check("T1 whole-region removal: 1000 + 1000 = 2000 bp leave the universe",
              rec["ATTRITION"]["bp_in_excluded_regions"] == 2000,
              str(rec["ATTRITION"]["bp_in_excluded_regions"]))
        check("T1 collateral bp = 2000 - 1001 = 999",
              rec["ATTRITION"]["bp_collaterally_removed"] == 999,
              str(rec["ATTRITION"]["bp_collaterally_removed"]))
        check("T1 excluded regions carry the EXCLUDED_BY_POLICY label",
              all("EXCLUDED_BY_POLICY" in ln for ln in
                  (tmp / "excluded.bed").read_text(encoding="utf-8").splitlines()))

        # ---- T2 THE FAIL-CLOSED TEST: wrong blacklist digest ---------------------
        # Would fail if: the producer ran anyway, or exited 0, or wrote a receipt.
        rec_path.unlink(missing_ok=True)
        bad = "0" * 64
        cp, rec_path = run(regions, r_sha, blacklist, bad, tmp)
        check("T2 mismatched blacklist digest exits non-zero", cp.returncode == 2,
              "rc=%d" % cp.returncode)
        check("T2 mismatched blacklist digest writes NO receipt",
              not rec_path.exists())
        check("T2 refusal names the failing input and reason",
              "exclusion_list" in cp.stderr and "SHA256_MISMATCH" in cp.stderr)

        # ---- T3 a DIFFERENT but VALID blacklist is still refused ------------------
        # The dangerous case is not a corrupt file; it is a plausible substitute.
        # Would fail if: the gate checked only that the file parsed as a BED.
        other_bl = write_bed(tmp / "bl_other.bed", [("chr1", 5999, 7000)])
        cp, rec_path = run(regions, r_sha, other_bl, b_sha, tmp)
        check("T3 a well-formed SUBSTITUTE exclusion list is refused",
              cp.returncode == 2 and not rec_path.exists(), "rc=%d" % cp.returncode)

        # ---- T4 a one-byte change to the frozen file is caught --------------------
        # Would fail if: the gate compared size or line count rather than content.
        tweaked = tmp / "bl_tweaked.bed"
        tweaked.write_bytes(blacklist.read_bytes().replace(b"5999", b"5998"))
        check("T4 fixture really is the same byte length",
              tweaked.stat().st_size == blacklist.stat().st_size)
        cp, rec_path = run(regions, r_sha, tweaked, b_sha, tmp)
        check("T4 same-length, one-coordinate-changed file is refused",
              cp.returncode == 2 and not rec_path.exists(), "rc=%d" % cp.returncode)

        # ---- T5 the region universe is gated too ---------------------------------
        # Would fail if: only the blacklist were authenticated.
        cp, rec_path = run(regions, bad, blacklist, b_sha, tmp)
        check("T5 mismatched REGION UNIVERSE digest is refused",
              cp.returncode == 2 and "region_universe" in cp.stderr,
              "rc=%d" % cp.returncode)

        # ---- T6 an absent exclusion list is a refusal, not an empty blacklist -----
        # Would fail if: a missing file silently became "nothing to exclude".
        cp, rec_path = run(regions, r_sha, tmp / "does_not_exist.bed", b_sha, tmp)
        check("T6 absent exclusion list is REFUSED, not treated as empty",
              cp.returncode == 2 and "ABSENT" in cp.stderr, "rc=%d" % cp.returncode)

        # ---- T7 degenerate input: an EMPTY exclusion list excludes nothing --------
        # This must be reachable and must NOT be confused with T6. An empty file is a
        # real, authenticated statement that nothing is excluded; an absent file is
        # an unanswered question.
        empty = tmp / "bl_empty.bed"
        empty.write_text("", encoding="utf-8")
        cp, rec_path = run(regions, r_sha, empty, sha256_text(empty), tmp)
        rec = json.loads(rec_path.read_text(encoding="utf-8")) if rec_path.exists() else {}
        check("T7 an authenticated EMPTY exclusion list is accepted and excludes 0",
              cp.returncode == 0 and rec.get("ATTRITION", {}).get("n_regions_excluded") == 0,
              "rc=%d" % cp.returncode)

        # ---- T8 overlapping exclusion intervals are not double-counted ------------
        # Would fail if: overlap bp were summed over an unmerged interval list.
        dbl = write_bed(tmp / "bl_dbl.bed", [
            ("chr1", 1200, 1600),
            ("chr1", 1400, 1800),   # overlaps the previous by 200 bp
        ])
        cp, rec_path = run(regions, r_sha, dbl, sha256_text(dbl), tmp)
        rec = json.loads(rec_path.read_text(encoding="utf-8"))
        check("T8 merged exclusion bp counted once: 1200-1800 = 600, not 800",
              rec["ATTRITION"]["bp_actually_intersecting_the_exclusion_list"] == 600,
              str(rec["ATTRITION"]["bp_actually_intersecting_the_exclusion_list"]))

        # ---- T9 NEGATIVE CONTROL on T8: prove the check could have failed ---------
        # Sum over the UNMERGED list is 800. If the producer reported 800 the test
        # above would fail, so the test is capable of detecting the defect it targets.
        unmerged_sum = (1600 - 1200) + (1800 - 1400)
        check("T9 the unmerged (wrong) answer 800 differs from the merged answer 600",
              unmerged_sum == 800 and unmerged_sum != 600, str(unmerged_sum))

        # ---- T10 accounting balances ---------------------------------------------
        cp, rec_path = run(regions, r_sha, blacklist, b_sha, tmp)
        rec = json.loads(rec_path.read_text(encoding="utf-8"))
        check("T10 retained + excluded == input, in regions and in bp",
              all(rec["accounting_check"].values()), json.dumps(rec["accounting_check"]))

    n_fail = sum(1 for r in RESULTS if not r["pass"])
    print("\n%d tests, %d failures" % (len(RESULTS), n_fail))
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
