#!/usr/bin/env python3
"""V69 Route B step 3: donor-aware MACS peak calling and the consensus region universe.

Reuses pycisTopic's own implementations rather than reimplementing them:
  pycisTopic.pseudobulk_peak_calling.peak_calling   (MACS per pseudobulk)
  pycisTopic.iterative_peak_calling.get_consensus_peaks  (iterative overlap)

PARAMETERS are the pycisTopic protocol defaults, adopted unchanged and NOT tuned:
  input_format BEDPE, shift 73, ext_size 146, keep_dup all, q_value 0.05,
  nolambda True, peak_half_width 250.

ERRATUM ON THE FROZEN TEXT. SECTION_2 of the prospective freeze wrote the MACS flags as
"--format BEDPE --keep-dup all --nomodel --shift 73 --ext_size 146 --call-summits
-q 0.05" and described them as "verbatim pycisTopic protocol defaults". That string
OMITTED --nolambda, which pycisTopic supplies by default. The freeze's stated intent --
protocol defaults, untuned -- is what is implemented here; the parameter string was
incomplete rather than different. Recorded rather than silently reconciled.

PEAK RECURRENCE is computed for EVERY consensus region and NO recurrence filter is
applied, because filtering regions by recurrence and then reporting recurrence would be
circular. SECTION_2 freezes this.

MACS2 vs MACS3: the freeze prefers MACS3 and permits MACS2 if MACS3 is unavailable,
"recorded explicitly". The validated container ships MACS2 2.2.9.1 and no MACS3, so
MACS2 is used and the version is recorded in the receipt.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import subprocess
from pathlib import Path

import pandas as pd
import pyranges as pr

PEAK_HALF_WIDTH = 250          # frozen, SECTION_2
MACS_PARAMS = dict(input_format="BEDPE", shift=73, ext_size=146,
                   keep_dup="all", q_value=0.05, nolambda=True)
GENOME_SIZE = "hs"


def utcnow() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path, chunk: int = 8 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def ordered_digest(items) -> str:
    h = hashlib.sha256()
    for i, s in enumerate(items):
        h.update(str(i).encode()); h.update(b"\x1f")
        h.update(str(s).encode()); h.update(b"\x1e")
    return h.hexdigest()


class FailClosed(Exception):
    def __init__(self, status, **detail):
        super().__init__(status)
        self.status = status
        self.detail = detail


def run(pseudobulk_receipt: Path, chromsizes: Path, out_dir: Path,
        macs_path: str, n_cpu: int, blacklist: str | None) -> dict:
    pb = json.loads(pseudobulk_receipt.read_text())
    if not str(pb.get("status", "")).startswith("PASS") or pb.get("PARTIAL_SCAN"):
        raise FailClosed("FAIL__PSEUDOBULK_RECEIPT_NOT_A_COMPLETE_PASS",
                         status=pb.get("status"), partial=pb.get("PARTIAL_SCAN"))

    beds, skipped_empty = {}, []
    for key, meta in pb["pseudobulks"].items():
        if meta["n_fragments"] == 0:
            skipped_empty.append(key)
            continue
        p = Path(meta["path"])
        if sha256_file(p) != meta["sha256"]:
            raise FailClosed("FAIL__PSEUDOBULK_BED_DIGEST_MISMATCH", pseudobulk=key)
        beds[key] = str(p)
    if not beds:
        raise FailClosed("FAIL__NO_NONEMPTY_PSEUDOBULKS")

    macs_version = subprocess.run([macs_path, "--version"], capture_output=True,
                                  text=True).stdout.strip() or \
        subprocess.run([macs_path, "--version"], capture_output=True,
                       text=True).stderr.strip()

    out_dir.mkdir(parents=True, exist_ok=True)
    peaks_dir = out_dir / "macs"
    peaks_dir.mkdir(exist_ok=True)

    from pycisTopic.pseudobulk_peak_calling import peak_calling
    from pycisTopic.iterative_peak_calling import get_consensus_peaks

    narrow = peak_calling(macs_path=macs_path, bed_paths=beds,
                          outdir=str(peaks_dir), genome_size=GENOME_SIZE,
                          n_cpu=n_cpu, skip_empty_peaks=True, **MACS_PARAMS)

    per_pb = {}
    for key, rng in narrow.items():
        df = rng.df if hasattr(rng, "df") else rng
        per_pb[key] = {"n_peaks": int(len(df)),
                       "donor": pb["pseudobulks"][key]["donor"],
                       "subcluster": pb["pseudobulks"][key]["subcluster"]}

    cs = pd.read_csv(chromsizes, sep="\t", header=None, names=["Chromosome", "End"])
    cs["Start"] = 0
    chrom_pr = pr.PyRanges(cs[["Chromosome", "Start", "End"]])

    consensus = get_consensus_peaks(narrow_peaks_dict=narrow,
                                    peak_half_width=PEAK_HALF_WIDTH,
                                    chromsizes=chrom_pr,
                                    path_to_blacklist=blacklist)
    cdf = consensus.df if hasattr(consensus, "df") else consensus
    cdf = cdf.sort_values(["Chromosome", "Start", "End"]).reset_index(drop=True)

    # Per-region donor recurrence, computed for EVERY region. No filter applied.
    cons_pr = pr.PyRanges(cdf[["Chromosome", "Start", "End"]])
    donors = sorted({v["donor"] for v in per_pb.values()})
    recurrence = pd.Series(0, index=cdf.index, dtype=int)
    for donor in donors:
        hit = pd.Series(False, index=cdf.index)
        for key, rng in narrow.items():
            if per_pb[key]["donor"] != donor:
                continue
            ov = cons_pr.overlap(rng if hasattr(rng, "Chromosome") else pr.PyRanges(rng))
            if len(ov) == 0:
                continue
            ovd = ov.df
            idx = cdf.reset_index().merge(
                ovd[["Chromosome", "Start", "End"]].drop_duplicates(),
                on=["Chromosome", "Start", "End"])["index"]
            hit.loc[idx] = True
        recurrence += hit.astype(int)
    cdf["n_donors_with_overlapping_peak"] = recurrence.to_numpy()
    cdf["fraction_donors"] = cdf["n_donors_with_overlapping_peak"] / max(len(donors), 1)
    cdf["name"] = (cdf["Chromosome"].astype(str) + ":" +
                   cdf["Start"].astype(str) + "-" + cdf["End"].astype(str))

    bed = out_dir / "V69_ROUTE_B_CONSENSUS_REGION_UNIVERSE.bed"
    cdf[["Chromosome", "Start", "End", "name"]].to_csv(
        bed, sep="\t", header=False, index=False)
    tbl = out_dir / "V69_ROUTE_B_CONSENSUS_REGIONS_WITH_RECURRENCE.csv.gz"
    cdf.to_csv(tbl, index=False, compression="gzip")

    widths = (cdf["End"] - cdf["Start"])
    return {
        "schema": "V69_ROUTEB_CONSENSUS_PEAKS_V1",
        "built_utc": utcnow(),
        "peak_caller": {"path": macs_path, "version": macs_version,
                        "macs3_preferred_but_absent": True,
                        "note": "The freeze prefers MACS3 and permits MACS2 if MACS3 is "
                                "unavailable, recorded explicitly. The validated "
                                "container ships MACS2 only."},
        "macs_parameters": MACS_PARAMS,
        "peak_half_width": PEAK_HALF_WIDTH,
        "parameter_erratum": (
            "SECTION_2's MACS flag string omitted --nolambda, which pycisTopic supplies "
            "by default and which the freeze's stated intent (protocol defaults, "
            "untuned) includes. Implemented as the protocol default; the frozen string "
            "was incomplete rather than different."),
        "blacklist": {"path": blacklist,
                      "applied": blacklist is not None,
                      "note": ("No blacklist is applied unless one is supplied and "
                               "pinned. Not applying one retains known-artifact regions "
                               "in the Route-B universe; this is recorded rather than "
                               "decided silently.")},
        "pseudobulks": {"n_used": len(beds), "n_skipped_empty": len(skipped_empty),
                        "skipped_empty": skipped_empty, "per_pseudobulk": per_pb},
        "donors": {"n_donors": len(donors), "donors": donors},
        "consensus": {
            "n_regions": int(len(cdf)),
            "total_bp": int(widths.sum()),
            "width_min": int(widths.min()), "width_max": int(widths.max()),
            "n_contigs": int(cdf["Chromosome"].nunique()),
            "donor_recurrence_distribution": {
                str(k): int(v) for k, v in
                cdf["n_donors_with_overlapping_peak"].value_counts().sort_index().items()},
            "recurrence_filter_applied": False,
            "why_no_filter": ("Filtering regions by donor recurrence and then reporting "
                              "recurrence would be circular. SECTION_2 freezes this."),
            "bed_path": str(bed), "bed_sha256": sha256_file(bed),
            "table_path": str(tbl), "table_sha256": sha256_file(tbl),
            "ordered_region_digest": ordered_digest(cdf["name"].tolist()),
        },
        "status": "PASS__ROUTEB_CONSENSUS_REGION_UNIVERSE_BUILT",
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pseudobulk-receipt", required=True)
    ap.add_argument("--chromsizes", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--macs-path", default="macs2")
    ap.add_argument("--n-cpu", type=int, default=8)
    ap.add_argument("--blacklist", default=None)
    ap.add_argument("--receipt", required=True)
    a = ap.parse_args(argv)
    try:
        r = run(Path(a.pseudobulk_receipt), Path(a.chromsizes), Path(a.out_dir),
                a.macs_path, a.n_cpu, a.blacklist)
    except FailClosed as e:
        r = {"schema": "V69_ROUTEB_CONSENSUS_PEAKS_V1", "status": e.status, **e.detail}
    Path(a.receipt).parent.mkdir(parents=True, exist_ok=True)
    Path(a.receipt).write_text(json.dumps(r, indent=2) + "\n")
    print(json.dumps({k: v for k, v in r.items() if k != "pseudobulks"}, indent=2)[:3500])
    return 0 if str(r["status"]).startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
