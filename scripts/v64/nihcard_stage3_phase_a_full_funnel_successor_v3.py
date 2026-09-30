#!/usr/bin/env python3
"""Phase A successor: the FULL frozen V2 funnel, composed with the qualified sampler.

WHY THIS EXISTS. The previous executor
(nihcard_stage3_phase_a_exact_executor_v2.py) implemented only the tail of
V64_NIH_CARD_STAGE3_PHASE_A_SUCCESSOR_CONTRACT_V2. It computed

    20,709 E2 edges -> CONTROL_A availability

and reported the result as Phase-A retention. The contract's primary funnel is

    20,709 E2 edges
      -> gene present in NIH-CARD
      -> gene mapping unambiguous in NIH-CARD
      -> linked distal overlaps a NIH-CARD consensus peak
      -> CONTROL_A exact admissible set available on the pre-drawn side
      -> retained primary population

so the first three linked-side eligibility stages were absent. That number, 13,510, is
withdrawn as Phase-A retention and stands only as FULL_E2_EXACT_CONTROL_A_AVAILABILITY.
A correctly computed number under the wrong name is worse than an obviously broken one,
because it closes a gate that is not actually closed.

This successor is a NEW producer. The historical executor is left untouched so the
retraction remains inspectable rather than being edited out of existence.

WHAT IS REUSED VERBATIM RATHER THAN REIMPLEMENTED. The control machinery is imported
from the historical executor module -- subseed derivation, A_exact loading with payload
hash verification, the interior-then-supplement index order, the disjointness assertion.
Re-implementing it would risk silent drift from the machinery the qualification suite
actually passed on. Because the master seed and the subseed derivation are unchanged, the
control drawn for a given edge is IDENTICAL to the previous run; only the population
being drawn over changes. That makes final_retained <= 13,510 a structural guarantee
rather than an expectation.

THE SUPPLEMENT COORDINATE HAZARD. A supplement start exists precisely because the
plus-strand affine shortcut could not certify it, so inferring its hg38 coordinates with
that same shortcut would be unsound -- and for a minus-strand or boundary start the
shortcut returns nothing at all. Every selected control here is therefore pushed through
the real frozen liftOver binary and must independently satisfy the full C3 gate plus
hg38 PU.1 and NIH-CARD peak support. A control that fails would mean A_exact contains an
inadmissible start, which is a contradiction and a STOP, not a row to drop quietly.

TRAINING=OFF. PHASE B=STOPPED. STAGE 4=NOT AUTHORISED. TD60=BLOCKED.
Identifiers, coordinates and approved metadata only. No RNA or ATAC matrix values are
read: gene presence comes from the RNA `var` annotation and the consensus peak set from
the ATAC `var` annotation, both of which are metadata.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
import shutil
import sys
from bisect import bisect_left, bisect_right
from collections import defaultdict

import h5py
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nihcard_exact_supplement_builder_v1 as B                       # noqa: E402
import nihcard_stage3_phase_a_exact_executor_v2 as EX                 # noqa: E402

W = B.W
RNA_H5AD = "D:/jepa_v5_outputs_20260925/nihcard/final_rna_data.h5ad"
ATAC_H5AD = "D:/jepa_v5_outputs_20260925/nihcard/final_atac_data.h5ad"
PEAKS_BED = "C:/Users/dushy/jepa_c3/nihcard_peaks.bed"
PU1_BED = f"{B.WIN}/ATAC_PU1.bed.gz"
PHASE_A_V2 = "results/v64/V64_NIH_CARD_STAGE3_PHASE_A_SUCCESSOR_CONTRACT_V2.json"
FEATURE_V2 = "results/v64/V64_NIH_CARD_STAGE3_FEATURE_ARTIFACT_CONTRACT_V2.json"
SUPP_DIR = "results/v64/nihcard_exact_supplement"
RE_DENSITY_FLANK = 50000
FULL_E2_CONTROL_A_AVAILABILITY = 13510      # logical upper bound, not a target


class Stop(Exception):
    """A frozen requirement failed. The rule is not weakened after seeing the failure."""


# ------------------------------------------------------------------ interval index
class Peaks:
    def __init__(self, by_chrom):
        self.v = {c: sorted(x) for c, x in by_chrom.items()}
        self.s = {c: [a for a, _ in v] for c, v in self.v.items()}
        self.e = {c: [b for _, b in v] for c, v in self.v.items()}
        self.m = {c: (max(b - a for a, b in v) if v else 0) for c, v in self.v.items()}

    def overlaps(self, c, s, e):
        v = self.v.get(c)
        if not v:
            return False
        j = bisect_left(self.s[c], e) - 1
        while j >= 0 and self.s[c][j] + self.m[c] > s:
            a, b = v[j]
            if b > s and a < e:
                return True
            j -= 1
        return False

    def count_in(self, c, lo, hi):
        """Peaks overlapping [lo, hi). Frozen re_density window."""
        v = self.v.get(c)
        if not v:
            return 0
        j = bisect_left(self.s[c], hi) - 1
        n = 0
        while j >= 0 and self.s[c][j] + self.m[c] > lo:
            a, b = v[j]
            if b > lo and a < hi:
                n += 1
            j -= 1
        return n


class AnchorIndex:
    """Distinct E2 promoter_keys whose distal partners overlap a query interval."""

    def __init__(self, rows, ix):
        d = defaultdict(list)
        for r in rows:
            pk = f'{r[ix["chrom"]]}:{r[ix["promoter_start_hg38"]]}-{r[ix["promoter_end_hg38"]]}'
            d[r[ix["chrom"]]].append((int(r[ix["distal_start_hg38"]]),
                                      int(r[ix["distal_end_hg38"]]), pk))
        self.v = {c: sorted(x) for c, x in d.items()}
        self.s = {c: [a for a, _, _ in v] for c, v in self.v.items()}
        self.m = {c: (max(b - a for a, b, _ in v) if v else 0) for c, v in self.v.items()}

    def frequency(self, c, s, e):
        v = self.v.get(c)
        if not v:
            return 0
        keys = set()
        j = bisect_left(self.s[c], e) - 1
        while j >= 0 and self.s[c][j] + self.m[c] > s:
            a, b, pk = v[j]
            if b > s and a < e:
                keys.add(pk)
            j -= 1
        return len(keys)


def load_bed_pairs(path):
    d = defaultdict(list)
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt") as fh:
        for l in fh:
            if l.strip() and not l.startswith(("#", "track")):
                f = l.split()
                d[f[0]].append((int(f[1]), int(f[2])))
    return d


def sha_file(p):
    return B.sha_file(p)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="D:/jepa_v5_outputs_20260925/v64_phase_a_v3")
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    workdir = os.path.join(B.WIN, "phaseav3_work")
    shutil.rmtree(workdir, ignore_errors=True)
    os.makedirs(workdir)

    def log(m):
        print(m, flush=True)

    # ---------------------------------------------------------------- inputs
    with gzip.open(B.E2, "rb") as fh:
        raw = fh.read()
    if B.sha_bytes(raw) != B.E2_SHA:
        raise Stop("E2 digest mismatch")
    el = raw.decode().rstrip("\n").split("\n")
    ix = {k: i for i, k in enumerate(el[0].split("\t"))}
    rows = [l.split("\t") for l in el[1:]]
    N = len(rows)
    if N != 20709:
        raise Stop(f"E2 denominator is {N}, contract fixes it at 20709")
    log(f"E2 edges: {N:,}")

    # gene identity from RNA var annotation only -- no /X access anywhere
    with h5py.File(RNA_H5AD, "r") as f:
        gid = [x.decode() if isinstance(x, bytes) else str(x)
               for x in f["var"]["gene_ids"][:]]
    gene_rowcount = defaultdict(int)
    for g in gid:
        gene_rowcount[g] += 1
    nihcard_genes = set(gene_rowcount)
    log(f"NIH-CARD RNA var: {len(gid):,} rows, {len(nihcard_genes):,} distinct gene_ids")

    # consensus peaks: bind the BED to the ATAC var annotation before using it
    with h5py.File(ATAC_H5AD, "r") as f:
        an = [x.decode() if isinstance(x, bytes) else str(x)
              for x in f["var"]["_index"][:]]
    recon = []
    for n in an:
        c, rest = n.split(":")
        s, e = rest.split("-")
        recon.append(f"{c}\t{s}\t{e}")
    bed_lines = [l.rstrip("\n") for l in open(PEAKS_BED) if l.strip()]
    if recon != bed_lines:
        raise Stop("nihcard_peaks.bed does not reproduce the ATAC var consensus peak set")
    log(f"consensus peaks bound to ATAC var: {len(bed_lines):,}")

    peaks = Peaks(load_bed_pairs(PEAKS_BED))
    pu1 = Peaks(load_bed_pairs(PU1_BED))
    anchors = AnchorIndex(rows, ix)

    # ------------------------------------------------- STEP 1 linked eligibility
    drop = {k: 0 for k in ("DROP_GENE_NOT_IN_NIHCARD",
                           "DROP_GENE_AMBIGUOUS_IN_NIHCARD",
                           "DROP_NO_CONSENSUS_PEAK_OVER_LINKED_DISTAL",
                           "DROP_CONTROL_A_DRAWN_SIDE_NO_ADMISSIBLE_START")}
    eligible, edge_stage = [], {}
    for i, r in enumerate(rows):
        g = r[ix["nearest_ensembl"]]
        if g not in nihcard_genes:
            drop["DROP_GENE_NOT_IN_NIHCARD"] += 1
            edge_stage[i] = "DROP_GENE_NOT_IN_NIHCARD"
            continue
        if gene_rowcount[g] > 1:
            drop["DROP_GENE_AMBIGUOUS_IN_NIHCARD"] += 1
            edge_stage[i] = "DROP_GENE_AMBIGUOUS_IN_NIHCARD"
            continue
        if not peaks.overlaps(r[ix["chrom"]], int(r[ix["distal_start_hg38"]]),
                              int(r[ix["distal_end_hg38"]])):
            drop["DROP_NO_CONSENSUS_PEAK_OVER_LINKED_DISTAL"] += 1
            edge_stage[i] = "DROP_NO_CONSENSUS_PEAK_OVER_LINKED_DISTAL"
            continue
        eligible.append(i)
    log(f"linked-side eligible: {len(eligible):,}  "
        f"(gene absent {drop['DROP_GENE_NOT_IN_NIHCARD']:,}, "
        f"ambiguous {drop['DROP_GENE_AMBIGUOUS_IN_NIHCARD']:,}, "
        f"no peak {drop['DROP_NO_CONSENSUS_PEAK_OVER_LINKED_DISTAL']:,})")

    # ------------------------------------------------------ STEP 2 exact controls
    A = EX.load_A_exact()
    if len(A) != N:
        raise Stop(f"A_exact covers {len(A)} edges, E2 has {N}")
    log(f"A_exact loaded and payload-hash verified for {len(A):,} edges")

    draws = {}
    for i in eligible:
        d = {}
        for which in ("A", "B"):
            ss = EX.subseed(i, which)
            rng = np.random.default_rng(ss)
            side = int(rng.choice([1, -1]))          # SIDE FIRST
            part = A[i].get(side, ([], []))
            n = EX.card_exact(part)
            if n == 0:
                d[which] = dict(ok=False, side=side, subseed=ss,
                                admissible_start_count=0)
                continue
            EX.assert_disjoint(part, i, side)
            u = int(rng.integers(0, n))
            s19 = EX.pick_exact(part, u, i, side)
            d[which] = dict(ok=True, side=side, subseed=ss, admissible_start_count=n,
                            hg19_start=s19, hg19_end=s19 + W,
                            from_supplement=s19 in set(part[1]))
        draws[i] = d
        if not d["A"]["ok"]:
            drop["DROP_CONTROL_A_DRAWN_SIDE_NO_ADMISSIBLE_START"] += 1
            edge_stage[i] = "DROP_CONTROL_A_DRAWN_SIDE_NO_ADMISSIBLE_START"

    retained = [i for i in eligible if draws[i]["A"]["ok"]]
    log(f"retained primary: {len(retained):,}")

    total = sum(drop.values()) + len(retained)
    if total != N:
        raise Stop(f"funnel reconciliation {total} != {N}")
    if len(retained) > FULL_E2_CONTROL_A_AVAILABILITY:
        raise Stop(f"retained {len(retained)} exceeds full-E2 CONTROL_A availability "
                   f"{FULL_E2_CONTROL_A_AVAILABILITY}")

    # --------------------------- STEP 3 authoritative hg38 for selected controls
    bed_rows, keyed = [], {}
    for i in retained:
        for which in ("A", "B"):
            d = draws[i][which]
            if not d.get("ok"):
                continue
            nm = f"e{i}_{which}"
            bed_rows.append((rows[i][ix["chrom"]], d["hg19_start"], d["hg19_end"], nm))
            keyed[nm] = (i, which)
    log(f"verifying {len(bed_rows):,} selected controls through the real liftOver binary")
    mapped = B.run_lift(workdir, "ctl", bed_rows, None)

    fails = []
    for nm, (i, which) in keyed.items():
        m = mapped.get(nm)
        d = draws[i][which]
        if m is None:
            fails.append(dict(name=nm, reason="failed C3 exact mapping or round-trip"))
            continue
        c38, s38, e38 = m
        if c38 != rows[i][ix["chrom"]] or e38 - s38 != W:
            fails.append(dict(name=nm, reason="chromosome or length gate"))
            continue
        if not pu1.overlaps(c38, s38, e38):
            fails.append(dict(name=nm, reason="no hg38 PU.1 support"))
            continue
        if not peaks.overlaps(c38, s38, e38):
            fails.append(dict(name=nm, reason="no hg38 NIH-CARD consensus peak support"))
            continue
        d["hg38_start"], d["hg38_end"] = s38, e38
    if fails:
        raise Stop(f"{len(fails)} selected controls failed authoritative re-verification, "
                   f"which would mean A_exact contains an inadmissible start: {fails[:5]}")
    log("all selected controls independently re-verified against the real binary")

    # ------------------------------------------------- STEP 4 structural fields
    prom_of, degree = {}, defaultdict(int)
    for i, r in enumerate(rows):
        pk = f'{r[ix["chrom"]]}:{r[ix["promoter_start_hg38"]]}-{r[ix["promoter_end_hg38"]]}'
        prom_of[i] = pk
        degree[pk] += 1
    prom_index = {pk: k for k, pk in enumerate(sorted(degree))}

    def structural(chrom, s38, e38, d0):
        mid = (s38 + e38) // 2
        return dict(re_density=peaks.count_in(chrom, mid - RE_DENSITY_FLANK,
                                              mid + RE_DENSITY_FLANK),
                    anchor_frequency=anchors.frequency(chrom, s38, e38),
                    source_hg19_distance_bp=d0,
                    log_distance=(math.log(d0) if d0 > 0 else None))

    out_rows, strata = [], defaultdict(int)
    for i in retained:
        r = rows[i]
        c = r[ix["chrom"]]
        d0 = int(r[ix["contact_distance_bp_hg19_source"]])
        pk = prom_of[i]
        dA, dB = draws[i]["A"], draws[i]["B"]
        coincident = bool(dB.get("ok") and dA["hg19_start"] == dB["hg19_start"]
                          and dA["side"] == dB["side"])
        forced = bool(coincident and dA["admissible_start_count"] == 1)
        n = dA["admissible_start_count"]
        stratum = ("FORCED_SINGLETON_SUPPORT_1" if n == 1 else
                   "SMALL_RANDOMIZED_SUPPORT_2_TO_10" if n <= 10 else
                   "RANDOMIZED_SUPPORT_GT10")
        strata[stratum] += 1

        base = dict(promoter_key=pk, promoter_index=prom_index[pk],
                    promoter_degree=degree[pk], edge_index=i)
        ls, le = int(r[ix["distal_start_hg38"]]), int(r[ix["distal_end_hg38"]])
        out_rows.append(dict(**base, pair_key=f"e{i}|LINKED",
                             population="LINKED", control_role="NONE",
                             distal_chrom=c, distal_start_hg38=ls, distal_end_hg38=le,
                             **structural(c, ls, le, d0)))
        for which in ("A", "B"):
            d = draws[i][which]
            if not d.get("ok"):
                continue
            out_rows.append(dict(
                **base, pair_key=f"e{i}|CONTROL_{which}",
                population="CONTROL", control_role=which,
                distal_chrom=c, distal_start_hg38=d["hg38_start"],
                distal_end_hg38=d["hg38_end"],
                hg19_start=d["hg19_start"], hg19_end=d["hg19_end"],
                hg38_start=d["hg38_start"], hg38_end=d["hg38_end"],
                drawn_side=d["side"], subseed=d["subseed"],
                admissible_start_count=d["admissible_start_count"],
                control_draws_coincident=coincident,
                coincidence_structurally_forced=forced,
                from_supplement=d["from_supplement"],
                randomness_stratum=stratum,
                **structural(c, d["hg38_start"], d["hg38_end"], d0)))

    # ------------------------------------------------------------- invariants
    pks = [r["pair_key"] for r in out_rows]
    if len(pks) != len(set(pks)):
        raise Stop("pair_key not globally unique")
    bypk = defaultdict(set)
    for r in out_rows:
        bypk[r["promoter_key"]].add(r["promoter_degree"])
    bad = {k: v for k, v in bypk.items() if len(v) > 1}
    if bad:
        raise Stop(f"promoter_degree inconsistent within promoter_key: {list(bad)[:3]}")
    VALID = {("LINKED", "NONE"), ("CONTROL", "A"), ("CONTROL", "B")}
    badc = [r["pair_key"] for r in out_rows
            if (r["population"], r["control_role"]) not in VALID]
    if badc:
        raise Stop(f"invalid population/control_role: {badc[:3]}")
    missing = [f for f in ("promoter_key", "promoter_index", "pair_key", "population",
                           "control_role", "source_hg19_distance_bp", "log_distance",
                           "promoter_degree", "re_density", "anchor_frequency",
                           "distal_chrom", "distal_start_hg38", "distal_end_hg38")
               if any(f not in r for r in out_rows)]
    if missing:
        raise Stop(f"required V2 structural fields missing: {missing}")

    # ---------------------------------------------------------------- artifacts
    art = os.path.join(a.out_dir, "PHASE_A_V3_ROWS.jsonl.gz")
    with gzip.open(art, "wt", newline="\n") as fh:
        for r in out_rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    funnel_p = os.path.join(a.out_dir, "PHASE_A_V3_FUNNEL_PER_EDGE.jsonl.gz")
    with gzip.open(funnel_p, "wt", newline="\n") as fh:
        for i in range(N):
            fh.write(json.dumps(dict(edge_index=i,
                                     outcome=edge_stage.get(i, "RETAINED_PRIMARY")),
                                sort_keys=True) + "\n")

    # counts
    nB_ok = sum(1 for i in retained if draws[i]["B"].get("ok"))
    nB_no = len(retained) - nB_ok
    a_fail_b_ok = sum(1 for i in eligible
                      if not draws[i]["A"]["ok"] and draws[i]["B"].get("ok"))
    coinc = sum(1 for r in out_rows
                if r.get("control_role") == "A" and r.get("control_draws_coincident"))
    forced_c = sum(1 for r in out_rows
                   if r.get("control_role") == "A"
                   and r.get("coincidence_structurally_forced"))
    cards = np.array([r["admissible_start_count"] for r in out_rows
                      if r.get("control_role") == "A"])
    supp_ctl = sum(1 for r in out_rows if r.get("from_supplement"))
    rg = {rows[i][ix["nearest_ensembl"]] for i in retained}
    rp = {prom_of[i] for i in retained}
    dgs = sorted((degree[prom_of[i]] for i in retained), reverse=True)
    emass = None
    if dgs:
        cut = max(1, len(rp) // 4)
        pr = sorted(({p: sum(1 for i in retained if prom_of[i] == p) for p in rp}).items(),
                    key=lambda x: -x[1])
        emass = round(sum(v for _, v in pr[:cut]) / len(retained), 6)

    shard_h = {os.path.basename(p): sha_file(p)
               for p in sorted(__import__("glob").glob(
                   os.path.join(SUPP_DIR, "shard_*.receipt.json")))}
    rec = dict(
        schema="V64_NIH_CARD_STAGE3_PHASE_A_FULL_FUNNEL_V3", date="2026-09-30",
        governs=[PHASE_A_V2, FEATURE_V2],
        supersedes_interpretation=dict(
            withdrawn="Phase A accepted at 13,510",
            correct_name_for_that_number="FULL_E2_EXACT_CONTROL_A_AVAILABILITY",
            historical_producer="scripts/v64/nihcard_stage3_phase_a_exact_executor_v2.py",
            left_untouched=True),
        PRIMARY_FUNNEL=dict(
            primary_denominator=N,
            DROP_GENE_NOT_IN_NIHCARD=drop["DROP_GENE_NOT_IN_NIHCARD"],
            DROP_GENE_AMBIGUOUS_IN_NIHCARD=drop["DROP_GENE_AMBIGUOUS_IN_NIHCARD"],
            DROP_NO_CONSENSUS_PEAK_OVER_LINKED_DISTAL=drop[
                "DROP_NO_CONSENSUS_PEAK_OVER_LINKED_DISTAL"],
            LINKED_SIDE_ELIGIBLE_BEFORE_CONTROLS=len(eligible),
            DROP_CONTROL_A_DRAWN_SIDE_NO_ADMISSIBLE_START=drop[
                "DROP_CONTROL_A_DRAWN_SIDE_NO_ADMISSIBLE_START"],
            RETAINED_PRIMARY=len(retained),
            reconciles_to_denominator=(sum(drop.values()) + len(retained) == N),
            upper_bound_check=dict(
                full_e2_control_A_availability=FULL_E2_CONTROL_A_AVAILABILITY,
                retained_le_bound=len(retained) <= FULL_E2_CONTROL_A_AVAILABILITY,
                why_the_bound_holds_structurally="master seed and subseed derivation are "
                    "unchanged, so the control drawn for a given edge is identical to the "
                    "full-E2 run; adding upstream filters can only remove edges")),
        NULL_ARM=dict(CONTROL_B_AVAILABLE=nB_ok,
                      CONTROL_B_DRAWN_SIDE_NO_ADMISSIBLE_START=nB_no,
                      A_FAILED_B_SUCCEEDED_NOT_RESCUED=a_fail_b_ok,
                      A_PASSED_B_FAILED=nB_no,
                      CONTROL_A_B_COINCIDENT=coinc,
                      COINCIDENCE_STRUCTURALLY_FORCED=forced_c,
                      COINCIDENCE_CHANCE_CAPABLE=coinc - forced_c,
                      rule="CONTROL_B never alters primary retention"),
        RANDOMNESS_STRATA=dict(strata),
        RETAINED_STRUCTURE=dict(
            retained_edges=len(retained), retained_genes=len(rg),
            retained_promoters=len(rp),
            promoter_degree=dict(
                min=int(min(dgs)), median=int(np.median(dgs)),
                p75=int(np.percentile(dgs, 75)), max=int(max(dgs))) if dgs else {},
            top_quartile_promoters_hold_fraction_of_retained_edges=emass,
            controls_drawn_from_supplement=supp_ctl,
            CONTROL_A_admissible_set=dict(
                min=int(cards.min()), p25=int(np.percentile(cards, 25)),
                median=int(np.median(cards)), p75=int(np.percentile(cards, 75)),
                p95=int(np.percentile(cards, 95)), max=int(cards.max()),
                n_eq_1=int((cards == 1).sum()), n_le_10=int((cards <= 10).sum()))
            if len(cards) else {}),
        ARTIFACT_STRUCTURE=dict(
            LINKED_rows=sum(1 for r in out_rows if r["population"] == "LINKED"),
            CONTROL_A_rows=sum(1 for r in out_rows if r["control_role"] == "A"),
            CONTROL_B_rows=sum(1 for r in out_rows if r["control_role"] == "B"),
            total_rows=len(out_rows), promoter_count=len(rp),
            pair_key_unique=True, hierarchy_invariants_hold=True),
        PROVENANCE=dict(
            producer_path=os.path.relpath(os.path.abspath(__file__), os.getcwd()),
            producer_sha256=sha_file(os.path.abspath(__file__)),
            historical_executor_sha256=sha_file(EX.__file__.replace(".pyc", ".py")),
            builder_sha256=sha_file(B.__file__.replace(".pyc", ".py")),
            phase_a_v2_contract_sha256=sha_file(PHASE_A_V2),
            feature_artifact_v2_contract_sha256=sha_file(FEATURE_V2),
            e2_table_sha256=B.E2_SHA,
            nihcard_rna_h5ad=dict(path=RNA_H5AD, bytes=os.path.getsize(RNA_H5AD),
                                  md5_from_authentication="f628b17aab355f80b912e3c715543cbd"),
            nihcard_atac_h5ad=dict(path=ATAC_H5AD, bytes=os.path.getsize(ATAC_H5AD),
                                   md5_from_authentication="b71589e0033e391e2fe97c1ae3928a7f"),
            nihcard_peaks_bed=dict(path=PEAKS_BED, sha256=sha_file(PEAKS_BED),
                                   bound_to="ATAC var _index, exact line-for-line match"),
            nott_pu1_hg38_sha256=sha_file(PU1_BED),
            liftover_binary=dict(path=f"{B.WIN}/liftOver_v479",
                                 sha256=sha_file(f"{B.WIN}/liftOver_v479"),
                                 committed_in_git=False,
                                 note="binary is referenced by digest; it is NOT committed"),
            chain_hg19ToHg38_sha256=sha_file(f"{B.WIN}/hg19ToHg38.over.chain.gz"),
            chain_hg38ToHg19_sha256=sha_file(f"{B.WIN}/hg38ToHg19.over.chain.gz"),
            supplement_shard_receipt_sha256=shard_h,
            supplement_aggregate_binding=hashlib.sha256(
                "".join(shard_h[k] for k in sorted(shard_h)).encode()).hexdigest(),
            master_seed=EX.MASTER_SEED,
            frozen_constants=dict(window_bp=W, minmatch=B.MINMATCH,
                                  dist_tol_frac=B.DIST_TOL_FRAC,
                                  dist_tol_abs=B.DIST_TOL_ABS,
                                  re_density_flank_bp=RE_DENSITY_FLANK),
            emitted_artifacts={
                os.path.basename(p): dict(path=p, bytes=os.path.getsize(p),
                                          sha256=sha_file(p))
                for p in (art, funnel_p)},
            receipts_not_bound_here=[
                "RNA/ATAC pairing closeout receipt: not located in this worktree; "
                "recorded as NOT_BOUND rather than asserted"]),
        anchor_frequency_definition="number of DISTINCT E2 promoter_keys with at least "
                                    "one E2 distal partner overlapping the interval by "
                                    ">=1 bp; computed identically for LINKED, CONTROL_A "
                                    "and CONTROL_B. Exact-start multiplicity FORBIDDEN.",
        matrix_access=dict(rna_X_read=False, atac_X_read=False,
                           what_was_read="RNA var/gene_ids and ATAC var/_index only, "
                                         "both annotation metadata"),
        governance=dict(training="OFF", phase_B="STOPPED", stage_4="NOT_AUTHORISED",
                        td60="BLOCKED", Morabito="PROTECTED",
                        correspondence_opened=False),
        status="COMPLETE")
    rp_path = os.path.join(a.out_dir, "PHASE_A_V3_RECEIPT.json")
    with open(rp_path, "w", newline="\n") as fh:
        json.dump(rec, fh, indent=2)
    log(json.dumps(dict(PRIMARY_FUNNEL=rec["PRIMARY_FUNNEL"], NULL_ARM=rec["NULL_ARM"],
                        RANDOMNESS_STRATA=rec["RANDOMNESS_STRATA"],
                        ARTIFACT_STRUCTURE=rec["ARTIFACT_STRUCTURE"],
                        RETAINED_STRUCTURE=rec["RETAINED_STRUCTURE"]), indent=2))
    shutil.rmtree(workdir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Stop as e:
        print(f"\nSTOP: {e}")
        raise SystemExit(2)
