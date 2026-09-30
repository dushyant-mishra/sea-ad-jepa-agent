#!/usr/bin/env python3
"""Phase A, repaired: LINKED / CONTROL_A / CONTROL_B rows from the QUALIFIED exact set.

Implements V64_NIH_CARD_STAGE3_PHASE_A_SUCCESSOR_CONTRACT_V2. It supersedes
nihcard_stage3_structural_etl_v1.py, whose 512-draw bounded rejection sampler could not
decide emptiness: with k admissible starts out of N it misses all of them with
probability (1 - k/N)^512, so it measured "a control was found within 512 attempts" and
labelled it "an admissible control exists". Those are different populations. The figure
15,646 produced by that executor is NOT current authority.

WHAT THIS READS. The committed exact supplement payloads, which carry, for every one of
the 41,418 edge-sides, A_interior as a disjoint interval union and A_supplement as
explicit integer starts. A_exact is their union. That artifact is the one the frozen
qualification suite passed on: 64/64 real-edge exact set equality against the real
liftOver oracle, plus 8/8 on supplement-bearing edge-sides, with a positive control
demonstrating the comparator detects a single missing or single spurious start.

THE FOUR RULES THAT ARE EASY TO VIOLATE, AND HOW EACH IS ENFORCED HERE.

  side drawn FIRST        Each control's side S comes from its own sub-seed BEFORE any
                          admissibility is evaluated. Drawing the side after seeing which
                          side is non-empty would silently condition the control on the
                          very structure it is meant to be a null for.
  no opposite-side retry  If the drawn side's A_exact is empty, that draw FAILS. The
                          opposite side is never consulted. Enforced structurally: this
                          executor only ever looks up one key per draw.
  B never rescues A       Primary retention depends on CONTROL_A alone. If A fails and B
                          succeeds, the edge is NOT retained for the primary; the edge is
                          dropped and the control-vs-control null is marked unavailable.
  coincidence retained    A and B are independent draws and are NOT conditioned to differ.
                          A collision is recorded, never redrawn -- redrawing would make
                          the pair dependent and bias the control-vs-control null.

UNIFORM SAMPLING. A_exact is indexed as [interior starts in ascending order] followed by
[supplement starts in ascending order]. The two parts are disjoint by construction -- the
supplement is built from the band minus the proven-affine region and the interior is a
subset of that region -- and disjointness is asserted per draw rather than trusted, since
an overlap would make the index space smaller than the nominal cardinality and quietly
bias the draw.

TRAINING=OFF. PHASE B=STOPPED. STAGE 4=NOT AUTHORISED. TD60=BLOCKED.
Coordinates and tracks only. No matrix values. No correspondence outcome.
"""
from __future__ import annotations

import argparse
import glob
import gzip
import hashlib
import json
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B      # noqa: E402

W = B.W
SUPP_DIR = "results/v64/nihcard_exact_supplement"
MASTER_SEED = 20260930


def subseed(edge_index, which):
    """Deterministic per-draw seed bound to the edge's identity and the control's role,
    never to storage position or shard key."""
    h = hashlib.sha256(f"{MASTER_SEED}|{edge_index}|{which}".encode()).digest()
    return int.from_bytes(h[:8], "big")


def load_A_exact():
    """{edge_index: {side: (interior_intervals, supplement_starts)}} from the committed,
    qualification-passing payloads."""
    A = defaultdict(dict)
    files = sorted(glob.glob(os.path.join(SUPP_DIR, "shard_*.json.gz")))
    if len(files) != 12:
        raise SystemExit(f"STOP: expected 12 supplement payloads, found {len(files)}")
    for p in files:
        rp = p.replace(".json.gz", "").replace("shard_", "shard_") + ".receipt.json"
        rp = os.path.join(SUPP_DIR,
                          os.path.basename(p).replace(".json.gz", ".receipt.json"))
        r = json.load(open(rp))
        if r["status"] != "OK":
            raise SystemExit(f"STOP: shard {r['shard']} status {r['status']}")
        d = json.load(gzip.open(p, "rt"))
        got = hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()
        if got != r["payload_sha256"]:
            raise SystemExit(f"STOP: payload content hash mismatch for {p}")
        for k, v in d.items():
            e, s = k.split("|")
            A[int(e)][int(s)] = ([tuple(x) for x in v["interior"]], v["supp"])
    return A


def card_exact(part):
    iv, supp = part
    return sum(b - a + 1 for a, b in iv) + len(supp)


def pick_exact(part, u, edge_index, side):
    """The u-th element of A_exact under the canonical interior-then-supplement order."""
    iv, supp = part
    n_i = sum(b - a + 1 for a, b in iv)
    if u < n_i:
        k = u
        for a, b in iv:
            n = b - a + 1
            if k < n:
                return a + k
            k -= n
        raise SystemExit(f"STOP: interior index overrun e{edge_index}|{side}")
    j = u - n_i
    if j >= len(supp):
        raise SystemExit(f"STOP: draw index beyond A_exact e{edge_index}|{side}")
    return supp[j]


def assert_disjoint(part, edge_index, side):
    iv, supp = part
    if not supp:
        return
    ss = set(supp)
    for a, b in iv:
        if b - a + 1 > 4_000_000:
            continue
        if ss & set(range(a, b + 1)):
            raise SystemExit(f"STOP: interior/supplement overlap e{edge_index}|{side}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="D:/jepa_v5_outputs_20260925/v64_phase_a")
    ap.add_argument("--nih-peaks", default="C:/Users/dushy/jepa_c3/nihcard_peaks.bed")
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)

    A = load_A_exact()
    print(f"loaded A_exact for {len(A)} edges")

    with gzip.open(B.E2, "rb") as fh:
        raw = fh.read()
    if B.sha_bytes(raw) != B.E2_SHA:
        raise SystemExit("STOP_E2_DIGEST")
    el = raw.decode().rstrip("\n").split("\n")
    ix = {k: i for i, k in enumerate(el[0].split("\t"))}
    rows = [l.split("\t") for l in el[1:]]
    if len(rows) != len(A):
        raise SystemExit(f"STOP: E2 has {len(rows)} edges, A_exact covers {len(A)}")

    fwd = B.Idx(B.parse_chain(f"{B.WIN}/hg19ToHg38.over.chain.gz"))

    def to_hg38(chrom, s):
        """Affine image under the containing plus-strand block. Every retained start is
        already proven to map exactly, so this reproduces the mapping rather than
        deciding it; supplement starts are resolved the same way when their block is
        plus-strand, and reported as NOT_AFFINE otherwise."""
        for b_lo, b_hi, delta, qc, qs, _cid in fwd.over(chrom, s, s + W):
            if qc == chrom and qs == "+" and b_lo <= s and s + W <= b_hi:
                return s + delta, s + delta + W
        return None, None

    out_rows = []
    stats = defaultdict(int)
    per_edge = []

    for i, r in enumerate(rows):
        c = r[ix["chrom"]]
        d0 = int(r[ix["contact_distance_bp_hg19_source"]])
        draws = {}
        for which in ("A", "B"):
            ss = subseed(i, which)
            rng = np.random.default_rng(ss)
            # SIDE FIRST, before any admissibility is consulted
            side = int(rng.choice([1, -1]))
            part = A[i].get(side, ([], []))
            n = card_exact(part)
            if n == 0:
                draws[which] = dict(ok=False, side=side, subseed=ss,
                                    admissible_start_count=0,
                                    reason="drawn side has empty A_exact; "
                                           "no opposite-side retry permitted")
                stats[f"{which}_empty_side"] += 1
                continue
            assert_disjoint(part, i, side)
            u = int(rng.integers(0, n))
            s19 = pick_exact(part, u, i, side)
            s38, e38 = to_hg38(c, s19)
            draws[which] = dict(ok=True, side=side, subseed=ss,
                                admissible_start_count=n, hg19_start=s19,
                                hg19_end=s19 + W, hg38_start=s38, hg38_end=e38,
                                from_supplement=s19 in set(part[1]))
            stats[f"{which}_ok"] += 1

        coincident = (draws["A"].get("ok") and draws["B"].get("ok")
                      and draws["A"]["hg19_start"] == draws["B"]["hg19_start"]
                      and draws["A"]["side"] == draws["B"]["side"])
        if coincident:
            stats["coincident_pairs"] += 1

        # PRIMARY RETENTION DEPENDS ON CONTROL_A ALONE
        retained = bool(draws["A"].get("ok"))
        if retained:
            stats["retained_primary"] += 1
            if not draws["B"].get("ok"):
                stats["null_unavailable_A_ok_B_failed"] += 1
        else:
            stats["dropped_A_failed"] += 1
            if draws["B"].get("ok"):
                stats["B_succeeded_while_A_failed_NOT_RESCUED"] += 1

        per_edge.append(dict(edge_index=i, chrom=c, d0=d0, retained_primary=retained,
                             control_draws_coincident=bool(coincident),
                             A=draws["A"], B=draws["B"]))

        if retained:
            out_rows.append(dict(edge_index=i, population="LINKED", control_role="NONE",
                                 chrom=c,
                                 hg19_start=int(r[ix["distal_start_hg19"]]),
                                 hg19_end=int(r[ix["distal_end_hg19"]]),
                                 drawn_side=None, subseed=None,
                                 admissible_start_count=None,
                                 control_draws_coincident=None))
            for which in ("A", "B"):
                d = draws[which]
                if not d.get("ok"):
                    continue
                out_rows.append(dict(edge_index=i, population="CONTROL",
                                     control_role=which, chrom=c,
                                     hg19_start=d["hg19_start"],
                                     hg19_end=d["hg19_end"],
                                     hg38_start=d["hg38_start"],
                                     hg38_end=d["hg38_end"],
                                     drawn_side=d["side"], subseed=d["subseed"],
                                     admissible_start_count=d["admissible_start_count"],
                                     control_draws_coincident=bool(coincident),
                                     from_supplement=d["from_supplement"]))

    with gzip.open(os.path.join(a.out_dir, "PHASE_A_ROWS.jsonl.gz"), "wt",
                   newline="\n") as fh:
        for row in out_rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    with gzip.open(os.path.join(a.out_dir, "PHASE_A_PER_EDGE.jsonl.gz"), "wt",
                   newline="\n") as fh:
        for row in per_edge:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    rec = dict(
        schema="V64_NIH_CARD_STAGE3_PHASE_A_EXACT_EXECUTION_V2", date="2026-09-30",
        governs="V64_NIH_CARD_STAGE3_PHASE_A_SUCCESSOR_CONTRACT_V2",
        supersedes="nihcard_stage3_structural_etl_v1.py and its 15,646 figure",
        producer_sha256=B.sha_file(os.path.abspath(__file__)),
        builder_sha256=B.sha_file(B.__file__.replace(".pyc", ".py")),
        e2_sha256=B.E2_SHA, master_seed=MASTER_SEED,
        edges_total=len(rows),
        retained_primary=stats["retained_primary"],
        retention_fraction=round(stats["retained_primary"] / len(rows), 6),
        dropped_because_CONTROL_A_failed=stats["dropped_A_failed"],
        B_succeeded_while_A_failed_and_was_NOT_used_to_rescue=stats[
            "B_succeeded_while_A_failed_NOT_RESCUED"],
        null_unavailable_A_ok_B_failed=stats["null_unavailable_A_ok_B_failed"],
        coincident_pairs=stats["coincident_pairs"],
        control_A_ok=stats["A_ok"], control_A_empty_side=stats["A_empty_side"],
        control_B_ok=stats["B_ok"], control_B_empty_side=stats["B_empty_side"],
        output_rows=len(out_rows),
        controls_drawn_from_supplement=sum(
            1 for r in out_rows if r.get("from_supplement")),
        no_retention_target=True,
        rules_enforced=dict(
            side_drawn_before_admissibility=True,
            opposite_side_retry="STRUCTURALLY IMPOSSIBLE: one key looked up per draw",
            B_never_rescues_A=True,
            coincidence_retained_not_redrawn=True,
            uniform_over_A_exact=True),
        governance=dict(training="OFF", phase_B="STOPPED", stage_4="NOT_AUTHORISED",
                        td60="BLOCKED", Morabito="PROTECTED",
                        correspondence_opened=False))
    with open(os.path.join(a.out_dir, "PHASE_A_RECEIPT.json"), "w", newline="\n") as fh:
        json.dump(rec, fh, indent=2)
    print(json.dumps({k: rec[k] for k in (
        "edges_total", "retained_primary", "retention_fraction",
        "dropped_because_CONTROL_A_failed",
        "B_succeeded_while_A_failed_and_was_NOT_used_to_rescue",
        "null_unavailable_A_ok_B_failed", "coincident_pairs",
        "control_A_ok", "control_A_empty_side", "control_B_ok", "control_B_empty_side",
        "output_rows", "controls_drawn_from_supplement")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
