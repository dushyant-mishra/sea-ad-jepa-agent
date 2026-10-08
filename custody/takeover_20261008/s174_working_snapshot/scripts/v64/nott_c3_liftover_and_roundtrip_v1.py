#!/usr/bin/env python3
"""Nott C3 mechanical execution: hg19->hg38 contact liftover + hg38->hg19 round trip.

DESCRIPTIVE ONLY. This script generates evidence. It does NOT adjudicate C3:
the two numeric gates the historical C3 contract requires -- an allowable
interval-length-change tolerance and a required exact round-trip recovery
fraction -- are still unfrozen, so qualification is emitted as
NOT_YET_ADJUDICABLE with PASS=null.

FROZEN IMPLEMENTATION SEMANTICS (identical forward and reverse)
  UCSC liftOver, archived build linux.x86_64.v479
  -minMatch=0.95
  NO -multiple for the authoritative mapping
  a second -multiple pass is used ONLY to DETECT anchors with more than one
  destination; those are rejected as ambiguous rather than silently resolved
  no nearest-neighbour rescue, no -fudgeThick, no -minBlocks relaxation

DENOMINATORS ARE PRESERVED THROUGHOUT. Every fraction is reported against the
original 104,802 microglia contacts, never against a surviving subset.

COORDINATE CONVENTION. The deposited table gives start/end with end-start = 5000
for every anchor. They are written to BED unchanged and compared back against the
same original values, so the 0-based/1-based question cancels in the round trip
and is noted rather than assumed away.

TRAINING=OFF. TD60=BLOCKED. No gene annotation is joined; coordinates only.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import subprocess
import sys
from collections import Counter

WSL_ROOT = "/mnt/c/Users/dushy/jepa_c3"
WIN_ROOT = "C:/Users/dushy/jepa_c3"
LIFTOVER = "./liftOver_v479"
MINMATCH = "0.95"


def wsl(cmd: str) -> str:
    r = subprocess.run(["wsl.exe", "-d", "Ubuntu", "--", "bash", "-lc",
                        f"cd {WSL_ROOT} && {cmd}"],
                       capture_output=True, text=True, timeout=7200)
    if r.returncode != 0 and "liftOver" not in r.stderr:
        raise SystemExit(f"WSL FAILED: {cmd}\n{r.stderr[-800:]}")
    return r.stdout + r.stderr


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def read_bed(path):
    """name -> (chrom, start, end). Duplicate names would be a defect, not a merge."""
    out = {}
    dup = 0
    with open(path) as fh:
        for line in fh:
            if not line.strip() or line.startswith("#"):
                continue
            f = line.rstrip("\n").split("\t")
            if f[3] in out:
                dup += 1
            out[f[3]] = (f[0], int(f[1]), int(f[2]))
    return out, dup


def multi_names(path):
    """Names appearing more than once under -multiple = ambiguous/split."""
    c = Counter()
    with open(path) as fh:
        for line in fh:
            if not line.strip() or line.startswith("#"):
                continue
            c[line.rstrip("\n").split("\t")[3]] += 1
    return {k for k, v in c.items() if v > 1}


def unmapped_reasons(path):
    """liftOver writes '#Reason' lines before each rejected record."""
    reasons = Counter()
    names = set()
    last = None
    with open(path) as fh:
        for line in fh:
            if line.startswith("#"):
                last = line.strip().lstrip("#").strip()
            elif line.strip():
                f = line.rstrip("\n").split("\t")
                names.add(f[3])
                reasons[last or "UNKNOWN"] += 1
    return names, dict(reasons)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    # ---------- 1. build the anchor BED from all 104,802 contacts
    src = os.path.join(WIN_ROOT, "nott_microglia_interactome.tsv.gz")
    pairs = []
    with gzip.open(src, "rt") as fh:
        hdr = fh.readline().rstrip("\n").split("\t")
        ix = {k: i for i, k in enumerate(hdr)}
        for line in fh:
            f = line.rstrip("\n").split("\t")
            pairs.append((f[ix["chr1"]], int(f[ix["start1"]]), int(f[ix["end1"]]),
                          f[ix["chr2"]], int(f[ix["start2"]]), int(f[ix["end2"]])))
    N_PAIRS = len(pairs)
    bed = os.path.join(WIN_ROOT, "anchors.hg19.bed")
    with open(bed, "w", newline="\n") as fh:
        for i, (c1, s1, e1, c2, s2, e2) in enumerate(pairs):
            fh.write(f"{c1}\t{s1}\t{e1}\tA{i}\n{c2}\t{s2}\t{e2}\tB{i}\n")
    N_ANCHORS = N_PAIRS * 2
    print(f"pairs {N_PAIRS:,}  anchor instances {N_ANCHORS:,}")

    # ---------- 2. forward lift, authoritative (no -multiple)
    wsl(f"{LIFTOVER} -minMatch={MINMATCH} anchors.hg19.bed hg19ToHg38.over.chain.gz "
        f"anchors.hg38.bed anchors.hg38.unmapped 2>&1 | tail -3")
    # ---------- 3. forward lift with -multiple, ONLY to detect ambiguity
    wsl(f"{LIFTOVER} -minMatch={MINMATCH} -multiple -noSerial anchors.hg19.bed "
        f"hg19ToHg38.over.chain.gz anchors.hg38.multi.bed anchors.hg38.multi.unmapped 2>&1 | tail -3")

    fwd, fwd_dup = read_bed(os.path.join(WIN_ROOT, "anchors.hg38.bed"))
    amb = multi_names(os.path.join(WIN_ROOT, "anchors.hg38.multi.bed"))
    unm_names, unm_reasons = unmapped_reasons(os.path.join(WIN_ROOT, "anchors.hg38.unmapped"))

    orig = {}
    for i, (c1, s1, e1, c2, s2, e2) in enumerate(pairs):
        orig[f"A{i}"] = (c1, s1, e1)
        orig[f"B{i}"] = (c2, s2, e2)

    accepted = {k: v for k, v in fwd.items() if k not in amb}
    chrom_change = sum(1 for k, v in accepted.items() if v[0] != orig[k][0])
    len_delta = Counter()
    for k, v in accepted.items():
        len_delta[(v[2] - v[1]) - (orig[k][2] - orig[k][1])] += 1
    pairs_both = sum(1 for i in range(N_PAIRS)
                     if f"A{i}" in accepted and f"B{i}" in accepted)

    fwd_stats = {
        "pairs_attempted": N_PAIRS,
        "anchors_attempted": N_ANCHORS,
        "anchors_single_successful_mapping": len(accepted),
        "anchors_unmapped": len(unm_names),
        "anchors_ambiguous_or_split_rejected": len(amb),
        "unmapped_reasons": unm_reasons,
        "duplicate_names_in_output": fwd_dup,
        "anchors_chromosome_changed": chrom_change,
        "anchor_interval_length_changes": {str(k): v for k, v in sorted(len_delta.items())},
        "anchors_length_unchanged": len_delta.get(0, 0),
        "pairs_both_anchors_mapped": pairs_both,
        "retained_pair_fraction_of_104802": round(pairs_both / N_PAIRS, 6),
        "accounting_check_anchors":
            len(accepted) + len(unm_names) + len(amb - set(unm_names)) == N_ANCHORS,
    }
    print(json.dumps(fwd_stats, indent=1)[:1200])

    # ---------- 4. round trip on the forward-retained anchors
    rt_in = os.path.join(WIN_ROOT, "anchors.hg38.retained.bed")
    retained_anchor_names = [n for i in range(N_PAIRS) for n in (f"A{i}", f"B{i}")
                             if f"A{i}" in accepted and f"B{i}" in accepted]
    with open(rt_in, "w", newline="\n") as fh:
        for n in retained_anchor_names:
            c, s, e = accepted[n]
            fh.write(f"{c}\t{s}\t{e}\t{n}\n")
    wsl(f"{LIFTOVER} -minMatch={MINMATCH} anchors.hg38.retained.bed hg38ToHg19.over.chain.gz "
        f"anchors.rt.hg19.bed anchors.rt.unmapped 2>&1 | tail -3")
    wsl(f"{LIFTOVER} -minMatch={MINMATCH} -multiple -noSerial anchors.hg38.retained.bed "
        f"hg38ToHg19.over.chain.gz anchors.rt.multi.bed anchors.rt.multi.unmapped 2>&1 | tail -3")

    rt, rt_dup = read_bed(os.path.join(WIN_ROOT, "anchors.rt.hg19.bed"))
    rt_amb = multi_names(os.path.join(WIN_ROOT, "anchors.rt.multi.bed"))
    rt_unm_names, rt_unm_reasons = unmapped_reasons(os.path.join(WIN_ROOT, "anchors.rt.unmapped"))
    rt_ok = {k: v for k, v in rt.items() if k not in rt_amb}

    exact = 0
    same_chrom_discordant = 0
    chrom_discordant = 0
    deltas = Counter()
    for k, v in rt_ok.items():
        o = orig[k]
        if v == o:
            exact += 1
        elif v[0] != o[0]:
            chrom_discordant += 1
        else:
            same_chrom_discordant += 1
            deltas[(v[1] - o[1], v[2] - o[2])] += 1
    pairs_exact = sum(1 for i in range(N_PAIRS)
                      if rt_ok.get(f"A{i}") == orig[f"A{i}"]
                      and rt_ok.get(f"B{i}") == orig[f"B{i}"])

    rt_stats = {
        "anchors_attempted": len(retained_anchor_names),
        "anchors_mapped_back_single": len(rt_ok),
        "anchors_unmapped_on_return": len(rt_unm_names),
        "anchors_ambiguous_on_return": len(rt_amb),
        "unmapped_reasons": rt_unm_reasons,
        "exact_anchor_recoveries": exact,
        "same_chromosome_discordant_recoveries": same_chrom_discordant,
        "chromosome_discordant_recoveries": chrom_discordant,
        "exact_both_anchor_pair_recoveries": pairs_exact,
        "exact_roundtrip_fraction_of_forward_retained_pairs":
            round(pairs_exact / pairs_both, 6) if pairs_both else None,
        "exact_roundtrip_fraction_of_original_104802":
            round(pairs_exact / N_PAIRS, 6),
        "coordinate_deltas_same_chromosome_non_exact":
            {f"start{d[0]:+d},end{d[1]:+d}": n for d, n in deltas.most_common(20)},
        "distinct_delta_patterns": len(deltas),
    }
    print(json.dumps(rt_stats, indent=1)[:1200])

    out = {
        "schema": "V64_NOTT_C3_LIFTOVER_ROUNDTRIP_DESCRIPTIVE_V1",
        "date": "2026-09-29",
        "status": "DESCRIPTIVE_EVIDENCE_ONLY",
        "qualification": "NOT_YET_ADJUDICABLE",
        "PASS": None,
        "why_not_adjudicable": (
            "The historical C3 contract requires two prospectively declared numeric "
            "gates that remain unfrozen: (1) allowable interval-length-change "
            "tolerance, and (2) required exact round-trip recovery fraction. Choosing "
            "either now, with these numbers in view, would be selecting a threshold "
            "after seeing the result."),
        "governance": {"training": "OFF", "td60": "BLOCKED",
                       "gene_annotation_joined": False},
        "implementation": {
            "tool": "UCSC liftOver, archived build linux.x86_64.v479",
            "tool_sha256": sha(os.path.join(WIN_ROOT, "liftOver_v479")),
            "tool_bytes": os.path.getsize(os.path.join(WIN_ROOT, "liftOver_v479")),
            "why_archived_build": (
                "the current linux.x86_64 build requires GLIBC 2.32/2.33/2.34 and the "
                "available WSL Ubuntu provides 2.31, so it could not execute. v479 is "
                "the most recent archived build that runs here and its digest is "
                "recorded so the exact binary is identifiable."),
            "minMatch": float(MINMATCH),
            "multiple": "NOT used for the authoritative mapping; a separate -multiple "
                        "-noSerial pass is used ONLY to detect anchors with more than "
                        "one destination, which are then REJECTED as ambiguous",
            "nearest_neighbour_rescue": False,
            "same_rules_forward_and_reverse": True,
            "chains": {
                "hg19ToHg38": sha(os.path.join(WIN_ROOT, "hg19ToHg38.over.chain.gz")),
                "hg38ToHg19": sha(os.path.join(WIN_ROOT, "hg38ToHg19.over.chain.gz"))},
            "coordinate_convention_note": (
                "the deposited table has end-start = 5000 for every anchor; values are "
                "written to BED unchanged and compared back against the same originals, "
                "so the 0-based/1-based question cancels in the round trip"),
        },
        "source": {
            "file": "nott_microglia_interactome.tsv.gz",
            "sha256": sha(src),
            "derived_from": "Nott 2019 Table S5 sha256 81c99689533d9da372cecdd469e7ff02cc985720105b83b3bd66c3ac8c93972e"},
        "forward_hg19_to_hg38": fwd_stats,
        "roundtrip_hg38_to_hg19": rt_stats,
    }
    with open(os.path.join(a.out_dir, "V64_NOTT_C3_LIFTOVER_ROUNDTRIP_V1.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print("\nqualification: NOT_YET_ADJUDICABLE (PASS=null) - gates unfrozen")
    return 0


if __name__ == "__main__":
    sys.exit(main())
