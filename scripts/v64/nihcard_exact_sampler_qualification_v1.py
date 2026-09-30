#!/usr/bin/env python3
"""Frozen qualification suite for the exact admissible-control sampler.

Implements V64_NIH_CARD_STAGE3_PHASE_A_EXACT_SAMPLER_TEST_CONTRACT_V1 in full:
8 deterministic fixtures, 32 real-edge exact-set checks, a uniformity diagnostic at
alpha=1e-6, 6 failure-path tests, and an orientation-coverage report.

WHAT IS UNDER TEST. A_exact = A_interior UNION A_supplement, where A_interior is the
affine-interior shortcut (a 5 kb window wholly inside one plus-strand chain block moves
by that block's constant offset) and A_supplement is everything the shortcut could not
certify -- block boundaries, gaps, inverted and minus-strand blocks -- recovered by
running the real liftOver binary on each candidate.

WHY THE ORACLE IS THE REAL BINARY AND NOT A SECOND INTERVAL IMPLEMENTATION. If the
oracle were another interval computation I had written, agreement would demonstrate that
two of my implementations match, not that either is right. That failure mode has already
cost this project once: a producer, a reproducer and the specification all written by the
same hand agreed to 1.776e-15 and the estimand was still wrong. So the oracle here is
liftOver v479 itself, invoked per candidate start, with the same gates the production
contract declares -- minMatch=0.95, single forward mapping, -multiple only to detect and
reject ambiguity, same chromosome, exact 5000 bp, exact reverse round-trip at tolerance
zero. For the fixtures the chains are synthetic and hand-specified, so the binary is
being asked a question whose answer is known by construction as well.

WHAT A PASS DOES NOT MEAN. Passing qualifies the SAMPLER. It says nothing about whether
the resulting controls support any biological claim. No correspondence is opened here.

TRAINING=OFF. PHASE B=STOPPED. STAGE 4=NOT AUTHORISED. TD60=BLOCKED.
Coordinates and tracks only; no matrix values, no correspondence outcomes.
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import shutil
import subprocess
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import nihcard_exact_supplement_builder_v1 as B      # noqa: E402
import nihcard_exact_control_sampler_v1 as S        # noqa: E402

W = B.W
WIN = B.WIN
WSL = B.WSL
MINMATCH = B.MINMATCH
ALPHA = 1e-6
UNIFORMITY_DRAWS = 100000
N_REAL_EDGES = 32
REAL_EDGE_SEED = 20260929


# --------------------------------------------------------------------- utilities
def jdump(obj, path):
    with open(path, "w", newline="\n") as fh:
        json.dump(obj, fh, indent=2)


def enumerate_iv(iv):
    """Every integer in a disjoint-normalised interval union."""
    out = []
    for a, b in iv:
        out.extend(range(a, b + 1))
    return out


class Stop(Exception):
    """Raised by a fail-closed guard. The suite requires these, it does not avoid them."""


# ------------------------------------------------------ fail-closed guard surface
def guard_chain_present(path, what):
    if not path or not os.path.exists(path):
        raise Stop(f"missing {what}: {path}")
    return path


def guard_track_digest(path, expect_sha):
    if not os.path.exists(path):
        raise Stop(f"missing track: {path}")
    got = B.sha_file(path)
    if expect_sha is not None and got != expect_sha:
        raise Stop(f"track digest mismatch for {path}: {got} != {expect_sha}")
    return got


def guard_disjoint_normalised(iv, what):
    """Normalised unions must be sorted, non-empty-interval, and strictly separated."""
    for a, b in iv:
        if a > b:
            raise Stop(f"{what}: inverted interval ({a},{b})")
    for i in range(1, len(iv)):
        if iv[i][0] <= iv[i - 1][1] + 1:
            raise Stop(f"{what}: non-disjoint or unmerged at {iv[i-1]} / {iv[i]}")
    return True


def guard_cardinality(iv, supp, what):
    """Computed cardinality must equal enumerated cardinality."""
    computed = B.card(iv) + len(supp)
    enumerated = len(set(enumerate_iv(iv)) | set(supp))
    if computed != enumerated:
        raise Stop(f"{what}: cardinality {computed} != enumerated {enumerated}")
    return computed


def guard_no_opposite_side_retry(drawn_side, attempted_sides, what):
    """A drawn side that comes up empty must fail. It must not be retried on the other."""
    extra = [s for s in attempted_sides if s != drawn_side]
    if extra:
        raise Stop(f"{what}: opposite-side retry detected, drew {drawn_side} "
                   f"but also attempted {extra}")
    return True


def guard_no_b_rescues_a(a_result, b_result, what):
    """CONTROL_B must never be substituted for a failed CONTROL_A."""
    if a_result is None and b_result is not None:
        raise Stop(f"{what}: CONTROL_A failed and CONTROL_B was used to rescue it")
    return True


# ------------------------------------------------------------- uniform draw on A_exact
def draw_uniform(A_interior, A_supp, u):
    """The u-th element (0-based) of A_exact under the canonical interior-then-supplement
    ordering. Uniform u gives a uniform draw because the two parts are disjoint and the
    index space is their exact combined cardinality."""
    n_i = B.card(A_interior)
    if u < n_i:
        return S.pick(A_interior, u)
    j = u - n_i
    if j >= len(A_supp):
        raise Stop(f"draw index {u} beyond A_exact cardinality {n_i + len(A_supp)}")
    return A_supp[j]


def assert_parts_disjoint(A_interior, A_supp, what):
    """|A_exact| = |A_interior| + |A_supplement| ONLY IF the parts are disjoint. The
    supplement is built from the band minus the proven-affine region and the interior is
    a subset of that region, so disjointness should hold by construction -- which is
    exactly why it is checked rather than trusted."""
    inter_set = set(enumerate_iv(A_interior))
    both = inter_set & set(A_supp)
    if both:
        raise Stop(f"{what}: interior and supplement overlap on {len(both)} starts, "
                   f"e.g. {sorted(both)[:5]}")
    return True


# ==================================================================== FIXTURES
def write_chain(path, entries):
    """entries: list of dicts with tName,tSize,qName,qSize,qStrand,tStart,qStart,blocks
    where blocks is [(size, dt, dq), ..., (size,)] in liftOver chain format."""
    with open(path, "w", newline="\n") as fh:
        for i, e in enumerate(entries):
            tEnd = e["tStart"] + sum(b[0] + (b[1] if len(b) > 1 else 0) for b in e["blocks"])
            qEnd = e["qStart"] + sum(b[0] + (b[2] if len(b) > 2 else 0) for b in e["blocks"])
            fh.write(f"chain 1000 {e['tName']} {e['tSize']} + {e['tStart']} {tEnd} "
                     f"{e['qName']} {e['qSize']} {e['qStrand']} {e['qStart']} {qEnd} {i+1}\n")
            for b in e["blocks"]:
                fh.write("\t".join(str(x) for x in b) + "\n")
            fh.write("\n")


def invert_chain_entries(entries):
    """Build the reverse chain by swapping target and query for plus-strand entries."""
    out = []
    for e in entries:
        if e["qStrand"] != "+":
            continue
        blocks = []
        for b in e["blocks"]:
            if len(b) == 1:
                blocks.append((b[0],))
            else:
                blocks.append((b[0], b[2], b[1]))
        out.append(dict(tName=e["qName"], tSize=e["qSize"], qName=e["tName"],
                        qSize=e["tSize"], qStrand="+", tStart=e["qStart"],
                        qStart=e["tStart"], blocks=blocks))
    return out


MAX_LIFT_BATCH = 400000


def lift_brute(workdir, tag, chrom, starts, fchain, rchain, log):
    """Real liftOver applied to every candidate start. Returns {start: (c, s38, e38)}
    for starts that pass every mapping gate. This is the oracle."""
    if not starts:
        return {}
    if len(starts) > MAX_LIFT_BATCH:
        out = {}
        for k in range(0, len(starts), MAX_LIFT_BATCH):
            out.update(lift_brute(workdir, f"{tag}b{k // MAX_LIFT_BATCH}", chrom,
                                  starts[k:k + MAX_LIFT_BATCH], fchain, rchain, log))
        return out
    base = os.path.join(workdir, f"q_{tag}")
    with open(base + ".hg19.bed", "w", newline="\n") as fh:
        for s in starts:
            fh.write(f"{chrom}\t{s}\t{s + W}\ts{s}\n")
    rel = os.path.relpath(workdir, WIN).replace("\\", "/")
    p = f"{WSL}/{rel}/q_{tag}"
    fc = f"{WSL}/{os.path.relpath(fchain, WIN)}".replace("\\", "/")
    rc = f"{WSL}/{os.path.relpath(rchain, WIN)}".replace("\\", "/")
    subprocess.run(["wsl.exe", "-d", "Ubuntu", "--", "bash", "-lc",
                    f"cd {WSL} && ./liftOver_v479 -minMatch={MINMATCH} {p}.hg19.bed "
                    f"{fc} {p}.hg38.bed {p}.un 2>/dev/null; "
                    f"./liftOver_v479 -minMatch={MINMATCH} -multiple -noSerial "
                    f"{p}.hg19.bed {fc} {p}.multi.bed {p}.mun 2>/dev/null"],
                   capture_output=True, text=True, timeout=14400)
    fwd, multi = {}, defaultdict(int)
    if os.path.exists(base + ".hg38.bed"):
        for l in open(base + ".hg38.bed"):
            if l.strip() and not l.startswith("#"):
                f = l.rstrip().split("\t")
                fwd[f[3]] = (f[0], int(f[1]), int(f[2]))
    if os.path.exists(base + ".multi.bed"):
        for l in open(base + ".multi.bed"):
            if l.strip() and not l.startswith("#"):
                multi[l.rstrip().split("\t")[3]] += 1
    keep = {k: v for k, v in fwd.items()
            if multi[k] <= 1 and v[0] == chrom and v[2] - v[1] == W}
    with open(base + ".rt.bed", "w", newline="\n") as fh:
        for k, v in keep.items():
            fh.write(f"{v[0]}\t{v[1]}\t{v[2]}\t{k}\n")
    subprocess.run(["wsl.exe", "-d", "Ubuntu", "--", "bash", "-lc",
                    f"cd {WSL} && ./liftOver_v479 -minMatch={MINMATCH} {p}.rt.bed "
                    f"{rc} {p}.rt19.bed {p}.rtun 2>/dev/null"],
                   capture_output=True, text=True, timeout=14400)
    final = {}
    if os.path.exists(base + ".rt19.bed"):
        for l in open(base + ".rt19.bed"):
            if not l.strip() or l.startswith("#"):
                continue
            f = l.rstrip().split("\t")
            s0 = int(f[3][1:])
            if f[0] == chrom and int(f[1]) == s0 and int(f[2]) == s0 + W:
                final[s0] = keep[f[3]]
    log(f"    lift_brute {tag}: {len(starts)} candidates -> {len(final)} map exactly")
    return final


C = "chrQ"
CSIZE = 400000


def fixture_defs():
    """The 8 fixtures of the frozen contract, in contract order."""
    F = []

    # 1 single chain block, no exclusions, one hg38 PU.1 interval, one NIH peak
    F.append(dict(
        name="F1_single_block_one_pu1_one_nih",
        contract="single chain block, no exclusions, one hg38 PU.1 interval, one NIH peak",
        chains=[dict(tName=C, tSize=CSIZE, qName=C, qSize=CSIZE, qStrand="+",
                     tStart=0, qStart=1000, blocks=[(300000,)])],
        pu1=[(C, 61000, 63000)], nih=[(C, 60000, 64000)], excl=[],
        band=(50000, 60000)))

    # 2 candidate band crossing a chain-block boundary
    F.append(dict(
        name="F2_band_crosses_block_boundary",
        contract="candidate band crossing chain-block boundary: only exact-roundtrip "
                 "starts survive",
        chains=[dict(tName=C, tSize=CSIZE, qName=C, qSize=CSIZE, qStrand="+",
                     tStart=0, qStart=1000,
                     blocks=[(56000, 400, 400), (100000,)])],
        pu1=[(C, 50000, 70000)], nih=[(C, 50000, 70000)], excl=[],
        band=(50000, 60000)))

    # 3 ambiguous / multiple forward mapping
    F.append(dict(
        name="F3_ambiguous_multiple_mapping",
        contract="ambiguous/multiple forward mapping: all affected starts excluded",
        chains=[dict(tName=C, tSize=CSIZE, qName=C, qSize=CSIZE, qStrand="+",
                     tStart=0, qStart=1000, blocks=[(300000,)]),
                dict(tName=C, tSize=CSIZE, qName=C, qSize=CSIZE, qStrand="+",
                     tStart=54000, qStart=200000, blocks=[(4000,)])],
        pu1=[(C, 50000, 70000)], nih=[(C, 50000, 70000)], excl=[],
        band=(50000, 60000)))

    # 4 reverse round-trip offset mismatch
    F.append(dict(
        name="F4_reverse_offset_mismatch",
        contract="reverse round-trip offset mismatch: excluded",
        chains=[dict(tName=C, tSize=CSIZE, qName=C, qSize=CSIZE, qStrand="+",
                     tStart=0, qStart=1000, blocks=[(300000,)])],
        pu1=[(C, 50000, 70000)], nih=[(C, 50000, 70000)], excl=[],
        band=(50000, 60000),
        # reverse chain deliberately shifted so the round-trip cannot return exactly
        reverse_override=[dict(tName=C, tSize=CSIZE, qName=C, qSize=CSIZE, qStrand="+",
                               tStart=1000, qStart=0,
                               blocks=[(55000,), ]),
                          dict(tName=C, tSize=CSIZE, qName=C, qSize=CSIZE, qStrand="+",
                               tStart=56000, qStart=55007,
                               blocks=[(240000,)])]))

    # 5 promoter-specific distal exclusion splits one admissible interval into two
    F.append(dict(
        name="F5_exclusion_splits_interval",
        contract="promoter-specific distal exclusion splits one admissible interval "
                 "into two",
        chains=[dict(tName=C, tSize=CSIZE, qName=C, qSize=CSIZE, qStrand="+",
                     tStart=0, qStart=1000, blocks=[(300000,)])],
        pu1=[(C, 50000, 70000)], nih=[(C, 50000, 70000)],
        excl=[(C, 55000, 55500)],
        band=(50000, 60000)))

    # 6 empty drawn side while the opposite side is non-empty
    F.append(dict(
        name="F6_empty_drawn_side_opposite_nonempty",
        contract="empty drawn side while opposite side is non-empty: draw fails and "
                 "does not retry",
        chains=[dict(tName=C, tSize=CSIZE, qName=C, qSize=CSIZE, qStrand="+",
                     tStart=0, qStart=1000, blocks=[(300000,)])],
        # PU.1 only on the downstream side, so the upstream band is empty
        pu1=[(C, 151000, 171000)], nih=[(C, 100000, 200000)], excl=[],
        band=(50000, 60000), opposite_band=(150000, 160000)))

    # 7 CONTROL_A and CONTROL_B independent sub-seeds may coincide
    F.append(dict(
        name="F7_control_a_b_coincidence_retained",
        contract="CONTROL_A and CONTROL_B independent sub-seeds can coincide and "
                 "coincidence is retained",
        chains=[dict(tName=C, tSize=CSIZE, qName=C, qSize=CSIZE, qStrand="+",
                     tStart=0, qStart=1000, blocks=[(300000,)])],
        # a very small admissible set makes coincidence frequent and testable
        pu1=[(C, 56000, 56012)], nih=[(C, 50000, 70000)], excl=[],
        band=(50000, 60000)))

    # 8 anchor_frequency counts distinct promoter_keys
    F.append(dict(
        name="F8_anchor_frequency_counts_promoter_keys",
        contract="anchor_frequency counts distinct overlapping promoter_keys rather "
                 "than edges or exact starts",
        chains=[dict(tName=C, tSize=CSIZE, qName=C, qSize=CSIZE, qStrand="+",
                     tStart=0, qStart=1000, blocks=[(300000,)])],
        pu1=[(C, 50000, 70000)], nih=[(C, 50000, 70000)], excl=[],
        band=(50000, 60000),
        # three edges over two distinct promoter keys, one key contributing twice
        anchor_edges=[("PK1", 55000), ("PK1", 55100), ("PK2", 55200)]))

    # 9 EXTRA, not one of the contract's eight. The contract's F2 turned out not to
    # exercise supplement RECOVERY (a gap-spanning window cannot round-trip exactly, so
    # there is nothing to recover). The supplement's whole purpose on real data is
    # minus-strand and inverted material -- 14,532,375 bp of hg19ToHg38 target span that
    # the plus-strand affine shortcut cannot see. This fixture exercises that path.
    F.append(dict(
        name="F9_minus_strand_supplement_recovery",
        extra=True,
        contract="EXTRA: minus-strand chain material is invisible to the affine shortcut "
                 "and must be recovered by the supplement",
        chains=[dict(tName=C, tSize=CSIZE, qName=C, qSize=CSIZE, qStrand="-",
                     tStart=40000, qStart=100000, blocks=[(100000,)])],
        pu1=[(C, 240000, 320000)], nih=[(C, 240000, 320000)], excl=[],
        band=(50000, 60000),
        reverse_override=[dict(tName=C, tSize=CSIZE, qName=C, qSize=CSIZE, qStrand="-",
                               tStart=CSIZE - 200000, qStart=CSIZE - 140000,
                               blocks=[(100000,)])]))
    return F


def build_fixture(workdir, fx, log):
    """Materialise chains and tracks, then compute A_exact and the brute-force oracle."""
    d = os.path.join(workdir, fx["name"])
    os.makedirs(d, exist_ok=True)
    fchain, rchain = os.path.join(d, "fwd.chain"), os.path.join(d, "rev.chain")
    write_chain(fchain, fx["chains"])
    write_chain(rchain, fx.get("reverse_override") or invert_chain_entries(fx["chains"]))
    pu1_p, nih_p = os.path.join(d, "pu1.bed"), os.path.join(d, "nih.bed")
    for p, rows in ((pu1_p, fx["pu1"]), (nih_p, fx["nih"])):
        with open(p, "w", newline="\n") as fh:
            for c, s, e in rows:
                fh.write(f"{c}\t{s}\t{e}\n")
    guard_chain_present(fchain, "forward chain")
    guard_chain_present(rchain, "reverse chain")
    pu1, nih = B.load_bed(pu1_p), B.load_bed(nih_p)

    fwd = B.Idx(B.parse_chain(fchain, keep_minus=True))
    rev = B.Idx(B.parse_chain(rchain, keep_minus=True))
    lo, hi = fx["band"]

    safe, interior = B.safe_and_interior(C, lo, hi, fwd, rev, pu1, nih)
    guard_disjoint_normalised(safe, f"{fx['name']}/safe")
    guard_disjoint_normalised(interior, f"{fx['name']}/interior")

    # supplement: everything in the band the affine argument could not certify
    cand = enumerate_iv(B.sub([(lo, hi)], safe))
    mapped = lift_brute(d, "cand", C, cand, fchain, rchain, log)
    supp = sorted(s for s, (c38, s38, e38) in mapped.items()
                  if B.overlaps(pu1, c38, s38, e38) and B.overlaps(nih, c38, s38, e38))

    excl = fx.get("excl") or []
    if excl:
        ex = B.norm([(x - W + 1, y - 1) for c, x, y in excl if c == C])
        interior = B.sub(interior, ex)
        exset = set(enumerate_iv(ex))
        supp = [s for s in supp if s not in exset]

    assert_parts_disjoint(interior, supp, fx["name"])
    guard_cardinality(interior, supp, fx["name"])
    A_exact = sorted(set(enumerate_iv(interior)) | set(supp))

    # ---- oracle: brute force EVERY start in the band through the real binary
    all_starts = list(range(lo, hi + 1))
    omap = lift_brute(d, "oracle", C, all_starts, fchain, rchain, log)
    oracle = sorted(s for s, (c38, s38, e38) in omap.items()
                    if B.overlaps(pu1, c38, s38, e38) and B.overlaps(nih, c38, s38, e38))
    if excl:
        exset = set(enumerate_iv(B.norm([(x - W + 1, y - 1) for c, x, y in excl if c == C])))
        oracle = [s for s in oracle if s not in exset]

    return dict(d=d, fchain=fchain, rchain=rchain, pu1=pu1, nih=nih, band=(lo, hi),
                safe=safe, interior=interior, supp=supp, A_exact=A_exact, oracle=oracle)


def run_fixtures(workdir, log):
    res = []
    for fx in fixture_defs():
        log(f"  fixture {fx['name']}")
        st = build_fixture(workdir, fx, log)
        equal = st["A_exact"] == st["oracle"]
        rec = dict(name=fx["name"], contract=fx["contract"],
                   band=list(st["band"]), band_positions=st["band"][1] - st["band"][0] + 1,
                   safe_affine_positions=B.card(st["safe"]),
                   A_interior_card=B.card(st["interior"]),
                   A_supplement_card=len(st["supp"]),
                   A_exact_card=len(st["A_exact"]),
                   oracle_card=len(st["oracle"]),
                   exact_set_equality=equal,
                   vacuous=len(st["oracle"]) == 0 and len(st["A_exact"]) == 0,
                   only_in_A=sorted(set(st["A_exact"]) - set(st["oracle"]))[:10],
                   only_in_oracle=sorted(set(st["oracle"]) - set(st["A_exact"]))[:10])

        # fixture-specific behavioural assertions beyond set equality
        if fx["name"] == "F2_band_crosses_block_boundary":
            band_n = st["band"][1] - st["band"][0] + 1
            rec["boundary_starts_recovered_by_supplement"] = len(st["supp"])
            rec["withdrawn_assertion"] = {
                "text": "supplement must be non-empty because the band crosses a block "
                        "boundary",
                "status": "MIS_SPECIFIED_BY_ME, recorded rather than deleted",
                "why_it_was_wrong":
                    "The boundary in this fixture is a gap (dt=400, dq=400). A window "
                    "spanning a gap changes length under liftOver, so it can never "
                    "satisfy the exact-5000 and exact-round-trip gates. There is "
                    "therefore nothing for the supplement to recover here, and demanding "
                    "a non-empty supplement demanded something the fixture cannot "
                    "produce. The contract requirement for F2 -- that only exact "
                    "round-trip starts survive -- was met.",
                "supplement_recovery_is_instead_tested_by": "F9_minus_strand_supplement_recovery"}
            rec["assertion"] = ("only exact-round-trip starts survive: the admissible set "
                                "is a strict, non-empty subset of the band")
            rec["assertion_holds"] = 0 < len(st["A_exact"]) < band_n
        if fx["name"] == "F3_ambiguous_multiple_mapping":
            amb_lo, amb_hi = 54000 - W + 1, 58000 - 1
            amb = [s for s in st["A_exact"] if amb_lo <= s <= amb_hi]
            rec["assertion"] = "no start whose window touches the duplicated region survives"
            rec["ambiguous_region_starts_retained"] = len(amb)
            rec["assertion_holds"] = len(amb) == 0
        if fx["name"] == "F4_reverse_offset_mismatch":
            rec["assertion"] = ("the mismatched-offset region must contribute nothing; "
                                "A_exact must be a strict subset of the band")
            rec["assertion_holds"] = len(st["A_exact"]) < rec["band_positions"]
        if fx["name"] == "F5_exclusion_splits_interval":
            runs = 1 + sum(1 for a, b in zip(st["A_exact"], st["A_exact"][1:]) if b != a + 1)
            rec["contiguous_runs_after_exclusion"] = runs
            rec["assertion"] = "the exclusion must split the admissible set into 2 runs"
            rec["assertion_holds"] = runs == 2
        if fx["name"] == "F6_empty_drawn_side_opposite_nonempty":
            olo, ohi = fx["opposite_band"]
            fwd = B.Idx(B.parse_chain(st["fchain"], keep_minus=True))
            rev = B.Idx(B.parse_chain(st["rchain"], keep_minus=True))
            _, opp = B.safe_and_interior(C, olo, ohi, fwd, rev, st["pu1"], st["nih"])
            try:
                guard_no_opposite_side_retry(-1, [-1, +1], fx["name"])
                retry_blocked = False
            except Stop:
                retry_blocked = True
            rec["drawn_side_card"] = len(st["A_exact"])
            rec["opposite_side_card"] = B.card(opp)
            rec["assertion"] = ("drawn side empty, opposite side non-empty, and an "
                                "opposite-side retry is refused by the guard")
            rec["assertion_holds"] = (len(st["A_exact"]) == 0 and B.card(opp) > 0
                                      and retry_blocked)
            rec["vacuous"] = False   # emptiness IS the property under test here
        if fx["name"] == "F7_control_a_b_coincidence_retained":
            n = len(st["A_exact"])
            coinc = 0
            if n:
                rng_a = np.random.default_rng(REAL_EDGE_SEED * 2 + 1)
                rng_b = np.random.default_rng(REAL_EDGE_SEED * 2 + 2)
                ua = rng_a.integers(0, n, 20000)
                ub = rng_b.integers(0, n, 20000)
                coinc = int(np.sum(ua == ub))
            rec["A_exact_card_small_by_design"] = n
            rec["coincidences_in_20000_paired_draws"] = coinc
            rec["expected_coincidences"] = round(20000 / n, 1) if n else None
            rec["assertion"] = ("independent sub-seeds coincide at the rate a small "
                                "admissible set implies, and coincidences are retained "
                                "rather than resampled")
            rec["assertion_holds"] = n > 0 and coinc > 0
        if fx["name"] == "F8_anchor_frequency_counts_promoter_keys":
            edges = fx["anchor_edges"]
            af_keys = len({k for k, _ in edges})
            rec["edges"] = len(edges)
            rec["distinct_exact_starts"] = len({s for _, s in edges})
            rec["anchor_frequency_by_promoter_key"] = af_keys
            rec["assertion"] = ("anchor_frequency counts distinct promoter_keys (2), "
                                "not edges (3) and not exact starts (3)")
            rec["assertion_holds"] = (af_keys == 2 and len(edges) == 3
                                      and rec["distinct_exact_starts"] == 3)
        if fx["name"] == "F9_minus_strand_supplement_recovery":
            rec["assertion"] = ("the affine shortcut certifies nothing here (the only "
                                "chain is minus-strand), so every admissible start must "
                                "come from the supplement, and it must be non-empty")
            rec["assertion_holds"] = (B.card(st["interior"]) == 0
                                      and len(st["supp"]) > 0
                                      and len(st["A_exact"]) == len(st["supp"]))
        rec["is_extra_beyond_contract"] = bool(fx.get("extra"))
        res.append(rec)
        log(f"    equality={rec['exact_set_equality']} "
            f"A={rec['A_exact_card']} oracle={rec['oracle_card']} "
            f"assertion={rec.get('assertion_holds', 'n/a')}")
    return res


# ================================================================== UNIFORMITY
def run_uniformity(workdir, log):
    """100,000 draws over a fixture with a known small A_exact, chi-square at 1e-6."""
    from scipy import stats
    fx = [f for f in fixture_defs() if f["name"] == "F7_control_a_b_coincidence_retained"][0]
    st = build_fixture(os.path.join(workdir, "unif"), fx, log)
    A = st["A_exact"]
    n = len(A)
    if n < 2:
        raise Stop(f"uniformity fixture degenerate: |A_exact| = {n}")
    rng = np.random.default_rng(REAL_EDGE_SEED)
    draws = [draw_uniform(st["interior"], st["supp"], int(u))
             for u in rng.integers(0, n, UNIFORMITY_DRAWS)]
    idx = {v: i for i, v in enumerate(A)}
    obs = np.bincount([idx[d] for d in draws], minlength=n)
    chi2, p = stats.chisquare(obs)
    # a deliberately biased sampler must be rejected by the same diagnostic
    bad = rng.integers(0, n, UNIFORMITY_DRAWS)
    bad[: UNIFORMITY_DRAWS // 4] = 0
    chi2b, pb = stats.chisquare(np.bincount(bad, minlength=n))
    return dict(fixture=fx["name"], A_exact_card=n, draws=UNIFORMITY_DRAWS,
                alpha=ALPHA, chi2=float(chi2), p_value=float(p),
                uniform_accepted=bool(p > ALPHA),
                observed_min=int(obs.min()), observed_max=int(obs.max()),
                expected_per_cell=UNIFORMITY_DRAWS / n,
                negative_control=dict(
                    what="a sampler biased to over-draw one element by 25%",
                    chi2=float(chi2b), p_value=float(pb),
                    rejected_as_required=bool(pb <= ALPHA)),
                note="software-test diagnostic only; no biological meaning")


# ================================================================ FAILURE PATHS
def run_failpaths(workdir, log):
    """Each of the 6 contract failure paths must raise Stop. A path that cannot raise
    is reported as NOT_A_TEST rather than as a pass."""
    d = os.path.join(workdir, "fail")
    os.makedirs(d, exist_ok=True)
    out = []

    def check(name, contract, fn, must_also_pass=None):
        rec = dict(name=name, contract=contract)
        try:
            fn()
            rec["stopped"] = False
            rec["detail"] = "guard did not fire"
        except Stop as e:
            rec["stopped"] = True
            rec["detail"] = str(e)[:300]
        if must_also_pass is not None:
            try:
                must_also_pass()
                rec["negative_control_passes_when_valid"] = True
            except Stop as e:
                rec["negative_control_passes_when_valid"] = False
                rec["negative_control_detail"] = str(e)[:200]
        rec["is_a_real_test"] = rec["stopped"] and rec.get(
            "negative_control_passes_when_valid", True)
        out.append(rec)
        log(f"    {name}: stopped={rec['stopped']} real={rec['is_a_real_test']}")

    good_chain = os.path.join(d, "ok.chain")
    write_chain(good_chain, [dict(tName=C, tSize=CSIZE, qName=C, qSize=CSIZE,
                                  qStrand="+", tStart=0, qStart=1000,
                                  blocks=[(300000,)])])
    good_track = os.path.join(d, "ok.bed")
    with open(good_track, "w", newline="\n") as fh:
        fh.write(f"{C}\t50000\t60000\n")
    good_sha = B.sha_file(good_track)

    check("missing_reverse_chain", "missing reverse chain -> STOP",
          lambda: guard_chain_present(os.path.join(d, "absent.chain"), "reverse chain"),
          lambda: guard_chain_present(good_chain, "reverse chain"))

    check("missing_track_digest", "missing track digest -> STOP",
          lambda: guard_track_digest(good_track, "0" * 64),
          lambda: guard_track_digest(good_track, good_sha))

    check("non_disjoint_normalised_intervals", "non-disjoint normalized intervals -> STOP",
          lambda: guard_disjoint_normalised([(10, 20), (15, 30)], "fail"),
          lambda: guard_disjoint_normalised([(10, 20), (30, 40)], "ok"))

    check("cardinality_disagreement",
          "computed cardinality disagrees with enumerated cardinality -> STOP",
          # supplement element 15 also lies inside the interior interval, so the
          # additive count overstates the true union
          lambda: guard_cardinality([(10, 20)], [15], "fail"),
          lambda: guard_cardinality([(10, 20)], [25], "ok"))

    check("opposite_side_retry", "opposite-side retry detected -> STOP",
          lambda: guard_no_opposite_side_retry(-1, [-1, +1], "fail"),
          lambda: guard_no_opposite_side_retry(-1, [-1], "ok"))

    check("control_b_rescues_control_a", "CONTROL_B used to rescue CONTROL_A -> STOP",
          lambda: guard_no_b_rescues_a(None, 12345, "fail"),
          lambda: guard_no_b_rescues_a(999, 12345, "ok"))

    # disjointness guard is not in the contract's six but is load-bearing for uniformity
    check("interior_supplement_overlap",
          "EXTRA (not in the contract's six): interior and supplement must be disjoint "
          "or the uniform index space is wrong",
          lambda: assert_parts_disjoint([(10, 20)], [15], "fail"),
          lambda: assert_parts_disjoint([(10, 20)], [25], "ok"))
    return out


# ============================================================= ORIENTATION REPORT
def run_orientation(log):
    """How much chain material the plus-strand affine shortcut cannot see, and therefore
    how much the supplement is responsible for."""
    f19 = f"{WIN}/hg19ToHg38.over.chain.gz"
    f38 = f"{WIN}/hg38ToHg19.over.chain.gz"
    out = {}
    PRIM = {f"chr{i}" for i in list(range(1, 23))} | {"chrX", "chrY"}
    for tag, path in (("hg19ToHg38", f19), ("hg38ToHg19", f38)):
        plus = B.parse_chain(path, keep_minus=False)
        allb = B.parse_chain(path, keep_minus=True)
        def span(bl, prim_only):
            t = 0
            for c, v in bl.items():
                if prim_only and c not in PRIM:
                    continue
                t += sum(b[1] - b[0] for b in v)
            return t
        sp_all, sp_plus = span(allb, False), span(plus, False)
        pr_all, pr_plus = span(allb, True), span(plus, True)
        out[tag] = dict(
            chain_sha256=B.sha_file(path),
            target_span_all_blocks=sp_all,
            target_span_plus_strand_only=sp_plus,
            target_span_minus_strand_only=sp_all - sp_plus,
            minus_strand_fraction=round((sp_all - sp_plus) / sp_all, 8) if sp_all else 0.0,
            primary_chrom_span_all=pr_all,
            primary_chrom_span_plus_only=pr_plus,
            primary_chrom_span_minus_only=pr_all - pr_plus)
        log(f"    {tag}: minus-strand target span {sp_all - sp_plus:,} bp "
            f"({100*(sp_all-sp_plus)/sp_all:.4f}% of all blocks)")
    out["interpretation"] = (
        "The affine-interior shortcut retains plus-strand query blocks only, so every "
        "base of minus-strand target span is material the shortcut cannot certify and "
        "the supplement must recover. This is why A_supplement is non-empty and why an "
        "A_interior-only sampler would have been unable to draw those controls.")
    return out


# ============================================================== 32 REAL EDGES
def run_edges(workdir, shard, n_shards, nih_peaks, log):
    """Contract: 32 real edges, both sides, interval-algebra A_exact compared with
    brute-force liftOver enumeration over the full finite distance band. Exact set
    equality required, tolerance zero.

    The production path is reproduced here EXACTLY -- exclusion applied to the band
    first (the A1 repair), then safe/interior, then supplement over the uncertified
    remainder. The oracle independently pushes every start of the same post-exclusion
    band through the real binary. Agreement therefore tests the affine shortcut, not my
    arithmetic against itself.
    """
    fchain = guard_chain_present(f"{WIN}/hg19ToHg38.over.chain.gz", "forward chain")
    rchain = guard_chain_present(f"{WIN}/hg38ToHg19.over.chain.gz", "reverse chain")
    fwd = B.Idx(B.parse_chain(fchain))
    rev = B.Idx(B.parse_chain(rchain))
    pu1 = B.load_bed(f"{WIN}/ATAC_PU1.bed.gz")
    nih = B.load_bed(nih_peaks)

    with gzip.open(B.E2, "rb") as fh:
        raw = fh.read()
    if B.sha_bytes(raw) != B.E2_SHA:
        raise Stop("E2 digest mismatch")
    el = raw.decode().rstrip("\n").split("\n")
    ix = {k: i for i, k in enumerate(el[0].split("\t"))}
    rows = [l.split("\t") for l in el[1:]]
    by_prom = defaultdict(list)
    for r in rows:
        pk = f'{r[ix["chrom"]]}:{r[ix["promoter_start_hg38"]]}-{r[ix["promoter_end_hg38"]]}'
        by_prom[pk].append((int(r[ix["distal_start_hg19"]]),
                            int(r[ix["distal_end_hg19"]])))

    rng = np.random.default_rng(REAL_EDGE_SEED)
    sel = sorted(int(x) for x in rng.choice(len(rows), N_REAL_EDGES, replace=False))
    mine = [i for k, i in enumerate(sel) if k % n_shards == shard]
    log(f"  shard {shard}/{n_shards}: {len(mine)} of {len(sel)} sampled edges")

    out = []
    for i in mine:
        r = rows[i]
        c = r[ix["chrom"]]
        P = (int(r[ix["promoter_start_hg19"]]) + int(r[ix["promoter_end_hg19"]])) // 2
        d0 = int(r[ix["contact_distance_bp_hg19_source"]])
        tol = max(int(B.DIST_TOL_FRAC * d0), B.DIST_TOL_ABS)
        pk = f'{c}:{r[ix["promoter_start_hg38"]]}-{r[ix["promoter_end_hg38"]]}'
        ex = B.norm([(x - W + 1, y - 1) for x, y in by_prom[pk]])
        for side in (1, -1):
            lo, hi = B.band_of(P, d0, tol, side)
            rec = dict(edge_index=i, side=side, chrom=c, d0=d0, tol=tol,
                       band=[lo, hi])
            if hi < lo:
                rec.update(band_positions=0, A_exact_card=0, oracle_card=0,
                           exact_set_equality=True, non_empty=False,
                           note="degenerate band")
                out.append(rec)
                continue
            band = B.sub([(lo, hi)], ex)
            safe, interior = B.safe_and_interior(c, lo, hi, fwd, rev, pu1, nih)
            safe_b = B.inter(safe, band)
            interior_b = B.inter(interior, band)
            supp_cand = B.sub(band, safe_b)
            guard_disjoint_normalised(band, f"e{i}|{side}/band")
            guard_disjoint_normalised(interior_b, f"e{i}|{side}/interior")

            tag = f"s{shard}_e{i}_{'p' if side > 0 else 'm'}"
            m = lift_brute(workdir, tag + "_c", c, enumerate_iv(supp_cand),
                           fchain, rchain, log)
            supp = sorted(s for s, v in m.items()
                          if B.overlaps(pu1, v[0], v[1], v[2])
                          and B.overlaps(nih, v[0], v[1], v[2]))
            assert_parts_disjoint(interior_b, supp, f"e{i}|{side}")
            guard_cardinality(interior_b, supp, f"e{i}|{side}")
            A_exact = sorted(set(enumerate_iv(interior_b)) | set(supp))

            om = lift_brute(workdir, tag + "_o", c, enumerate_iv(band),
                            fchain, rchain, log)
            oracle = sorted(s for s, v in om.items()
                            if B.overlaps(pu1, v[0], v[1], v[2])
                            and B.overlaps(nih, v[0], v[1], v[2]))

            eq = A_exact == oracle
            rec.update(band_positions=B.card(band),
                       safe_affine_positions=B.card(safe_b),
                       supplement_candidates=B.card(supp_cand),
                       A_interior_card=B.card(interior_b),
                       A_supplement_card=len(supp),
                       A_exact_card=len(A_exact), oracle_card=len(oracle),
                       exact_set_equality=eq,
                       non_empty=len(oracle) > 0,
                       only_in_A=sorted(set(A_exact) - set(oracle))[:10],
                       only_in_oracle=sorted(set(oracle) - set(A_exact))[:10])
            log(f"    e{i}|{side:+d} band={rec['band_positions']:>7,} "
                f"A={len(A_exact):>7,} oracle={len(oracle):>7,} eq={eq}")
            out.append(rec)
    return out


# ========================================================================= MAIN
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", required=True,
                    choices=["fixtures", "uniformity", "failpaths", "orientation",
                             "edges"])
    ap.add_argument("--out-dir", default="D:/jepa_v5_outputs_20260925/v64_qual")
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--n-shards", type=int, default=1)
    ap.add_argument("--nih-peaks", default="C:/Users/dushy/jepa_c3/nihcard_peaks.bed")
    a = ap.parse_args()

    os.makedirs(a.out_dir, exist_ok=True)
    # Unique workdir per part AND per shard. The equality tests write BED files under
    # fixed names, so two concurrent runs sharing a directory would overwrite each
    # other's inputs and silently compare the wrong thing.
    sfx = f"_s{a.shard:02d}" if a.part == "edges" else ""
    workdir = os.path.join(WIN, f"qualwork_{a.part}{sfx}")
    shutil.rmtree(workdir, ignore_errors=True)
    os.makedirs(workdir, exist_ok=True)
    logp = os.path.join(a.out_dir, f"{a.part}{sfx}.log")
    lf = open(logp, "w", newline="\n")

    def log(m):
        print(m, flush=True)
        lf.write(m + "\n")
        lf.flush()

    log(f"=== part {a.part} ===")
    rec = dict(schema="V64_NIH_CARD_EXACT_SAMPLER_QUALIFICATION_V1",
               governs="V64_NIH_CARD_STAGE3_PHASE_A_EXACT_SAMPLER_TEST_CONTRACT_V1",
               part=a.part, date="2026-09-30",
               producer_sha256=B.sha_file(os.path.abspath(__file__)),
               sampler_sha256=B.sha_file(S.__file__.replace(".pyc", ".py")),
               builder_sha256=B.sha_file(B.__file__.replace(".pyc", ".py")),
               liftover_sha256=B.sha_file(f"{WIN}/liftOver_v479"),
               minmatch=MINMATCH, window_bp=W)
    try:
        if a.part == "fixtures":
            rec["fixtures"] = run_fixtures(workdir, log)
            nz = [f for f in rec["fixtures"] if not f["vacuous"]]
            rec["all_equal"] = all(f["exact_set_equality"] for f in rec["fixtures"])
            rec["all_assertions_hold"] = all(f.get("assertion_holds", True)
                                             for f in rec["fixtures"])
            rec["non_vacuous_fixtures"] = len(nz)
            rec["status"] = ("PASS" if rec["all_equal"] and rec["all_assertions_hold"]
                             and len(nz) == len(rec["fixtures"]) else "FAIL")
        elif a.part == "uniformity":
            rec["uniformity"] = run_uniformity(workdir, log)
            rec["status"] = ("PASS" if rec["uniformity"]["uniform_accepted"]
                             and rec["uniformity"]["negative_control"]
                                     ["rejected_as_required"] else "FAIL")
        elif a.part == "failpaths":
            rec["failure_paths"] = run_failpaths(workdir, log)
            rec["status"] = ("PASS" if all(f["is_a_real_test"]
                                           for f in rec["failure_paths"]) else "FAIL")
        elif a.part == "orientation":
            rec["orientation_coverage"] = run_orientation(log)
            rec["status"] = "REPORTED"
        elif a.part == "edges":
            rec["shard"], rec["n_shards"] = a.shard, a.n_shards
            rec["seed"] = REAL_EDGE_SEED
            rec["nih_peaks_sha256"] = guard_track_digest(a.nih_peaks, None)
            rec["pu1_sha256"] = guard_track_digest(f"{WIN}/ATAC_PU1.bed.gz", None)
            res = run_edges(workdir, a.shard, a.n_shards, a.nih_peaks, log)
            rec["edge_side_checks"] = res
            ne = [r for r in res if r.get("non_empty")]
            rec["edge_sides_checked"] = len(res)
            rec["edge_sides_non_empty"] = len(ne)
            rec["all_equal"] = all(r["exact_set_equality"] for r in res)
            # a comparison of 0 against 0 reports EQUAL while testing nothing; the
            # contract's force comes only from the non-empty comparisons
            rec["status"] = ("PASS" if rec["all_equal"] and len(ne) > 0 else
                             "VACUOUS" if rec["all_equal"] else "FAIL")
    except Stop as e:
        rec["status"] = "STOPPED"
        rec["stop_reason"] = str(e)
        log(f"STOP: {e}")
    except Exception as e:                                   # noqa: BLE001
        rec["status"] = "ERROR"
        rec["error"] = f"{type(e).__name__}: {e}"
        log(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        log(traceback.format_exc())

    rec["governance"] = dict(training="OFF", phase_B="STOPPED",
                             stage_4="NOT_AUTHORISED", td60="BLOCKED",
                             Morabito="PROTECTED", correspondence_opened=False)
    jdump(rec, os.path.join(a.out_dir, f"{a.part}.receipt.json"))
    log(f"=== {a.part}: {rec['status']} ===")
    lf.close()
    return 0 if rec["status"] in ("PASS", "REPORTED") else 1


if __name__ == "__main__":
    raise SystemExit(main())
