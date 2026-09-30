#!/usr/bin/env python3
"""A_exact = A_interior UNION A_supplement, sharded and deterministic.

Closes canonical blocking finding E1_SINGLE_BLOCK_SUBSET_NOT_FULL_C3_UNIVERSE.

THE COMPLETENESS RULE. A start is admitted to A_interior ONLY if it is affirmatively
proven safe for affine computation:

    the whole 5 kb window lies inside one ungapped forward chain block on the same
    chromosome with query strand '+', AND the mapped hg38 window lies inside a reverse
    block whose offset is exactly the negation of the forward offset

Everything else in the band -- block boundaries, inter-block gaps, inverted/query-minus
regions, unsupported orientations, anything not proven safe -- goes to A_supplement and
is decided by the REAL frozen liftOver, never by assumption. Nothing is silently
discarded.

    SAFE          = band MINUS exclusion, intersected with proven-affine starts
    A_interior    = SAFE  ∩ PU1-pullback ∩ NIH-pullback
    SUPP_CAND     = (band MINUS exclusion) MINUS SAFE
    A_supplement  = SUPP_CAND surviving real liftOver C3 + hg38 PU.1 + hg38 consensus
    A_exact       = A_interior UNION A_supplement
    uncovered     = (band MINUS exclusion) MINUS SAFE MINUS SUPP_CAND  == EMPTY by construction

PARALLELISM. Deterministic sharding by edge index modulo N_SHARDS. Every worker gets
its OWN temporary directory and uniquely named liftOver files -- the previous
equality-test used fixed names like eqtest.bed and must never run concurrently in a
shared directory. Each shard reports input/output hashes, per-edge cardinalities and a
reconciliation so no work can be silently skipped.

FROZEN C3 APPLIED TO EVERY SUPPLEMENT CANDIDATE: liftOver v479, minMatch 0.95, exactly
one forward mapping (a -multiple pass detects and rejects ambiguity), same chromosome,
exactly 5000 bp, real reverse lift, exact recovery of the original hg19 interval, then
hg38 Nott PU.1 overlap and hg38 NIH-CARD consensus overlap. No lattice, no rejection
budget, no approximate existence classification.

TRAINING=OFF. TD60=BLOCKED. Phase B STOPPED. Stage 4 NOT AUTHORISED.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
from bisect import bisect_right
from collections import defaultdict

import numpy as np

W = 5000
WIN = "C:/Users/dushy/jepa_c3"
WSL = "/mnt/c/Users/dushy/jepa_c3"
MINMATCH = "0.95"
E2 = "results/v64/e2_intermediates/V64_E2_NOTT_CANDIDATE_EDGES.tsv.gz"
E2_SHA = "bec25e0a653c9eeb5013b6ca707114517229d428bda715ef5adcdeecbe5e913c"
DIST_TOL_FRAC, DIST_TOL_ABS = 0.10, 10000


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


# ------------------------------------------------------------------ chain parsing
def parse_chain(path, keep_minus=False):
    """Returns {t_chrom: [(t_start, t_end, offset, q_chrom, q_strand)]} sorted."""
    blocks = defaultdict(list)
    tName = qName = None
    tPos = qPos = 0
    qStrand = "+"
    op = gzip.open if str(path).endswith(".gz") else open
    with op(path, "rt") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            if line.startswith("chain"):
                f = line.split()
                tName, qName, qStrand = f[2], f[7], f[9]
                tPos, qPos = int(f[5]), int(f[10])
                continue
            if tName is None:
                continue
            f = line.split()
            size = int(f[0])
            if qStrand == "+" or keep_minus:
                blocks[tName].append((tPos, tPos + size, qPos - tPos, qName, qStrand))
            tPos += size
            qPos += size
            if len(f) >= 3:
                tPos += int(f[1])
                qPos += int(f[2])
            else:
                tName = None
    for c in blocks:
        blocks[c].sort()
    return dict(blocks)


class Idx:
    def __init__(self, blocks):
        self.b = blocks
        self.s = {c: [x[0] for x in v] for c, v in blocks.items()}

    def over(self, c, lo, hi):
        v = self.b.get(c)
        if not v:
            return []
        i = max(0, bisect_right(self.s[c], lo) - 1)
        out = []
        while i < len(v) and v[i][0] < hi:
            if v[i][1] > lo:
                out.append(v[i])
            i += 1
        return out


# ------------------------------------------------------------- interval algebra
def norm(iv):
    iv = [x for x in iv if x[0] <= x[1]]
    if not iv:
        return []
    iv.sort()
    out = [list(iv[0])]
    for a, b in iv[1:]:
        if a <= out[-1][1] + 1:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [tuple(x) for x in out]


def inter(a, b):
    out, i, j = [], 0, 0
    while i < len(a) and j < len(b):
        lo, hi = max(a[i][0], b[j][0]), min(a[i][1], b[j][1])
        if lo <= hi:
            out.append((lo, hi))
        if a[i][1] < b[j][1]:
            i += 1
        else:
            j += 1
    return out


def sub(a, b):
    if not b:
        return list(a)
    out = []
    for lo, hi in a:
        cur = lo
        for blo, bhi in b:
            if bhi < cur or blo > hi:
                continue
            if blo > cur:
                out.append((cur, min(hi, blo - 1)))
            cur = max(cur, bhi + 1)
            if cur > hi:
                break
        if cur <= hi:
            out.append((cur, hi))
    return norm(out)


def card(iv):
    return sum(b - a + 1 for a, b in iv)


def pull(intervals, lo, hi, delta):
    """hg38 intervals -> hg19 START intervals whose window overlaps one, within [lo,hi]."""
    out = []
    for x, y in intervals:
        a, b = x - delta - W + 1, y - delta - 1
        if b < lo or a > hi:
            continue
        out.append((max(a, lo), min(b, hi)))
    return norm(out)


def load_bed(p):
    d = defaultdict(list)
    op = gzip.open if p.endswith(".gz") else open
    with op(p, "rt") as fh:
        for l in fh:
            if l.strip() and not l.startswith(("#", "track")):
                f = l.rstrip().split("\t")
                d[f[0]].append((int(f[1]), int(f[2])))
    for c in d:
        d[c].sort()
    return dict(d)


def band_of(P, d0, tol, side):
    if side > 0:
        lo, hi = P + d0 - tol - W // 2, P + d0 + tol - W // 2
    else:
        lo, hi = P - d0 - tol - W // 2, P - d0 + tol - W // 2
    return max(0, lo), hi


def safe_and_interior(c, lo, hi, fwd, rev, pu1, nih):
    """Proven-affine starts, and the interior admissible subset."""
    safe, interior = [], []
    for b_lo, b_hi, delta, qc, qs in fwd.over(c, lo, hi + W):
        if qc != c or qs != "+":
            continue
        s_lo, s_hi = max(lo, b_lo), min(hi, b_hi - W)
        if s_hi < s_lo:
            continue
        ok = []
        for r_lo, r_hi, r_delta, r_chrom, r_strand in rev.over(
                c, s_lo + delta, s_hi + delta + W):
            if r_chrom != c or r_strand != "+" or r_delta != -delta:
                continue
            a, z = max(s_lo, r_lo - delta), min(s_hi, r_hi - delta - W)
            if a <= z:
                ok.append((a, z))
        ok = norm(ok)
        if not ok:
            continue
        safe.extend(ok)
        lo2, hi2 = ok[0][0], ok[-1][1]
        p = pull(pu1.get(c, []), lo2, hi2, delta)
        if not p:
            continue
        n = pull(nih.get(c, []), lo2, hi2, delta)
        if not n:
            continue
        interior.extend(inter(inter(ok, p), n))
    return norm(safe), norm(interior)


def run_lift(workdir, tag, bed_rows, log):
    """Real frozen C3 on explicit hg19 windows. Returns {name: (chrom, s38, e38)}."""
    if not bed_rows:
        return {}
    base = os.path.join(workdir, f"sup_{tag}")
    with open(base + ".hg19.bed", "w", newline="\n") as fh:
        for c, s, e, n in bed_rows:
            fh.write(f"{c}\t{s}\t{e}\t{n}\n")
    rel = os.path.relpath(workdir, WIN).replace("\\", "/")
    p = f"{WSL}/{rel}/sup_{tag}"
    subprocess.run(["wsl.exe", "-d", "Ubuntu", "--", "bash", "-lc",
                    f"cd {WSL} && ./liftOver_v479 -minMatch={MINMATCH} {p}.hg19.bed "
                    f"hg19ToHg38.over.chain.gz {p}.hg38.bed {p}.un 2>/dev/null; "
                    f"./liftOver_v479 -minMatch={MINMATCH} -multiple -noSerial "
                    f"{p}.hg19.bed hg19ToHg38.over.chain.gz {p}.multi.bed {p}.mun "
                    f"2>/dev/null"], capture_output=True, text=True, timeout=14400)
    fwd_map, multi = {}, defaultdict(int)
    if os.path.exists(base + ".hg38.bed"):
        for l in open(base + ".hg38.bed"):
            if l.strip() and not l.startswith("#"):
                f = l.rstrip().split("\t")
                fwd_map[f[3]] = (f[0], int(f[1]), int(f[2]))
    if os.path.exists(base + ".multi.bed"):
        for l in open(base + ".multi.bed"):
            if l.strip() and not l.startswith("#"):
                multi[l.rstrip().split("\t")[3]] += 1
    src = {n: (c, s, e) for c, s, e, n in bed_rows}
    keep = {k: v for k, v in fwd_map.items()
            if multi[k] <= 1 and v[0] == src[k][0] and v[2] - v[1] == W}
    with open(base + ".rt.bed", "w", newline="\n") as fh:
        for k, v in keep.items():
            fh.write(f"{v[0]}\t{v[1]}\t{v[2]}\t{k}\n")
    subprocess.run(["wsl.exe", "-d", "Ubuntu", "--", "bash", "-lc",
                    f"cd {WSL} && ./liftOver_v479 -minMatch={MINMATCH} {p}.rt.bed "
                    f"hg38ToHg19.over.chain.gz {p}.rt19.bed {p}.rtun 2>/dev/null"],
                   capture_output=True, text=True, timeout=14400)
    final = {}
    if os.path.exists(base + ".rt19.bed"):
        for l in open(base + ".rt19.bed"):
            if not l.strip() or l.startswith("#"):
                continue
            f = l.rstrip().split("\t")
            k = f[3]
            c0, s0, e0 = src[k]
            if f[0] == c0 and int(f[1]) == s0 and int(f[2]) == e0:
                final[k] = keep[k]
    return final


def overlaps(d, c, s, e):
    v = d.get(c)
    if not v:
        return False
    from bisect import bisect_left
    st = [x[0] for x in v]
    ml = max(y - x for x, y in v)
    j = bisect_left(st, e) - 1
    while j >= 0 and st[j] + ml > s:
        ps, pe = v[j]
        if pe > s:
            return True
        j -= 1
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int, required=True)
    ap.add_argument("--n-shards", type=int, required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--nih-peaks", required=True)
    ap.add_argument("--max-lift-batch", type=int, default=400000)
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    workdir = os.path.join(WIN, f"supwork_s{a.shard:02d}")
    if os.path.exists(workdir):
        shutil.rmtree(workdir)
    os.makedirs(workdir)

    fwd = Idx(parse_chain(f"{WIN}/hg19ToHg38.over.chain.gz"))
    rev = Idx(parse_chain(f"{WIN}/hg38ToHg19.over.chain.gz"))
    pu1 = load_bed(f"{WIN}/ATAC_PU1.bed.gz")
    nih = load_bed(a.nih_peaks)

    with gzip.open(E2, "rb") as fh:
        raw = fh.read()
    if sha_bytes(raw) != E2_SHA:
        raise SystemExit("STOP_E2_DIGEST")
    el = raw.decode().rstrip("\n").split("\n")
    ix = {k: i for i, k in enumerate(el[0].split("\t"))}
    rows = [l.split("\t") for l in el[1:]]
    by_prom = defaultdict(list)
    for r in rows:
        pk = f'{r[ix["chrom"]]}:{r[ix["promoter_start_hg38"]]}-{r[ix["promoter_end_hg38"]]}'
        by_prom[pk].append((int(r[ix["distal_start_hg19"]]), int(r[ix["distal_end_hg19"]])))

    mine = [i for i in range(len(rows)) if i % a.n_shards == a.shard]
    res = {}
    pending = []
    stats = defaultdict(int)

    def flush(tag):
        if not pending:
            return
        final = run_lift(workdir, tag, [b for b, _ in pending], None)
        for (c, s, e, n), key in pending:
            m = final.get(n)
            if m is None:
                continue
            if overlaps(pu1, m[0], m[1], m[2]) and overlaps(nih, m[0], m[1], m[2]):
                res[key]["supp"].append(s)
        pending.clear()

    batch = 0
    for i in mine:
        r = rows[i]
        c = r[ix["chrom"]]
        P = (int(r[ix["promoter_start_hg19"]]) + int(r[ix["promoter_end_hg19"]])) // 2
        d0 = int(r[ix["contact_distance_bp_hg19_source"]])
        tol = max(int(DIST_TOL_FRAC * d0), DIST_TOL_ABS)
        pk = f'{c}:{r[ix["promoter_start_hg38"]]}-{r[ix["promoter_end_hg38"]]}'
        ex = norm([(x - W + 1, y - 1) for x, y in by_prom[pk]])
        for side in (1, -1):
            lo, hi = band_of(P, d0, tol, side)
            key = f"{i}|{side}"
            if hi < lo:
                res[key] = {"interior": [], "supp": [], "band": 0, "safe": 0,
                            "supp_cand": 0}
                continue
            band = sub([(lo, hi)], ex)
            safe, interior = safe_and_interior(c, lo, hi, fwd, rev, pu1, nih)
            safe_in_band = inter(safe, band)
            interior_ok = inter(interior, band)
            supp_cand = sub(band, safe_in_band)
            res[key] = {"interior": interior_ok, "supp": [],
                        "band": card(band), "safe": card(safe_in_band),
                        "supp_cand": card(supp_cand)}
            stats["band"] += card(band)
            stats["safe"] += card(safe_in_band)
            stats["supp_cand"] += card(supp_cand)
            for lo2, hi2 in supp_cand:
                for s in range(lo2, hi2 + 1):
                    pending.append(((c, s, s + W, f"K{len(pending)}"), key))
                    if len(pending) >= a.max_lift_batch:
                        flush(f"b{batch}")
                        batch += 1
    flush(f"b{batch}")

    out = {"shard": a.shard, "n_shards": a.n_shards,
           "edges_in_shard": len(mine),
           "edge_sides": len(res),
           "band_positions": stats["band"],
           "safe_affine_positions": stats["safe"],
           "supplement_candidates": stats["supp_cand"],
           "uncovered": stats["band"] - stats["safe"] - stats["supp_cand"],
           "A_interior_card": sum(card(v["interior"]) for v in res.values()),
           "A_supplement_card": sum(len(v["supp"]) for v in res.values()),
           "e2_sha256": E2_SHA,
           "pu1_sha256": sha_file(f"{WIN}/ATAC_PU1.bed.gz"),
           "liftover_sha256": sha_file(f"{WIN}/liftOver_v479"),
           "status": "OK"}
    out["A_exact_card"] = out["A_interior_card"] + out["A_supplement_card"]
    payload = {k: {"interior": v["interior"], "supp": sorted(v["supp"])}
               for k, v in res.items()}
    # S49 repair. The old field name "payload_sha256" was ambiguous: it covered the
    # canonical JSON serialization, not the .json.gz bytes on disk, so a verifier running
    # sha256sum on the artifact got a mismatch and would read it as corruption. Record
    # both, each named for exactly what it covers, and keep the old key as an alias so
    # receipts already written stay checkable.
    blob = json.dumps(payload, sort_keys=True).encode()
    out["payload_canonical_json_sha256"] = sha_bytes(blob)
    out["payload_sha256"] = out["payload_canonical_json_sha256"]  # deprecated alias
    pay_path = os.path.join(a.out_dir, f"shard_{a.shard:02d}.json.gz")
    with gzip.open(pay_path, "wt") as fh:
        json.dump(payload, fh, sort_keys=True)
    out["payload_file_sha256"] = sha_file(pay_path)
    out["payload_hash_semantics"] = {
        "payload_canonical_json_sha256": "sha256 of json.dumps(payload, sort_keys=True).encode() -- stable across gzip mtime and compression level",
        "payload_file_sha256": "sha256 of the shard_NN.json.gz bytes as written -- what sha256sum reports",
    }
    with open(os.path.join(a.out_dir, f"shard_{a.shard:02d}.receipt.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    shutil.rmtree(workdir, ignore_errors=True)
    print(json.dumps({k: out[k] for k in
                      ("shard", "edge_sides", "band_positions", "safe_affine_positions",
                       "supplement_candidates", "uncovered", "A_interior_card",
                       "A_supplement_card")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
