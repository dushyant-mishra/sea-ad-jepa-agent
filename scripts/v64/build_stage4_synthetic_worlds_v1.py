#!/usr/bin/env python3
"""Build four synthetic Phase-B substrates in the REAL on-disk format.

WHY THIS EXISTS. Testing the executor's helper functions proves the arithmetic. It does
not prove the orchestration: the metacell-to-donor join, the availability unpacking, the
eligibility funnel, the promoter folds, the arm pairing, the weighting, the bootstrap and
the writer are where a real run would actually go wrong. So these worlds are written to
disk as PHASE_B_SUBSTRATE_s*.npz, PHASE_B_T5_DONOR_AGGREGATES.npz and
PHASE_B_T3_T4_AVAILABILITY.npz with exactly the arrays, dtypes and key semantics the real
substrate carries, and the executor reads them through its ordinary entrypoint. The only
difference between a synthetic run and a real run is the bytes.

WHAT IS PLANTED. Each world records its own truth in a manifest BEFORE the executor is
ever run, so the comparison is prospective rather than a story told afterwards.

  BIOLOGY_POSITIVE  a genuine within-donor regulatory relationship on linked pairs only
  TRUE_NULL         nothing at all
  MEASURED_TECHNICAL  an apparent relationship driven entirely by sequencing depth, which
                    the frozen 14-term basis carries, so the adjustment should remove it
  HIDDEN_CONFOUND   an apparent relationship driven by a factor that varies BETWEEN
                    metacells of the same donor, loads on both modalities, and is
                    orthogonal to depth. The frozen basis cannot see it. This world is
                    EXPECTED TO FOOL the executor and is kept for exactly that reason.

A world that the method fails is not a broken test. It is the part of the qualification
that says what a real Stage-4 number will and will not mean.

GEOMETRY. These are reduced-scale worlds: 60 donors, 11 metacells each, 200 edges. The
real substrate is 282 donors, 3,231 metacells and 13,175 edges. The RATIOS are matched --
metacells per donor, the share of edges carrying a CONTROL_B, the sparsity of the T3/T4
payloads, the presence of donors that fail eligibility -- because the orchestration is
sensitive to shape, not to size. The scale difference is stated in every receipt rather
than glossed.

No real matrix, no real substrate and no protected outcome is read by this file.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B                      # noqa: E402

ROOT = "D:/jepa_v5_outputs_20260925/v64_stage4_synthetic"

# geometry, matched to the real substrate in ratio
N_DONORS_OK = 60            # donors that pass eligibility
N_DONORS_SMALL = 5          # donors with too few microglia -- the funnel must drop them
N_METACELLS = 11            # real: 3231 / 282 = 11.5
N_EDGES = 200
CONTROL_B_SHARE = 0.836     # real: 11012 / 13175
N_GENES = 200
N_INTERVALS = 400
N_SHARDS = 2                # more than one, so the dictionary-agreement path is exercised
NUCLEI_OK = 25              # per metacell, so an eligible donor has 275 >= 100
NUCLEI_SMALL = 8            # 88 < 100 -> ineligible

WORLDS = ("BIOLOGY_POSITIVE", "TRUE_NULL", "MEASURED_TECHNICAL", "HIDDEN_CONFOUND")
# Built on request for the G2 sensitivity curve and deliberately NOT one of the canonical
# four, so the canonical fixture set that every qualification receipt describes is
# unchanged by this experiment existing.
EXTRA_WORLDS = ("HIDDEN_CONFOUND_K",)
CONFOUND_BLOCKS_DEFAULT = 1


def _pack(mat):
    """Availability as the real substrate carries it: big-endian packbits over a C-order
    ravel of a [metacell x feature] boolean matrix."""
    return np.packbits(np.ascontiguousarray(mat, dtype=bool), bitorder="big")


def build_world(world, seed):
    rng = np.random.default_rng(seed)
    n_don = N_DONORS_OK + N_DONORS_SMALL
    donors = ["SYN-%04d" % i for i in range(n_don)]

    # ---- metacells. The short donors get 3 metacells, below the minimum of 4, so both
    # eligibility rules are exercised and not just the nuclei rule.
    mc_donor, mc_nuclei = [], []
    for i, d in enumerate(donors):
        k = N_METACELLS if i < N_DONORS_OK else 3
        n = NUCLEI_OK if i < N_DONORS_OK else NUCLEI_SMALL
        mc_donor += [d] * k
        mc_nuclei += [n] * k
    mc_donor = np.array(mc_donor)
    mc_nuclei = np.array(mc_nuclei, dtype=np.int32)
    n_mc = len(mc_donor)
    donor_of_mc = mc_donor
    mc_index_of_donor = {d: np.where(mc_donor == d)[0] for d in donors}

    # ---- sequencing depth. This is a REAL technical variable: it is what
    # rna_depth_sensitivity and atac_depth_sensitivity are slopes against, so the frozen
    # basis can see anything that acts through it.
    log_depth = rng.normal(0.0, 0.45, n_mc)
    total_rna = np.exp(9.5 + log_depth)
    total_atac = np.exp(10.6 + log_depth * 0.9 + rng.normal(0, 0.1, n_mc))

    # ---- the hidden factor. It varies BETWEEN metacells of the same donor, like depth,
    # but is constructed orthogonal to depth so no depth slope can absorb it.
    hidden = rng.normal(0.0, 1.0, n_mc)
    hidden = hidden - np.polyval(np.polyfit(log_depth, hidden, 1), log_depth)
    hidden /= hidden.std()

    # ---- edges, genes, intervals, built under the FROZEN CONTROL CONSTRUCTION
    # S99. These worlds previously drew control intervals uniformly at random, so the
    # linked and control arms differed on accessibility and distance BY CONSTRUCTION --
    # exactly the failure the design contract anticipates when it says a control without
    # the accessibility requirement "would differ from linked edges on accessibility by
    # construction, and the contrast would measure accessibility rather than linkage".
    # Every control here is now built the way the contract builds one:
    #   same promoter, held fixed          same chromosome
    #   5,000 bp interval width            distance matched within +/-10% or 10 kb
    #   must not overlap the linked distal interval
    #   must carry >= 1 consensus peak and >= 1 accessibility (PU.1-equivalent) peak
    # The second control draw is independent, as the contract requires for the
    # control-versus-control null.
    genes = np.array(sorted("SYNG%05d" % i for i in range(N_GENES)), dtype="<U15")
    gpos = {g: i for i, g in enumerate(genes)}
    n_prom = max(2, N_EDGES // 4)
    promoter_pos = rng.integers(2_000_000, 8_000_000, n_prom).astype(np.int64)
    edge_promoter = rng.integers(0, n_prom, N_EDGES)
    edge_gene = rng.integers(0, N_GENES, N_EDGES)
    has_b = rng.random(N_EDGES) < CONTROL_B_SHARE

    IV_W = 5000
    iv_registry, iv_list = {}, []

    def interval_at(start):
        """Intervals live on a fixed 5 kb grid, so a start resolves to one identity."""
        s = int(round(start / IV_W) * IV_W)
        if s not in iv_registry:
            iv_registry[s] = len(iv_list)
            iv_list.append(s)
        return iv_registry[s]

    def draw_matched(p, d_linked, linked_start, used, tries=200):
        """A control at a distance matched to the linked edge, on either side of the SAME
        promoter, not overlapping the linked interval. Returns None if no admissible
        control exists, which the contract handles by TRIMMING the edge rather than
        extrapolating one."""
        tol = max(0.10 * d_linked, 10_000)
        for _ in range(tries):
            d = d_linked + rng.uniform(-tol, tol)
            if d < IV_W:
                continue
            start = p + (1 if rng.random() < 0.5 else -1) * d
            if start < 0:
                continue
            s = int(round(start / IV_W) * IV_W)
            if abs(s - linked_start) < IV_W:          # would overlap the linked interval
                continue
            if s in used:
                continue
            # verify AFTER snapping to the 5 kb grid. Checking the tolerance on the
            # pre-snap draw and then moving the interval is how 16 controls ended up
            # outside their own matching window.
            err = abs(abs(s - p) - d_linked)
            if err > tol:
                continue
            return s, err
        return None, None

    edge_linked_iv = np.full(N_EDGES, -1, np.int64)
    edge_ctrla_iv = np.full(N_EDGES, -1, np.int64)
    edge_ctrlb_iv = np.full(N_EDGES, -1, np.int64)
    edge_distance = np.zeros(N_EDGES, float)
    trimmed, match_err_a, match_err_b = [], [], []
    for e in range(N_EDGES):
        p = int(promoter_pos[edge_promoter[e]])
        d = float(rng.uniform(20_000, 400_000))
        linked_start = int(round((p + (1 if rng.random() < 0.5 else -1) * d) / IV_W) * IV_W)
        edge_distance[e] = abs(linked_start - p)
        edge_linked_iv[e] = interval_at(linked_start)
        used = {linked_start}
        sa, ea = draw_matched(p, edge_distance[e], linked_start, used)
        if sa is None:
            trimmed.append(e)                      # no admissible control: TRIM the edge
            continue
        used.add(sa)
        edge_ctrla_iv[e] = interval_at(sa)
        match_err_a.append(ea)
        if has_b[e]:
            sb, eb = draw_matched(p, edge_distance[e], linked_start, used)
            if sb is not None:
                edge_ctrlb_iv[e] = interval_at(sb)
                match_err_b.append(eb)

    iv_start = np.array(iv_list, np.int64)
    n_iv_real = len(iv_start)
    iv_end = iv_start + IV_W
    iv_chrom = np.array(["chr1"] * n_iv_real, dtype="<U5")
    n_peaks = rng.integers(1, 6, n_iv_real).astype(np.int32)
    # Accessibility qualification is SYMMETRIC by construction: every interval that can
    # enter either arm carries at least one accessibility peak, which is what the frozen
    # control rule enforces. Nothing here is accessible on one arm and not the other.
    iv_accessible = np.ones(n_iv_real, bool)

    pair_keys, pair_gene, pair_interval, pair_arm, pair_edge = [], [], [], [], []
    for e in range(N_EDGES):
        if e in trimmed:
            continue
        arms = [("LINKED", edge_linked_iv[e]), ("CONTROL_A", edge_ctrla_iv[e])]
        if edge_ctrlb_iv[e] >= 0:
            arms.append(("CONTROL_B", edge_ctrlb_iv[e]))
        for arm, iv in arms:
            pair_keys.append("e%d|%s" % (e, arm))
            pair_gene.append(genes[edge_gene[e]])
            pair_interval.append(int(iv))
            pair_arm.append(arm)
            pair_edge.append(e)
    order = np.argsort(np.array(pair_keys))
    pair_keys = np.array(pair_keys, dtype="<U24")[order]
    pair_gene = np.array(pair_gene, dtype="<U15")[order]
    pair_interval = np.array(pair_interval, dtype=np.int32)[order]
    pair_arm = np.array(pair_arm)[order]
    pair_edge = np.array(pair_edge)[order]
    n_pairs = len(pair_keys)

    # ================================================= the planted signal
    # Base expression, shared by every world. Depth enters BOTH modalities, which by
    # itself already creates an apparent correspondence -- that is the point of world 3.
    rna = rng.normal(4.0, 0.6, (n_mc, N_GENES)) + 0.8 * log_depth[:, None]
    atac = rng.normal(3.0, 0.5, (n_mc, n_iv_real)) + 0.7 * log_depth[:, None]

    planted = {}
    if world == "BIOLOGY_POSITIVE":
        # a genuine regulatory coupling: for each edge, a shared within-donor latent that
        # drives the linked gene's RNA and the linked interval's ATAC, and NOTHING on the
        # control intervals.
        beta = 1.4
        for e in range(N_EDGES):
            z = rng.normal(0, 1, n_mc)
            rna[:, edge_gene[e]] += beta * z
            atac[:, edge_linked_iv[e]] += beta * z
        planted = dict(mechanism="shared within-donor latent on linked pairs only",
                       beta=beta, expect="Delta > 0 and LCB95 > 0")
    elif world == "TRUE_NULL":
        planted = dict(mechanism="nothing planted beyond shared sequencing depth",
                       expect="adjusted Delta near 0 and LCB95 <= 0")
    elif world == "MEASURED_TECHNICAL":
        # the apparent coupling is depth, and only depth. The frozen basis carries the
        # within-donor depth slopes, so the adjustment is designed to see this.
        for e in range(N_EDGES):
            g = 1.6 * rng.uniform(0.6, 1.4)
            rna[:, edge_gene[e]] += g * log_depth
            atac[:, edge_linked_iv[e]] += g * log_depth
        planted = dict(mechanism="edge-specific loading on sequencing depth, linked arm "
                                 "only; depth IS in the frozen basis",
                       expect="raw Delta > 0, adjusted Delta near 0")
    elif world in ("HIDDEN_CONFOUND", "HIDDEN_CONFOUND_K"):
        # K independent metacell-varying factors, each orthogonal to depth, shared by a
        # block of edges. K=1 is the original world: one factor behind every edge. K equal
        # to the edge count gives every edge its own factor, which is structurally the
        # same object as the planted biology -- that end of the curve is a tautology, not
        # a failure, and the pre-commitment says so.
        K = 1 if world == "HIDDEN_CONFOUND" else int(globals().get(
            "_CONFOUND_BLOCKS", CONFOUND_BLOCKS_DEFAULT))
        K = max(1, min(K, N_EDGES))
        factors = []
        for _ in range(K):
            f = rng.normal(0.0, 1.0, n_mc)
            f = f - np.polyval(np.polyfit(log_depth, f, 1), log_depth)
            factors.append(f / f.std())
        block_of_edge = rng.integers(0, K, N_EDGES)
        for e in range(N_EDGES):
            g = 1.4 * rng.uniform(0.6, 1.4)
            f = factors[int(block_of_edge[e])]
            rna[:, edge_gene[e]] += g * f
            atac[:, edge_linked_iv[e]] += g * f
        planted = dict(mechanism="edge-specific loading on a metacell-varying factor that "
                                 "is orthogonal to depth and absent from the frozen basis",
                       confound_blocks_K=int(K),
                       edges_per_block=round(N_EDGES / K, 2),
                       expect="Delta stays large. THE EXECUTOR IS EXPECTED TO BE FOOLED; "
                              "this is recorded as an interpretation limit, not a bug.")

    # Clipping at zero after adding variance raises the MEAN of the higher-variance arm,
    # which by itself shifts distal_accessibility between linked and control and shows up
    # in the balance gate as if it were imbalance. The baselines are set high enough that
    # the clip almost never binds, and the rate is recorded so the claim is checkable
    # rather than asserted.
    clip_rna = float((rna < 0).mean())
    clip_atac = float((atac < 0).mean())
    rna = np.clip(rna, 0, None).astype(np.float32)
    atac = np.clip(atac, 0, None).astype(np.float32)

    # ================================================= missingness, planted on purpose
    rna_avail = np.ones((n_mc, N_GENES), bool)
    atac_avail = np.ones((n_mc, n_iv_real), bool)
    # Plant each class on a gene or interval that a PAIR ACTUALLY USES. Planting it on an
    # unused feature produces a funnel count of zero and a test that cannot fail.
    used_g = sorted({gpos[str(g)] for g in pair_gene})
    used_iv = sorted({int(v) for v in pair_interval})
    g_struct, g_zero = used_g[0], used_g[1]
    iv_const = used_iv[0]
    # one gene STRUCTURALLY UNMEASURED in one donor -- must come back MISSING, never 0
    d0 = mc_index_of_donor[donors[0]]
    rna_avail[np.ix_(d0, [g_struct])] = False
    rna[np.ix_(d0, [g_struct])] = 0.0   # nothing stored where nothing was measured
    # one gene with measured zero coverage in one donor -- measured, and still MISSING for
    # the correlation, but for a different reason that the funnel must name separately
    d1 = mc_index_of_donor[donors[1]]
    rna[np.ix_(d1, [g_zero])] = 0.0
    # one interval with zero variance in one donor -- a real constant, not an absence
    d2 = mc_index_of_donor[donors[2]]
    atac[np.ix_(d2, [iv_const])] = 3.25
    planted_missing = dict(
        structurally_unmeasured=dict(donor=donors[0], gene=str(genes[g_struct]),
                                     pairs_affected=int((np.array(
                                         [gpos[str(g)] for g in pair_gene])
                                         == g_struct).sum())),
        measured_zero_coverage=dict(donor=donors[1], gene=str(genes[g_zero]),
                                    pairs_affected=int((np.array(
                                        [gpos[str(g)] for g in pair_gene])
                                        == g_zero).sum())),
        zero_variance=dict(donor=donors[2], interval=int(iv_const),
                           pairs_affected=int((pair_interval == iv_const).sum())))

    # ================================================= T3 / T4 sparse payloads
    # sparse absence means MEASURED ZERO, exactly as in the real substrate, so a value of
    # zero is simply not stored and availability stays True.
    t3_m, t3_g, t3_v = np.nonzero(rna)[0], np.nonzero(rna)[1], rna[rna != 0]
    t4_m, t4_i = np.nonzero(atac)
    t4_v = atac[atac != 0]

    # ================================================= T5 donor x pair grid
    eligible_donors = [d for d in donors if len(mc_index_of_donor[d]) >= 4
                       and mc_nuclei[mc_index_of_donor[d]].sum() >= 100]
    t5_donor = np.repeat(np.array(donors), n_pairs)
    t5_pair = np.tile(pair_keys, len(donors))
    n_t5 = len(t5_donor)

    def slope(y, x):
        xc = x - x.mean()
        v = (xc * xc).sum()
        return 0.0 if v == 0 else float((xc * (y - y.mean())).sum() / v)

    prom_act = np.zeros(n_t5, np.float32)
    dist_acc = np.zeros(n_t5, np.float32)
    rna_slope = np.zeros(n_t5, np.float32)
    atac_slope = np.zeros(n_t5, np.float32)
    n_contrib = np.zeros(n_t5, np.int16)
    npk = np.zeros(n_t5, np.int32)
    for di, d in enumerate(donors):
        mcs = mc_index_of_donor[d]
        lr, la = np.log1p(total_rna[mcs]), np.log1p(total_atac[mcs])
        base = di * n_pairs
        for pi in range(n_pairs):
            gi = gpos[str(pair_gene[pi])]
            vi = int(pair_interval[pi])
            r, a = rna[mcs, gi], atac[mcs, vi]
            j = base + pi
            prom_act[j] = r.mean()
            dist_acc[j] = a.mean()
            rna_slope[j] = slope(r, lr)
            atac_slope[j] = slope(a, la)
            n_contrib[j] = len(mcs)
            npk[j] = n_peaks[vi]

    states = np.array(["MEASURED", "NOT_MEASURED_RNA_ZERO_COVERAGE",
                       "NOT_MEASURED_ATAC_ZERO_COVERAGE",
                       "NOT_MEASURED_STRUCTURAL", "NOT_EVALUABLE"], dtype="<U31")
    rna_ok = np.ones(n_t5, bool)
    atac_ok = np.ones(n_t5, bool)
    code = np.zeros(n_t5, np.int8)
    for di, d in enumerate(donors):
        mcs = mc_index_of_donor[d]
        base = di * n_pairs
        for pi in range(n_pairs):
            gi = gpos[str(pair_gene[pi])]
            vi = int(pair_interval[pi])
            j = base + pi
            if not rna_avail[mcs, gi].any():
                rna_ok[j] = False
                code[j] = 3
            elif (rna[mcs, gi] == 0).all():
                code[j] = 1
            elif (atac[mcs, vi] == 0).all():
                atac_ok[j] = False
                code[j] = 2

    # ================================================= write it out
    out = os.path.join(ROOT, world)
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        os.remove(os.path.join(out, f))

    shard_bounds = np.array_split(np.arange(n_mc), N_SHARDS)
    shard_paths = []
    for si, mcs in enumerate(shard_bounds):
        m3 = np.isin(t3_m, mcs)
        m4 = np.isin(t4_m, mcs)
        p = os.path.join(out, "PHASE_B_SUBSTRATE_s%02d.npz" % si)
        np.savez(
            p,
            t1_donor=np.array([], dtype="<U10"), t1_rna_row=np.array([], np.int64),
            t1_metacell=np.array([], np.int32),
            t2_donor=donor_of_mc[mcs].astype("<U10"),
            t2_metacell=mcs.astype(np.int32),
            t2_n_nuclei=mc_nuclei[mcs],
            t2_total_rna=total_rna[mcs], t2_total_atac=total_atac[mcs],
            t3_metacell=t3_m[m3].astype(np.int32), t3_gene=t3_g[m3].astype(np.int32),
            t3_value=t3_v[m3].astype(np.float32),
            t4_metacell=t4_m[m4].astype(np.int32), t4_interval=t4_i[m4].astype(np.int32),
            t4_value=t4_v[m4].astype(np.float32),
            genes=genes, interval_chrom=iv_chrom, interval_start=iv_start,
            interval_end=iv_end, n_assigned_peaks=n_peaks,
            pair_keys=pair_keys, pair_gene=pair_gene, pair_interval=pair_interval)
        shard_paths.append(p)

    np.savez(os.path.join(out, "PHASE_B_T5_DONOR_AGGREGATES.npz"),
             states=states, donor=t5_donor.astype("<U10"),
             pair_key=t5_pair.astype("<U24"),
             promoter_activity=prom_act, distal_accessibility=dist_acc,
             rna_depth_sensitivity=rna_slope, atac_depth_sensitivity=atac_slope,
             n_metacells_contributing=n_contrib,
             rna_available=rna_ok, atac_available=atac_ok,
             availability_state_code=code, n_assigned_peaks=npk)

    np.savez(os.path.join(out, "PHASE_B_T3_T4_AVAILABILITY.npz"),
             t3_available_packed=_pack(rna_avail),
             t3_shape=np.array([n_mc, N_GENES], np.int32),
             t4_available_packed=_pack(atac_avail),
             t4_shape=np.array([n_mc, n_iv_real], np.int32),
             factor_rna_metacell_ok=np.ones(n_mc, bool),
             factor_atac_metacell_ok=np.ones(n_mc, bool),
             factor_interval_ok=np.ones(n_iv_real, bool),
             metacell_id=np.arange(n_mc, dtype=np.int32))

    # the per-pair geometry the 14-term basis needs, in the Phase-A row schema
    rows = []
    for pi in range(n_pairs):
        e = int(pair_edge[pi])
        arm = str(pair_arm[pi])
        iv = int(pair_interval[pi])
        rows.append(dict(pair_key=str(pair_keys[pi]), population=
                         "LINKED" if arm == "LINKED" else "CONTROL",
                         control_role="NONE" if arm == "LINKED" else arm.split("_")[1],
                         edge_index=e, promoter_index=int(edge_promoter[e]),
                         promoter_key="syn:%d" % edge_promoter[e],
                         source_hg19_distance_bp=int(abs(int(iv_start[iv])
                                                          - int(promoter_pos[edge_promoter[e]])) + 1),
                         log_distance=float(np.log(abs(int(iv_start[iv])
                                                       - int(promoter_pos[edge_promoter[e]])) + 1)),
                         promoter_degree=int((edge_promoter == edge_promoter[e]).sum()),
                         re_density=int(n_peaks[iv]) * 7,
                         anchor_frequency=int((pair_interval == iv).sum())))
    with open(os.path.join(out, "PHASE_A_ROWS.json"), "w", newline="\n") as fh:
        json.dump(rows, fh)

    digests = {os.path.basename(p): B.sha_file(p) for p in shard_paths}
    for f in ("PHASE_B_T5_DONOR_AGGREGATES.npz", "PHASE_B_T3_T4_AVAILABILITY.npz",
              "PHASE_A_ROWS.json"):
        digests[f] = B.sha_file(os.path.join(out, f))

    # ---- prove the synthetic arms actually satisfy the frozen matching rules
    viol_dist, viol_overlap, viol_prom = [], [], []
    for e in range(N_EDGES):
        if e in trimmed:
            continue
        p_pos = int(promoter_pos[edge_promoter[e]])
        dl = abs(int(iv_start[edge_linked_iv[e]]) - p_pos)
        tol = max(0.10 * dl, 10_000)
        for ivx in (edge_ctrla_iv[e], edge_ctrlb_iv[e]):
            if ivx < 0:
                continue
            dc = abs(int(iv_start[ivx]) - p_pos)
            if abs(dc - dl) > tol:
                viol_dist.append(dict(edge=e, linked=dl, control=dc, tol=tol))
            if abs(int(iv_start[ivx]) - int(iv_start[edge_linked_iv[e]])) < IV_W:
                viol_overlap.append(e)
    matching_audit = dict(
        rule="same promoter held fixed, same chromosome, 5,000 bp width, source distance "
             "matched within +/-10 percent or 10 kb whichever is larger, control must not "
             "overlap the linked interval, and every interval entering either arm carries "
             "a consensus peak and an accessibility peak",
        edges_built=N_EDGES, edges_trimmed_no_admissible_control=len(trimmed),
        controls_checked=len(match_err_a) + len(match_err_b),
        distance_match_violations=len(viol_dist),
        overlap_violations=len(viol_overlap),
        promoter_is_fixed_by_construction=True,
        accessibility_qualification_symmetric=bool(iv_accessible.all()),
        worst_distance_mismatch_bp=float(max(match_err_a + match_err_b))
        if (match_err_a or match_err_b) else None,
        median_distance_mismatch_bp=float(np.median(match_err_a + match_err_b))
        if (match_err_a or match_err_b) else None,
        all_frozen_matching_rules_satisfied=bool(not viol_dist and not viol_overlap
                                                 and iv_accessible.all()))
    if not matching_audit["all_frozen_matching_rules_satisfied"]:
        raise SystemExit("world %s violates the frozen control construction: %d distance, "
                         "%d overlap" % (world, len(viol_dist), len(viol_overlap)))

    manifest = dict(
        schema="V64_STAGE4_SYNTHETIC_WORLD_V1", IS_SYNTHETIC=True, world=world, seed=seed,
        contains_no_real_measurement=True,
        geometry=dict(donors=len(donors), eligible_donors=len(eligible_donors),
                      metacells=n_mc, genes=N_GENES, intervals=n_iv_real,
                      edges=N_EDGES, pairs=n_pairs, shards=N_SHARDS,
                      t3_nnz=int(len(t3_v)), t4_nnz=int(len(t4_v)),
                      t5_rows=n_t5),
        scale_note="reduced scale. The real substrate is 282 donors, 3,231 metacells and "
                   "13,175 edges; ratios are matched, absolute size is not.",
        matching_audit=matching_audit,
        clipping=dict(fraction_rna_clipped_at_zero=clip_rna,
                      fraction_atac_clipped_at_zero=clip_atac,
                      why="a clip that binds often raises the mean of the "
                          "higher-variance arm and manufactures imbalance"),
        planted_truth=planted,
        planted_missingness=planted_missing,
        digests=digests)
    mp = os.path.join(out, "WORLD_MANIFEST.json")
    with open(mp, "w", newline="\n") as fh:
        json.dump(manifest, fh, indent=2)
    print("  %-20s donors=%d(%d eligible) metacells=%d pairs=%d t3=%d t4=%d"
          % (world, len(donors), len(eligible_donors), n_mc, n_pairs,
             len(t3_v), len(t4_v)))
    return manifest


CANONICAL_SEED_BASE = 20260929


def main(seed_base=None, only=None, donors=None) -> int:
    # The seed base is a parameter so the worlds can be rebuilt at other draws and the
    # conclusions checked for seed dependence. The CANONICAL worlds are the ones at
    # CANONICAL_SEED_BASE, and every committed manifest is built from that base.
    if seed_base is None:
        import argparse
        ap = argparse.ArgumentParser()
        ap.add_argument("--seed-base", type=int, default=CANONICAL_SEED_BASE)
        ap.add_argument("--only", default=None,
                        help="build just these worlds, comma separated")
        ap.add_argument("--confound-blocks", type=int, default=None,
                        help="K, the number of independent confound factors, for the "
                             "HIDDEN_CONFOUND_K world only")
        ap.add_argument("--donors", type=int, default=None,
                        help="override the eligible donor count, for calibration sweeps")
        a = ap.parse_args()
        seed_base, only, donors = a.seed_base, a.only, a.donors
        if a.confound_blocks:
            globals()["_CONFOUND_BLOCKS"] = int(a.confound_blocks)
        if donors:
            globals()["N_DONORS_OK"] = donors
        if only:
            globals()["_ONLY"] = [w.strip() for w in only.split(",")]
    os.makedirs(ROOT, exist_ok=True)
    print("building synthetic Phase-B worlds under " + ROOT
          + " at seed base " + str(seed_base))
    mans = {}
    only = globals().get("_ONLY")
    for i, w in enumerate(WORLDS + EXTRA_WORLDS):
        if only and w not in only:
            continue
        mans[w] = build_world(w, seed=seed_base + i)
    rec = dict(schema="V64_STAGE4_SYNTHETIC_WORLDS_BUILD_V1", date="2026-10-01",
               root=ROOT, worlds=sorted(mans), seed_base=seed_base,
               eligible_donors_configured=N_DONORS_OK,
               is_canonical_build=seed_base == CANONICAL_SEED_BASE,
               producer_sha256=B.sha_file(os.path.abspath(__file__)),
               manifests={w: m["digests"] for w, m in mans.items()},
               is_partial_build=bool(only) or len(mans) != len(WORLDS),
               planted={w: m["planted_truth"] for w, m in mans.items()},
               reads_no_real_measurement=True,
               computed_correspondence_values=0)
    p = "results/v64/phase_b_design/V64_STAGE4_SYNTHETIC_WORLDS_BUILD_V1.json"
    with open(p, "w", newline="\n") as fh:
        json.dump(rec, fh, indent=2)
    print("build receipt sha256 " + B.sha_file(p))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
