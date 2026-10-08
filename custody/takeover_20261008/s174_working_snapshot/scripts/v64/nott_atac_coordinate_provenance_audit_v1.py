#!/usr/bin/env python3
"""ATAC coordinate-provenance audit: re-lift FILER's source coordinates ourselves.

FILER/NIAGADS distributes the Nott 2019 ATAC peaks already lifted to hg38, under
a chain and procedure that are not recorded. The Nott contact map is lifted to
hg38 by US, with the authenticated UCSC chain. Two independent lift procedures
therefore meet in hg38 on a design whose entire content is
contact INTERSECT accessibility -- so a peak and an anchor could disagree because
of liftover rather than biology.

The files retain their hg19 source coordinates in columns 4-6, which makes the
question directly answerable:

    re-lift columns 4-6 with OUR authenticated chain, under the SAME frozen
    semantics, and compare to FILER's hg38 columns 1-3.

THE PRIMARY TEST IS EXACT COORDINATE EQUALITY. No overlap tolerance is defined
here and none may be introduced after seeing discordance.

Frozen semantics, identical to the contact liftover:
  UCSC liftOver archived build linux.x86_64.v479, -minMatch=0.95,
  NO -multiple for the authoritative mapping, a separate -multiple pass used ONLY
  to detect and REJECT ambiguous/split rows, no nearest-neighbour rescue.

Denominators are the ORIGINAL row counts, never a surviving subset.

TRAINING=OFF. TD60=BLOCKED. Coordinates only.
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
TRACKS = {"PU1_microglia": "ATAC_PU1.bed.gz",
          "NeuN_neuron": "ATAC_NeuN.bed.gz",
          "Olig2_oligodendrocyte": "ATAC_Olig2.bed.gz"}


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
    out = {}
    with open(path) as fh:
        for line in fh:
            if not line.strip() or line.startswith("#"):
                continue
            f = line.rstrip("\n").split("\t")
            out[f[3]] = (f[0], int(f[1]), int(f[2]))
    return out


def multi_names(path):
    c = Counter()
    with open(path) as fh:
        for line in fh:
            if not line.strip() or line.startswith("#"):
                continue
            c[line.rstrip("\n").split("\t")[3]] += 1
    return {k for k, v in c.items() if v > 1}


def unmapped_info(path):
    names, reasons, last = set(), Counter(), None
    with open(path) as fh:
        for line in fh:
            if line.startswith("#"):
                last = line.strip().lstrip("#").strip()
            elif line.strip():
                names.add(line.rstrip("\n").split("\t")[3])
                reasons[last or "UNKNOWN"] += 1
    return names, dict(reasons)


def audit(track, fname):
    src = os.path.join(WIN_ROOT, fname)
    filer, source = {}, {}
    n = 0
    with gzip.open(src, "rt") as fh:
        for line in fh:
            if line.startswith("#") or not line.strip():
                continue
            f = line.rstrip("\n").split("\t")
            k = f"R{n}"
            filer[k] = (f[0], int(f[1]), int(f[2]))        # FILER hg38, cols 1-3
            source[k] = (f[3], int(f[4]), int(f[5]))       # source hg19, cols 4-6
            n += 1
    bed = os.path.join(WIN_ROOT, f"atac_{track}.hg19.bed")
    with open(bed, "w", newline="\n") as fh:
        for k, (c, s, e) in source.items():
            fh.write(f"{c}\t{s}\t{e}\t{k}\n")

    wsl(f"{LIFTOVER} -minMatch={MINMATCH} atac_{track}.hg19.bed hg19ToHg38.over.chain.gz "
        f"atac_{track}.relift.bed atac_{track}.unmapped 2>&1 | tail -2")
    wsl(f"{LIFTOVER} -minMatch={MINMATCH} -multiple -noSerial atac_{track}.hg19.bed "
        f"hg19ToHg38.over.chain.gz atac_{track}.multi.bed atac_{track}.multi.unmapped 2>&1 | tail -2")

    relift = read_bed(os.path.join(WIN_ROOT, f"atac_{track}.relift.bed"))
    amb = multi_names(os.path.join(WIN_ROOT, f"atac_{track}.multi.bed"))
    unm, unm_reasons = unmapped_info(os.path.join(WIN_ROOT, f"atac_{track}.unmapped"))
    ok = {k: v for k, v in relift.items() if k not in amb}

    exact = same_chrom_disc = chrom_disc = 0
    deltas = Counter()
    lenchg = Counter()
    for k, v in ok.items():
        f_ = filer[k]
        lenchg[(v[2] - v[1]) - (source[k][2] - source[k][1])] += 1
        if v == f_:
            exact += 1
        elif v[0] != f_[0]:
            chrom_disc += 1
        else:
            same_chrom_disc += 1
            deltas[(v[1] - f_[1], v[2] - f_[2])] += 1
    return {
        "track": track, "file": fname, "sha256": sha(src),
        "original_row_denominator": n,
        "relifted_single_mappings": len(ok),
        "exact_chrom_start_end_matches": exact,
        "same_chromosome_coordinate_discordant": same_chrom_disc,
        "chromosome_discordant": chrom_disc,
        "unmapped_rows": len(unm),
        "ambiguous_or_split_rows": len(amb),
        "unmapped_reasons": unm_reasons,
        "exact_match_fraction_of_original_denominator": round(exact / n, 6),
        "source_to_relift_interval_length_unchanged": lenchg.get(0, 0),
        "source_to_relift_interval_length_changed": sum(v for k, v in lenchg.items() if k),
        "source_to_relift_length_delta_range":
            [min(lenchg), max(lenchg)] if lenchg else None,
        "top_coordinate_deltas_vs_FILER":
            {f"start{d[0]:+d},end{d[1]:+d}": c for d, c in deltas.most_common(10)},
        "distinct_delta_patterns": len(deltas),
        "accounting_check": len(ok) + len(unm) + len(amb - unm) == n,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    results = {}
    for track, fname in TRACKS.items():
        r = audit(track, fname)
        results[track] = r
        print(f"{track:24s} n={r['original_row_denominator']:>6,}  "
              f"exact={r['exact_chrom_start_end_matches']:>6,} "
              f"({100*r['exact_match_fraction_of_original_denominator']:.4f}%)  "
              f"discordant(same chr)={r['same_chromosome_coordinate_discordant']:>4}  "
              f"chr-disc={r['chromosome_discordant']}  unmapped={r['unmapped_rows']}  "
              f"ambig={r['ambiguous_or_split_rows']}")

    out = {
        "schema": "V64_NOTT_ATAC_COORDINATE_PROVENANCE_AUDIT_V1",
        "date": "2026-09-29",
        "status": "DESCRIPTIVE_EVIDENCE_ONLY",
        "primary_test": "EXACT coordinate equality (chrom, start, end). No overlap "
                        "tolerance is defined and none may be introduced after seeing "
                        "discordance.",
        "governance": {"training": "OFF", "td60": "BLOCKED",
                       "gene_annotation_joined": False},
        "implementation": {
            "tool": "UCSC liftOver archived build linux.x86_64.v479",
            "tool_sha256": sha(os.path.join(WIN_ROOT, "liftOver_v479")),
            "minMatch": float(MINMATCH),
            "multiple": "detection-only, ambiguous rows REJECTED",
            "chain_hg19ToHg38_sha256": sha(os.path.join(WIN_ROOT, "hg19ToHg38.over.chain.gz")),
            "same_semantics_as_contact_liftover": True},
        "why": ("FILER lifted these tracks to hg38 under an unrecorded chain while the "
                "contact map is lifted by us with the UCSC chain. Two lift procedures "
                "meeting in hg38 could make a peak and an anchor disagree for reasons "
                "that are not biological. The retained hg19 source coordinates in "
                "columns 4-6 make that directly testable."),
        "tracks": results,
    }
    with open(os.path.join(a.out_dir, "V64_NOTT_ATAC_PROVENANCE_AUDIT_V1.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
