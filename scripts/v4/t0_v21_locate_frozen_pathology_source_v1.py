#!/usr/bin/env python3
"""Find the pathology source that reproduces V20's frozen digest.

`t0_stage2b_discovery_at8_v1._raw_digest` hashes raw bytes with no line-ending
normalization, and this repository checks text out with CRLF on Windows. The
obvious candidate hashes to 20c444d0..., not the frozen ebbe9bc0..., so either a
different copy is the authority or the checkout differs from what V20 read by
line endings alone.

This reports digests only. No endpoint column is parsed and no AT8 value is read.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

FROZEN = "ebbe9bc0c623c663331425794bd8fb1b4c4f3657455cf55d806cc383ea6d8e3a"

CANDIDATES = [
    Path("D:/Jepa project/data/raw/metadata/"
         "sea-ad_all_mtg_quant_neuropath_bydonorid_081122.csv"),
    Path("D:/Jepa project/data/processed/metadata/"
         "sea_ad_mtg_donor_pathology_targets.csv"),
    Path("D:/jepa_t0_mat_20260908/data/raw/metadata/"
         "sea-ad_all_mtg_quant_neuropath_bydonorid_081122.csv"),
]


def digests(path: Path) -> dict[str, str]:
    payload = path.read_bytes()
    return {
        "raw": hashlib.sha256(payload).hexdigest(),
        "lf": hashlib.sha256(payload.replace(b"\r\n", b"\n")).hexdigest(),
        "crlf": hashlib.sha256(
            payload.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")).hexdigest(),
        "bytes": str(len(payload)),
    }


def main() -> int:
    print("frozen identity: %s\n" % FROZEN)
    for path in CANDIDATES:
        if not path.is_file():
            print("  MISSING  %s" % path)
            continue
        d = digests(path)
        hit = next((k for k in ("raw", "lf", "crlf") if d[k] == FROZEN), None)
        print("  %s" % path)
        print("     bytes %s" % d["bytes"])
        for k in ("raw", "lf", "crlf"):
            print("     %-5s %s%s" % (k, d[k],
                                      "   <== MATCH" if d[k] == FROZEN else ""))
        if hit:
            print("     -> reproduces the frozen identity under %r" % hit)
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
