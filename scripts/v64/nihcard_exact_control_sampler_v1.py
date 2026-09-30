#!/usr/bin/env python3
"""Exact admissible-control-set construction by chain-block interval algebra.

Implements the exact_computation_strategy of
V64_NIH_CARD_STAGE3_PHASE_A_SUCCESSOR_CONTRACT_V2.

WHY THIS EXISTS. My previous design used a 512-draw rejection sampler to decide
whether an edge had any admissible control. The audit showed the arithmetic is fatal:
with k admissible starts out of N, a bounded search misses them all with probability
(1 - k/N)^512, and the genome-wide PU.1 overlap rate gives no per-edge lower bound on
k/N. An edge with one valid start in 200,000 is missed 99.74% of the time. The funnel
would then have measured "a control was found within 512 attempts" and labelled it
"an admissible control exists" -- two different scientific populations.

Note the nuance that makes this specifically an EXISTENCE bug: conditional on success,
rejection sampling does draw uniformly from the admissible set. The bias is not among
the successes. It is false-negative classification of edges as unsupported.

THE EXACT METHOD. A 5 kb window lying wholly inside one ungapped chain block is
translated by that block's constant offset. So every hg38 constraint pulls back to an
hg19 start interval exactly:

    window [s, s+5000) inside hg19 block b with offset d  ->  hg38 [s+d, s+d+5000)
    hg38 interval I overlapped  <->  s in [I.start - d - 4999, I.end - d - 1]

The admissible set is therefore a finite union of integer intervals, computed without
enumerating a single base, and its exact cardinality supports uniform sampling by
cumulative count. No lattice and no draw budget anywhere.

CONSERVATISM, STATED. Restricting to windows wholly inside one ungapped block is a
SUBSET of what liftOver might map. It cannot admit an inadmissible control, but it
could in principle miss one that liftOver would map exactly across a block boundary.
That is why the frozen test contract requires exact set equality against brute-force
liftOver enumeration on fixtures and on 32 real edges: the claim is tested, not
assumed.

TRAINING=OFF. TD60=BLOCKED. Coordinates only; no matrix values, no correspondence.
"""
from __future__ import annotations

import gzip
from bisect import bisect_right
from collections import defaultdict

W = 5000


# ----------------------------------------------------------------- chain parsing
def parse_chain(path):
    """hg19->hg38 style chain -> {t_chrom: sorted [(t_start, t_end, offset, q_chrom)]}.

    Only + strand target blocks are retained; liftOver's standard chains for these
    assemblies are + strand on the query side, and any other case is skipped rather
    than guessed at.
    """
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
                tName, qName = f[2], f[7]
                qStrand = f[9]
                tPos, qPos = int(f[5]), int(f[10])
                continue
            if tName is None:
                continue
            f = line.split()
            size = int(f[0])
            if qStrand == "+":
                blocks[tName].append((tPos, tPos + size, qPos - tPos, qName))
            tPos += size
            qPos += size
            if len(f) >= 3:
                tPos += int(f[1])
                qPos += int(f[2])
            else:
                tName = None
    out = {}
    for c, v in blocks.items():
        v.sort()
        out[c] = v
    return out


class ChainIndex:
    def __init__(self, blocks):
        self.blocks = blocks
        self.starts = {c: [b[0] for b in v] for c, v in blocks.items()}

    def block_at(self, chrom, pos):
        v = self.blocks.get(chrom)
        if not v:
            return None
        i = bisect_right(self.starts[chrom], pos) - 1
        if i < 0:
            return None
        b = v[i]
        return b if b[0] <= pos < b[1] else None

    def blocks_overlapping(self, chrom, lo, hi):
        v = self.blocks.get(chrom)
        if not v:
            return []
        i = bisect_right(self.starts[chrom], lo) - 1
        if i < 0:
            i = 0
        out = []
        while i < len(v) and v[i][0] < hi:
            if v[i][1] > lo:
                out.append(v[i])
            i += 1
        return out


# -------------------------------------------------------------- interval algebra
def norm(iv):
    """Sort, merge and disjoint-normalise a list of inclusive integer intervals."""
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
        lo = max(a[i][0], b[j][0])
        hi = min(a[i][1], b[j][1])
        if lo <= hi:
            out.append((lo, hi))
        if a[i][1] < b[j][1]:
            i += 1
        else:
            j += 1
    return out


def subtract(a, b):
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


def pick(iv, k):
    """The k-th integer (0-based) of a disjoint-normalised interval union."""
    for a, b in iv:
        n = b - a + 1
        if k < n:
            return a + k
        k -= n
    raise IndexError("k beyond cardinality")


# ------------------------------------------------------- the admissible-set build
def starts_overlapping(intervals, lo, hi, delta):
    """hg38 intervals -> hg19 START intervals whose window overlaps one of them.

    window [s, s+W) overlaps hg38 [x, y)  <->  s+delta < y and s+delta+W > x
                                          <->  s in [x-delta-W+1, y-delta-1]
    Restricted to [lo, hi].
    """
    out = []
    for x, y in intervals:
        a = x - delta - W + 1
        b = y - delta - 1
        if b < lo or a > hi:
            continue
        out.append((max(a, lo), min(b, hi)))
    return norm(out)


def admissible_starts(chrom, P, d0, tol, side, fwd, rev, pu1_by_chrom, nih_by_chrom,
                      excl_hg19):
    """Exact integer-start set for one edge and one pre-drawn side."""
    if side > 0:
        band_lo, band_hi = P + d0 - tol - W // 2, P + d0 + tol - W // 2
    else:
        band_lo, band_hi = P - d0 - tol - W // 2, P - d0 + tol - W // 2
    band_lo = max(0, band_lo)
    if band_hi < band_lo:
        return []
    acc = []
    for b_lo, b_hi, delta, q_chrom in fwd.blocks_overlapping(chrom, band_lo,
                                                             band_hi + W):
        if q_chrom != chrom:
            continue
        s_lo = max(band_lo, b_lo)
        s_hi = min(band_hi, b_hi - W)          # whole window inside this block
        if s_hi < s_lo:
            continue
        # exact reverse round trip: hg38 window must sit in a reverse block whose
        # offset is exactly -delta, so s + delta + (-delta) == s
        rev_ok = []
        for r_lo, r_hi, r_delta, r_chrom in rev.blocks_overlapping(
                chrom, s_lo + delta, s_hi + delta + W):
            if r_chrom != chrom or r_delta != -delta:
                continue
            a = max(s_lo, r_lo - delta)
            z = min(s_hi, r_hi - delta - W)
            if a <= z:
                rev_ok.append((a, z))
        rev_ok = norm(rev_ok)
        if not rev_ok:
            continue
        lo2, hi2 = rev_ok[0][0], rev_ok[-1][1]
        pu = starts_overlapping(pu1_by_chrom.get(chrom, []), lo2, hi2, delta)
        if not pu:
            continue
        nh = starts_overlapping(nih_by_chrom.get(chrom, []), lo2, hi2, delta)
        if not nh:
            continue
        acc.extend(inter(inter(rev_ok, pu), nh))
    A = norm(acc)
    if excl_hg19:
        ex = norm([(x - W + 1, y - 1) for x, y in excl_hg19])
        A = subtract(A, ex)
    return A
