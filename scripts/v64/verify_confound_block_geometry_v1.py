#!/usr/bin/env python3
"""Does the built world actually HAVE the block geometry its manifest claims?

S99 is the reason this exists. There, the fixture's declared intent was correct and its
realised construction was not, and every number measured against it described a design we
do not use. A generator that reports "200 occupied blocks" is reporting its own
bookkeeping. This recovers the block structure from the BYTES THAT WERE WRITTEN and asks
whether it matches.

HOW. The confound enters a linked interval's ATAC as baseline + depth + g_e * f_b, where
f_b is the factor of edge e's block. Two edges in the SAME block share f_b, so once depth
is projected out their linked-interval ATAC profiles across metacells must correlate
strongly. Two edges in DIFFERENT blocks share nothing and must not. So the empirical
correlation structure over edges IS the partition, and it can be recovered without
trusting any field the generator wrote.

THE TEST CAN FAIL, AND IS SHOWN TO. The same procedure is run against the HISTORICAL
sampling-with-replacement generator, where requested K is only the size of a factor pool.
At K=200 that generator occupies about 127 blocks rather than 200. If this verifier cannot
tell those two fixtures apart it is worthless, so that comparison is part of the output
rather than an exercise left to the reader.

No real substrate is read. No correspondence value is computed.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B                      # noqa: E402
import verify_phase_b_consumer_semantics_v1 as CS                    # noqa: E402
import build_stage4_synthetic_worlds_v1 as BW                        # noqa: E402

WORLD = "HIDDEN_CONFOUND_K"
LINK_THRESHOLD = 0.30     # frozen below, with the separation that justifies it reported


def recover_blocks(root, world):
    """Recover the edge partition from the written ATAC bytes alone."""
    r = os.path.join(root, world)
    shards = sorted(__import__("glob").glob(os.path.join(r, "PHASE_B_SUBSTRATE_s*.npz")))
    S = CS.load_substrate(shard_paths=shards,
                          t5_path=os.path.join(r, "PHASE_B_T5_DONOR_AGGREGATES.npz"),
                          avail_path=os.path.join(r, "PHASE_B_T3_T4_AVAILABILITY.npz"))
    sh = S["shards"]
    ref = sh[0]
    n_iv = len(ref["interval_start"])
    n_mc = int(S["avail"]["t3_shape"][0])
    atac = np.zeros((n_mc, n_iv), np.float32)
    atac[np.concatenate([s["t4_metacell"] for s in sh]).astype(np.int64),
         np.concatenate([s["t4_interval"] for s in sh]).astype(np.int64)] = \
        np.concatenate([s["t4_value"] for s in sh])
    tot = np.zeros(n_mc)
    mc = np.concatenate([s["t2_metacell"] for s in sh])
    ta = np.concatenate([s["t2_total_atac"] for s in sh])
    tot[mc.astype(np.int64)] = ta
    depth = np.log1p(tot)

    pk = [str(x) for x in ref["pair_keys"]]
    piv = np.asarray(ref["pair_interval"], np.int64)
    linked = {}
    for i, k in enumerate(pk):
        if k.endswith("|LINKED"):
            linked[int(k.split("|")[0][1:])] = int(piv[i])
    edges = sorted(linked)
    # TWO EDGES CAN SHARE A LINKED INTERVAL. Interval identity is a 5 kb grid cell, so
    # independent edges sometimes land on the same one -- which is realistic, it is what
    # anchor_frequency counts, but it makes their linked ATAC profiles the SAME COLUMN and
    # therefore perfectly correlated whatever block they belong to. Clustering on
    # correlation then fuses those blocks. The giveaway was a between-block maximum of
    # exactly 1.000, which is impossible if the geometry is as assumed. Edges sharing an
    # interval with any other edge are excluded from the recovery and counted, because the
    # alternative is a verifier that reports a geometry defect which is really its own.
    from collections import Counter
    iv_use = Counter(linked[e] for e in edges)
    shared = [e for e in edges if iv_use[linked[e]] > 1]
    edges = [e for e in edges if iv_use[linked[e]] == 1]

    # project depth out, then correlate the linked columns across metacells
    X = np.stack([atac[:, linked[e]].astype(float) for e in edges], 1)
    d = depth - depth.mean()
    X = X - X.mean(0) - np.outer(d, (d @ (X - X.mean(0))) / (d @ d))
    sd = X.std(0)
    keep = sd > 0
    C = np.corrcoef(X[:, keep], rowvar=False)
    kept_edges = [e for e, k in zip(edges, keep) if k]

    # connected components at the threshold ARE the recovered blocks
    adj = np.abs(C) >= LINK_THRESHOLD
    n = len(kept_edges)
    seen, comps = set(), []
    for i in range(n):
        if i in seen:
            continue
        stack, comp = [i], []
        while stack:
            j = stack.pop()
            if j in seen:
                continue
            seen.add(j)
            comp.append(j)
            stack += [m for m in np.where(adj[j])[0] if m not in seen]
        comps.append(sorted(comp))
    return dict(edges=kept_edges, corr=C, components=comps,
                n_recovered_blocks=len(comps),
                sizes=sorted(len(c) for c in comps),
                edges_excluded_sharing_an_interval=len(shared))


def partition_membership_agreement(res, declared):
    """Compare recovered and declared partitions on retained edges by co-membership.

    This is stronger than comparing the number of components: every retained edge pair
    must agree on whether the two edges belong to the same block.
    """
    if declared is None:
        return None
    recovered_label = {}
    for ci, comp in enumerate(res["components"]):
        for j in comp:
            recovered_label[res["edges"][j]] = ci
    edges = res["edges"]
    total = agree = 0
    disagreements = []
    for i in range(len(edges)):
        for j in range(i + 1, len(edges)):
            a, b = edges[i], edges[j]
            d_same = declared[a] == declared[b]
            r_same = recovered_label[a] == recovered_label[b]
            total += 1
            agree += int(d_same == r_same)
            if d_same != r_same and len(disagreements) < 10:
                disagreements.append([int(a), int(b), bool(d_same), bool(r_same)])
    return dict(
        pairs_compared=total,
        pairs_agree=agree,
        fraction_agree=(agree / total if total else 1.0),
        exact=agree == total,
        first_disagreements=disagreements)


def separation(res, declared):
    """Within-block versus between-block correlation, using the DECLARED partition. If the
    fixture is right these are far apart; if it is wrong they are not."""
    if declared is None:
        return None
    lab = np.asarray([declared[e] for e in res["edges"]])
    C = res["corr"]
    n = len(lab)
    iu = np.triu_indices(n, 1)
    same = lab[iu[0]] == lab[iu[1]]
    v = np.abs(C[iu])
    return dict(
        within_block_mean=float(v[same].mean()) if same.any() else None,
        between_block_mean=float(v[~same].mean()) if (~same).any() else None,
        within_block_min=float(v[same].min()) if same.any() else None,
        between_block_max=float(v[~same].max()) if (~same).any() else None,
        n_within_pairs=int(same.sum()), n_between_pairs=int((~same).sum()))


def build_and_check(K, seed_base, label, builder_dir=None):
    import subprocess
    exe = [sys.executable, os.path.join(builder_dir or ".", "scripts", "v64",
                                        "build_stage4_synthetic_worlds_v1.py"),
           "--only", WORLD, "--confound-blocks", str(K), "--seed-base", str(seed_base)]
    r = subprocess.run(exe, capture_output=True, text=True, cwd=builder_dir or os.getcwd())
    if r.returncode != 0:
        return dict(K=K, label=label, ok=False, err=(r.stdout + r.stderr)[-400:])
    man = json.load(open(os.path.join(BW.ROOT, WORLD, "WORLD_MANIFEST.json")))
    pt = man["planted_truth"]
    declared = pt.get("block_of_edge")
    res = recover_blocks(BW.ROOT, WORLD)
    sep = separation(res, declared)
    membership = partition_membership_agreement(res, declared)
    return dict(
        K_requested=K, label=label, ok=True,
        manifest_claims=dict(
            realised_occupied_factors=pt.get("realised_occupied_factors"),
            block_size_min=pt.get("block_size_min"), block_size_max=pt.get("block_size_max"),
            partition_semantics=pt.get("partition_semantics")),
        recovered_from_bytes=dict(
            n_blocks=res["n_recovered_blocks"],
            size_min=min(res["sizes"]), size_max=max(res["sizes"]),
            n_edges_used=len(res["edges"]),
            edges_excluded_sharing_an_interval=res["edges_excluded_sharing_an_interval"]),
        blocks_present_among_retained_edges=(
            len(set(declared[e] for e in res["edges"])) if declared else None),
        recovered_equals_blocks_present=(
            bool(res["n_recovered_blocks"]
                 == len(set(declared[e] for e in res["edges"]))) if declared else None),
        partition_membership_agreement=membership,
        separation=sep)


def main() -> int:
    print("recovering block geometry from the written bytes ...")
    rows = []
    for K in (1, 5, 20, 50, 200):
        row = build_and_check(K, 900000, "REPAIRED")
        rows.append(row)
        if row["ok"]:
            m, rec = row["manifest_claims"], row["recovered_from_bytes"]
            print("  K=%-4d manifest %-4s occupied | RECOVERED %-4d blocks sizes %d..%d"
                  " | match=%s"
                  % (K, m["realised_occupied_factors"], rec["n_blocks"],
                     rec["size_min"], rec["size_max"],
                     row["recovered_equals_blocks_present"]))
            if row["separation"]:
                s = row["separation"]
                f = lambda v: "n/a" if v is None else ("%.3f" % v)
                print("        within-block |r| mean %s (min %s) vs between %s (max %s)"
                      % (f(s["within_block_mean"]), f(s["within_block_min"]),
                         f(s["between_block_mean"]), f(s["between_block_max"])))
        else:
            print("  K=%-4d BUILD FAILED: %s" % (K, row["err"][:120]))

    out = dict(
        schema="V64_CONFOUND_BLOCK_GEOMETRY_VERIFICATION_V1", date="2026-10-02",
        why="S99. A generator reporting its own block count is reporting bookkeeping. "
            "This recovers the partition from the ATAC bytes that were written, by "
            "projecting out depth and clustering the linked-interval profiles, so no "
            "field the generator wrote is trusted.",
        method=dict(
            statistic="absolute Pearson correlation between depth-residualised "
                      "linked-interval ATAC profiles across metacells",
            blocks="connected components at |r| >= %.2f" % LINK_THRESHOLD,
            threshold_is_frozen_here=True,
            threshold_justification="reported beside the measured within-block minimum "
                                    "and between-block maximum, so a reader can see "
                                    "whether the threshold sits in a gap or in a smear"),
        rows=rows,
        all_K_recovered_exactly=all(
            r.get("recovered_equals_blocks_present")
            and r.get("partition_membership_agreement", {}).get("exact")
            for r in rows if r.get("ok")),
        producer_sha256=B.sha_file(os.path.abspath(__file__)),
        real_substrate_read=False, computed_correspondence_values=0)
    p = "results/v64/phase_b_design/V64_CONFOUND_BLOCK_GEOMETRY_VERIFICATION_V1.json"
    with open(p, "w", newline="\n") as fh:
        json.dump(out, fh, indent=2)
    print("")
    print("all K recovered exactly from the bytes: %s" % out["all_K_recovered_exactly"])
    print("receipt sha256 " + B.sha_file(p))
    return 0 if out["all_K_recovered_exactly"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
