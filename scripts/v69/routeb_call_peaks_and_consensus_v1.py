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
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v69_custody import CustodyError, bind_file, remap  # noqa: E402

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


# V74 REPAIR 4. An empty consensus set used to reach `int(widths.min())`, where pandas
# returns NaN for an empty Series and int(NaN) raises ValueError. ValueError is not a
# FailClosed, so main() would not catch it: the run died with a traceback and NO RECEIPT
# WAS WRITTEN AT ALL. A silent crash is worse than a bad receipt, because nothing on
# disk records that the step was attempted. The emptiness is now its own named state,
# raised BEFORE any width, min or max is computed.
CONSENSUS_EMPTY_STATUS = "FAIL__CONSENSUS_PEAK_SET_IS_EMPTY"


def assert_consensus_nonempty(cdf, *, n_pseudobulks_used=None,
                              n_pseudobulks_skipped_empty=None) -> None:
    """Fail closed, by name, if consensus peak construction returned no regions.

    Zero regions is a real possible outcome -- every pseudobulk could be filtered out,
    MACS could call nothing above threshold, or a blacklist could remove everything --
    and it must be reported as that, not as a width statistic over an empty set and not
    as an uncaught exception.
    """
    n = 0 if cdf is None else int(len(cdf))
    if n == 0:
        raise FailClosed(
            CONSENSUS_EMPTY_STATUS,
            n_consensus_regions=0,
            n_pseudobulks_used=n_pseudobulks_used,
            n_pseudobulks_skipped_empty=n_pseudobulks_skipped_empty,
            note=("Consensus peak construction returned zero regions. No region "
                  "universe exists, so no width, recurrence or coverage statistic is "
                  "defined. Nothing downstream may proceed, and this is NOT a region "
                  "universe of size zero -- it is an absent region universe."))


def recurrence_denominator(pseudobulk_meta: dict, submitted_keys, keys_with_peaks) -> dict:
    """Who counts in the denominator of a region's donor recurrence.

    The answer is the donors that COULD have contributed a peak -- those with a
    non-empty pseudobulk submitted to MACS -- not the donors that happened to produce
    one. pycisTopic's peak_calling(skip_empty_peaks=True) drops a pseudobulk that called
    nothing, so a donor whose every pseudobulk came back empty would silently leave the
    denominator and inflate every region's fraction_donors. A donor that submitted
    fragments and called no peak contributes a zero; it does not disappear.

    Kept as a separate function so it can be exercised without MACS or pycisTopic.
    """
    submitted = sorted({pseudobulk_meta[k]["donor"] for k in submitted_keys})
    with_peaks = sorted({pseudobulk_meta[k]["donor"] for k in keys_with_peaks})
    return {
        "donors_submitted": submitted,
        "donors_with_peaks": with_peaks,
        "donors_submitted_without_peaks": [d for d in submitted
                                           if d not in set(with_peaks)],
        "pseudobulks_submitted_without_peaks": sorted(set(submitted_keys)
                                                      - set(keys_with_peaks)),
        "denominator": len(submitted),
    }


def run(pseudobulk_receipt: Path, chromsizes: Path, out_dir: Path,
        macs_path: str, n_cpu: int, blacklist: str | None,
        host_prefix: str = "", container_prefix: str = "") -> dict:
    def R(p):
        return remap(p, host_prefix, container_prefix)

    pb = json.loads(pseudobulk_receipt.read_text())
    if not str(pb.get("status", "")).startswith("PASS") or pb.get("PARTIAL_SCAN"):
        raise FailClosed("FAIL__PSEUDOBULK_RECEIPT_NOT_A_COMPLETE_PASS",
                         status=pb.get("status"), partial=pb.get("PARTIAL_SCAN"))

    # ---- V74 REPAIR 3: inherit the upstream custody chain, by content -------------
    # A receipt that merely says PASS is not enough. The upstream step must have
    # actually digested the 63.6 GB fragment file it read, and every small input it
    # bound must still have the bytes it bound. Re-verifying costs milliseconds, and
    # the fragment file is NOT re-read: its identity was established in the pass that
    # consumed it.
    if pb.get("custody_contract") != "V74_ROUTEB_CUSTODY_V1":
        raise FailClosed("FAIL__PSEUDOBULK_RECEIPT_PREDATES_THE_CUSTODY_CONTRACT",
                         custody_contract=pb.get("custody_contract"),
                         required="V74_ROUTEB_CUSTODY_V1",
                         note=("A pre-V74 pseudobulk receipt checked the fragment "
                               "file's SIZE and copied its digest from the acquisition "
                               "receipt, so its fragment identity was never measured."))
    fid = pb.get("fragment_identity") or {}
    if fid.get("verified") is not True:
        raise FailClosed("FAIL__UPSTREAM_FRAGMENT_BYTES_WERE_NEVER_VERIFIED",
                         fragment_identity=fid)
    if (str(fid.get("observed_sha256", "")).strip().lower()
            != str(fid.get("expected_sha256", "")).strip().lower()):
        raise FailClosed("FAIL__UPSTREAM_FRAGMENT_DIGEST_DISAGREES_WITH_ITS_AUTHORITY",
                         fragment_identity=fid)

    rebound = {}
    for name, rec in (pb.get("bound_inputs") or {}).items():
        want = rec.get("sha256")
        if not isinstance(want, str) or len(want) != 64:
            raise FailClosed("FAIL__UPSTREAM_BOUND_INPUT_HAS_NO_DIGEST",
                             bound_input=name, record=rec)
        rebound[name] = bind_file(R(rec["path"]), label=rec.get("label", name),
                                  role="REVERIFIED_UPSTREAM_INPUT",
                                  expected_sha256=want,
                                  expected_bytes=rec.get("bytes"))
        rebound[name]["host_path_in_upstream_receipt"] = rec["path"]
    rebound["pseudobulk_receipt"] = bind_file(
        pseudobulk_receipt, label="V69_ROUTEB_PSEUDOBULK_FRAGMENTS_V1.json",
        role="UPSTREAM_RECEIPT")
    rebound["consensus_producer"] = bind_file(
        Path(__file__).resolve(), label="producer", role="EXECUTING_SOURCE")
    rebound["custody_module"] = bind_file(
        Path(__file__).resolve().parent / "v69_custody.py", label="v69_custody.py",
        role="IMPORTED_SOURCE")
    rebound["chromsizes"] = bind_file(chromsizes, label="chromsizes",
                                      role="GENOME_CONTIG_AUTHORITY")
    if blacklist is not None:
        rebound["blacklist"] = bind_file(blacklist, label="blacklist",
                                         role="REGION_EXCLUSION_AUTHORITY")

    beds, skipped_empty = {}, []
    for key, meta in pb["pseudobulks"].items():
        if meta["n_fragments"] == 0:
            skipped_empty.append(key)
            continue
        p = R(meta["path"])
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

    import pyranges as pr
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

    # BEFORE any width / min / max, and before the recurrence loop.
    assert_consensus_nonempty(cdf, n_pseudobulks_used=len(beds),
                              n_pseudobulks_skipped_empty=len(skipped_empty))

    # Per-region donor recurrence, computed for EVERY region. No filter applied.
    cons_pr = pr.PyRanges(cdf[["Chromosome", "Start", "End"]])

    # V74 REPAIR. The recurrence denominator must be the donors that COULD have
    # contributed a peak -- those with a non-empty pseudobulk submitted to MACS -- not
    # the donors that happened to produce one. peak_calling(skip_empty_peaks=True) drops
    # a pseudobulk that called nothing, so a donor whose every pseudobulk came back
    # empty would silently vanish from the denominator and inflate every region's
    # fraction_donors. Both counts are recorded so the difference is visible.
    _den = recurrence_denominator(pb["pseudobulks"], list(beds), list(narrow))
    donors_submitted = _den["donors_submitted"]
    donors_with_peaks = _den["donors_with_peaks"]
    donors_submitted_without_peaks = _den["donors_submitted_without_peaks"]
    pseudobulks_submitted_without_peaks = _den["pseudobulks_submitted_without_peaks"]
    donors = donors_submitted
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
    cdf["fraction_donors"] = (cdf["n_donors_with_overlapping_peak"]
                              / max(len(donors_submitted), 1))
    cdf["name"] = (cdf["Chromosome"].astype(str) + ":" +
                   cdf["Start"].astype(str) + "-" + cdf["End"].astype(str))

    bed = out_dir / "V69_ROUTE_B_CONSENSUS_REGION_UNIVERSE.bed"
    cdf[["Chromosome", "Start", "End", "name"]].to_csv(
        bed, sep="\t", header=False, index=False)
    tbl = out_dir / "V69_ROUTE_B_CONSENSUS_REGIONS_WITH_RECURRENCE.csv.gz"
    cdf.to_csv(tbl, index=False, compression="gzip")

    assert_consensus_nonempty(cdf, n_pseudobulks_used=len(beds),
                              n_pseudobulks_skipped_empty=len(skipped_empty))
    widths = (cdf["End"] - cdf["Start"])
    return {
        "schema": "V69_ROUTEB_CONSENSUS_PEAKS_V1",
        "built_utc": utcnow(),
        "custody_contract": "V74_ROUTEB_CUSTODY_V1",
        "path_remapping": {
            "applied": bool(host_prefix),
            "host_prefix": host_prefix or None,
            "container_prefix": container_prefix or None,
            "note": ("Upstream receipts record the absolute HOST path where each "
                     "artifact actually lived; that record is never rewritten. This "
                     "producer, running inside the container, reads the same bytes at "
                     "a different mount point and verifies their digests there."),
        },
        "bound_inputs": rebound,
        "upstream_fragment_identity": fid,
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
        "donors": {
            "n_donors": len(donors_submitted),
            "donors": donors_submitted,
            "recurrence_denominator": "DONORS_WITH_A_NONEMPTY_PSEUDOBULK_SUBMITTED",
            "n_donors_with_at_least_one_called_peak": len(donors_with_peaks),
            "donors_submitted_without_any_called_peak": donors_submitted_without_peaks,
            "pseudobulks_submitted_without_any_called_peak":
                pseudobulks_submitted_without_peaks,
            "why": ("A donor that submitted fragments and called no peak contributes a "
                    "zero to recurrence; it must not be removed from the denominator, "
                    "which would inflate every region's fraction_donors."),
        },
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
    ap.add_argument("--host-prefix", default="",
                    help="Host path prefix recorded in upstream receipts.")
    ap.add_argument("--container-prefix", default="",
                    help="Where that prefix is bind-mounted in this container.")
    a = ap.parse_args(argv)
    try:
        r = run(Path(a.pseudobulk_receipt), Path(a.chromsizes), Path(a.out_dir),
                a.macs_path, a.n_cpu, a.blacklist,
                a.host_prefix, a.container_prefix)
    except FailClosed as e:
        r = {"schema": "V69_ROUTEB_CONSENSUS_PEAKS_V1", "built_utc": utcnow(),
             "status": e.status, **e.detail}
    except CustodyError as e:
        r = {"schema": "V69_ROUTEB_CONSENSUS_PEAKS_V1", "built_utc": utcnow(),
             "status": e.status, **e.detail}
    # The verdict must live in the object that is written, never only in stdout.
    # This writes first and then reports from the bytes on disk.
    if "status" not in r:
        r["status"] = "FAIL__RECEIPT_HAS_NO_STATUS_FIELD"
    Path(a.receipt).parent.mkdir(parents=True, exist_ok=True)
    Path(a.receipt).write_text(json.dumps(r, indent=2) + "\n")
    on_disk = json.loads(Path(a.receipt).read_text())
    print(json.dumps({k: v for k, v in on_disk.items()
                      if k not in ("pseudobulks", "bound_inputs")}, indent=2)[:3500])
    print("RECEIPT_ON_DISK_STATUS=" + str(on_disk["status"]))
    return 0 if str(on_disk["status"]).startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
