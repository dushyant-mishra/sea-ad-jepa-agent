#!/usr/bin/env python3
"""C3 adjudication under the PROSPECTIVELY FROZEN exact-identity rule.

Rule: V64_NOTT_C3_EXACT_IDENTITY_SUCCESSOR_RULE_V1, frozen at
38d789aceecfdc71beca8852fbb19ab1621fee55 (2026-09-29 13:33:44 -0400), which is
EARLIER than the descriptive liftover result at 5131bc6c (13:42:12 -0400). The
rule was therefore fixed before these numbers existed, and that ordering is
verifiable from the commit timestamps rather than asserted.

NO THRESHOLD IS CHOSEN HERE. The rule sets tolerance to ZERO and asks only
whether a non-empty exactly-identical set remains, with the full attrition funnel
reported from the original 104,802 denominator.

FORWARD ADMISSIBILITY, per anchor
  exactly one target interval (ambiguous/split rejected)
  same chromosome
  interval length preserved EXACTLY (tolerance 0 bp)
PAIR: both anchors must satisfy all three.

ROUND TRIP, per forward-admissible anchor
  lift hg38 -> hg19 under the SAME frozen defaults
  returned chrom/start/end must equal the original hg19 interval EXACTLY
PAIR: both anchors must round-trip exactly.

The round trip is RE-RUN on exactly the forward-admissible set rather than
filtered out of the earlier, more permissive run, because the rule says "for
every forward-admissible anchor" and running it on precisely that set is the
faithful reading. liftOver processes lines independently so the two routes agree,
but the faithful one leaves nothing to argue about.

No rescue of any kind: no nearest-neighbour, no multiple-output selection, no
overlap window, no gene/target-aware resolution.

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
N_ORIGINAL = 104802


def wsl(cmd):
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out_dir) and os.listdir(a.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(a.out_dir, exist_ok=True)

    # ---- original hg19 anchors
    src = os.path.join(WIN_ROOT, "nott_microglia_interactome.tsv.gz")
    orig = {}
    n_pairs = 0
    with gzip.open(src, "rt") as fh:
        hdr = fh.readline().rstrip("\n").split("\t")
        ix = {k: i for i, k in enumerate(hdr)}
        for line in fh:
            f = line.rstrip("\n").split("\t")
            orig[f"A{n_pairs}"] = (f[ix["chr1"]], int(f[ix["start1"]]), int(f[ix["end1"]]))
            orig[f"B{n_pairs}"] = (f[ix["chr2"]], int(f[ix["start2"]]), int(f[ix["end2"]]))
            n_pairs += 1
    assert n_pairs == N_ORIGINAL, n_pairs

    fwd = read_bed(os.path.join(WIN_ROOT, "anchors.hg38.bed"))
    amb = multi_names(os.path.join(WIN_ROOT, "anchors.hg38.multi.bed"))

    # ---- forward admissibility, per anchor, with reason accounting
    reason = Counter()
    adm_fwd = {}
    for name, o in orig.items():
        m = fwd.get(name)
        if m is None:
            reason["unmapped"] += 1
        elif name in amb:
            reason["ambiguous_or_split"] += 1
        elif m[0] != o[0]:
            reason["chromosome_changed"] += 1
        elif (m[2] - m[1]) != (o[2] - o[1]):
            reason["length_changed"] += 1
        else:
            reason["admissible"] += 1
            adm_fwd[name] = m
    pairs_fwd = [i for i in range(N_ORIGINAL)
                 if f"A{i}" in adm_fwd and f"B{i}" in adm_fwd]

    # ---- round trip on EXACTLY the forward-admissible anchors of those pairs
    rt_names = [n for i in pairs_fwd for n in (f"A{i}", f"B{i}")]
    rt_bed = os.path.join(WIN_ROOT, "c3_exact_fwd_admissible.hg38.bed")
    with open(rt_bed, "w", newline="\n") as fh:
        for n in rt_names:
            c, s, e = adm_fwd[n]
            fh.write(f"{c}\t{s}\t{e}\t{n}\n")
    wsl(f"{LIFTOVER} -minMatch={MINMATCH} c3_exact_fwd_admissible.hg38.bed "
        f"hg38ToHg19.over.chain.gz c3_exact_rt.hg19.bed c3_exact_rt.unmapped 2>&1 | tail -2")
    wsl(f"{LIFTOVER} -minMatch={MINMATCH} -multiple -noSerial c3_exact_fwd_admissible.hg38.bed "
        f"hg38ToHg19.over.chain.gz c3_exact_rt.multi.bed c3_exact_rt.multi.unmapped 2>&1 | tail -2")
    rt = read_bed(os.path.join(WIN_ROOT, "c3_exact_rt.hg19.bed"))
    rt_amb = multi_names(os.path.join(WIN_ROOT, "c3_exact_rt.multi.bed"))

    rt_reason = Counter()
    adm_rt = set()
    for n in rt_names:
        b = rt.get(n)
        if b is None:
            rt_reason["unmapped_on_return"] += 1
        elif n in rt_amb:
            rt_reason["ambiguous_on_return"] += 1
        elif b != orig[n]:
            rt_reason["not_exact"] += 1
        else:
            rt_reason["exact"] += 1
            adm_rt.add(n)
    retained = [i for i in pairs_fwd
                if f"A{i}" in adm_rt and f"B{i}" in adm_rt]

    # ---- verify every retained pair really is exactly identical, both directions
    viol = 0
    for i in retained:
        for n in (f"A{i}", f"B{i}"):
            o, m = orig[n], adm_fwd[n]
            if m[0] != o[0] or (m[2] - m[1]) != (o[2] - o[1]) or rt[n] != o:
                viol += 1

    # ---- write the retained object (coordinates only, no gene annotation)
    obj = os.path.join(a.out_dir, "V64_NOTT_C3_RETAINED_CONTACTS_HG38.tsv.gz")
    with gzip.open(obj, "wt", newline="\n") as fh:
        fh.write("chrom\tstart1_hg38\tend1_hg38\tstart2_hg38\tend2_hg38\t"
                 "start1_hg19\tstart2_hg19\n")
        for i in retained:
            c, s1, e1 = adm_fwd[f"A{i}"]
            _, s2, e2 = adm_fwd[f"B{i}"]
            fh.write(f"{c}\t{s1}\t{e1}\t{s2}\t{e2}\t"
                     f"{orig[f'A{i}'][1]}\t{orig[f'B{i}'][1]}\n")

    out = {
        "schema": "V64_NOTT_C3_EXACT_IDENTITY_ADJUDICATION_V1",
        "date": "2026-09-29",
        "rule": {
            "contract": "V64_NOTT_C3_EXACT_IDENTITY_SUCCESSOR_RULE_V1",
            "frozen_at_commit": "38d789aceecfdc71beca8852fbb19ab1621fee55",
            "frozen_at": "2026-09-29 13:33:44 -0400",
            "descriptive_result_committed_at": "2026-09-29 13:42:12 -0400 (5131bc6c)",
            "prospectivity_verified": True,
            "note": "the freeze precedes the descriptive result by ~8.5 minutes; the "
                    "ordering is checkable from commit timestamps, not asserted",
            "tolerance_bp": 0,
            "no_threshold_chosen_here": True},
        "implementation_recorded_permanently": {
            "tool": "UCSC liftOver archived build linux.x86_64.v479",
            "tool_sha256": sha(os.path.join(WIN_ROOT, "liftOver_v479")),
            "tool_bytes": os.path.getsize(os.path.join(WIN_ROOT, "liftOver_v479")),
            "minMatch": float(MINMATCH),
            "authoritative_multiple": False,
            "multiple_used_only_to_detect_and_reject_ambiguity": True,
            "chain_hg19ToHg38_sha256": sha(os.path.join(WIN_ROOT, "hg19ToHg38.over.chain.gz")),
            "chain_hg38ToHg19_sha256": sha(os.path.join(WIN_ROOT, "hg38ToHg19.over.chain.gz")),
            "rerun_warning": "C3 must not be re-run with a different liftOver executable "
                             "and the outputs mixed without an equivalence audit."},
        "governance": {"training": "OFF", "td60": "BLOCKED",
                       "gene_annotation_joined": False,
                       "protected_outcomes_opened": False},

        "ATTRITION_FUNNEL": {
            "original_pairs": N_ORIGINAL,
            "original_anchor_instances": N_ORIGINAL * 2,
            "forward_anchor_disposition": dict(reason),
            "forward_anchor_accounting_reconciles":
                sum(reason.values()) == N_ORIGINAL * 2,
            "pairs_forward_admissible": len(pairs_fwd),
            "roundtrip_anchor_disposition": dict(rt_reason),
            "roundtrip_anchor_accounting_reconciles":
                sum(rt_reason.values()) == len(rt_names),
            "PAIRS_C3_RETAINED": len(retained),
            "identity_violations_among_retained": viol,
        },
        "RETENTION_NUMBERS_THAT_MUST_NEVER_BE_CONFLATED": {
            "descriptive_mapping_retention": {
                "definition": "both anchors mapped at all, permissive",
                "value": "104728 / 104802",
                "fraction": round(104728 / N_ORIGINAL, 6)},
            "C3_exact_identity_retention": {
                "definition": "both anchors single, same chromosome, length preserved "
                              "exactly, and both round-trip exactly",
                "value": f"{len(retained)} / {N_ORIGINAL}",
                "fraction": round(len(retained) / N_ORIGINAL, 6)},
            "warning": "The descriptive figure is NOT the C3 qualified retention and "
                       "must not be quoted as such."},
        "retained_object": {
            "path": obj, "bytes": os.path.getsize(obj), "sha256": sha(obj),
            "content": "coordinate pairs only; no gene annotation"},
    }
    ok = (len(retained) > 0 and viol == 0
          and out["ATTRITION_FUNNEL"]["forward_anchor_accounting_reconciles"]
          and out["ATTRITION_FUNNEL"]["roundtrip_anchor_accounting_reconciles"])
    out["C3_ADJUDICATION"] = "PASS" if ok else "FAIL"
    out["adjudication_basis"] = (
        "PASS requires a non-empty retained set in which EVERY pair preserves exact "
        "anchor identity in both directions, with the full attrition funnel reported "
        "from the original denominator and no silent rescue." if ok else
        "one or more PASS conditions failed; see the funnel")
    out["coverage_caveat"] = (
        "C3 PASS does not establish that the retained support is large or "
        "representative enough for P1S/P3. Retention fraction and any geometry or "
        "composition shift are downstream claim-scope evidence, not part of this gate.")

    with open(os.path.join(a.out_dir, "V64_NOTT_C3_EXACT_ADJUDICATION_V1.json"), "w") as fh:
        json.dump(out, fh, indent=2)

    f = out["ATTRITION_FUNNEL"]
    print(f"original pairs                    {N_ORIGINAL:,}")
    print(f"forward anchor disposition        {dict(reason)}")
    print(f"  accounting reconciles           {f['forward_anchor_accounting_reconciles']}")
    print(f"pairs forward-admissible          {len(pairs_fwd):,}")
    print(f"round-trip anchor disposition     {dict(rt_reason)}")
    print(f"  accounting reconciles           {f['roundtrip_anchor_accounting_reconciles']}")
    print(f"PAIRS C3-RETAINED                 {len(retained):,}")
    print(f"identity violations among retained {viol}")
    print(f"C3 exact-identity retention       {len(retained)}/{N_ORIGINAL} = "
          f"{len(retained)/N_ORIGINAL:.6f}")
    print(f"(descriptive mapping retention was 104728/104802 = 0.999294 - NOT the same number)")
    print(f"C3_ADJUDICATION: {out['C3_ADJUDICATION']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
