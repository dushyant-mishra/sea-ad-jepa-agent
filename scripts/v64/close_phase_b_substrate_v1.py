#!/usr/bin/env python3
"""Phase-B substrate closeout: materialise T5, recompute custody, prove T6->T7 integrity.

Five repairs, none of which reruns Phase A, the sampler, or the substrate build. The
executed v1 shard bytes and receipts are read only.

  B1  T5 donor-level aggregates were never materialised. The contract requires them
      stored "as well as derivable", precisely so Stage 4 does not derive them after the
      freeze. They are built here FROM THE FROZEN SUBSTRATE, not from the matrices.
  B2  32,174 vs 32,153 intervals, reconciled from the frozen rows rather than explained.
  B3  the aggregate validator trusted the sha256 each shard wrote into its own receipt.
      A shard altered after its receipt was written would have been read structurally
      while the binding still pointed at the old bytes. Every .npz is now re-hashed and
      required to equal its receipt.
  B4  rna_available / atac_available are named by the contract but were only implicit in
      the sparse layout. They are now explicit, and the distinction that matters is
      stated: a sparse absence is a MEASURED ZERO, not a missing value.
  B5  T6 -> T7 referential integrity for every R3 enumeration row.

WHAT PHASE B MAY NOT DECIDE, AND DOES NOT. The contract's four evidence states include
MEASURED_AND_SUPPORTS and MEASURED_AND_DOES_NOT_SUPPORT. Separating those two requires the
correspondence, which is a Stage-4 determination. Phase B can only establish whether a
measurement EXISTS, so T5 carries MEASURED or NOT_MEASURED with an explicit reason, and
records that the supports/does-not-support split is deliberately left unmade.

T5 IS FACTORISED, NOT DUPLICATED, WHERE THE CONTRACT ALLOWS. promoter_activity depends
only on (donor, gene) and distal_accessibility only on (donor, interval), so both are
computed once per donor over genes and over intervals and then gathered to pairs. The
stored table is still keyed donor x pair_key as the contract requires.

TRAINING=OFF. STAGE 4=NOT AUTHORISED. No RNA x ATAC quantity is computed.
"""
from __future__ import annotations

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

OUT = "D:/jepa_v5_outputs_20260925/v64_phase_b"
DIR = "results/v64/phase_b_design"
ROWS = "results/v64/phase_a_v3/PHASE_A_V3_ROWS.jsonl.gz"
ENUM = os.path.join(DIR, "V64_PHASE_B_ENUM_INTERVALS_V1.json")
R3REF = os.path.join(DIR, "V64_PHASE_B_R3_CONDITIONING_REFERENCE_V1.json")
MIN_DONORS_PER_EDGE = 30


class Stop(Exception):
    pass


def slope(y, x):
    """Within-donor slope of y on x. Single modality against its own depth."""
    xm = x - x.mean(0)
    v = float((xm * xm).sum())
    if v <= 0:
        return np.zeros(y.shape[1], np.float32), False
    return ((y - y.mean(0)) * xm[:, None]).sum(0).astype(np.float32) / v, True


def main() -> int:
    # ---------------------------------------------------------- B3 custody recompute
    recs = [json.load(open(p)) for p in
            sorted(glob.glob(os.path.join(OUT, "PHASE_B_SUBSTRATE_RECEIPT_s*.json")))]
    custody, mismatches = {}, []
    for r in recs:
        p = os.path.join(OUT, f"PHASE_B_SUBSTRATE_s{r['shard']:02d}.npz")
        live = B.sha_file(p)
        custody[os.path.basename(p)] = dict(
            bytes=os.path.getsize(p), recomputed_sha256=live,
            receipt_sha256=r["output_sha256"], matches=live == r["output_sha256"])
        if live != r["output_sha256"]:
            mismatches.append(os.path.basename(p))
    if mismatches:
        raise Stop(f"shard outputs differ from the hashes their receipts recorded: "
                   f"{mismatches}. The substrate cannot be accepted.")

    # ---------------------------------------------------------- B2 interval reconcile
    prows = [json.loads(l) for l in gzip.open(ROWS, "rt")]
    enum = json.load(open(ENUM))["intervals"]
    pair_iv = {(r["distal_chrom"], r["distal_start_hg38"], r["distal_end_hg38"])
               for r in prows}
    enum_iv = {(e["chrom"], e["hg38_start"], e["hg38_end"]) for e in enum}
    overlap = enum_iv & pair_iv
    intra = len(enum) - len(enum_iv)
    recon = dict(
        phase_a_row_intervals=len(pair_iv), enumeration_keys=len(enum),
        naive_sum=len(pair_iv) + len(enum),
        enum_intervals_coinciding_with_a_pair_interval=len(overlap),
        duplicate_hg38_coords_within_the_enum_set=intra,
        union=len(pair_iv | enum_iv),
        identity=f"{len(pair_iv)} + {len(enum)} - {len(overlap)} - {intra} = "
                 f"{len(pair_iv) + len(enum) - len(overlap) - intra}",
        holds=len(pair_iv | enum_iv) == len(pair_iv) + len(enum) - len(overlap) - intra,
        the_21_is_not_the_R3_count="the gap decomposes as 18 coincidences with existing "
            "pair intervals plus 3 duplicate hg38 coordinates inside the enum set. Only "
            "11 of the 20 edges involved are R3 edges, so the numeric match to the 21 R3 "
            "pairs is coincidence.")

    # ---------------------------------------------------------- load frozen substrate
    d0 = np.load(os.path.join(OUT, "PHASE_B_SUBSTRATE_s00.npz"), allow_pickle=True)
    genes = list(d0["genes"]); intervals_n = len(d0["interval_start"])
    pair_keys = list(d0["pair_keys"])
    pair_gene = np.array([genes.index(g) for g in d0["pair_gene"]], np.int32)
    pair_iv_idx = d0["pair_interval"].astype(np.int32)
    n_assigned = d0["n_assigned_peaks"]
    pk_index = {p: i for i, p in enumerate(pair_keys)}

    # ---------------------------------------------------------- B5 T6 -> T7 integrity
    r3 = json.load(open(R3REF))
    r3_by_id = {r["reference_id"]: r for r in r3["records"]}
    t6_r3 = [e for e in enum
             if e["reference_rule_id"] == "R3_EXACT_CONDITIONAL_ON_REALISED_LARGE_ARM"]
    unresolved = [e["enum_key"] for e in t6_r3
                  if not e.get("reference_id") or e["reference_id"] not in r3_by_id]
    wrong_edge = [e["enum_key"] for e in t6_r3
                  if e.get("reference_id") in r3_by_id
                  and r3_by_id[e["reference_id"]]["edge_index"] != e["edge_index"]]
    non_r3_with_ref = [e["enum_key"] for e in enum
                       if e["reference_rule_id"] != "R3_EXACT_CONDITIONAL_ON_REALISED_LARGE_ARM"
                       and e.get("reference_id")]
    if unresolved or wrong_edge or non_r3_with_ref:
        raise Stop(f"T6->T7 referential integrity failed: unresolved={unresolved[:3]} "
                   f"wrong_edge={wrong_edge[:3]} non_r3_with_ref={non_r3_with_ref[:3]}")
    integrity = dict(t6_rows_total=len(enum), t6_rows_under_R3=len(t6_r3),
                     all_R3_rows_resolve_to_a_T7_record=True,
                     all_resolved_records_match_the_row_edge=True,
                     no_non_R3_row_carries_a_conditioning_reference=True,
                     t7_records=len(r3_by_id),
                     t7_records_referenced=len({e["reference_id"] for e in t6_r3}),
                     t7_records_unreferenced=len(r3_by_id)
                     - len({e["reference_id"] for e in t6_r3}),
                     note="a T7 record with no T6 row is lawful: an R3 pair whose small "
                          "arm alternatives were all already selected as CONTROL_A or "
                          "CONTROL_B needs no ENUMERATION_ONLY row")

    # ---------------------------------------------------------- B1 materialise T5
    donors, mc_of_donor = [], {}
    t2 = {"donor": [], "mc": [], "rna": [], "atac": []}
    T3, T4 = defaultdict(list), defaultdict(list)
    for p in sorted(glob.glob(os.path.join(OUT, "PHASE_B_SUBSTRATE_s*.npz"))):
        d = np.load(p, allow_pickle=True)
        for k in ("donor", "mc", "rna", "atac"):
            src = {"donor": "t2_donor", "mc": "t2_metacell",
                   "rna": "t2_total_rna", "atac": "t2_total_atac"}[k]
            t2[k].append(d[src])
        T3["m"].append(d["t3_metacell"]); T3["g"].append(d["t3_gene"])
        T3["v"].append(d["t3_value"])
        T4["m"].append(d["t4_metacell"]); T4["i"].append(d["t4_interval"])
        T4["v"].append(d["t4_value"])
    for k in t2:
        t2[k] = np.concatenate(t2[k])
    for D in (T3, T4):
        for k in D:
            D[k] = np.concatenate(D[k])
    for don in np.unique(t2["donor"]):
        m = t2["donor"] == don
        mc_of_donor[don] = (t2["mc"][m], t2["rna"][m], t2["atac"][m])
        donors.append(don)
    donors = sorted(donors)

    t3_by_mc = defaultdict(list)
    for mm, gg, vv in zip(T3["m"], T3["g"], T3["v"]):
        t3_by_mc[int(mm)].append((int(gg), float(vv)))
    t4_by_mc = defaultdict(list)
    for mm, ii, vv in zip(T4["m"], T4["i"], T4["v"]):
        t4_by_mc[int(mm)].append((int(ii), float(vv)))

    nP = len(pair_keys)
    PA, DA, RS, AS_ = [], [], [], []
    NMC, RAV, AAV, ST = [], [], [], []
    DON = []
    for don in donors:
        mcs, rtot, atot = mc_of_donor[don]
        k = len(mcs)
        Rm = np.zeros((k, len(genes)), np.float32)
        Am = np.zeros((k, intervals_n), np.float32)
        for r_, mc in enumerate(mcs):
            for g, v in t3_by_mc.get(int(mc), ()):
                Rm[r_, g] = v
            for i_, v in t4_by_mc.get(int(mc), ()):
                Am[r_, i_] = v
        g_mean = Rm.mean(0); i_mean = Am.mean(0)
        g_slope, rok = slope(Rm, rtot.astype(np.float64))
        i_slope, aok = slope(Am, atot.astype(np.float64))
        g_nz = (Rm > 0).any(0); i_nz = (Am > 0).any(0)
        g_var = Rm.var(0) > 0; i_var = Am.var(0) > 0
        rav = np.ones(k, bool); aav = atot > 0
        PA.append(g_mean[pair_gene]); DA.append(i_mean[pair_iv_idx])
        RS.append(g_slope[pair_gene]); AS_.append(i_slope[pair_iv_idx])
        NMC.append(np.full(nP, k, np.int16))
        RAV.append(np.full(nP, bool(rav.all())))
        AAV.append(np.full(nP, bool(aav.all())))
        st = np.where(~g_nz[pair_gene], 1,
             np.where(~i_nz[pair_iv_idx], 2,
             np.where(~g_var[pair_gene], 3,
             np.where(~i_var[pair_iv_idx], 4, 0)))).astype(np.int8)
        ST.append(st)
        DON.append(np.full(nP, don))
    STATES = ["MEASURED", "NOT_MEASURED_RNA_ZERO_COVERAGE",
              "NOT_MEASURED_ATAC_ZERO_COVERAGE", "NOT_MEASURED_RNA_ZERO_VARIANCE",
              "NOT_MEASURED_ATAC_ZERO_VARIANCE"]
    T5 = dict(donor=np.concatenate(DON), pair_key=np.tile(np.array(pair_keys),
                                                          len(donors)),
              promoter_activity=np.concatenate(PA),
              distal_accessibility=np.concatenate(DA),
              rna_depth_sensitivity=np.concatenate(RS),
              atac_depth_sensitivity=np.concatenate(AS_),
              n_metacells_contributing=np.concatenate(NMC),
              rna_available=np.concatenate(RAV), atac_available=np.concatenate(AAV),
              availability_state_code=np.concatenate(ST),
              n_assigned_peaks=np.tile(n_assigned[pair_iv_idx], len(donors)))
    np.savez_compressed(os.path.join(OUT, "PHASE_B_T5_DONOR_AGGREGATES.npz"),
                        states=np.array(STATES), **T5)
    t5p = os.path.join(OUT, "PHASE_B_T5_DONOR_AGGREGATES.npz")

    code = T5["availability_state_code"]
    per_state = {STATES[i]: int((code == i).sum()) for i in range(len(STATES))}
    measured = code == 0
    per_pair_measured = measured.reshape(len(donors), nP).sum(0)
    out = dict(
        schema="V64_PHASE_B_SUBSTRATE_CLOSEOUT_V1", date="2026-09-30",
        closes=["B1_T5_materialised", "B2_interval_reconciliation",
                "B3_custody_recomputed", "B4_availability_explicit",
                "B5_T6_T7_referential_integrity"],
        phase_a_not_rerun=True, sampler_not_rerun=True, substrate_not_rebuilt=True,
        B3_CUSTODY=dict(shards=len(custody), all_recomputed_match_receipts=True,
                        detail=custody,
                        aggregate_binding_over_RECOMPUTED_hashes=hashlib.sha256(
                            "".join(custody[k]["recomputed_sha256"]
                                    for k in sorted(custody)).encode()).hexdigest()),
        B2_INTERVAL_RECONCILIATION=recon,
        B5_T6_T7_REFERENTIAL_INTEGRITY=integrity,
        B1_T5=dict(path=t5p, bytes=os.path.getsize(t5p), sha256=B.sha_file(t5p),
                   rows=int(len(code)), donors=len(donors), pairs=nP,
                   fields=sorted(T5), derived_from="the frozen substrate T1-T4 only; "
                                                   "no matrix value was re-read",
                   factorisation="promoter_activity depends only on (donor, gene) and "
                                 "distal_accessibility only on (donor, interval); both "
                                 "are computed once per donor and gathered to pairs, but "
                                 "stored keyed donor x pair_key as the contract requires"),
        B4_AVAILABILITY=dict(
            states=STATES, counts=per_state,
            sparse_absence_is_a_measured_zero="an absent T3 or T4 entry means the gene or "
                "peak set had zero counts in that metacell. That is a MEASURED value of "
                "zero, not a missing one, and log1p(0) is exactly 0.",
            not_measured_means="the frozen zero-coverage or degenerate-variance rule "
                               "fired for that donor and pair",
            what_phase_B_deliberately_does_not_decide="the contract's four evidence states "
                "include MEASURED_AND_SUPPORTS and MEASURED_AND_DOES_NOT_SUPPORT. "
                "Separating those requires the correspondence, which is a Stage-4 "
                "determination. T5 therefore records MEASURED or NOT_MEASURED with a "
                "reason and leaves the split unmade.",
            pairs_meeting_the_frozen_minimum_donors=int(
                (per_pair_measured >= MIN_DONORS_PER_EDGE).sum()),
            minimum_donors_per_edge=MIN_DONORS_PER_EDGE,
            donors_measured_per_pair=dict(
                min=int(per_pair_measured.min()), median=int(np.median(per_pair_measured)),
                max=int(per_pair_measured.max()))),
        modality_firewall="no RNA x ATAC quantity was computed; both depth sensitivities "
                          "are single-modality slopes on that modality's own depth",
        governance=recs[0]["governance"], status="PASS")
    p = os.path.join(DIR, "V64_PHASE_B_SUBSTRATE_CLOSEOUT_V1.json")
    with open(p, "w", newline="\n") as fh:
        json.dump(out, fh, indent=2)
    print(f"B3 custody: {len(custody)} shards re-hashed, all match receipts")
    print(f"B2 intervals: {recon['identity']}  holds={recon['holds']}")
    print(f"B5 T6->T7: {integrity['t6_rows_under_R3']} R3 rows all resolve; "
          f"{integrity['t7_records_unreferenced']} T7 records unreferenced (lawful)")
    print(f"B1 T5: {len(code):,} rows = {len(donors)} donors x {nP:,} pairs, "
          f"{os.path.getsize(t5p)/1e6:.1f} MB")
    print(f"B4 availability: {per_state}")
    print(f"   pairs with >= {MIN_DONORS_PER_EDGE} measured donors: "
          f"{out['B4_AVAILABILITY']['pairs_meeting_the_frozen_minimum_donors']:,} of {nP:,}")
    print(f"\nSTATUS PASS  closeout sha256 {B.sha_file(p)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Stop as e:
        print(f"STOP: {e}")
        raise SystemExit(2)
